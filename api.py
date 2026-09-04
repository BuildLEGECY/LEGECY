import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from wallet_intelligence import build_wallet_profile
from wallet_profile import build_profile_summary


load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://127.0.0.1:5500,http://localhost:5500",
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title="LEGECY Wallet Intelligence API",
    description="Solana wallet intelligence, reputation and smart-money analysis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "LEGECY",
        "service": "Solana Wallet Intelligence API",
        "status": "online",
        "version": "1.0.0",
        "environment": APP_ENV,
    }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "legecy-api",
        "environment": APP_ENV,
    }


@app.get("/wallet/{wallet_address}")
async def analyze_wallet(wallet_address: str):
    wallet_address = wallet_address.strip()

    if not wallet_address:
        raise HTTPException(
            status_code=400,
            detail={"message": "Wallet address is required."},
        )

    try:
        profile = await build_wallet_profile(
            wallet_address,
            limit=20,
        )

        return build_profile_summary(profile)

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid Solana wallet address."},
        )

    except Exception:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Wallet analysis failed.",
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
