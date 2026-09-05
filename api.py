import asyncio
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from solders.pubkey import Pubkey

from wallet_intelligence_fast import build_wallet_profile
from wallet_profile import build_profile_summary


load_dotenv()


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
API_VERSION = "1.7.0"

BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = BASE_DIR / "dashboard" / "index.html"

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
ANALYSIS_TIMEOUT_SECONDS = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "45"))

CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "15"))
CACHE_MAX_ENTRIES = int(os.getenv("CACHE_MAX_ENTRIES", "100"))

_rate_limit_state = {}
_wallet_cache = {}

_metrics = {
    "requests_total": 0,
    "responses_2xx": 0,
    "responses_4xx": 0,
    "responses_5xx": 0,
    "wallet_analysis_requests": 0,
    "wallet_analysis_success": 0,
    "wallet_analysis_errors": 0,
    "wallet_analysis_timeouts": 0,
    "rate_limit_rejections": 0,
    "cache_hits": 0,
    "cache_misses": 0,
    "total_response_time_ms": 0.0,
    "wallet_analysis_time_ms": 0.0,
}

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


class ErrorResponse(BaseModel):
    message: str = Field(description="Human-readable error message.")


class WalletProfileResponse(BaseModel):
    """Stable public contract for the normalized wallet intelligence response."""

    wallet: Optional[str] = Field(
        default=None,
        description="Analyzed Solana wallet address.",
    )
    analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Transaction coverage and analysis metadata.",
    )
    activity: Dict[str, Any] = Field(
        default_factory=dict,
        description="Wallet activity and movement metrics.",
    )
    swap_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Successful, failed and attempted swap metrics.",
    )
    trading: Dict[str, Any] = Field(
        default_factory=dict,
        description="Trading activity and token-diversity metrics.",
    )
    trade_performance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Trade-level performance and P/L information when available.",
    )
    behavior: Dict[str, Any] = Field(
        default_factory=dict,
        description="Derived wallet behavior signals.",
    )
    protocols: Dict[str, Any] = Field(
        default_factory=dict,
        description="Protocol usage detected from analyzed transactions.",
    )
    reputation: Dict[str, Any] = Field(
        default_factory=dict,
        description="Wallet reputation score and supporting signals.",
    )
    smart_money: Dict[str, Any] = Field(
        default_factory=dict,
        description="Smart-money score, rating, confidence and signals.",
    )
    data_confidence: Dict[str, Any] = Field(
        default_factory=dict,
        description="Coverage-based confidence of the wallet analysis.",
    )
    generated_at: Optional[str] = Field(
        default=None,
        description="UTC timestamp when the normalized profile was generated.",
    )
    cache: Dict[str, Any] = Field(
        default_factory=dict,
        description="Cache status for this API response.",
    )


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
    _metrics["requests_total"] += 1

    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        _metrics["total_response_time_ms"] += duration_ms

        if 200 <= response.status_code < 300:
            _metrics["responses_2xx"] += 1
        elif 400 <= response.status_code < 500:
            _metrics["responses_4xx"] += 1
        elif response.status_code >= 500:
            _metrics["responses_5xx"] += 1

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
        _metrics["total_response_time_ms"] += duration_ms
        _metrics["responses_5xx"] += 1

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
        _metrics["rate_limit_rejections"] += 1
        retry_after = max(1, int(RATE_LIMIT_WINDOW_SECONDS - (now - window_start)))
        raise HTTPException(
            status_code=429,
            detail={
                "message": "Too many wallet analysis requests. Please try again later."
            },
            headers={"Retry-After": str(retry_after)},
        )

    _rate_limit_state[client_ip] = (window_start, request_count + 1)

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
    "/metrics",
    tags=["Public"],
    summary="Get production metrics",
    description=(
        "Return process-local operational metrics for requests, wallet analysis, "
        "cache behavior, rate limiting, errors and response latency."
    ),
    response_description="Current LEGECY operational metrics.",
)
async def metrics():
    requests_total = _metrics["requests_total"]
    average_response_time_ms = (
        _metrics["total_response_time_ms"] / requests_total
        if requests_total
        else 0.0
    )

    wallet_requests = _metrics["wallet_analysis_requests"]
    average_wallet_analysis_time_ms = (
        _metrics["wallet_analysis_time_ms"] / wallet_requests
        if wallet_requests
        else 0.0
    )

    return {
        "version": API_VERSION,
        "environment": APP_ENV,
        "requests": {
            "total": requests_total,
            "2xx": _metrics["responses_2xx"],
            "4xx": _metrics["responses_4xx"],
            "5xx": _metrics["responses_5xx"],
            "average_response_time_ms": round(average_response_time_ms, 2),
        },
        "wallet_analysis": {
            "requests": wallet_requests,
            "success": _metrics["wallet_analysis_success"],
            "errors": _metrics["wallet_analysis_errors"],
            "timeouts": _metrics["wallet_analysis_timeouts"],
            "average_time_ms": round(average_wallet_analysis_time_ms, 2),
        },
        "cache": {
            "hits": _metrics["cache_hits"],
            "misses": _metrics["cache_misses"],
            "ttl_seconds": CACHE_TTL_SECONDS,
            "max_entries": CACHE_MAX_ENTRIES,
        },
        "rate_limit": {
            "rejections": _metrics["rate_limit_rejections"],
            "requests_per_window": RATE_LIMIT_REQUESTS,
            "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
        },
    }


@app.get(
    "/wallet/{wallet_address}",
    tags=["Wallet Intelligence"],
    summary="Analyze a Solana wallet",
    description=(
        "Analyze recent on-chain activity for a Solana wallet and return a "
        "stable normalized intelligence profile. The response includes transaction "
        "coverage, activity metrics, swap and trading information, behavior, "
        "protocol usage, reputation, smart-money scoring and data confidence. "
        "The top-level response contract is documented in the OpenAPI schema. "
        "Repeated requests for the same wallet may be served from a short-lived "
        "cache, and transaction analysis uses bounded concurrent RPC requests."
    ),
    response_model=WalletProfileResponse,
    response_description="Stable normalized LEGECY wallet intelligence profile.",
    responses={
        200: {
            "description": "Wallet intelligence profile returned successfully.",
            "content": {
                "application/json": {
                    "example": {
                        "wallet": "BC2JZCGY6sXbQdXoqNzxm7JZxf9Q1bue8Ue9rAgbdwA7",
                        "analysis": {
                            "total_transactions": 20,
                            "requested_transactions": 20,
                            "analyzed_transactions": 18,
                            "unavailable_transactions": 2,
                        },
                        "activity": {"total_activities": 18, "buys": 7, "sells": 5},
                        "swap_metrics": {"successful_swaps": 10, "failed_swaps": 1},
                        "trading": {"trading_activity": 12, "unique_tokens": 8},
                        "trade_performance": {},
                        "behavior": {"classification": "ACTIVE DEX TRADER"},
                        "protocols": {"Jupiter": 8, "Raydium": 4},
                        "reputation": {"score": 72, "rating": "GOOD"},
                        "smart_money": {
                            "score": 68.4,
                            "rating": "GOOD",
                            "confidence": {"score": 90, "level": "HIGH"},
                        },
                        "data_confidence": {
                            "score": 90,
                            "coverage": 90,
                            "level": "HIGH",
                        },
                        "generated_at": "2026-09-05T00:00:00+00:00",
                        "cache": {"status": "MISS", "ttl_seconds": 15},
                    }
                }
            },
        },
        400: {
            "model": ErrorResponse,
            "description": "The supplied wallet address is invalid or cannot be processed.",
        },
        429: {
            "model": ErrorResponse,
            "description": "The client exceeded the wallet-analysis request limit.",
        },
        500: {
            "model": ErrorResponse,
            "description": "An unexpected wallet-analysis error occurred.",
        },
        504: {
            "model": ErrorResponse,
            "description": "Wallet analysis exceeded the configured timeout.",
        },
    },
)
async def analyze_wallet(wallet_address: str, request: Request):
    check_rate_limit(request)
    wallet_address = validate_wallet_address(wallet_address)
    _metrics["wallet_analysis_requests"] += 1

    cached_profile = get_cached_wallet_profile(wallet_address)
    if cached_profile is not None:
        _metrics["cache_hits"] += 1
        _metrics["wallet_analysis_success"] += 1
        response = build_profile_summary(cached_profile)
        response["cache"] = {"status": "HIT", "ttl_seconds": CACHE_TTL_SECONDS}
        return response

    _metrics["cache_misses"] += 1
    analysis_start = time.perf_counter()

    try:
        profile = await asyncio.wait_for(
            build_wallet_profile(
                wallet_address,
                limit=20,
            ),
            timeout=ANALYSIS_TIMEOUT_SECONDS,
        )

        _metrics["wallet_analysis_time_ms"] += (
            time.perf_counter() - analysis_start
        ) * 1000
        _metrics["wallet_analysis_success"] += 1
        cache_wallet_profile(wallet_address, profile)
        response = build_profile_summary(profile)
        response["cache"] = {"status": "MISS", "ttl_seconds": CACHE_TTL_SECONDS}
        return response

    except HTTPException:
        _metrics["wallet_analysis_errors"] += 1
        raise

    except asyncio.TimeoutError:
        _metrics["wallet_analysis_timeouts"] += 1
        _metrics["wallet_analysis_errors"] += 1
        _metrics["wallet_analysis_time_ms"] += (
            time.perf_counter() - analysis_start
        ) * 1000
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
        _metrics["wallet_analysis_errors"] += 1
        _metrics["wallet_analysis_time_ms"] += (
            time.perf_counter() - analysis_start
        ) * 1000
        raise HTTPException(
            status_code=400,
            detail={"message": "Unable to process the wallet address."},
        )

    except Exception:
        _metrics["wallet_analysis_errors"] += 1
        _metrics["wallet_analysis_time_ms"] += (
            time.perf_counter() - analysis_start
        ) * 1000
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
