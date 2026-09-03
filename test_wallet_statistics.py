from wallet_statistics import calculate_wallet_statistics


activities = [

    {
        "event": "POSSIBLE_BUY",
        "wallet_sol_change": -1.0,
        "token_changes": [
            {
                "mint": "TOKEN_A",
                "change": 100,
                "direction": "received"
            }
        ],
        "protocols": [
            {
                "name": "Raydium AMM v4"
            }
        ]
    },

    {
        "event": "POSSIBLE_SELL",
        "wallet_sol_change": 2.0,
        "token_changes": [
            {
                "mint": "TOKEN_A",
                "change": -100,
                "direction": "sent"
            }
        ],
        "protocols": [
            {
                "name": "Raydium AMM v4"
            }
        ]
    },

    {
        "event": "POSSIBLE_LIQUIDITY",
        "wallet_sol_change": -0.5,
        "token_changes": [
            {
                "mint": "TOKEN_B",
                "change": 50,
                "direction": "received"
            }
        ],
        "protocols": [
            {
                "name": "Orca Whirlpool"
            }
        ]
    }
]


result = calculate_wallet_statistics(
    activities
)


assert result["total_activities"] == 3
assert result["buys"] == 1
assert result["sells"] == 1
assert result["liquidity_actions"] == 1
assert result["trading_activity"] == 2
assert result["unique_tokens"] == 2
assert result["total_sol_spent"] == 1.5
assert result["total_sol_received"] == 2.0
assert result["protocol_usage"]["Raydium AMM v4"] == 2
assert result["protocol_usage"]["Orca Whirlpool"] == 1

print("WALLET STATISTICS TEST: PASS")
print()
print("Activities:", result["total_activities"])
print("Buys:", result["buys"])
print("Sells:", result["sells"])
print("Liquidity:", result["liquidity_actions"])
print("Unique tokens:", result["unique_tokens"])
print("SOL spent:", result["total_sol_spent"])
print("SOL received:", result["total_sol_received"])
print("Protocols:", result["protocol_usage"])