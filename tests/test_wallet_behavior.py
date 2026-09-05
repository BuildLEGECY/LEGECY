from wallet_behavior import calculate_wallet_behavior


def test_active_multi_protocol_trader():
    statistics = {
        "total_activities": 10,
        "token_swaps": 9,
        "swap_failed": 1,
        "trading_activity": 9,
        "unique_tokens": 5,
        "protocol_usage": {
            "Meteora DLMM": 3,
            "Orca Whirlpool": 3,
            "Raydium AMM v4": 3,
        },
        "liquidity_actions": 0,
        "transfers_received": 0,
        "transfers_sent": 0,
    }

    result = calculate_wallet_behavior(statistics)

    assert result["trading_style"] == "ACTIVE DEX TRADER"
    assert result["risk_level"] == "MODERATE"
    assert result["trading_frequency"] == "HIGH"
    assert result["token_diversity"] == "HIGH"
    assert result["protocol_diversity"] == "HIGH"
    assert result["failed_swap_rate"] == 11.11


def test_regular_trader():
    statistics = {
        "total_activities": 5,
        "token_swaps": 4,
        "swap_failed": 0,
        "trading_activity": 4,
        "unique_tokens": 3,
        "protocol_usage": {
            "Orca Whirlpool": 4,
            "Raydium CLMM": 1,
        },
    }

    result = calculate_wallet_behavior(statistics)

    assert result["trading_style"] == "REGULAR TRADER"
    assert result["risk_level"] == "LOW"
    assert result["trading_frequency"] == "MODERATE"
    assert result["token_diversity"] == "MODERATE"
    assert result["protocol_diversity"] == "MODERATE"


def test_high_failed_swap_rate():
    statistics = {
        "total_activities": 4,
        "token_swaps": 4,
        "swap_failed": 2,
        "trading_activity": 4,
        "unique_tokens": 2,
        "protocol_usage": {
            "Meteora DLMM": 4,
        },
    }

    result = calculate_wallet_behavior(statistics)

    assert result["risk_level"] == "HIGH"
    assert result["failed_swap_rate"] == 50.0


def test_low_activity_wallet():
    statistics = {
        "total_activities": 1,
        "token_swaps": 1,
        "swap_failed": 0,
        "trading_activity": 1,
        "unique_tokens": 1,
        "protocol_usage": {},
    }

    result = calculate_wallet_behavior(statistics)

    assert result["trading_style"] == "OCCASIONAL TRADER"
    assert result["trading_frequency"] == "LOW"
    assert result["token_diversity"] == "LOW"
    assert result["protocol_diversity"] == "NONE"


def test_empty_wallet():
    result = calculate_wallet_behavior({})

    assert result["trading_style"] == "LOW ACTIVITY"
    assert result["risk_level"] == "LOW"
    assert result["trading_frequency"] == "NONE"
    assert result["failed_swap_rate"] == 0.0
