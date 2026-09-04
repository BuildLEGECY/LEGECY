# LEGECY - Wallet Reputation
#
# Converts wallet statistics into a simple reputation score.


def calculate_reputation_score(statistics):
    """
    Calculate a reputation score from wallet behavior.

    The score is intentionally simple for now.
    Later we can make this much more sophisticated.
    """

    if not statistics:
        return {
            "score": 0.0,
            "rating": "UNKNOWN",
            "signals": []
        }

    score = 0.0
    signals = []

    # ---------------------------------------------------------
    # Trading activity
    # ---------------------------------------------------------

    buys = statistics.get("buys", 0)
    sells = statistics.get("sells", 0)
    token_swaps = statistics.get("token_swaps", 0)
    failed_swaps = statistics.get("swap_failed", 0)

    trading_activity = (
        buys +
        sells +
        token_swaps
    )

    if trading_activity > 0:
        score += 20
        signals.append("Active trader")

    if trading_activity >= 5:
        score += 10
        signals.append("High trading activity")

    # ---------------------------------------------------------
    # Successful vs failed swaps
    # ---------------------------------------------------------

    if token_swaps > 0:
        score += min(token_swaps * 2, 10)
        signals.append("Uses token swaps")

    if failed_swaps > 0:
        # Failed transactions are a small negative signal,
        # but they should not destroy the reputation score.
        penalty = min(failed_swaps * 2, 10)
        score -= penalty
        signals.append(f"{failed_swaps} failed swap attempt(s)")

    # ---------------------------------------------------------
    # Token diversity
    # ---------------------------------------------------------

    unique_tokens = statistics.get("unique_tokens", 0)

    if unique_tokens >= 2:
        score += 10
        signals.append("Moderate token diversity")

    if unique_tokens >= 5:
        score += 5
        signals.append("High token diversity")

    # ---------------------------------------------------------
    # Protocol usage
    # ---------------------------------------------------------

    protocol_usage = statistics.get("protocol_usage", {})

    if protocol_usage:
        score += 10
        signals.append("Uses known protocols")

    if len(protocol_usage) >= 3:
        score += 5
        signals.append("Uses multiple known protocols")

    # ---------------------------------------------------------
    # Buy / sell balance
    # ---------------------------------------------------------

    if buys > 0 and sells > 0:
        score += 10
        signals.append("Has both buy and sell activity")

    # ---------------------------------------------------------
    # Keep score inside 0-100
    # ---------------------------------------------------------

    score = max(0.0, min(100.0, score))
    score = round(score, 1)

    # ---------------------------------------------------------
    # Rating
    # ---------------------------------------------------------

    if score >= 80:
        rating = "HIGH"

    elif score >= 60:
        rating = "GOOD"

    elif score >= 40:
        rating = "MODERATE"

    elif score >= 20:
        rating = "LOW"

    else:
        rating = "UNKNOWN"

    return {
        "score": score,
        "rating": rating,
        "signals": signals
    }