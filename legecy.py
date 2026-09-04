import asyncio
import sys

from wallet_intelligence import build_wallet_profile


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
    print(f"Wallet: {profile.get('wallet')}")
    print(
        f"Transactions analyzed: "
        f"{profile.get('decoded_activities', 0)}"
    )

    print()
    print("ACTIVITY")
    print("-" * 70)

    print(
        f"Buys: {statistics.get('buys', 0)}"
    )

    print(
        f"Sells: {statistics.get('sells', 0)}"
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

    print()
    print("TRADING")
    print("-" * 70)

    print(
        f"Unique tokens: "
        f"{statistics.get('unique_tokens', 0)}"
    )

    print(
        f"SOL spent: "
        f"{statistics.get('sol_spent', 0)}"
    )

    print(
        f"SOL received: "
        f"{statistics.get('sol_received', 0)}"
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

    protocols = {}

    for activity in profile.get(
        "activities",
        []
    ):
        for protocol in activity.get(
            "protocols",
            []
        ):
            if isinstance(protocol, dict):
                name = protocol.get("name")
            else:
                name = str(protocol)

            if name:
                protocols[name] = (
                    protocols.get(name, 0) + 1
                )

    if protocols:
        for name, count in protocols.items():
            print(
                f"{name}: {count}"
            )
    else:
        print("No recognized protocols")

    print()
    print("REPUTATION")
    print("-" * 70)

    score = statistics.get(
        "reputation_score"
    )

    print(
        f"Score: {score}"
    )

    print()
    print("=" * 70)
    print("LEGECY ANALYSIS COMPLETE")
    print("=" * 70)


async def main():
    if len(sys.argv) < 2:
        print()
        print("LEGECY Wallet Intelligence")
        print()
        print(
            "Usage:"
        )
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

    except Exception as exc:
        print()
        print(
            f"LEGECY analysis failed: {exc}"
        )
        print()


if __name__ == "__main__":
    asyncio.run(main())