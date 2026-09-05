import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from solders.pubkey import Pubkey

_DEFAULT_WATCHLIST_FILE = Path("data/watchlist.json")
WATCHLIST_FILE = Path(os.getenv("WATCHLIST_FILE", str(_DEFAULT_WATCHLIST_FILE)))
WATCHLIST_DB_FILE = Path(os.getenv("WATCHLIST_DB_FILE", "data/watchlist.db"))
_LOCK = Lock()


def _using_legacy_json():
    return WATCHLIST_FILE != _DEFAULT_WATCHLIST_FILE or bool(os.getenv("WATCHLIST_FILE"))


def _ensure_json_storage():
    WATCHLIST_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not WATCHLIST_FILE.exists():
        WATCHLIST_FILE.write_text("[]", encoding="utf-8")


def _load_json():
    _ensure_json_storage()
    try:
        data = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError, TypeError):
        return []


def _save_json(items):
    _ensure_json_storage()
    temp = WATCHLIST_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(items, indent=2), encoding="utf-8")
    temp.replace(WATCHLIST_FILE)


def _connect():
    WATCHLIST_DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(WATCHLIST_DB_FILE, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=10000")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS watchlist (wallet TEXT PRIMARY KEY, label TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL)"
    )
    connection.commit()
    return connection


def _row_to_item(row):
    return {"wallet": row["wallet"], "label": row["label"], "created_at": row["created_at"]}


def _migrate_json_to_sqlite(connection):
    if not WATCHLIST_FILE.exists():
        return
    try:
        items = json.loads(WATCHLIST_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return
    if not isinstance(items, list) or not items:
        return
    existing = connection.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0]
    if existing:
        return
    rows = []
    for item in items:
        if not isinstance(item, dict):
            continue
        wallet = str(item.get("wallet", "")).strip()
        if wallet:
            rows.append((wallet, str(item.get("label", "") or "").strip()[:100], str(item.get("created_at", "") or datetime.now(timezone.utc).isoformat())))
    if rows:
        connection.executemany("INSERT OR IGNORE INTO watchlist(wallet, label, created_at) VALUES (?, ?, ?)", rows)
        connection.commit()


def _list_sqlite():
    connection = _connect()
    try:
        _migrate_json_to_sqlite(connection)
        rows = connection.execute("SELECT wallet, label, created_at FROM watchlist ORDER BY rowid ASC").fetchall()
        return [_row_to_item(row) for row in rows]
    finally:
        connection.close()


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
        return _load_json() if _using_legacy_json() else _list_sqlite()


def add_wallet(wallet: str, label: str = ""):
    wallet = validate_wallet(wallet)
    label = str(label or "").strip()[:100]
    with _LOCK:
        if _using_legacy_json():
            items = _load_json()
            for item in items:
                if item.get("wallet") == wallet:
                    return item, False
            item = {"wallet": wallet, "label": label, "created_at": datetime.now(timezone.utc).isoformat()}
            items.append(item)
            _save_json(items)
            return item, True
        connection = _connect()
        try:
            _migrate_json_to_sqlite(connection)
            existing = connection.execute("SELECT wallet, label, created_at FROM watchlist WHERE wallet = ?", (wallet,)).fetchone()
            if existing:
                return _row_to_item(existing), False
            created_at = datetime.now(timezone.utc).isoformat()
            connection.execute("INSERT INTO watchlist(wallet, label, created_at) VALUES (?, ?, ?)", (wallet, label, created_at))
            connection.commit()
            return {"wallet": wallet, "label": label, "created_at": created_at}, True
        finally:
            connection.close()


def remove_wallet(wallet: str):
    wallet = validate_wallet(wallet)
    with _LOCK:
        if _using_legacy_json():
            items = _load_json()
            remaining = [item for item in items if item.get("wallet") != wallet]
            removed = len(remaining) != len(items)
            if removed:
                _save_json(remaining)
            return removed
        connection = _connect()
        try:
            cursor = connection.execute("DELETE FROM watchlist WHERE wallet = ?", (wallet,))
            connection.commit()
            return cursor.rowcount > 0
        finally:
            connection.close()


def is_watched(wallet: str) -> bool:
    wallet = validate_wallet(wallet)
    return any(item.get("wallet") == wallet for item in list_watchlist())
