import asyncio
from collections import Counter

from wallet_intelligence import build_wallet_profile


TEST_WALLET = "MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa"


async def main():

    print("=" * 60)
    print("LEGECY - WALLET INTELLIGENCE TEST")
    print("=" * 60)

    profile = await build_wallet_profile(
        TEST_WALLET,
        limit=10
    )

    activities = profile.get("activities", [])

    print()
    print("=" * 60)
    print("WALLET RESULT")
    print("=" * 60)

    print(f"Wallet: {TEST_WALLET}")
    print(
        f"Transactions analyzed: "
        f"{profile.get('total_transactions', 0)}"
    )
    print(
        f"Decoded activities: "
        f"{profile.get('decoded_activities', 0)}"
    )

    counts = Counter()

    for activity in activities:

        event = activity.get(
            "event",
            "UNKNOWN"
        )

        counts[event] += 1

    print()
    print("EVENT SUMMARY")
    print("-" * 40)

    for event, count in counts.most_common():

        print(f"{event}: {count}")

    print()
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())