import asyncio
from datetime import datetime

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

WALLET = "7W8nmmbkwA1VFhzFjg3BU57ZwtS3XXCq9MwM61EN7USE"
RPC_URL = "https://api.mainnet.solana.com"

CHECK_INTERVAL = 5


async def get_balance(client, wallet):
    response = await client.get_balance(wallet)
    return response.value / 1_000_000_000


async def main():
    wallet = Pubkey.from_string(WALLET)

    print("=" * 60)
    print("                 LEGECY")
    print("          LIVE WALLET WATCHER")
    print("=" * 60)
    print(f"Wallet: {WALLET}")
    print("Network: Solana Mainnet")
    print("Mode: READ ONLY")
    print("Trading: DISABLED")
    print()

    async with AsyncClient(RPC_URL) as client:

        if not await client.is_connected():
            print("❌ Solana connection failed.")
            return

        print("✅ Connected to Solana Mainnet")

        previous_balance = await get_balance(client, wallet)
        previous_signatures = set()

        print(f"Starting balance: {previous_balance:.9f} SOL")
        print()
        print("👀 LEGECY is now watching...")
        print("Press CTRL+C to stop.")
        print("-" * 60)

        while True:
            try:
                current_balance = await get_balance(client, wallet)

                response = await client.get_signatures_for_address(
                    wallet,
                    limit=10
                )

                signatures = {
                    str(tx.signature)
                    for tx in response.value
                }

                new_transactions = signatures - previous_signatures

                now = datetime.now().strftime("%H:%M:%S")

                if current_balance != previous_balance:
                    change = current_balance - previous_balance

                    print(
                        f"[{now}] 💰 Balance changed: "
                        f"{change:+.9f} SOL"
                    )

                    print(
                        f"       New balance: "
                        f"{current_balance:.9f} SOL"
                    )

                    previous_balance = current_balance

                if new_transactions:
                    print(
                        f"[{now}] 🚨 "
                        f"{len(new_transactions)} new transaction(s)"
                    )

                    for signature in new_transactions:
                        print(f"       TX: {signature}")

                if not previous_signatures:
                    previous_signatures = signatures
                else:
                    previous_signatures.update(signatures)

                await asyncio.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:
                print("\nLEGECY stopped.")
                break

            except Exception as error:
                print(f"[ERROR] {error}")
                await asyncio.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())