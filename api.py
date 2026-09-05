import asyncio
import logging
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from solders.pubkey import Pubkey

from wallet_comparison import compare_wallet_profiles
from wallet_intelligence_fast import build_wallet_profile
from wallet_profile import build_profile_summary

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
API_VERSION = "1.9.0"
BASE_DIR = Path(__file__).resolve().parent
DASHBOARD_FILE = BASE_DIR / "dashboard" / "index.html"

RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "20"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
ANALYSIS_TIMEOUT_SECONDS = int(os.getenv("ANALYSIS_TIMEOUT_SECONDS", "45"))
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "15"))
CACHE_MAX_ENTRIES = int(os.getenv("CACHE_MAX_ENTRIES", "100"))
DEFAULT_HISTORY_LIMIT = int(os.getenv("DEFAULT_HISTORY_LIMIT", "20"))
MAX_HISTORY_LIMIT = int(os.getenv("MAX_HISTORY_LIMIT", "100"))
DEFAULT_HISTORY_LIMIT = max(1, min(DEFAULT_HISTORY_LIMIT, MAX_HISTORY_LIMIT))
MAX_HISTORY_LIMIT = max(DEFAULT_HISTORY_LIMIT, MAX_HISTORY_LIMIT)

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
    "comparison_requests": 0,
    "comparison_success": 0,
    "comparison_errors": 0,
}

CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500",
    ).split(",")
    if origin.strip()
]

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())
logger = logging.getLogger("legecy-api")


class ErrorResponse(BaseModel):
    message: str = Field(description="Human-readable error message.")


class WalletProfileResponse(BaseModel):
    wallet: Optional[str] = Field(default=None, description="Analyzed Solana wallet address.")
    analysis: Dict[str, Any] = Field(default_factory=dict, description="Transaction coverage and analysis metadata.")
    activity: Dict[str, Any] = Field(default_factory=dict, description="Wallet activity and movement metrics.")
    swap_metrics: Dict[str, Any] = Field(default_factory=dict, description="Successful, failed and attempted swap metrics.")
    trading: Dict[str, Any] = Field(default_factory=dict, description="Trading activity and token-diversity metrics.")
    trade_performance: Dict[str, Any] = Field(default_factory=dict, description="Trade-level performance and P/L information when available.")
    behavior: Dict[str, Any] = Field(default_factory=dict, description="Derived wallet behavior signals.")
    protocols: Dict[str, Any] = Field(default_factory=dict, description="Protocol usage detected from analyzed transactions.")
    reputation: Dict[str, Any] = Field(default_factory=dict, description="Wallet reputation score and supporting signals.")
    smart_money: Dict[str, Any] = Field(default_factory=dict, description="Smart-money score, rating, confidence and signals.")
    data_confidence: Dict[str, Any] = Field(default_factory=dict, description="Coverage-based confidence of the wallet analysis.")
    generated_at: Optional[str] = Field(default=None, description="UTC timestamp when the normalized profile was generated.")
    cache: Dict[str, Any] = Field(default_factory=dict, description="Cache status for this API response.")


class WalletComparisonResponse(BaseModel):
    wallet_a: Optional[str] = Field(default=None, description="First analyzed Solana wallet.")
    wallet_b: Optional[str] = Field(default=None, description="Second analyzed Solana wallet.")
    winner: Dict[str, Any] = Field(default_factory=dict, description="Overall comparative winner and win counts.")
    composite: Dict[str, Any] = Field(default_factory=dict, description="Weighted comparative signal.")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Side-by-side intelligence metrics.")
    confidence: Dict[str, Any] = Field(default_factory=dict, description="Comparison confidence based on both wallet profiles.")


app = FastAPI(
    title="LEGECY Wallet Intelligence API",
    description=(
        "Public API for Solana wallet intelligence, reputation, trading behavior, "
        "data confidence, smart-money analysis and wallet comparison."
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
            request_id, request.method, request.url.path, response.status_code, duration_ms,
        )
        return response
    except Exception:
        duration_ms = (time.perf_counter() - start_time) * 1000
        _metrics["total_response_time_ms"] += duration_ms
        _metrics["responses_5xx"] += 1
        logger.exception(
            "request_id=%s method=%s path=%s status=500 duration_ms=%.2f",
            request_id, request.method, request.url.path, duration_ms,
        )
        raise


def validate_wallet_address(wallet_address: str) -> str:
    wallet_address = wallet_address.strip()
    if not wallet_address:
        raise HTTPException(status_code=400, detail={"message": "Wallet address is required."})
    try:
        Pubkey.from_string(wallet_address)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail={"message": "Invalid Solana wallet address."})
    return wallet_address


def check_rate_limit(request: Request) -> None:
    now = time.monotonic()
    client_ip = request.client.host if request.client else "unknown"
    window_start, request_count = _rate_limit_state.get(client_ip, (now, 0))
    if now - window_start >= RATE_LIMIT_WINDOW_SECONDS:
        window_start, request_count = now, 0
    if request_count >= RATE_LIMIT_REQUESTS:
        _metrics["rate_limit_rejections"] += 1
        retry_after = max(1, int(RATE_LIMIT_WINDOW_SECONDS - (now - window_start)))
        raise HTTPException(
            status_code=429,
            detail={"message": "Too many wallet analysis requests. Please try again later."},
            headers={"Retry-After": str(retry_after)},
        )
    _rate_limit_state[client_ip] = (window_start, request_count + 1)
    if len(_rate_limit_state) > 1000:
        cutoff = now - RATE_LIMIT_WINDOW_SECONDS
        for ip in [ip for ip, (started, _) in _rate_limit_state.items() if started < cutoff]:
            _rate_limit_state.pop(ip, None)


def _cache_key(wallet_address: str, history_limit: int):
    return f"{wallet_address}:{history_limit}"


def get_cached_wallet_profile(wallet_address: str, history_limit: int = DEFAULT_HISTORY_LIMIT):
    key = _cache_key(wallet_address, history_limit)
    cached = _wallet_cache.get(key)
    if cached is None:
        return None
    created_at, profile = cached
    if time.monotonic() - created_at >= CACHE_TTL_SECONDS:
        _wallet_cache.pop(key, None)
        return None
    return profile


def cache_wallet_profile(wallet_address: str, profile, history_limit: int = DEFAULT_HISTORY_LIMIT) -> None:
    key = _cache_key(wallet_address, history_limit)
    _wallet_cache[key] = (time.monotonic(), profile)
    if len(_wallet_cache) <= CACHE_MAX_ENTRIES:
        return
    oldest_key = min(_wallet_cache, key=lambda item: _wallet_cache[item][0])
    _wallet_cache.pop(oldest_key, None)


async def _analyze_for_compare(wallet_address: str, limit: int):
    cached = get_cached_wallet_profile(wallet_address, limit)
    if cached is not None:
        _metrics["cache_hits"] += 1
        return cached
    _metrics["cache_misses"] += 1
    profile = await build_wallet_profile(wallet_address, limit=limit)
    cache_wallet_profile(wallet_address, profile, limit)
    return profile


@app.get("/", tags=["Public"], summary="Open the LEGECY dashboard", description="Serve the public LEGECY wallet-intelligence dashboard.", response_description="The LEGECY dashboard HTML page.")
async def root():
    if DASHBOARD_FILE.exists():
        return FileResponse(DASHBOARD_FILE, media_type="text/html")
    return {"name": "LEGECY", "service": "Solana Wallet Intelligence API", "status": "online", "version": API_VERSION, "environment": APP_ENV}


@app.get("/api", tags=["Public"], summary="Get API information", description="Return service metadata and the currently deployed API version.", response_description="LEGECY API service information.")
async def api_info():
    return {"name": "LEGECY", "service": "Solana Wallet Intelligence API", "status": "online", "version": API_VERSION, "environment": APP_ENV}


@app.get("/health", tags=["Public"], summary="Check API health", description="Lightweight health check intended for monitoring and deployment systems.", response_description="Current API health status.")
async def health():
    return {"status": "ok", "service": "legecy-api", "version": API_VERSION, "environment": APP_ENV}


@app.get("/metrics", tags=["Public"], summary="Get production metrics", description="Return process-local operational metrics for requests, wallet analysis, comparison, cache behavior, rate limiting, errors and response latency.", response_description="Current LEGECY operational metrics.")
async def metrics():
    total = _metrics["requests_total"]
    wallet_requests = _metrics["wallet_analysis_requests"]
    return {
        "version": API_VERSION,
        "environment": APP_ENV,
        "requests": {
            "total": total,
            "2xx": _metrics["responses_2xx"],
            "4xx": _metrics["responses_4xx"],
            "5xx": _metrics["responses_5xx"],
            "average_response_time_ms": round(_metrics["total_response_time_ms"] / total if total else 0.0, 2),
        },
        "wallet_analysis": {
            "requests": wallet_requests,
            "success": _metrics["wallet_analysis_success"],
            "errors": _metrics["wallet_analysis_errors"],
            "timeouts": _metrics["wallet_analysis_timeouts"],
            "average_time_ms": round(_metrics["wallet_analysis_time_ms"] / wallet_requests if wallet_requests else 0.0, 2),
        },
        "comparison": {
            "requests": _metrics["comparison_requests"],
            "success": _metrics["comparison_success"],
            "errors": _metrics["comparison_errors"],
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
        "history": {"default_limit": DEFAULT_HISTORY_LIMIT, "max_limit": MAX_HISTORY_LIMIT},
    }


@app.get(
    "/wallet/{wallet_address}",
    tags=["Wallet Intelligence"],
    summary="Analyze a Solana wallet",
    description=(
        "Analyze a configurable number of recent on-chain transactions for a Solana wallet. "
        "The default history depth is 20 and the public API allows up to the configured maximum. "
        "Deeper analysis uses bounded concurrent RPC requests and contributes to the normalized "
        "activity, trading, behavior, reputation, smart-money and confidence profile."
    ),
    response_model=WalletProfileResponse,
    response_description="Stable normalized LEGECY wallet intelligence profile.",
    responses={
        200: {"description": "Wallet intelligence profile returned successfully."},
        400: {"model": ErrorResponse, "description": "The supplied wallet address or history limit is invalid."},
        429: {"model": ErrorResponse, "description": "The client exceeded the wallet-analysis request limit."},
        500: {"model": ErrorResponse, "description": "An unexpected wallet-analysis error occurred."},
        504: {"model": ErrorResponse, "description": "Wallet analysis exceeded the configured timeout."},
    },
)
async def analyze_wallet(
    wallet_address: str,
    request: Request,
    limit: int = Query(
        default=DEFAULT_HISTORY_LIMIT,
        ge=1,
        le=MAX_HISTORY_LIMIT,
        description="Number of recent transactions to analyze. Default is 20; up to the configured maximum is supported.",
    ),
):
    check_rate_limit(request)
    wallet_address = validate_wallet_address(wallet_address)
    _metrics["wallet_analysis_requests"] += 1
    cached_profile = get_cached_wallet_profile(wallet_address, limit)
    if cached_profile is not None:
        _metrics["cache_hits"] += 1
        _metrics["wallet_analysis_success"] += 1
        response = build_profile_summary(cached_profile)
        response["cache"] = {"status": "HIT", "ttl_seconds": CACHE_TTL_SECONDS, "history_limit": limit}
        return response
    _metrics["cache_misses"] += 1
    analysis_start = time.perf_counter()
    try:
        profile = await asyncio.wait_for(build_wallet_profile(wallet_address, limit=limit), timeout=ANALYSIS_TIMEOUT_SECONDS)
        _metrics["wallet_analysis_time_ms"] += (time.perf_counter() - analysis_start) * 1000
        _metrics["wallet_analysis_success"] += 1
        cache_wallet_profile(wallet_address, profile, limit)
        response = build_profile_summary(profile)
        response["cache"] = {"status": "MISS", "ttl_seconds": CACHE_TTL_SECONDS, "history_limit": limit}
        return response
    except HTTPException:
        _metrics["wallet_analysis_errors"] += 1
        raise
    except asyncio.TimeoutError:
        _metrics["wallet_analysis_timeouts"] += 1
        _metrics["wallet_analysis_errors"] += 1
        _metrics["wallet_analysis_time_ms"] += (time.perf_counter() - analysis_start) * 1000
        logger.warning("Wallet analysis timed out for wallet=%s limit=%s timeout_seconds=%s", wallet_address, limit, ANALYSIS_TIMEOUT_SECONDS)
        raise HTTPException(status_code=504, detail={"message": "Wallet analysis timed out. Please try again later."})
    except ValueError:
        _metrics["wallet_analysis_errors"] += 1
        _metrics["wallet_analysis_time_ms"] += (time.perf_counter() - analysis_start) * 1000
        raise HTTPException(status_code=400, detail={"message": "Unable to process the wallet address."})
    except Exception:
        _metrics["wallet_analysis_errors"] += 1
        _metrics["wallet_analysis_time_ms"] += (time.perf_counter() - analysis_start) * 1000
        logger.exception("Wallet analysis failed for wallet=%s limit=%s", wallet_address, limit)
        raise HTTPException(status_code=500, detail={"message": "Wallet analysis failed. Please try again later."})


@app.get(
    "/compare/{wallet_a}/{wallet_b}",
    tags=["Wallet Intelligence"],
    summary="Compare two Solana wallets",
    description=(
        "Analyze two Solana wallets with the same history depth and return a side-by-side "
        "comparison of smart-money score, reputation, trading activity, token diversity, "
        "swap performance, protocol diversity and confidence. The comparison is a derived "
        "on-chain intelligence signal, not a financial prediction."
    ),
    response_model=WalletComparisonResponse,
    response_description="LEGECY wallet-to-wallet intelligence comparison.",
    responses={
        200: {"description": "Wallet comparison returned successfully."},
        400: {"model": ErrorResponse, "description": "One or both wallet addresses or the history limit are invalid."},
        429: {"model": ErrorResponse, "description": "The client exceeded the wallet-analysis request limit."},
        500: {"model": ErrorResponse, "description": "Wallet comparison failed."},
        504: {"model": ErrorResponse, "description": "Wallet comparison exceeded the configured timeout."},
    },
)
async def compare_wallets(
    wallet_a: str,
    wallet_b: str,
    request: Request,
    limit: int = Query(
        default=DEFAULT_HISTORY_LIMIT,
        ge=1,
        le=MAX_HISTORY_LIMIT,
        description="Number of recent transactions to analyze for each wallet.",
    ),
):
    check_rate_limit(request)
    wallet_a = validate_wallet_address(wallet_a)
    wallet_b = validate_wallet_address(wallet_b)
    if wallet_a == wallet_b:
        raise HTTPException(status_code=400, detail={"message": "Wallet A and Wallet B must be different addresses."})
    _metrics["comparison_requests"] += 1
    try:
        profiles = await asyncio.wait_for(
            asyncio.gather(
                _analyze_for_compare(wallet_a, limit),
                _analyze_for_compare(wallet_b, limit),
            ),
            timeout=ANALYSIS_TIMEOUT_SECONDS,
        )
        normalized_a = build_profile_summary(profiles[0])
        normalized_b = build_profile_summary(profiles[1])
        result = compare_wallet_profiles(normalized_a, normalized_b)
        result["history_limit"] = limit
        result["generated_at"] = __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()
        _metrics["comparison_success"] += 1
        return result
    except HTTPException:
        _metrics["comparison_errors"] += 1
        raise
    except asyncio.TimeoutError:
        _metrics["comparison_errors"] += 1
        raise HTTPException(status_code=504, detail={"message": "Wallet comparison timed out. Please try again later."})
    except ValueError:
        _metrics["comparison_errors"] += 1
        raise HTTPException(status_code=400, detail={"message": "Unable to process the wallet addresses."})
    except Exception:
        _metrics["comparison_errors"] += 1
        logger.exception("Wallet comparison failed for wallet_a=%s wallet_b=%s", wallet_a, wallet_b)
        raise HTTPException(status_code=500, detail={"message": "Wallet comparison failed. Please try again later."})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api:app",
        host=os.getenv("API_HOST", "127.0.0.1"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=False,
    )
