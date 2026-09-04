import logging
import os
import time
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from solders.pubkey import Pubkey

from wallet_intelligence import build_wallet_profile
from wallet_profile import build_profile_summary


load_dotenv()


APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
API_VERSION = "1.1.0"

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
    description="Solana wallet intelligence, reputation and smart-money analysis.",
    version=API_VERSION,
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
    """
    Validate and normalize a Solana wallet address.
    """
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


@app.get("/")
async def root():
    return {
        "name": "LEGECY",
        "service": "Solana Wallet Intelligence API",
        "status": "online",
        "version": API_VERSION,
        "environment": APP_ENV,
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "legecy-api",
        "version": API_VERSION,
        "environment": APP_ENV,
    }


@app.get("/wallet/{wallet_address}")
async def analyze_wallet(wallet_address: str):
    wallet_address = validate_wallet_address(wallet_address)

    try:
        profile = await build_wallet_profile(
            wallet_address,
            limit=20,
        )

        return build_profile_summary(profile)

    except HTTPException:
        raise

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