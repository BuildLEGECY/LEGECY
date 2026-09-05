from trade_engine import (
    SOL_MINT,
    normalize_asset,
    calculate_trade_performance,
)


def test_sol_mint_normalizes_to_sol():
    assert normalize_asset(SOL_MINT) == "SOL"


def test_wsol_normalizes_to_sol():
    assert normalize_asset("WSOL") == "SOL"


def test_normal_token_is_unchanged():
    assert normalize_asset("TOKEN_A") == "TOKEN_A"


def test_sol_to_token_creates_sol_cost_position():
    activities = [
        {
            "transaction_failed": False,
            "trade": {
                "input_asset": SOL_MINT,
                "input_amount": 1.0,
                "output_asset": "TOKEN_A",
                "output_amount": 100.0,
            },
        }
    ]

    result = calculate_trade_performance(activities)

    assert result["trades"] == 1
    assert "TOKEN_A" in result["open_positions"]

    position = result["open_positions"]["TOKEN_A"][0]

    assert position["amount"] == 100.0
    assert position["cost_asset"] == "SOL"
    assert position["cost_amount"] == 1.0


def test_token_to_sol_closes_position():
    activities = [
        {
            "transaction_failed": False,
            "trade": {
                "input_asset": SOL_MINT,
                "input_amount": 1.0,
                "output_asset": "TOKEN_A",
                "output_amount": 100.0,
            },
        },
        {
            "transaction_failed": False,
            "trade": {
                "input_asset": "TOKEN_A",
                "input_amount": 100.0,
                "output_asset": SOL_MINT,
                "output_amount": 1.5,
            },
        },
    ]

    result = calculate_trade_performance(activities)

    assert result["trades"] == 2
    assert result["closed_trades"] == 1
    assert result["winning_trades"] == 1
    assert result["losing_trades"] == 0
    assert result["breakeven_trades"] == 0
    assert result["win_rate"] == 100.0
    assert result["realized_profit_loss"] == 0.5
    assert "TOKEN_A" not in result["open_positions"]


def test_token_to_sol_loss():
    activities = [
        {
            "transaction_failed": False,
            "trade": {
                "input_asset": "SOL",
                "input_amount": 1.0,
                "output_asset": "TOKEN_A",
                "output_amount": 100.0,
            },
        },
        {
            "transaction_failed": False,
            "trade": {
                "input_asset": "TOKEN_A",
                "input_amount": 100.0,
                "output_asset": SOL_MINT,
                "output_amount": 0.7,
            },
        },
    ]

    result = calculate_trade_performance(activities)

    assert result["closed_trades"] == 1
    assert result["winning_trades"] == 0
    assert result["losing_trades"] == 1
    assert result["breakeven_trades"] == 0
    assert result["win_rate"] == 0.0
    assert result["realized_profit_loss"] == -0.3


def test_partial_fifo_sale():
    activities = [
        {
            "transaction_failed": False,
            "trade": {
                "input_asset": "SOL",
                "input_amount": 1.0,
                "output_asset": "TOKEN_A",
                "output_amount": 100.0,
            },
        },
        {
            "transaction_failed": False,
            "trade": {
                "input_asset": "SOL",
                "input_amount": 1.2,
                "output_asset": "TOKEN_A",
                "output_amount": 100.0,
            },
        },
        {
            "transaction_failed": False,
            "trade": {
                "input_asset": "TOKEN_A",
                "input_amount": 150.0,
                "output_asset": SOL_MINT,
                "output_amount": 1.8,
            },
        },
    ]

    result = calculate_trade_performance(activities)

    assert result["trades"] == 3
    assert result["closed_trades"] == 2
    assert result["realized_profit_loss"] == 0.2

    # First FIFO lot:
    # 100 TOKEN cost 1.0 SOL
    # 100 TOKEN sold proportionally for 1.2 SOL
    # Profit = 0.2 SOL
    #
    # Second FIFO lot:
    # 50 TOKEN cost 0.6 SOL
    # 50 TOKEN sold proportionally for 0.6 SOL
    # Profit = 0.0 SOL (breakeven)

    assert result["winning_trades"] == 1
    assert result["losing_trades"] == 0
    assert result["breakeven_trades"] == 1

    assert "TOKEN_A" in result["open_positions"]

    remaining = result["open_positions"]["TOKEN_A"]

    assert len(remaining) == 1
    assert remaining[0]["amount"] == 50.0
    assert remaining[0]["cost_asset"] == "SOL"
    assert remaining[0]["cost_amount"] == 0.6