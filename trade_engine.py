SOL_MINT = "So11111111111111111111111111111111111111112"
SOL_ASSET = "SOL"


def normalize_asset(asset):
    if not asset:
        return asset

    asset = str(asset)

    if asset == SOL_MINT:
        return SOL_ASSET

    if asset.upper() == "WSOL":
        return SOL_ASSET

    return asset


def calculate_trade_performance(activities):
    if not activities:
        return {
            "trades": 0,
            "closed_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "breakeven_trades": 0,
            "win_rate": None,
            "realized_profit_loss": 0.0,
            "closed_trade_details": [],
            "open_positions": {},
        }

    inventory = {}
    closed_trades = []
    valid_trades = 0

    for activity in activities:

        if activity.get("transaction_failed"):
            continue

        trade = activity.get("trade")

        if not trade:
            continue

        input_asset = normalize_asset(
            trade.get("input_asset")
        )

        output_asset = normalize_asset(
            trade.get("output_asset")
        )

        try:
            input_amount = float(
                trade.get("input_amount")
            )
            output_amount = float(
                trade.get("output_amount")
            )
        except (TypeError, ValueError):
            continue

        if (
            not input_asset
            or not output_asset
            or input_amount <= 0
            or output_amount <= 0
        ):
            continue

        valid_trades += 1

        remaining_input = input_amount

        if input_asset in inventory:

            while (
                remaining_input > 1e-12
                and inventory[input_asset]
            ):

                lot = inventory[input_asset][0]

                available = float(
                    lot["amount"]
                )

                if available <= 1e-12:
                    inventory[input_asset].pop(0)
                    continue

                consumed = min(
                    remaining_input,
                    available
                )

                fraction = consumed / available

                cost_amount = (
                    float(lot["cost_amount"])
                    * fraction
                )

                cost_asset = normalize_asset(
                    lot["cost_asset"]
                )

                proceeds = (
                    output_amount
                    * (
                        consumed / input_amount
                    )
                )

                if cost_asset == output_asset:

                    profit_loss = (
                        proceeds - cost_amount
                    )

                    closed_trades.append(
                        {
                            "asset": input_asset,
                            "amount": consumed,
                            "cost_asset": cost_asset,
                            "cost": cost_amount,
                            "proceeds_asset": output_asset,
                            "proceeds": proceeds,
                            "profit_loss": profit_loss,
                        }
                    )

                lot["amount"] = (
                    available - consumed
                )

                lot["cost_amount"] = (
                    float(lot["cost_amount"])
                    - cost_amount
                )

                remaining_input -= consumed

                if lot["amount"] <= 1e-12:
                    inventory[input_asset].pop(0)

        inventory.setdefault(
            output_asset,
            []
        )

        inventory[output_asset].append(
            {
                "amount": output_amount,
                "cost_asset": input_asset,
                "cost_amount": input_amount,
            }
        )

    realized_profit_loss = sum(
        trade["profit_loss"]
        for trade in closed_trades
    )

    winning_trades = sum(
        1
        for trade in closed_trades
        if trade["profit_loss"] > 1e-12
    )

    losing_trades = sum(
        1
        for trade in closed_trades
        if trade["profit_loss"] < -1e-12
    )

    breakeven_trades = sum(
        1
        for trade in closed_trades
        if abs(trade["profit_loss"]) <= 1e-12
    )

    if closed_trades:
        win_rate = (
            winning_trades
            / len(closed_trades)
        ) * 100
    else:
        win_rate = None

    open_positions = {}

    for asset, lots in inventory.items():

        remaining_lots = [
            lot
            for lot in lots
            if float(lot.get("amount", 0))
            > 1e-12
        ]

        if remaining_lots:
            open_positions[
                normalize_asset(asset)
            ] = remaining_lots

    return {
        "trades": valid_trades,
        "closed_trades": len(closed_trades),
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "breakeven_trades": breakeven_trades,
        "win_rate": (
            round(win_rate, 2)
            if win_rate is not None
            else None
        ),
        "realized_profit_loss": round(
            realized_profit_loss,
            9
        ),
        "closed_trade_details": closed_trades,
        "open_positions": open_positions,
    }