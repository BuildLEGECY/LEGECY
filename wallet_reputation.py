# LEGECY - Wallet Reputation
#
# Behavior-based wallet reputation scoring.
# This version does NOT estimate profit or win rate.


def calculate_reputation_score(statistics):
    """
    Calculate a behavior-based reputation score from 0 to 100.

    This score measures observable activity quality.
    It is NOT a prediction of future profitability.
    """

    if not statistics:
        return {
            "score": 0.0,
            "rating": "UNKNOWN",
            "signals": []
        }

    score = 0.0
    signals = []

    total = statistics.get(
        "total_activities",
        0
    )

    buys = statistics.get(
        "buys",
        0
    )

    sells = statistics.get(
        "sells",
        0
    )

    liquidity = statistics.get(
        "liquidity_actions",
        0
    )

    unknown = statistics.get(
        "unknown",
        0
    )

    unique_tokens = statistics.get(
        "unique_tokens",
        0
    )

    protocol_usage = statistics.get(
        "protocol_usage",
        {}
    )

    # ---------------------------------------------------------
    # Activity
    # ---------------------------------------------------------

    if total >= 10:

        score += 15

        signals.append(
            "Active wallet"
        )

    elif total >= 5:

        score += 10

        signals.append(
            "Moderately active wallet"
        )

    elif total > 0:

        score += 5

        signals.append(
            "Limited activity"
        )

    # ---------------------------------------------------------
    # Trading activity
    # ---------------------------------------------------------

    trading_activity = buys + sells

    if trading_activity >= 5:

        score += 20

        signals.append(
            "Strong trading activity"
        )

    elif trading_activity >= 2:

        score += 12

        signals.append(
            "Some trading activity"
        )

    elif trading_activity > 0:

        score += 6

        signals.append(
            "Limited trading activity"
        )

    # ---------------------------------------------------------
    # Buy / sell balance
    # ---------------------------------------------------------

    if buys > 0 and sells > 0:

        score += 15

        signals.append(
            "Both entries and exits observed"
        )

    elif buys > 0:

        score += 8

        signals.append(
            "Buy activity observed"
        )

    elif sells > 0:

        score += 8

        signals.append(
            "Sell activity observed"
        )

    # ---------------------------------------------------------
    # Token diversity
    # ---------------------------------------------------------

    if unique_tokens >= 10:

        score += 15

        signals.append(
            "High token diversity"
        )

    elif unique_tokens >= 3:

        score += 10

        signals.append(
            "Moderate token diversity"
        )

    elif unique_tokens > 0:

        score += 5

        signals.append(
            "Limited token diversity"
        )

    # ---------------------------------------------------------
    # Protocol usage
    # ---------------------------------------------------------

    protocol_count = len(
        protocol_usage
    )

    if protocol_count >= 3:

        score += 15

        signals.append(
            "Uses multiple known protocols"
        )

    elif protocol_count >= 2:

        score += 10

        signals.append(
            "Uses multiple protocols"
        )

    elif protocol_count == 1:

        score += 5

        signals.append(
            "Known protocol usage detected"
        )

    # ---------------------------------------------------------
    # Unknown activity penalty
    # ---------------------------------------------------------

    if total > 0:

        unknown_ratio = (
            unknown / total
        )

        if unknown_ratio >= 0.75:

            score -= 15

            signals.append(
                "High proportion of unknown activity"
            )

        elif unknown_ratio >= 0.50:

            score -= 8

            signals.append(
                "Moderate unknown activity"
            )

    # ---------------------------------------------------------
    # Liquidity activity
    # ---------------------------------------------------------

    if liquidity > 0:

        score += 5

        signals.append(
            "Liquidity activity observed"
        )

    # ---------------------------------------------------------
    # Clamp score
    # ---------------------------------------------------------

    score = max(
        0.0,
        min(
            100.0,
            score
        )
    )

    # ---------------------------------------------------------
    # Rating
    # ---------------------------------------------------------

    if score >= 80:

        rating = "HIGH"

    elif score >= 60:

        rating = "GOOD"

    elif score >= 40:

        rating = "MODERATE"

    elif score > 0:

        rating = "LOW"

    else:

        rating = "UNKNOWN"

    return {

        "score": round(
            score,
            2
        ),

        "rating": rating,

        "signals": signals
    }