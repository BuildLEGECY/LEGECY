def calculate_reputation_score(statistics):
    if not isinstance(statistics, dict):
        statistics = {}

    total = int(
        statistics.get("total_activities", 0) or 0
    )

    trading_activity = int(
        statistics.get("trading_activity", 0) or 0
    )

    unique_tokens = int(
        statistics.get("unique_tokens", 0) or 0
    )

    swap_failed = int(
        statistics.get("swap_failed", 0) or 0
    )

    token_swaps = int(
        statistics.get("token_swaps", 0) or 0
    )

    liquidity_actions = int(
        statistics.get("liquidity_actions", 0) or 0
    )

    protocols = statistics.get(
        "protocol_usage",
        {}
    ) or {}

    protocol_count = len(protocols)

    trade_performance = statistics.get(
        "trade_performance",
        {}
    ) or {}

    closed_trades = int(
        trade_performance.get(
            "closed_trades",
            0
        ) or 0
    )

    winning_trades = int(
        trade_performance.get(
            "winning_trades",
            0
        ) or 0
    )

    losing_trades = int(
        trade_performance.get(
            "losing_trades",
            0
        ) or 0
    )

    realized_pnl = float(
        trade_performance.get(
            "realized_profit_loss",
            0
        ) or 0
    )

    behavior = statistics.get(
        "behavior",
        {}
    ) or {}

    risk_level = str(
        behavior.get(
            "risk_level",
            ""
        )
    ).upper()

    score = 50.0
    signals = []

    # --------------------------------
    # Activity quality
    # --------------------------------

    if trading_activity >= 10:
        score += 10
        signals.append(
            "Highly active trader"
        )

    elif trading_activity >= 5:
        score += 7
        signals.append(
            "Active trader"
        )

    elif trading_activity >= 3:
        score += 4
        signals.append(
            "Regular trading activity"
        )

    elif trading_activity > 0:
        score += 2

    # --------------------------------
    # Token diversity
    # --------------------------------

    if unique_tokens >= 10:
        score += 8
        signals.append(
            "Very high token diversity"
        )

    elif unique_tokens >= 5:
        score += 6
        signals.append(
            "High token diversity"
        )

    elif unique_tokens >= 3:
        score += 3
        signals.append(
            "Moderate token diversity"
        )

    # --------------------------------
    # Protocol diversity
    # --------------------------------

    if protocol_count >= 4:
        score += 8
        signals.append(
            "Uses multiple known protocols"
        )

    elif protocol_count >= 2:
        score += 5
        signals.append(
            "Uses multiple trading protocols"
        )

    elif protocol_count == 1:
        score += 2
        signals.append(
            "Uses a known protocol"
        )

    # --------------------------------
    # Failed swaps
    #
    # Keep the existing behavior rate,
    # but reduce how strongly a tiny
    # sample affects reputation.
    # --------------------------------

    failed_rate = 0.0

    if token_swaps > 0:
        failed_rate = (
            swap_failed
            / token_swaps
        ) * 100

    # Number of observed swap events.
    observed_swaps = token_swaps + swap_failed

    if observed_swaps >= 20:
        risk_weight = 1.0

    elif observed_swaps >= 10:
        risk_weight = 0.75

    elif observed_swaps >= 5:
        risk_weight = 0.5

    else:
        risk_weight = 0.25

    if failed_rate >= 50:
        penalty = 20 * risk_weight
        score -= penalty

        signals.append(
            "High failed-swap rate"
        )

    elif failed_rate >= 25:
        penalty = 12 * risk_weight
        score -= penalty

        signals.append(
            "Elevated failed-swap rate"
        )

    elif failed_rate >= 10:
        penalty = 6 * risk_weight
        score -= penalty

        signals.append(
            "Some failed swap attempts"
        )

    elif swap_failed == 0 and token_swaps > 0:
        score += 5
        signals.append(
            "No failed swap attempts"
        )

    # --------------------------------
    # Trading performance
    # --------------------------------

    if closed_trades > 0:

        win_rate = (
            winning_trades
            / closed_trades
        ) * 100

        if win_rate >= 70:
            score += 12
            signals.append(
                "Strong trading win rate"
            )

        elif win_rate >= 50:
            score += 6
            signals.append(
                "Positive trading win rate"
            )

        elif win_rate < 30:
            score -= 8
            signals.append(
                "Low trading win rate"
            )

        if realized_pnl > 0:
            score += 8
            signals.append(
                "Positive realized P/L"
            )

        elif realized_pnl < 0:
            score -= 8
            signals.append(
                "Negative realized P/L"
            )

    # --------------------------------
    # Liquidity participation
    # --------------------------------

    if liquidity_actions > 0:
        score += 3
        signals.append(
            "Interacts with liquidity positions"
        )

    # --------------------------------
    # Behavior risk
    # --------------------------------

    if risk_level == "HIGH":
        score -= 4

    elif risk_level == "MODERATE":
        score -= 2

    elif risk_level == "LOW":
        score += 2

    # --------------------------------
    # Small analysis window
    # --------------------------------

    if total < 10:
        signals.append(
            "Limited analysis sample"
        )

    elif total <= 20:
        signals.append(
            "Reputation based on recent activity"
        )

    # --------------------------------
    # Clamp
    # --------------------------------

    score = max(
        0.0,
        min(100.0, score)
    )

    score = round(
        score,
        2
    )

    # --------------------------------
    # Rating
    # --------------------------------

    if score >= 80:
        rating = "EXCELLENT"

    elif score >= 65:
        rating = "GOOD"

    elif score >= 50:
        rating = "MODERATE"

    elif score >= 35:
        rating = "WEAK"

    else:
        rating = "POOR"

    return {
        "score": score,
        "rating": rating,
        "signals": signals,
    }