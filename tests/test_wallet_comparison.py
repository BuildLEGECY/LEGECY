from wallet_comparison import compare_wallet_profiles


def profile(wallet, smart, reputation, activity, tokens, success, failure, protocols, confidence):
    return {
        "wallet": wallet,
        "smart_money": {"score": smart},
        "reputation": {"score": reputation},
        "trading": {"trading_activity": activity, "unique_tokens": tokens},
        "swap_metrics": {"successful_swaps": success, "swap_failure_rate": failure},
        "protocols": {name: 1 for name in protocols},
        "data_confidence": {"score": confidence, "level": "HIGH"},
    }


def test_comparison_selects_stronger_wallet():
    a = profile("A", 80, 75, 20, 10, 15, 2, ["Jupiter", "Raydium"], 95)
    b = profile("B", 60, 55, 10, 5, 8, 10, ["Jupiter"], 90)

    result = compare_wallet_profiles(a, b)

    assert result["winner"]["side"] == "A"
    assert result["winner"]["wallet"] == "A"
    assert result["metrics"]["smart_money"]["winner"] == "A"
    assert result["metrics"]["swap_failure_rate"]["winner"] == "A"


def test_comparison_uses_lower_confidence_as_comparison_confidence():
    a = profile("A", 70, 70, 10, 5, 8, 2, ["Jupiter"], 82)
    b = profile("B", 70, 70, 10, 5, 8, 2, ["Jupiter"], 61)

    result = compare_wallet_profiles(a, b)

    assert result["winner"]["side"] == "TIE"
    assert result["confidence"]["comparison"] == 61


def test_comparison_lower_failure_rate_wins():
    a = profile("A", 50, 50, 5, 3, 4, 1, ["Jupiter"], 90)
    b = profile("B", 50, 50, 5, 3, 4, 5, ["Jupiter"], 90)

    result = compare_wallet_profiles(a, b)

    assert result["metrics"]["swap_failure_rate"]["winner"] == "A"
