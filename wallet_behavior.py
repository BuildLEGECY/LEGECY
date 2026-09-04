def calculate_wallet_behavior(statistics):
    if not isinstance(statistics, dict):
        statistics = {}

    total = int(
        statistics.get("total_activities", 0) or 0
    )

    swaps = int(
        statistics.get("token_swaps", 0) or 0
    )

    failed = int(
        statistics.get("swap_failed", 0) or 0
    )

    liquidity = int(
        statistics.get("liquidity_actions", 0) or 0
    )

    transfers = (
        int(statistics.get("transfers_received", 0) or 0)
        + int(statistics.get("transfers_sent", 0) or 0)
    )

    unique_tokens = int(
        statistics.get("unique_tokens", 0) or 0
    )

    protocols = statistics.get(
        "protocol_usage",
        {}
    ) or {}

    protocol_count = len(protocols)

    trading_activity = int(
        statistics.get("trading_activity", 0) or 0
    )

    # Use the proper swap failure rate when
    # it has already been calculated by statistics.
    if "swap_failure_rate" in statistics:
        try:
            failed_rate = float(
                statistics.get(
                    "swap_failure_rate",
                    0.0
                )
            )
        except (TypeError, ValueError):
            failed_rate = 0.0

    # Backward-compatible fallback for direct
    # wallet_behavior() calls and existing tests.
    elif swaps:
        failed_rate = round(
            (failed / swaps) * 100,
            2
        )

    else:
        failed_rate = 0.0

    signals = []

    # --------------------------------
    # Trading style
    # --------------------------------

    if trading_activity >= 8:
        trading_style = "ACTIVE DEX TRADER"
        signals.append(
            "Frequently performs trading activity"
        )

    elif trading_activity >= 3:
        trading_style = "REGULAR TRADER"
        signals.append(
            "Shows regular trading activity"
        )

    elif trading_activity > 0:
        trading_style = "OCCASIONAL TRADER"
        signals.append(
            "Shows occasional trading activity"
        )

    else:
        trading_style = "LOW ACTIVITY"
        signals.append(
            "Little or no trading activity"
        )

    # --------------------------------
    # Token diversity
    # --------------------------------

    if unique_tokens >= 5:
        token_diversity = "HIGH"
        signals.append(
            "Trades across many tokens"
        )

    elif unique_tokens >= 3:
        token_diversity = "MODERATE"
        signals.append(
            "Trades across several tokens"
        )

    else:
        token_diversity = "LOW"

    # --------------------------------
    # Protocol diversity
    # --------------------------------

    if protocol_count >= 3:
        protocol_diversity = "HIGH"
        signals.append(
            "Uses multiple trading protocols"
        )

    elif protocol_count >= 2:
        protocol_diversity = "MODERATE"
        signals.append(
            "Uses more than one trading protocol"
        )

    elif protocol_count == 1:
        protocol_diversity = "LOW"
        signals.append(
            "Primarily uses one known protocol"
        )

    else:
        protocol_diversity = "NONE"

    # --------------------------------
    # Trading frequency
    # --------------------------------

    if swaps >= 8:
        trading_frequency = "HIGH"

    elif swaps >= 3:
        trading_frequency = "MODERATE"

    elif swaps > 0:
        trading_frequency = "LOW"

    else:
        trading_frequency = "NONE"

    # --------------------------------
    # Risk level
    # --------------------------------

    if failed_rate >= 50:
        risk_level = "HIGH"
        signals.append(
            "High failed-swap rate"
        )

    elif failed_rate >= 10:
        risk_level = "MODERATE"
        signals.append(
            "Some failed swap attempts"
        )

    else:
        risk_level = "LOW"

    # --------------------------------
    # Other behavior
    # --------------------------------

    if liquidity > 0:
        signals.append(
            "Interacts with liquidity positions"
        )

    if transfers > 0:
        signals.append(
            "Uses wallet transfer activity"
        )

    return {
        "trading_style": trading_style,
        "risk_level": risk_level,
        "trading_frequency": trading_frequency,
        "token_diversity": token_diversity,
        "protocol_diversity": protocol_diversity,
        "failed_swap_rate": failed_rate,
        "signals": signals,
    }