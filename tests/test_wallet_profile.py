from wallet_profile import (
    build_profile_summary,
    save_profile,
    load_profile,
)


def sample_profile():
    return {
        "wallet": "TEST_WALLET",

        "total_transactions": 3,

        "decoded_activities": 3,

        "unavailable_transactions": 0,

        "statistics": {
            "buys": 1,
            "sells": 1,
            "token_swaps": 1,
            "swap_failed": 0,
            "liquidity_actions": 0,
            "transfers_received": 0,
            "transfers_sent": 0,
            "unknown": 0,

            "trading_activity": 3,

            "unique_tokens": 2,

            "tokens": [
                "TOKEN_A",
                "TOKEN_B",
            ],

            "total_sol_spent": 1.5,

            "total_sol_received": 2.0,

            "win_rate": None,

            "profit_loss": 0.0,

            "protocol_usage": {
                "Jupiter": 2,
                "Raydium": 1,
            },

            "trade_performance": {
                "trades": 3,
                "closed_trades": 2,
                "winning_trades": 1,
                "losing_trades": 1,
                "win_rate": 50.0,
                "realized_profit_loss": 0.25,
                "open_positions": {
                    "TOKEN_B": [
                        {
                            "amount": 100,
                            "cost_asset": "SOL",
                            "cost_amount": 1.0,
                        }
                    ]
                },
            },

            "reputation_score": {
                "score": 75,
                "rating": "GOOD",
                "signals": [
                    "Active trader"
                ],
            },
        },
    }


def test_build_profile_summary():
    profile = sample_profile()

    summary = build_profile_summary(
        profile
    )

    assert summary["wallet"] == "TEST_WALLET"

    assert (
        summary["analysis"]["total_transactions"]
        == 3
    )

    assert (
        summary["activity"]["token_swaps"]
        == 1
    )

    assert (
        summary["trading"]["unique_tokens"]
        == 2
    )

    assert (
        summary["trade_performance"]["trades"]
        == 3
    )

    assert (
        summary["trade_performance"]["closed_trades"]
        == 2
    )

    assert (
        summary["trade_performance"]["winning_trades"]
        == 1
    )

    assert (
        summary["trade_performance"]["losing_trades"]
        == 1
    )

    assert (
        summary["trade_performance"]["win_rate"]
        == 50.0
    )

    assert (
        summary["trade_performance"][
            "realized_profit_loss"
        ]
        == 0.25
    )

    assert (
        "TOKEN_B"
        in summary["trade_performance"][
            "open_positions"
        ]
    )

    assert (
        summary["protocols"]["Jupiter"]
        == 2
    )

    assert (
        summary["reputation"]["score"]
        == 75
    )

    assert (
        summary["reputation"]["rating"]
        == "GOOD"
    )

    assert "generated_at" in summary


def test_save_profile(tmp_path):
    profile = sample_profile()

    filename = tmp_path / "profile.json"

    save_profile(
        profile,
        filename
    )

    assert filename.exists()

    with open(
        filename,
        "r",
        encoding="utf-8"
    ) as file:
        data = __import__(
            "json"
        ).load(file)

    assert (
        data["wallet"]
        == "TEST_WALLET"
    )

    assert (
        data["trade_performance"][
            "realized_profit_loss"
        ]
        == 0.25
    )


def test_load_profile(tmp_path):
    profile = sample_profile()

    filename = tmp_path / "profile.json"

    save_profile(
        profile,
        filename
    )

    loaded = load_profile(
        filename
    )

    assert (
        loaded["wallet"]
        == "TEST_WALLET"
    )

    assert (
        loaded["trading"][
            "trading_activity"
        ]
        == 3
    )

    assert (
        loaded["trade_performance"][
            "closed_trades"
        ]
        == 2
    )

    assert (
        loaded["trade_performance"][
            "win_rate"
        ]
        == 50.0
    )

    assert (
        loaded["reputation"]["rating"]
        == "GOOD"
    )