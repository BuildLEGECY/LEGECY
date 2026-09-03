import asyncio
import json
import os
from datetime import datetime

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature

RPC_URL = "https://api.mainnet.solana.com"

WALLETS_FILE = "wallets.txt"
SEEN_FILE = "data/seen_transactions.json"

CHECK_INTERVAL = 8
RPC_DELAY = 2


def load_wallets():
    if not os.path.exists(WALLETS_FILE):
        return []

    wallets = []

    with open(WALLETS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith("#"):
                continue

            try:
                Pubkey.from_string(line)
                wallets.append(line)
            except Exception:
                print(f"Invalid wallet ignored: {line}")

    return wallets


def load_seen():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(SEEN_FILE):
        return {}

    try:
        with open(SEEN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_seen(seen):
    os.makedirs("data", exist_ok=True)

    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(seen, f, indent=2)


async def get_recent_signatures(client, wallet):
    try:
        result = await client.get_signatures_for_address(
            Pubkey.from_string(wallet),
            limit=5,
            commitment="finalized"
        )

        return [str(x.signature) for x in result.value]

    except Exception as error:
        print(f"RPC signature error: {error}")
        return []


async def get_transaction(client, signature):
    try:
        await asyncio.sleep(RPC_DELAY)

        result = await client.get_transaction(
            Signature.from_string(signature),
            encoding="jsonParsed",
            commitment="finalized",
            max_supported_transaction_version=0
        )

        return result.value

    except Exception as error:
        print(f"RPC transaction error: {error}")
        return None


def analyze_transaction(tx, wallet):
    if tx is None:
        return None

    meta = tx.transaction.meta

    if meta is None:
        return None

    message = tx.transaction.transaction.message

    # Find the watched wallet inside the transaction.
    wallet_index = None

    for index, account in enumerate(message.account_keys):

        try:
            address = str(account.pubkey)
        except AttributeError:
            address = str(account)

        if address == wallet:
            wallet_index = index
            break

    sol_change = 0

    if wallet_index is not None:
        before = meta.pre_balances[wallet_index]
        after = meta.post_balances[wallet_index]

        sol_change = (after - before) / 1_000_000_000

    token_changes = []

    before_tokens = meta.pre_token_balances or []
    after_tokens = meta.post_token_balances or []

    before_map = {}

    for item in before_tokens:
        owner = getattr(item, "owner", None)

        if owner and str(owner) == wallet:
            key = str(item.mint)

            try:
                amount = float(item.ui_token_amount.ui_amount or 0)
            except Exception:
                amount = 0

            before_map[key] = amount

    after_map = {}

    for item in after_tokens:
        owner = getattr(item, "owner", None)

        if owner and str(owner) == wallet:
            key = str(item.mint)

            try:
                amount = float(item.ui_token_amount.ui_amount or 0)
            except Exception:
                amount = 0

            after_map[key] = amount

    all_mints = set(before_map) | set(after_map)

    for mint in all_mints:

        before_amount = before_map.get(mint, 0)
        after_amount = after_map.get(mint, 0)

        change = after_amount - before_amount

        if abs(change) > 0:
            token_changes.append({
                "mint": mint,
                "change": change
            })

    return {
        "slot": tx.slot,
        "success": meta.err is None,
        "sol_change": sol_change,
        "token_changes": token_changes
    }


def print_activity(wallet, signature, activity):

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print()
    print("=" * 70)
    print(f"🚨 LEGECY ACTIVITY — {now}")
    print("=" * 70)

    print(f"Wallet: {wallet}")
    print(f"Transaction: {signature}")
    print(f"Slot: {activity['slot']}")

    if not activity["success"]:
        print("Status: ❌ FAILED")
        print("=" * 70)
        return

    print("Status: ✅ SUCCESS")

    sol_change = activity["sol_change"]

    if sol_change > 0:
        print(f"SOL change: +{sol_change:.9f}")
    elif sol_change < 0:
        print(f"SOL change: {sol_change:.9f}")
    else:
        print("SOL change: 0")

    if activity["token_changes"]:

        print()
        print("TOKEN ACTIVITY:")

        for token in activity["token_changes"]:

            change = token["change"]

            if change > 0:
                direction = "🟢 RECEIVED"
            else:
                direction = "🔴 SENT"

            print(
                f"{direction} | "
                f"{change:+.6f} | "
                f"{token['mint']}"
            )

    else:
        print("Token activity: none detected")

    print("=" * 70)


async def main():

    print("=" * 70)
    print("                     LEGECY")
    print("              SMART WALLET INTELLIGENCE")
    print("=" * 70)

    wallets = load_wallets()

    if not wallets:
        print()
        print("No wallets in wallets.txt")
        print("Add public Solana wallet addresses first.")
        return

    print()
    print(f"Tracking {len(wallets)} wallet(s)")
    print("Network: Solana Mainnet")
    print("Mode: READ ONLY")
    print("Trading: DISABLED")
    print()

    for wallet in wallets:
        print(f"🐋 {wallet}")

    print()
    print("Connecting...")

    seen = load_seen()

    async with AsyncClient(RPC_URL) as client:

        if not await client.is_connected():
            print("❌ Connection failed.")
            return

        print("✅ Connected to Solana Mainnet")
        print()

        # IMPORTANT:
        # Mark existing transactions as known.
        # This prevents LEGECY from downloading many old transactions.
        for wallet in wallets:

            if wallet not in seen:

                current = await get_recent_signatures(
                    client,
                    wallet
                )

                seen[wallet] = current

                print(
                    f"Initialized {wallet[:8]}... "
                    f"with {len(current)} existing transactions."
                )

                save_seen(seen)

                await asyncio.sleep(RPC_DELAY)

        print()
        print("👀 LEGECY is now watching for NEW activity...")
        print("Press CTRL+C to stop.")
        print("-" * 70)

        while True:

            try:

                for wallet in wallets:

                    current = await get_recent_signatures(
                        client,
                        wallet
                    )

                    known = set(seen.get(wallet, []))

                    new_transactions = [
                        sig for sig in current
                        if sig not in known
                    ]

                    for signature in reversed(new_transactions):

                        print()
                        print(
                            f"🔎 New transaction detected "
                            f"for {wallet[:8]}..."
                        )

                        tx = await get_transaction(
                            client,
                            signature
                        )

                        if tx:

                            activity = analyze_transaction(
                                tx,
                                wallet
                            )

                            if activity:
                                print_activity(
                                    wallet,
                                    signature,
                                    activity
                                )

                        seen.setdefault(wallet, []).append(
                            signature
                        )

                        seen[wallet] = seen[wallet][-100:]

                        save_seen(seen)

                    await asyncio.sleep(RPC_DELAY)

                await asyncio.sleep(CHECK_INTERVAL)

            except KeyboardInterrupt:

                print()
                print("LEGECY stopped.")
                break

            except Exception as error:

                print()
                print(f"⚠️ Monitor error: {error}")

                await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())