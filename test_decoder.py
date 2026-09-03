from transaction_decoder import classify_transaction


def make_transaction(
    sol_before,
    sol_after,
    pre_tokens=None,
    post_tokens=None,
    programs=None,
    logs=None,
):
    return {
        "meta": {
            "preBalances": [sol_before],
            "postBalances": [sol_after],
            "preTokenBalances": pre_tokens or [],
            "postTokenBalances": post_tokens or [],
        },
        "programs": programs or [],
        "logs": logs or [],
    }


# ---------------------------------------------------------
# TEST 1 - BUY
# ---------------------------------------------------------

buy_transaction = make_transaction(
    2_000_000_000,
    1_000_000_000,
    post_tokens=[
        {
            "accountIndex": 1,
            "mint": "TEST_TOKEN",
            "uiTokenAmount": {"uiAmount": 100},
        }
    ],
)

result = classify_transaction(buy_transaction)

assert result["event"] == "POSSIBLE_BUY"

print("TEST 1 - BUY: PASS")


# ---------------------------------------------------------
# TEST 2 - TRANSFER RECEIVED
# ---------------------------------------------------------

received_transaction = make_transaction(
    2_000_000_000,
    2_000_000_000,
    post_tokens=[
        {
            "accountIndex": 1,
            "mint": "TEST_TOKEN",
            "uiTokenAmount": {"uiAmount": 100},
        }
    ],
)

result = classify_transaction(received_transaction)

assert result["event"] == "TRANSFER_RECEIVED"

print("TEST 2 - TRANSFER RECEIVED: PASS")


# ---------------------------------------------------------
# TEST 3 - SELL
# ---------------------------------------------------------

sell_transaction = make_transaction(
    1_000_000_000,
    2_000_000_000,
    pre_tokens=[
        {
            "accountIndex": 1,
            "mint": "TEST_TOKEN",
            "uiTokenAmount": {"uiAmount": 100},
        }
    ],
)

result = classify_transaction(sell_transaction)

assert result["event"] == "POSSIBLE_SELL"

print("TEST 3 - SELL: PASS")


# ---------------------------------------------------------
# TEST 4 - TRANSFER SENT
# ---------------------------------------------------------

sent_transaction = make_transaction(
    2_000_000_000,
    2_000_000_000,
    pre_tokens=[
        {
            "accountIndex": 1,
            "mint": "TEST_TOKEN",
            "uiTokenAmount": {"uiAmount": 100},
        }
    ],
)

result = classify_transaction(sent_transaction)

assert result["event"] == "TRANSFER_SENT"

print("TEST 4 - TRANSFER SENT: PASS")


# ---------------------------------------------------------
# TEST 5 - LIQUIDITY
# ---------------------------------------------------------

liquidity_transaction = make_transaction(
    2_000_000_000,
    1_500_000_000,

    pre_tokens=[
        {
            "accountIndex": 1,
            "mint": "TOKEN_A",
            "uiTokenAmount": {"uiAmount": 100},
        }
    ],

    post_tokens=[
        {
            "accountIndex": 1,
            "mint": "TOKEN_A",
            "uiTokenAmount": {"uiAmount": 0},
        },
        {
            "accountIndex": 1,
            "mint": "TOKEN_B",
            "uiTokenAmount": {"uiAmount": 200},
        }
    ],

    programs=["Raydium"],

    logs=[
        "Program log: Instruction: AddLiquidity"
    ],
)

result = classify_transaction(liquidity_transaction)

assert result["event"] == "POSSIBLE_LIQUIDITY"

print("TEST 5 - LIQUIDITY: PASS")


# ---------------------------------------------------------
# TEST 6 - UNKNOWN
# ---------------------------------------------------------

unknown_transaction = make_transaction(
    2_000_000_000,
    2_000_000_000,
)

result = classify_transaction(unknown_transaction)

assert result["event"] == "UNKNOWN"

print("TEST 6 - UNKNOWN: PASS")


# ---------------------------------------------------------
# FINAL RESULT
# ---------------------------------------------------------

print()
print("ALL DECODER TESTS PASSED")