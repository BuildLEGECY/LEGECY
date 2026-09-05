from wallet_reputation import calculate_reputation_score


statistics = {

    "total_activities": 10,

    "buys": 4,

    "sells": 3,

    "liquidity_actions": 1,

    "unknown": 2,

    "unique_tokens": 5,

    "protocol_usage": {
        "Raydium AMM v4": 4,
        "Orca Whirlpool": 3,
        "Jupiter Z": 2
    }
}


result = calculate_reputation_score(
    statistics
)


assert 0 <= result["score"] <= 100

assert result["rating"] in [
    "HIGH",
    "GOOD",
    "MODERATE",
    "LOW",
    "UNKNOWN"
]

assert len(result["signals"]) > 0


print("WALLET REPUTATION TEST: PASS")
print()
print("Score:", result["score"])
print("Rating:", result["rating"])
print("Signals:")

for signal in result["signals"]:

    print(
        " -",
        signal
    )