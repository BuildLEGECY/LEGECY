from wallet_statistics import calculate_wallet_statistics


def test_empty_statistics():
    result = calculate_wallet_statistics([])

    assert result["total_activities"] == 0
    assert result["trading_activity"] == 0
    assert result["unique_tokens"] == 0
    assert result["win_rate"] is None
    assert result["profit_loss"] == 0.0


def test_statistics_include_trade_performance():
    activities = [
        {
            "event": "TOKEN_SWAP",
            "transaction_failed": False,
            "wallet_sol_change": -0.1,
            "token_changes": [
                {
                    "mint": "TOKEN_A",
                    "change": -100,
                    "direction": "sent",
                },
                {
                    "mint": "TOKEN_B",
                    "change": 200,
                    "direction": "received",
                },
            ],
            "trade": {
                "input_asset": "TOKEN_A",
                "input_amount": 100,
                "output_asset": "TOKEN_B",
                "output_amount": 200,
            },
            "protocols": [
                {
                    "name": "Test Protocol"
                }
            ],
        }
    ]

    result = calculate_wallet_statistics(
        activities
    )

    assert result["token_swaps"] == 1
    assert result["trading_activity"] == 1
    assert result["unique_tokens"] == 2

    assert "trade_performance" in result
    assert result["trade_performance"]["trades"] == 1

    assert result["win_rate"] is None
    assert result["profit_loss"] == 0.0

    assert (
        result["protocol_usage"]["Test Protocol"]
        == 1
    )


def test_failed_swap_is_counted_but_not_traded():
    activities = [
        {
            "event": "SWAP_FAILED",
            "transaction_failed": True,
            "wallet_sol_change": -0.001,
            "token_changes": [],
            "trade": None,
            "protocols": [],
        }
    ]

    result = calculate_wallet_statistics(
        activities
    )

    assert result["swap_failed"] == 1
    assert result["trading_activity"] == 0
    assert result["trade_performance"]["trades"] == 0
    assert result["win_rate"] is None