from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from watchlist import add_wallet, list_watchlist, remove_wallet

router = APIRouter(tags=["Watchlist"])


class WatchlistItem(BaseModel):
    wallet: str
    label: str = ""
    created_at: str


class WatchlistAddRequest(BaseModel):
    wallet: str = Field(min_length=32, max_length=64)
    label: str = Field(default="", max_length=100)


class WatchlistResponse(BaseModel):
    wallet: Optional[str] = None
    label: str = ""
    created_at: Optional[str] = None
    added: Optional[bool] = None


@router.get("/watchlist", response_model=List[WatchlistItem], summary="List watched wallets")
async def get_watchlist():
    return list_watchlist()


@router.post("/watchlist", response_model=WatchlistResponse, summary="Add a wallet to the watchlist")
async def create_watchlist_item(payload: WatchlistAddRequest):
    try:
        item, added = add_wallet(payload.wallet, payload.label)
        return {**item, "added": added}
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"message": str(error)})


@router.delete("/watchlist/{wallet}", summary="Remove a wallet from the watchlist")
async def delete_watchlist_item(wallet: str):
    try:
        removed = remove_wallet(wallet)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"message": str(error)})
    if not removed:
        raise HTTPException(status_code=404, detail={"message": "Wallet is not on the watchlist."})
    return {"wallet": wallet, "removed": True}
