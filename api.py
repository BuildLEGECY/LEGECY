import asyncio
import logging
import os
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from solders.pubkey import Pubkey

from wallet_intelligence_fast import build_wallet_profile
from wallet_profile import build_profile_summary


load_dotenv()


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
API_VERSION = "1.5.0"

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = BASE_DIR / "dashboard" / "index.html"

# Lightweight production protection. This intentionally uses only the
# standard library so deployment does not need another dependency.
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
ANALYSIS_TIMEOUT_SECONDS = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "45"))

# Short-lived in-memory cache for repeated wallet lookups. This avoids
# re-running the full RPC analysis when a dashboard/user requests the same
# wallet again within a short window.
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "15"))
CACHE_MAX_ENTRIES = int(os.getenv("CACHE_MAX_ENTRIES", "100"))

_rate_limit_state = {}
_wallet_cache = {}

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500",
    ).split(",")
    if origin.strip()
]


logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
)

logger = logging.getLogger("legecy-api")


app = FastAPI(
    title="LEGECY Wallet Intelligence API",
    description=(
        "Public API for Solana wallet intelligence, reputation, trading "
        "behavior, data confidence and smart-money analysis."
    ),
    version=API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    contact={"name": "LEGECY"},
    license_info={"name": "Project License"},
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.perf_counter()

    try:
        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-MS"] = f"{duration_ms:.2f}"

        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

        return response

    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.exception(
            "request_id=%s method=%s path=%s status=500 duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )

        raise


def validate_wallet_address(wallet_address: str) -> str:
    """Validate and normalize a Solana wallet address."""
    wallet_address = wallet_address.strip()

    if not wallet_address:
        raise HTTPException(
            status_code=400,
            detail={"message": "Wallet address is required."},
        )

    try:
        Pubkey.from_string(wallet_address)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid Solana wallet address."},
        )

    return wallet_address


def check_rate_limit(request: Request) -> None:
    """Apply a small per-client limit to expensive wallet analysis calls."""
    now = time.monotonic()
    client_ip = request.client.host if request.client else "unknown"

    window_start, request_count = _rate_limit_state.get(client_ip, (now, 0))

    if now - window_start >= RATE_LIMIT_WINDOW_SECONDS:
        window_start = now
        request_count = 0

    if request_count >= RATE_LIMIT_REQUESTS:
        retry_after = max(1, int(RATE_LIMIT_WINDOW_SECONDS - (now - window_start)))
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Too many wallet analysis requests. Please try again later."
            },
            headers={"Retry-After": str(retry_after)},
        )

    _rate_limit_state[client_ip] = (window_start, request_count + 1)

    # Prevent stale client entries from growing forever on long-running servers.
    if len(_rate_limit_state) > 1000:
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS
        stale = [
            ip
            for ip, (started, _) in _rate_limit_state.items()
            if started < cutoff
        ]
        for ip in stale:
            _rate_limit_state.pop(ip, None)


def get_cached_wallet_profile(wallet_address: str):
    """Return a fresh cached wallet profile, if one exists."""
    cached = _wallet_cache.get(wallet_address)
    if cached is None:
        return None

    created_at, profile = cached
    if time.monotonic() - created_at >= CACHE_TTL_SECONDS:
        _wallet_cache.pop(wallet_address, None)
        return None

    return profile


def cache_wallet_profile(wallet_address: str, profile) -> None:
    """Store a wallet profile and keep the in-memory cache bounded."""
    now = time.monotonic()
    _wallet_cache[wallet_address] = (now, profile)

    if len(_wallet_cache) <= CACHE_MAX_ENTRIES:
        return

    oldest_wallet = min(
        _wallet_cache,
        key=lambda wallet: _wallet_cache[wallet][0],
    )
    _wallet_cache.pop(oldest_wallet, None)


@app.get(
    "/",
    tags=["Public"],
    summary="Open the LEGECY dashboard",
    description="Serve the public LEGECY wallet-intelligence dashboard.",
    response_description="The LEGECY dashboard HTML page.",
)
async def root():
    """Serve the public LEGECY dashboard."""
    if DASHBOARD_FILE.exists():
        return FileResponse(DASHBOARD_FILE, media_type="text/html")

    return {
        "name": "LEGECY",
        "service": "Solana Wallet Intelligence API",
        "status": "online",
        "version": API_VERSION,
        "environment": APP_ENV,
    }


@app.get(
    "/api",
    tags=["Public"],
    summary="Get API information",
    description="Return service metadata and the currently deployed API version.",
    response_description="LEGECY API service information.",
)
async def api_info():
    return {
        "name": "LEGECY",
        "service": "Solana Wallet Intelligence API",
        "status": "online",
        "version": API_VERSION,
        "environment": APP_ENV,
    }


@app.get(
    "/health",
    tags=["Public"],
    summary="Check API health",
    description="Lightweight health check intended for monitoring and deployment systems.",
    response_description="Current API health status.",
)
async def health():
    return {
        "status": "ok",
        "service": "legecy-api",
        "version": API_VERSION,
        "environment": APP_ENV,
    }


@app.get(
    "/wallet/{wallet_address}",
    tags=["Wallet Intelligence"],
    summary="Analyze a Solana wallet",
    description=(
        "Analyze recent on-chain activity for a Solana wallet and return a "
        "normalized intelligence profile. The response can include transaction "
        "coverage, activity metrics, token and protocol information, trading "
        "performance, behavior signals, reputation, smart-money scoring and "
        "data-confidence information. Repeated requests for the same wallet "
        "may be served from a short-lived cache. Transaction analysis uses "
        "bounded concurrent RPC requests for better latency."
    ),
    response_description="Normalized LEGECY wallet intelligence profile.",
    responses={
        400: {
            "description": "The supplied wallet address is invalid or cannot be processed."
        },
        429: {
            "description": "The client exceeded the wallet-analysis request limit."
        },
        500: {
            "description": "An unexpected wallet-analysis error occurred."
        },
        504: {
            "description": "Wallet analysis exceeded the configured timeout."
        },
    },
)
async def analyze_wallet(wallet_address: str, request: Request):
    check_rate_limit(request)
    wallet_address = validate_wallet_address(wallet_address)

    cached_profile = get_cached_wallet_profile(wallet_address)
    if cached_profile is not None:
        response = build_profile_summary(cached_profile)
        response["cache"] = {"status": "HIT", "ttl_seconds": CACHE_TTL_SECONDS}
        return response

    try:
        profile = await asyncio.wait_for(
            build_wallet_profile(
                wallet_address,
                limit=20,
            ),
            timeout=ANALYSIS_TIMEOUT_SECONDS,
        )

        cache_wallet_profile(wallet_address, profile)
        response = build_profile_summary(profile)
        response["cache"] = {"status": "MISS", "ttl_seconds": CACHE_TTL_SECONDS}
        return response

    except HTTPException:
        raise

    except asyncio.TimeoutError:
        logger.warning(
            "Wallet analysis timed out for wallet=%s timeout_seconds=%s",
            wallet_address,
            ANALYSIS_TIMEOUT_SECONDS,
        )
        raise HTTPException(
            status_code=504,
            detail={
                "message": "Wallet analysis timed out. Please try again later.",
            },
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"message": "Unable to process the wallet address."},
        )

    except Exception:
        logger.exception(
            "Wallet analysis failed for wallet=%s",
            wallet_address,
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": "Wallet analysis failed. Please try again later.",
            },
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=False,
    )
