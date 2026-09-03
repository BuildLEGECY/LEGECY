# LEGECY - Wallet Statistics
#
# Converts decoded transaction activities into
# high-level wallet behavior statistics.


def calculate_wallet_statistics(activities):
    """
    Calculate basic behavioral statistics from
    decoded wallet activities.
    """

    if activities is None:
        activities = []

    total = len(activities)

    buys = 0
    sells = 0
    liquidity = 0
    transfers_received = 0
    transfers_sent = 0
    unknown = 0

    total_sol_spent = 0.0
    total_sol_received = 0.0

    protocols = {}

    tokens = set()

    # ---------------------------------------------------------
    # Process activities
    # ---------------------------------------------------------

    for activity in activities:

        event = activity.get(
            "event",
            "UNKNOWN"
        )

        # -----------------------------------------------------
        # Event counts
        # -----------------------------------------------------

        if event == "POSSIBLE_BUY":
            buys += 1

        elif event == "POSSIBLE_SELL":
            sells += 1

        elif event == "POSSIBLE_LIQUIDITY":
            liquidity += 1

        elif event == "TRANSFER_RECEIVED":
            transfers_received += 1

        elif event == "TRANSFER_SENT":
            transfers_sent += 1

        elif event == "UNKNOWN":
            unknown += 1

        # -----------------------------------------------------
        # SOL movement
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Token mints
        # -----------------------------------------------------

        for token in activity.get(
            "token_changes",
            []
        ):

            mint = token.get("mint")

            if mint:
                tokens.add(str(mint))

        # -----------------------------------------------------
        # Protocol usage
        # -----------------------------------------------------

        for protocol in activity.get(
            "protocols",
            []
        ):

            name = protocol.get(
                "name"
            )

            if not name:
                continue

            protocols[name] = (
                protocols.get(name, 0) + 1
            )

    # ---------------------------------------------------------
    # Trading activity
    # ---------------------------------------------------------

    trading_activity = (
        buys
        + sells
    )

    # ---------------------------------------------------------
    # Build profile
    # ---------------------------------------------------------

    return {

        "total_activities": total,

        "buys": buys,

        "sells": sells,

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

        "protocol_usage": protocols,

        # These stay None until we have
        # reliable trade pairing.
        "win_rate": None,

        "profit_loss": None,

        "reputation_score": None
    }