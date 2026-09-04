import json

from wallet_profile import build_profile_summary, save_profile, load_profile


def sample_profile():
    return {
        "wallet": "TEST_WALLET",
        "total_transactions": 3,
        "decoded_activities": 3,
        "unavailable_transactions": 0,
        "statistics": {
            "buys": 1,
            "sells": 1,
            "token_swaps": 1,
            "swap_failed": 0,
            "liquidity_actions": 0,
            "transfers_received": 0,
            "transfers_sent": 0,
            "unknown": 0,
            "trading_activity": 3,
            "unique_tokens": 2,
            "tokens": ["TOKEN_A", "TOKEN_B"],
            "total_sol_spent": 1.5,
            "total_sol_received": 2.0,
            "win_rate": None,
            "profit_loss": None,
            "protocol_usage": {
                "Jupiter": 2,
                "Raydium": 1
            },
            "reputation_score": {
                "score": 75,
                "rating": "GOOD",
                "signals": ["Active trader"]
            }
        }
    }


def test_build_profile_summary():
    profile = sample_profile()
    summary = build_profile_summary(profile)

    assert summary["wallet"] == "TEST_WALLET"
    assert summary["analysis"]["total_transactions"] == 3
    assert summary["activity"]["token_swaps"] == 1
    assert summary["trading"]["unique_tokens"] == 2
    assert summary["protocols"]["Jupiter"] == 2
    assert summary["reputation"]["score"] == 75
    assert summary["reputation"]["rating"] == "GOOD"
    assert "generated_at" in summary


def test_save_profile(tmp_path):
    profile = sample_profile()
    filename = tmp_path / "profile.json"

    save_profile(profile, filename)

    assert filename.exists()

    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)

    assert data["wallet"] == "TEST_WALLET"
    assert data["reputation"]["score"] == 75


def test_load_profile(tmp_path):
    profile = sample_profile()
    filename = tmp_path / "profile.json"

    save_profile(profile, filename)
    loaded = load_profile(filename)

    assert loaded["wallet"] == "TEST_WALLET"
    assert loaded["trading"]["trading_activity"] == 3
    assert loaded["reputation"]["rating"] == "GOOD"