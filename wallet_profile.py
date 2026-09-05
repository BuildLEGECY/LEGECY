from datetime import datetime, timezone
import json
import os

from smart_money_engine import calculate_smart_money


# =========================================================
# DATA CONFIDENCE
# =========================================================

def calculate_data_confidence(
    requested_transactions,
    analyzed_transactions,
    unavailable_transactions,
):
    requested = max(int(requested_transactions or 0), 0)
    analyzed = max(int(analyzed_transactions or 0), 0)
    unavailable = max(int(unavailable_transactions or 0), 0)

    if requested == 0:
        return {
            "level": "NONE",
            "score": 0,
            "coverage": 0.0,
            "requested_transactions": 0,
            "analyzed_transactions": analyzed,
            "unavailable_transactions": unavailable,
        }

    coverage = (analyzed / requested) * 100

    if coverage >= 90:
        level = "HIGH"
    elif coverage >= 70:
        level = "GOOD"
    elif coverage >= 40:
        level = "LIMITED"
    else:
        level = "LOW"

    return {
        "level": level,
        "score": round(coverage, 2),
        "coverage": round(coverage, 2),
        "requested_transactions": requested,
        "analyzed_transactions": analyzed,
        "unavailable_transactions": unavailable,
    }


# =========================================================
# PROFILE SUMMARY
# =========================================================

def build_profile_summary(profile):
    if not isinstance(profile, dict):
        profile = {}

    # -----------------------------------------------------
    # Statistics
    # -----------------------------------------------------

    statistics = profile.get("statistics", {})

    if not isinstance(statistics, dict):
        statistics = {}

    # -----------------------------------------------------
    # Analysis
    # -----------------------------------------------------

    analysis = profile.get("analysis", {})

    if not isinstance(analysis, dict):
        analysis = {}

    total_transactions = profile.get(
        "total_transactions",
        analysis.get(
            "total_transactions",
            analysis.get(
                "requested_transactions",
                0,
            ),
        ),
    )

    analyzed_transactions = profile.get(
        "decoded_activities",
        analysis.get(
            "analyzed_transactions",
            0,
        ),
    )

    unavailable_transactions = profile.get(
        "unavailable_transactions",
        analysis.get(
            "unavailable_transactions",
            0,
        ),
    )

    requested_transactions = profile.get(
        "requested_transactions",
        analysis.get(
            "requested_transactions",
            total_transactions,
        ),
    )

    # -----------------------------------------------------
    # Data confidence
    # -----------------------------------------------------

    data_confidence = profile.get(
        "data_confidence"
    )

    if not isinstance(data_confidence, dict):
        data_confidence = calculate_data_confidence(
            requested_transactions,
            analyzed_transactions,
            unavailable_transactions,
        )

    # -----------------------------------------------------
    # Trade performance
    # -----------------------------------------------------

    trade_performance = profile.get(
        "trade_performance"
    )

    if not isinstance(trade_performance, dict):
        trade_performance = statistics.get(
            "trade_performance",
            {},
        )

    if not isinstance(trade_performance, dict):
        trade_performance = {}

    # -----------------------------------------------------
    # Reputation
    # -----------------------------------------------------

    reputation = profile.get(
        "reputation"
    )

    if not isinstance(reputation, dict):
        reputation = statistics.get(
            "reputation_score",
            {},
        )

    if not isinstance(reputation, dict):
        reputation = {}

    # -----------------------------------------------------
    # Activity
    # -----------------------------------------------------

    activity = profile.get(
        "activity"
    )

    if not isinstance(activity, dict):
        activity = {
            "total_activities": statistics.get(
                "total_activities",
                statistics.get(
                    "trading_activity",
                    0,
                ),
            ),
            "buys": statistics.get(
                "buys",
                0,
            ),
            "sells": statistics.get(
                "sells",
                0,
            ),
            "token_swaps": statistics.get(
                "token_swaps",
                0,
            ),
            "unique_tokens": statistics.get(
                "unique_tokens",
                0,
            ),
            "total_sol_spent": statistics.get(
                "total_sol_spent",
                0.0,
            ),
            "total_sol_received": statistics.get(
                "total_sol_received",
                0.0,
            ),
        }

    # -----------------------------------------------------
    # Swap metrics
    # -----------------------------------------------------

    swap_metrics = profile.get(
        "swap_metrics"
    )

    if not isinstance(swap_metrics, dict):
        successful_swaps = statistics.get(
            "successful_swaps",
            statistics.get(
                "token_swaps",
                0,
            ),
        )

        failed_swaps = statistics.get(
            "failed_swaps",
            statistics.get(
                "swap_failed",
                0,
            ),
        )

        swap_attempts = statistics.get(
            "swap_attempts",
            successful_swaps + failed_swaps,
        )

        swap_failure_rate = statistics.get(
            "swap_failure_rate"
        )

        if swap_failure_rate is None:
            if swap_attempts:
                swap_failure_rate = (
                    failed_swaps
                    / swap_attempts
                ) * 100
            else:
                swap_failure_rate = 0.0

        swap_metrics = {
            "successful_swaps": successful_swaps,
            "failed_swaps": failed_swaps,
            "swap_attempts": swap_attempts,
            "swap_failure_rate": round(
                float(swap_failure_rate),
                2,
            ),
        }

    # -----------------------------------------------------
    # Trading
    # -----------------------------------------------------

    trading = profile.get(
        "trading"
    )

    if not isinstance(trading, dict):
        trading = {
            "trading_activity": statistics.get(
                "trading_activity",
                0,
            ),
            "unique_tokens": statistics.get(
                "unique_tokens",
                0,
            ),
            "trades": statistics.get(
                "trading_activity",
                0,
            ),
        }

    # -----------------------------------------------------
    # Protocols
    # -----------------------------------------------------

    protocols = profile.get(
        "protocols"
    )

    if not isinstance(protocols, dict):
        protocols = statistics.get(
            "protocol_usage",
            {},
        )

    if not isinstance(protocols, dict):
        protocols = {}

    # -----------------------------------------------------
    # Behavior
    # -----------------------------------------------------

    behavior = profile.get(
        "behavior"
    )

    if not isinstance(behavior, dict):
        behavior = statistics.get(
            "behavior",
            {},
        )

    if not isinstance(behavior, dict):
        behavior = {}

    # -----------------------------------------------------
    # Smart Money Engine
    # -----------------------------------------------------
    #
    # Give the Smart Money Engine the same confidence
    # information used by the final profile.
    #

    smart_money_statistics = dict(statistics)
    smart_money_statistics["data_confidence"] = (
        data_confidence
    )

    # Always recalculate Smart Money from the final normalized inputs.
    # This prevents a stale Smart Money result from an earlier pipeline
    # stage from overriding the final data-confidence score.
    smart_money = calculate_smart_money(
        statistics=smart_money_statistics,
        behavior=behavior,
        reputation=reputation,
    )

    # -----------------------------------------------------
    # Generated timestamp
    # -----------------------------------------------------

    generated_at = profile.get(
        "generated_at"
    )

    if not generated_at:
        generated_at = datetime.now(
            timezone.utc
        ).isoformat()

    # -----------------------------------------------------
    # Final normalized profile
    # -----------------------------------------------------

    return {
        "wallet": profile.get(
            "wallet"
        ),

        "analysis": {
            **analysis,
            "total_transactions": int(
                total_transactions or 0
            ),
            "requested_transactions": int(
                requested_transactions or 0
            ),
            "analyzed_transactions": int(
                analyzed_transactions or 0
            ),
            "unavailable_transactions": int(
                unavailable_transactions or 0
            ),
        },

        "activity": activity,

        "swap_metrics": swap_metrics,

        "trading": trading,

        "trade_performance": trade_performance,

        "behavior": behavior,

        "protocols": protocols,

        "reputation": reputation,

        "smart_money": smart_money,

        "data_confidence": data_confidence,

        "generated_at": generated_at,
    }


# =========================================================
# BUILD WALLET PROFILE
# =========================================================

def build_wallet_profile(
    wallet,
    activities=None,
    requested_transactions=None,
):
    if activities is None:
        activities = []

    analyzed_transactions = len(
        activities
    )

    if requested_transactions is None:
        requested_transactions = analyzed_transactions

    requested_transactions = max(
        int(requested_transactions or 0),
        0,
    )

    unavailable_transactions = max(
        requested_transactions
        - analyzed_transactions,
        0,
    )

    from wallet_statistics import (
        calculate_wallet_statistics,
    )

    from wallet_reputation import (
        calculate_reputation_score,
    )

    statistics = calculate_wallet_statistics(
        activities
    )

    reputation = calculate_reputation_score(
        statistics
    )

    statistics["reputation_score"] = reputation

    data_confidence = calculate_data_confidence(
        requested_transactions,
        analyzed_transactions,
        unavailable_transactions,
    )

    # -----------------------------------------------------
    # Behavior
    # -----------------------------------------------------

    behavior = statistics.get(
        "behavior",
        {},
    )

    if not isinstance(behavior, dict):
        behavior = {}

    # -----------------------------------------------------
    # Smart Money
    # -----------------------------------------------------

    smart_money_statistics = dict(statistics)
    smart_money_statistics["data_confidence"] = (
        data_confidence
    )

    smart_money = calculate_smart_money(
        statistics=smart_money_statistics,
        behavior=behavior,
        reputation=reputation,
    )

    return {
        "wallet": wallet,

        "total_transactions": requested_transactions,

        "decoded_activities": analyzed_transactions,

        "unavailable_transactions": (
            unavailable_transactions
        ),

        "statistics": statistics,

        "analysis": {
            "total_transactions": requested_transactions,
            "requested_transactions": requested_transactions,
            "analyzed_transactions": analyzed_transactions,
            "unavailable_transactions": (
                unavailable_transactions
            ),
        },

        "trade_performance": statistics.get(
            "trade_performance",
            {},
        ),

        "reputation": reputation,

        "smart_money": smart_money,

        "data_confidence": data_confidence,

        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }


# =========================================================
# SAVE PROFILE
# =========================================================

def save_profile(
    profile,
    path_or_directory="profiles",
):
    path_or_directory = os.fspath(
        path_or_directory
    )

    if path_or_directory.lower().endswith(
        ".json"
    ):
        path = path_or_directory

        directory = os.path.dirname(
            path
        )

        if directory:
            os.makedirs(
                directory,
                exist_ok=True,
            )

    else:
        os.makedirs(
            path_or_directory,
            exist_ok=True,
        )

        wallet = profile.get(
            "wallet",
            "unknown",
        )

        path = os.path.join(
            path_or_directory,
            f"{wallet}.json",
        )

    # Save the normalized LEGECY profile.
    normalized_profile = build_profile_summary(
        profile
    )

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            normalized_profile,
            file,
            indent=2,
        )

    return path


# =========================================================
# LOAD PROFILE
# =========================================================

def load_profile(path):
    path = os.fspath(path)

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)