from trade_engine import calculate_trade_performance
from wallet_behavior import calculate_wallet_behavior


def calculate_wallet_statistics(activities):
    if activities is None:
        activities = []

    total = len(activities)

    buys = 0
    sells = 0
    token_swaps = 0
    swap_failed = 0
    liquidity = 0

    transfers_received = 0
    transfers_sent = 0
    unknown = 0

    total_sol_spent = 0.0
    total_sol_received = 0.0

    protocols = {}
    tokens = set()

    for activity in activities:
        event = str(
            activity.get(
                "event",
                "UNKNOWN"
            )
        ).upper()

        if event == "POSSIBLE_BUY":
            buys += 1

        elif event == "POSSIBLE_SELL":
            sells += 1

        elif event == "TOKEN_SWAP":
            token_swaps += 1

        elif event == "SWAP_FAILED":
            swap_failed += 1

        elif event == "POSSIBLE_LIQUIDITY":
            liquidity += 1

        elif event == "TRANSFER_RECEIVED":
            transfers_received += 1

        elif event == "TRANSFER_SENT":
            transfers_sent += 1

        elif event == "UNKNOWN":
            unknown += 1

        sol_change = activity.get(
            "wallet_sol_change",
            0.0
        )

        try:
            sol_change = float(sol_change)
        except (TypeError, ValueError):
            sol_change = 0.0

        if sol_change < 0:
            total_sol_spent += abs(sol_change)

        elif sol_change > 0:
            total_sol_received += sol_change

        for token in activity.get(
            "token_changes",
            []
        ):
            if not isinstance(token, dict):
                continue

            mint = token.get("mint")

            if mint:
                tokens.add(str(mint))

        for protocol in activity.get(
            "protocols",
            []
        ):
            if isinstance(protocol, dict):
                name = protocol.get("name")
            else:
                name = str(protocol)

            if not name:
                continue

            protocols[name] = (
                protocols.get(name, 0) + 1
            )

    # --------------------------------
    # Swap metrics
    # --------------------------------

    successful_swaps = token_swaps
    failed_swaps = swap_failed

    swap_attempts = (
        successful_swaps
        + failed_swaps
    )

    if swap_attempts > 0:
        swap_failure_rate = round(
            (
                failed_swaps
                / swap_attempts
            ) * 100,
            2
        )
    else:
        swap_failure_rate = 0.0

    trading_activity = (
        buys
        + sells
        + token_swaps
    )

    # --------------------------------
    # Trade performance
    # --------------------------------

    trade_performance = (
        calculate_trade_performance(
            activities
        )
    )

    # --------------------------------
    # Behavior
    # --------------------------------

    behavior_input = {
        "total_activities": total,
        "token_swaps": token_swaps,
        "swap_failed": swap_failed,
        "swap_failure_rate": swap_failure_rate,
        "trading_activity": trading_activity,
        "unique_tokens": len(tokens),
        "protocol_usage": protocols,
        "liquidity_actions": liquidity,
        "transfers_received": transfers_received,
        "transfers_sent": transfers_sent,
    }

    behavior = calculate_wallet_behavior(
        behavior_input
    )

    return {
        "total_activities": total,

        "buys": buys,
        "sells": sells,
        "token_swaps": token_swaps,
        "swap_failed": swap_failed,

        "successful_swaps": successful_swaps,
        "failed_swaps": failed_swaps,
        "swap_attempts": swap_attempts,
        "swap_failure_rate": swap_failure_rate,

        "liquidity_actions": liquidity,

        "transfers_received": transfers_received,
        "transfers_sent": transfers_sent,

        "unknown": unknown,

        "trading_activity": trading_activity,

        "unique_tokens": len(tokens),
        "tokens": sorted(tokens),

        "total_sol_spent": round(
            total_sol_spent,
            9
        ),

        "total_sol_received": round(
            total_sol_received,
            9
        ),

        "trade_performance": trade_performance,

        "win_rate": trade_performance.get(
            "win_rate"
        ),

        "profit_loss": trade_performance.get(
            "realized_profit_loss",
            0.0
        ),

        "behavior": behavior,

        "reputation_score": None,

        "protocol_usage": protocols,
    }