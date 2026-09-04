import asyncio

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from wallet_intelligence import build_wallet_profile
from wallet_profile import build_profile_summary


app = FastAPI(
    title="LEGECY Wallet Intelligence API",
    description="Solana wallet intelligence, reputation and smart-money analysis.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "name": "LEGECY",
        "service": "Solana Wallet Intelligence API",
        "status": "online",
        "version": "1.0.0",
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "legecy-api",
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
        normalized = build_profile_summary(profile)
        return normalized

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={"message": "Invalid Solana wallet address."},
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "message": "Wallet analysis failed.",
                "error": str(exc),
            },
        )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )
