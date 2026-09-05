import asyncio
import os
import sys

from wallet_intelligence import build_wallet_profile
from wallet_profile import save_profile


def print_profile(profile):
    statistics = profile.get(
        "statistics",
        {}
    )

    print()
    print("=" * 70)
    print("LEGECY - WALLET PROFILE")
    print("=" * 70)

    print()
    print(
        f"Wallet: "
        f"{profile.get('wallet')}"
    )

    print(
        f"Transactions analyzed: "
        f"{profile.get('decoded_activities', 0)}"
    )

    # ---------------------------------------------------------
    # Data confidence
    # ---------------------------------------------------------

    requested_transactions = profile.get(
        "total_transactions",
        profile.get(
            "requested_transactions",
            profile.get(
                "decoded_activities",
                0
            )
        )
    )

    analyzed_transactions = profile.get(
        "decoded_activities",
        0
    )

    unavailable_transactions = profile.get(
        "unavailable_transactions",
        max(
            int(requested_transactions or 0)
            - int(analyzed_transactions or 0),
            0
        )
    )

    if requested_transactions:
        coverage = (
            analyzed_transactions
            / requested_transactions
        ) * 100
    else:
        coverage = 0.0

    if coverage >= 90:
        confidence_level = "HIGH"
    elif coverage >= 70:
        confidence_level = "GOOD"
    elif coverage >= 40:
        confidence_level = "LIMITED"
    elif requested_transactions == 0:
        confidence_level = "NONE"
    else:
        confidence_level = "LOW"

    print()
    print("DATA CONFIDENCE")
    print("-" * 70)

    print(
        f"Requested transactions: "
        f"{requested_transactions}"
    )

    print(
        f"Analyzed transactions: "
        f"{analyzed_transactions}"
    )

    print(
        f"Unavailable transactions: "
        f"{unavailable_transactions}"
    )

    print(
        f"Coverage: "
        f"{round(coverage, 2)}%"
    )

    print(
        f"Confidence: "
        f"{confidence_level}"
    )

    # ---------------------------------------------------------
    # Activity
    # ---------------------------------------------------------

    print()
    print("ACTIVITY")
    print("-" * 70)

    print(
        f"Buys: "
        f"{statistics.get('buys', 0)}"
    )

    print(
        f"Sells: "
        f"{statistics.get('sells', 0)}"
    )

    print(
        f"Token swaps: "
        f"{statistics.get('token_swaps', 0)}"
    )

    print(
        f"Failed swaps: "
        f"{statistics.get('swap_failed', 0)}"
    )

    print(
        f"Liquidity actions: "
        f"{statistics.get('liquidity_actions', 0)}"
    )

    print(
        f"Transfers received: "
        f"{statistics.get('transfers_received', 0)}"
    )

    print(
        f"Transfers sent: "
        f"{statistics.get('transfers_sent', 0)}"
    )

    print(
        f"Unknown: "
        f"{statistics.get('unknown', 0)}"
    )

    # ---------------------------------------------------------
    # Swap metrics
    # ---------------------------------------------------------

    swap_metrics = {
        "successful_swaps": statistics.get(
            "successful_swaps",
            statistics.get(
                "token_swaps",
                0
            )
        ),
        "failed_swaps": statistics.get(
            "failed_swaps",
            statistics.get(
                "swap_failed",
                0
            )
        ),
        "swap_attempts": statistics.get(
            "swap_attempts",
            0
        ),
        "swap_failure_rate": statistics.get(
            "swap_failure_rate",
            0.0
        )
    }

    print()
    print("SWAP METRICS")
    print("-" * 70)

    print(
        f"Successful swaps: "
        f"{swap_metrics['successful_swaps']}"
    )

    print(
        f"Failed swaps: "
        f"{swap_metrics['failed_swaps']}"
    )

    print(
        f"Swap attempts: "
        f"{swap_metrics['swap_attempts']}"
    )

    print(
        f"Failure rate: "
        f"{swap_metrics['swap_failure_rate']}%"
    )

    # ---------------------------------------------------------
    # Trading
    # ---------------------------------------------------------

    print()
    print("TRADING")
    print("-" * 70)

    print(
        f"Trading activity: "
        f"{statistics.get('trading_activity', 0)}"
    )

    print(
        f"Unique tokens: "
        f"{statistics.get('unique_tokens', 0)}"
    )

    print(
        f"SOL spent: "
        f"{statistics.get('total_sol_spent', 0)}"
    )

    print(
        f"SOL received: "
        f"{statistics.get('total_sol_received', 0)}"
    )

    print(
        f"Win rate: "
        f"{statistics.get('win_rate')}"
    )

    print(
        f"Profit/Loss: "
        f"{statistics.get('profit_loss')}"
    )

    # ---------------------------------------------------------
    # Trading performance
    # ---------------------------------------------------------

    performance = statistics.get(
        "trade_performance",
        {}
    )

    print()
    print("TRADING PERFORMANCE")
    print("-" * 70)

    print(
        f"Trades: "
        f"{performance.get('trades', 0)}"
    )

    print(
        f"Closed trades: "
        f"{performance.get('closed_trades', 0)}"
    )

    print(
        f"Winning trades: "
        f"{performance.get('winning_trades', 0)}"
    )

    print(
        f"Losing trades: "
        f"{performance.get('losing_trades', 0)}"
    )

    print(
        f"Breakeven trades: "
        f"{performance.get('breakeven_trades', 0)}"
    )

    print(
        f"Win rate: "
        f"{performance.get('win_rate')}"
    )

    print(
        f"Realized P/L: "
        f"{performance.get('realized_profit_loss', 0.0)}"
    )

    open_positions = performance.get(
        "open_positions",
        {}
    )

    print()

    if open_positions:
        print("Open positions:")

        for asset, lots in open_positions.items():
            total_amount = sum(
                float(lot.get("amount", 0))
                for lot in lots
            )

            print(
                f"- {asset}: "
                f"{total_amount}"
            )

    else:
        print("Open positions: None")

    # ---------------------------------------------------------
    # Behavior
    # ---------------------------------------------------------

    behavior = statistics.get(
        "behavior",
        {}
    )

    print()
    print("BEHAVIOR")
    print("-" * 70)

    print(
        f"Trading style: "
        f"{behavior.get('trading_style', 'UNKNOWN')}"
    )

    print(
        f"Risk level: "
        f"{behavior.get('risk_level', 'UNKNOWN')}"
    )

    print(
        f"Trading frequency: "
        f"{behavior.get('trading_frequency', 'UNKNOWN')}"
    )

    print(
        f"Token diversity: "
        f"{behavior.get('token_diversity', 'UNKNOWN')}"
    )

    print(
        f"Protocol diversity: "
        f"{behavior.get('protocol_diversity', 'UNKNOWN')}"
    )

    print(
        f"Behavior failed-swap rate: "
        f"{behavior.get('failed_swap_rate', 0.0)}%"
    )

    behavior_signals = behavior.get(
        "signals",
        []
    )

    if behavior_signals:
        print()
        print("Behavior signals:")

        for signal in behavior_signals:
            print(
                f"- {signal}"
            )

    # ---------------------------------------------------------
    # Protocols
    # ---------------------------------------------------------

    print()
    print("PROTOCOLS")
    print("-" * 70)

    protocols = statistics.get(
        "protocol_usage",
        {}
    )

    if protocols:
        for name, count in protocols.items():
            print(
                f"{name}: {count}"
            )
    else:
        print(
            "No recognized protocols"
        )

    # ---------------------------------------------------------
    # Reputation
    # ---------------------------------------------------------

    print()
    print("REPUTATION")
    print("-" * 70)

    reputation = statistics.get(
        "reputation_score",
        {}
    )

    if isinstance(
        reputation,
        dict
    ):
        print(
            f"Score: "
            f"{reputation.get('score', 0)}"
        )

        print(
            f"Rating: "
            f"{reputation.get('rating', 'UNKNOWN')}"
        )

        signals = reputation.get(
            "signals",
            []
        )

        if signals:
            print()
            print("Signals:")

            for signal in signals:
                print(
                    f"- {signal}"
                )

    else:
        print(
            f"Score: {reputation}"
        )

    print()
    print("=" * 70)
    print("LEGECY ANALYSIS COMPLETE")
    print("=" * 70)


async def main():
    if len(sys.argv) < 2:
        print()
        print(
            "LEGECY Wallet Intelligence"
        )
        print()
        print("Usage:")
        print(
            "  python legecy.py <wallet_address>"
        )
        print()
        return

    wallet_address = sys.argv[1]

    try:
        profile = await build_wallet_profile(
            wallet_address,
            limit=20
        )

        print_profile(profile)

        # -----------------------------------------------------
        # Save reusable JSON profile
        # -----------------------------------------------------

        os.makedirs(
            "profiles",
            exist_ok=True
        )

        filename = os.path.join(
            "profiles",
            f"{wallet_address}.json"
        )

        save_profile(
            profile,
            filename
        )

        print()
        print(
            f"Profile saved: {filename}"
        )

    except Exception as exc:
        print()
        print(
            f"LEGECY analysis failed: {exc}"
        )
        print()


if __name__ == "__main__":
    asyncio.run(main())