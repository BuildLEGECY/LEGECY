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
        api.cache_wallet_profile(wallet, profile, 20)

        assert api.get_cached_wallet_profile(wallet, 20) == profile
    finally:
        api._wallet_cache.clear()
        api.CACHE_TTL_SECONDS = original_ttl


def test_wallet_cache_keeps_history_depths_separate():
    wallet = "history-depth-wallet"
    short_profile = {"wallet": wallet, "limit": 20}
    deep_profile = {"wallet": wallet, "limit": 100}

    try:
        api._wallet_cache.clear()
        api.cache_wallet_profile(wallet, short_profile, 20)
        api.cache_wallet_profile(wallet, deep_profile, 100)

        assert api.get_cached_wallet_profile(wallet, 20) == short_profile
        assert api.get_cached_wallet_profile(wallet, 100) == deep_profile
    finally:
        api._wallet_cache.clear()


def test_wallet_cache_expires():
    wallet = "cache-expiry-wallet"
    profile = {"wallet": wallet}

    original_ttl = api.CACHE_TTL_SECONDS
    try:
        api.CACHE_TTL_SECONDS = 0
        api._wallet_cache.clear()
        api.cache_wallet_profile(wallet, profile, 20)

        time.sleep(0.001)
        assert api.get_cached_wallet_profile(wallet, 20) is None
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
                20,
            )

        assert len(api._wallet_cache) == 3
        assert f"{wallet_prefix}0:20" not in api._wallet_cache
        assert f"{wallet_prefix}3:20" in api._wallet_cache
    finally:
        api._wallet_cache.clear()
        api.CACHE_MAX_ENTRIES = original_max


def test_wallet_response_schema_documents_stable_top_level_fields():
    schema = api.app.openapi()
    response_schema = (
        schema["paths"]["/wallet/{wallet_address}"]["get"]
        ["responses"]["200"]["content"]["application/json"]["schema"]
    )

    assert response_schema["$ref"].endswith("#/components/schemas/WalletProfileResponse")

    properties = schema["components"]["schemas"]["WalletProfileResponse"]["properties"]
    expected_fields = {
        "wallet",
        "analysis",
        "activity",
        "swap_metrics",
        "trading",
        "trade_performance",
        "behavior",
        "protocols",
        "reputation",
        "smart_money",
        "data_confidence",
        "generated_at",
        "cache",
    }

    assert expected_fields.issubset(properties.keys())


def test_error_responses_use_error_schema():
    schema = api.app.openapi()
    responses = schema["paths"]["/wallet/{wallet_address}"]["get"]["responses"]

    for status_code in ("400", "429", "500", "504"):
        response = responses[status_code]
        assert response["content"]["application/json"]["schema"]["$ref"].endswith(
            "#/components/schemas/ErrorResponse"
        )


def test_wallet_endpoint_documents_history_limit():
    schema = api.app.openapi()
    operation = schema["paths"]["/wallet/{wallet_address}"]["get"]
    parameters = {item["name"]: item for item in operation["parameters"]}

    assert "limit" in parameters
    limit_schema = parameters["limit"]["schema"]
    assert limit_schema["default"] == api.DEFAULT_HISTORY_LIMIT
    assert limit_schema["maximum"] == api.MAX_HISTORY_LIMIT
    assert limit_schema["minimum"] == 1
