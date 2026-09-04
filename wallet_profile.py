import json
from datetime import datetime, timezone


def build_profile_summary(profile):
    statistics = profile.get("statistics", {})
    reputation = statistics.get("reputation_score", {})

    return {
        "wallet": profile.get("wallet"),
        "analysis": {
            "total_transactions": profile.get("total_transactions", 0),
            "decoded_activities": profile.get("decoded_activities", 0),
            "unavailable_transactions": profile.get(
                "unavailable_transactions", 0
            ),
        },
        "activity": {
            "buys": statistics.get("buys", 0),
            "sells": statistics.get("sells", 0),
            "token_swaps": statistics.get("token_swaps", 0),
            "failed_swaps": statistics.get("swap_failed", 0),
            "liquidity_actions": statistics.get("liquidity_actions", 0),
            "transfers_received": statistics.get("transfers_received", 0),
            "transfers_sent": statistics.get("transfers_sent", 0),
            "unknown": statistics.get("unknown", 0),
        },
        "trading": {
            "trading_activity": statistics.get("trading_activity", 0),
            "unique_tokens": statistics.get("unique_tokens", 0),
            "tokens": statistics.get("tokens", []),
            "total_sol_spent": statistics.get("total_sol_spent", 0),
            "total_sol_received": statistics.get("total_sol_received", 0),
            "win_rate": statistics.get("win_rate"),
            "profit_loss": statistics.get("profit_loss"),
        },
        "protocols": statistics.get("protocol_usage", {}),
        "reputation": {
            "score": reputation.get("score", 0),
            "rating": reputation.get("rating", "UNKNOWN"),
            "signals": reputation.get("signals", []),
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def save_profile(profile, filename):
    summary = build_profile_summary(profile)

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)


def load_profile(filename):
    with open(filename, "r", encoding="utf-8") as file:
        return json.load(file)