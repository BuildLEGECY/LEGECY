from smart_money_ranking import rank_smart_wallets


def profile(wallet, smart, reputation, confidence):
    return {
        "wallet": wallet,
        "smart_money": {"score": smart},
        "reputation": {"score": reputation},
        "data_confidence": {"score": confidence},
        "behavior": {},
    }


def test_ranking_orders_by_quality_adjusted_score():
    result = rank_smart_wallets([
        profile("low", 60, 60, 50),
        profile("high", 80, 80, 100),
    ])
    assert result[0]["wallet"] == "high"
    assert result[0]["rank"] == 1
    assert result[1]["rank"] == 2


def test_min_confidence_filter():
    result = rank_smart_wallets([
        profile("low-confidence", 95, 90, 20),
        profile("trusted", 70, 70, 80),
    ], min_confidence=50)
    assert [item["wallet"] for item in result] == ["trusted"]


def test_ranking_score_is_bounded():
    result = rank_smart_wallets([profile("wallet", 150, 150, 150)])
    assert 0 <= result[0]["ranking_score"] <= 100
