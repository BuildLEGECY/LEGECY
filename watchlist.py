import json
import os
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from solders.pubkey import Pubkey

WATCHLIST_FILE = Path(os.getenv("WATCHLIST_FILE", "data/watchlist.json"))
_LOCK = Lock()


def _ensure_storage():
    WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not WATCHLIST_FILE.exists():
        WATCHLIST_FILE.write_text("[]", encoding="utf-8")


def _load():
    _ensure_storage()
    try:
        data = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def _save(items):
    _ensure_storage()
    temp = WATCHLIST_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(items, indent=2), encoding="utf-8")
    temp.replace(WATCHLIST_FILE)


def validate_wallet(wallet: str) -> str:
    wallet = str(wallet).strip()
    if not wallet:
        raise ValueError("Wallet address is required.")
    try:
        Pubkey.from_string(wallet)
    except (ValueError, TypeError):
        raise ValueError("Invalid Solana wallet address.")
    return wallet


def list_watchlist():
    with _LOCK:
        return _load()


def add_wallet(wallet: str, label: str = ""):
    wallet = validate_wallet(wallet)
    label = str(label or "").strip()[:100]
    with _LOCK:
        items = _load()
        for item in items:
            if item.get("wallet") == wallet:
                return item, False
        item = {
            "wallet": wallet,
            "label": label,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        items.append(item)
        _save(items)
        return item, True


def remove_wallet(wallet: str):
    wallet = validate_wallet(wallet)
    with _LOCK:
        items = _load()
        remaining = [item for item in items if item.get("wallet") != wallet]
        removed = len(remaining) != len(items)
        if removed:
            _save(remaining)
        return removed


def is_watched(wallet: str) -> bool:
    wallet = validate_wallet(wallet)
    return any(item.get("wallet") == wallet for item in list_watchlist())
