import json

import watchlist


def test_add_list_and_remove_wallet(tmp_path, monkeypatch):
    storage = tmp_path / "watchlist.json"
    monkeypatch.setattr(watchlist, "WATCHLIST_FILE", storage)
    wallet = "11111111111111111111111111111111"

    item, added = watchlist.add_wallet(wallet, "Test wallet")
    assert added is True
    assert item["wallet"] == wallet
    assert item["label"] == "Test wallet"

    duplicate, added = watchlist.add_wallet(wallet, "Other label")
    assert added is False
    assert duplicate["label"] == "Test wallet"
    assert watchlist.is_watched(wallet) is True

    items = watchlist.list_watchlist()
    assert len(items) == 1
    assert json.loads(storage.read_text(encoding="utf-8"))[0]["wallet"] == wallet

    assert watchlist.remove_wallet(wallet) is True
    assert watchlist.remove_wallet(wallet) is False
    assert watchlist.list_watchlist() == []


def test_sqlite_storage_survives_new_connection(tmp_path, monkeypatch):
    monkeypatch.delenv("WATCHLIST_FILE", raising=False)
    monkeypatch.setattr(watchlist, "WATCHLIST_FILE", watchlist._DEFAULT_WATCHLIST_FILE)
    monkeypatch.setattr(watchlist, "WATCHLIST_DB_FILE", tmp_path / "watchlist.db")
    wallet = "11111111111111111111111111111111"

    item, added = watchlist.add_wallet(wallet, "Persistent wallet")
    assert added is True
    assert item["label"] == "Persistent wallet"

    # Simulate a fresh process by closing the existing database connection path
    # and reading through the public API again.
    assert watchlist.list_watchlist() == [item]

    assert watchlist.remove_wallet(wallet) is True
    assert watchlist.list_watchlist() == []


def test_invalid_wallet_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(watchlist, "WATCHLIST_FILE", tmp_path / "watchlist.json")
    try:
        watchlist.add_wallet("not-a-solana-wallet")
    except ValueError as error:
        assert "Invalid Solana wallet address" in str(error)
    else:
        raise AssertionError("invalid wallet should be rejected")
