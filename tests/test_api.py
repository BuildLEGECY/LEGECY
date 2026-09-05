import time

import pytest
from fastapi import HTTPException

import api


def test_validate_wallet_address_accepts_valid_address():
    wallet = "BC2JZCGY6sXbQdXoqNzxm7JZxf9Q1bue8Ue9rAgbdwA7"
    assert api.validate_wallet_address(wallet) == wallet


def test_validate_wallet_address_rejects_invalid_address():
    with pytest.raises(HTTPException) as exc_info:
        api.validate_wallet_address("not-a-solana-wallet")

    assert exc_info.value.status_code == 400


def test_wallet_cache_returns_fresh_profile():
    wallet = "cache-test-wallet"
    profile = {"wallet": wallet, "value": 123}

    original_ttl = api.CACHE_TTL_SECONDS
    try:
        api.CACHE_TTL_SECONDS = 15
        api._wallet_cache.clear()
        api.cache_wallet_profile(wallet, profile)

        assert api.get_cached_wallet_profile(wallet) == profile
    finally:
        api._wallet_cache.clear()
        api.CACHE_TTL_SECONDS = original_ttl


def test_wallet_cache_expires():
    wallet = "cache-expiry-wallet"
    profile = {"wallet": wallet}

    original_ttl = api.CACHE_TTL_SECONDS
    try:
        api.CACHE_TTL_SECONDS = 0
        api._wallet_cache.clear()
        api.cache_wallet_profile(wallet, profile)

        time.sleep(0.001)
        assert api.get_cached_wallet_profile(wallet) is None
    finally:
        api._wallet_cache.clear()
        api.CACHE_TTL_SECONDS = original_ttl


def test_wallet_cache_is_bounded():
    wallet_prefix = "bounded-wallet-"
    original_max = api.CACHE_MAX_ENTRIES
    try:
        api.CACHE_MAX_ENTRIES = 3
        api._wallet_cache.clear()

        for index in range(4):
            api.cache_wallet_profile(
                f"{wallet_prefix}{index}",
                {"index": index},
            )

        assert len(api._wallet_cache) == 3
        assert f"{wallet_prefix}0" not in api._wallet_cache
        assert f"{wallet_prefix}3" in api._wallet_cache
    finally:
        api._wallet_cache.clear()
        api.CACHE_MAX_ENTRIES = original_max
