import asyncio
import sys

from wallet_intelligence import build_wallet_profile


def print_profile(profile):
    statistics = profile.get("statistics", {})

    print()
    print("=" * 70)
    print("LEGECY - WALLET PROFILE")
    print("=" * 70)

    print()
    print(f"Wallet: {profile.get('wallet')}")
    print(
        f"Transactions analyzed: "
        f"{profile.get('decoded_activities', 0)}"
    )

    print()
    print("ACTIVITY")
    print("-" * 70)

    print(f"Buys: {statistics.get('buys', 0)}")
    print(f"Sells: {statistics.get('sells', 0)}")
    print(f"Token swaps: {statistics.get('token_swaps', 0)}")
    print(f"Failed swaps: {statistics.get('swap_failed', 0)}")

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

    print(f"Unknown: {statistics.get('unknown', 0)}")

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

    print()
    print("PROTOCOLS")
    print("-" * 70)

    protocols = statistics.get("protocol_usage", {})

    if protocols:
        for name, count in protocols.items():
            print(f"{name}: {count}")
    else:
        print("No recognized protocols")

    print()
    print("REPUTATION")
    print("-" * 70)

    reputation = statistics.get("reputation_score", {})

    if isinstance(reputation, dict):
        print(f"Score: {reputation.get('score', 0)}")
        print(f"Rating: {reputation.get('rating', 'UNKNOWN')}")

        signals = reputation.get("signals", [])

        if signals:
            print()
            print("Signals:")

            for signal in signals:
                print(f"- {signal}")

    else:
        print(f"Score: {reputation}")

    print()
    print("=" * 70)
    print("LEGECY ANALYSIS COMPLETE")
    print("=" * 70)


async def main():
    if len(sys.argv) < 2:
        print()
        print("LEGECY Wallet Intelligence")
        print()
        print("Usage:")
        print("  python legecy.py <wallet_address>")
        print()
        return

    wallet_address = sys.argv[1]

    try:
        profile = await build_wallet_profile(
            wallet_address,
            limit=20
        )

        print_profile(profile)

    except Exception as exc:
        print()
        print(f"LEGECY analysis failed: {exc}")
        print()


if __name__ == "__main__":
    asyncio.run(main())