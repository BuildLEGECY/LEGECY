# LEGECY - Wallet Statistics
#
# Converts decoded transaction activities into
# high-level wallet behavior statistics.


def calculate_wallet_statistics(activities):
    """
    Calculate behavioral statistics from decoded wallet activities.
    """

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
        event = str(activity.get("event", "UNKNOWN")).upper()

        # Activity counts
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

        # SOL movement
        sol_change = activity.get("wallet_sol_change", 0.0)

        try:
            sol_change = float(sol_change)
        except (TypeError, ValueError):
            sol_change = 0.0

        if sol_change < 0:
            total_sol_spent += abs(sol_change)

        elif sol_change > 0:
            total_sol_received += sol_change

        # Tokens
        for token in activity.get("token_changes", []):
            if not isinstance(token, dict):
                continue

            mint = token.get("mint")

            if mint:
                tokens.add(str(mint))

        # Protocols
        for protocol in activity.get("protocols", []):
            if isinstance(protocol, dict):
                name = protocol.get("name")
            else:
                name = str(protocol)

            if not name:
                continue

            protocols[name] = protocols.get(name, 0) + 1

    # All successful trading activity
    trading_activity = buys + sells + token_swaps

    return {
        "total_activities": total,

        "buys": buys,
        "sells": sells,
        "token_swaps": token_swaps,
        "swap_failed": swap_failed,

        "liquidity_actions": liquidity,

        "transfers_received": transfers_received,
        "transfers_sent": transfers_sent,

        "unknown": unknown,

        "trading_activity": trading_activity,

        "unique_tokens": len(tokens),
        "tokens": sorted(tokens),

        "total_sol_spent": round(total_sol_spent, 9),
        "total_sol_received": round(total_sol_received, 9),

        "protocol_usage": protocols,

        "win_rate": None,
        "profit_loss": None,

        "reputation_score": None,
    }