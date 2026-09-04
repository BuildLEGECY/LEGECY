from wallet_intelligence import build_trade_data


def test_token_to_token_trade():
    token_changes = [
        {
            "mint": "TOKEN_A",
            "change": -100.0,
            "direction": "sent",
        },
        {
            "mint": "TOKEN_B",
            "change": 250.0,
            "direction": "received",
        },
    ]

    trade = build_trade_data(
        token_changes,
        sol_change=0.0,
        transaction_failed=False
    )

    assert trade is not None
    assert trade["input_asset"] == "TOKEN_A"
    assert trade["input_amount"] == 100.0
    assert trade["output_asset"] == "TOKEN_B"
    assert trade["output_amount"] == 250.0


def test_failed_transaction_has_no_trade():
    token_changes = [
        {
            "mint": "TOKEN_A",
            "change": -100.0,
            "direction": "sent",
        },
        {
            "mint": "TOKEN_B",
            "change": 250.0,
            "direction": "received",
        },
    ]

    trade = build_trade_data(
        token_changes,
        sol_change=0.0,
        transaction_failed=True
    )

    assert trade is None


def test_incomplete_token_movement_has_no_trade():
    token_changes = [
        {
            "mint": "TOKEN_A",
            "change": -100.0,
            "direction": "sent",
        }
    ]

    trade = build_trade_data(
        token_changes,
        sol_change=0.0,
        transaction_failed=False
    )

    assert trade is None