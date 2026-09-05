def _number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def calculate_smart_money(statistics=None, behavior=None, reputation=None):
    statistics = statistics if isinstance(statistics, dict) else {}
    behavior = behavior if isinstance(behavior, dict) else {}
    reputation = reputation if isinstance(reputation, dict) else {}

    trading_activity = _number(statistics.get("trading_activity"))
    unique_tokens = _number(statistics.get("unique_tokens"))
    protocols = statistics.get("protocol_usage", {})
    protocol_count = len(protocols) if isinstance(protocols, dict) else 0

    token_swaps = _number(statistics.get("token_swaps"))
    failed_swaps = _number(statistics.get("swap_failed"))
    attempts = token_swaps + failed_swaps
    failure_rate = (failed_swaps / attempts * 100) if attempts else 0.0

    reputation_score = _number(reputation.get("score"), 50)

    activity_strength = min(trading_activity / 20.0, 1.0) * 25.0
    token_diversity = min(unique_tokens / 10.0, 1.0) * 15.0
    protocol_diversity = min(protocol_count / 5.0, 1.0) * 15.0
    reliability = (1.0 - min(failure_rate / 100.0, 1.0)) * 20.0
    reputation_contribution = (reputation_score - 50.0) * 0.20

    score = (
        25.0
        + activity_strength
        + token_diversity
        + protocol_diversity
        + reliability
        + reputation_contribution
    )

    positive_signals = []
    risk_signals = []

    if trading_activity >= 10:
        positive_signals.append("Active DEX trader")
    elif trading_activity >= 3:
        positive_signals.append("Meaningful trading activity")
    else:
        risk_signals.append("Limited trading activity")

    if unique_tokens >= 5:
        positive_signals.append("Broad token exposure")
    elif unique_tokens <= 1:
        risk_signals.append("Low token diversity")

    if protocol_count >= 3:
        positive_signals.append("High protocol diversity")
    elif protocol_count == 0:
        risk_signals.append("No protocol diversity observed")

    if failure_rate <= 10 and attempts:
        positive_signals.append("Reliable swap execution")
    elif failure_rate > 25:
        risk_signals.append("High swap failure rate")

    if reputation_score >= 75:
        positive_signals.append("Strong reputation signal")
    elif reputation_score < 40:
        risk_signals.append("Weak reputation signal")

    if behavior.get("trading_frequency") in {"HIGH", "high"}:
        positive_signals.append("High-frequency behavior")

    if behavior.get("protocol_diversity") in {"HIGH", "high"}:
        positive_signals.append("High protocol diversity behavior")

    confidence_data = statistics.get("data_confidence", {})
    if not isinstance(confidence_data, dict):
        confidence_data = {}

    # Missing confidence data must not be treated as perfect coverage.
    # A caller that does not provide coverage gets LOW confidence rather than
    # an artificially HIGH smart-money confidence signal.
    coverage = _number(confidence_data.get("coverage"), 0.0)
    coverage = max(0.0, min(100.0, coverage))

    score = max(0.0, min(100.0, score))

    if score >= 80:
        rating = "STRONG"
    elif score >= 65:
        rating = "GOOD"
    elif score >= 50:
        rating = "MODERATE"
    elif score >= 35:
        rating = "WEAK"
    else:
        rating = "LOW"

    if coverage >= 90:
        confidence_level = "HIGH"
    elif coverage >= 70:
        confidence_level = "GOOD"
    elif coverage >= 40:
        confidence_level = "LIMITED"
    else:
        confidence_level = "LOW"

    return {
        "score": round(score, 2),
        "rating": rating,
        "confidence": {
            "score": round(coverage, 2),
            "level": confidence_level,
        },
        "signals": positive_signals,
        "risk_signals": risk_signals,
        "metrics": {
            "trading_activity": trading_activity,
            "unique_tokens": unique_tokens,
            "protocol_count": protocol_count,
            "swap_failure_rate": round(failure_rate, 2),
            "reputation_score": round(reputation_score, 2),
            "coverage": round(coverage, 2),
        },
    }
