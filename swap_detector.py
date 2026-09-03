import asyncio
from solders.pubkey import Pubkey
from solders.signature import Signature
from solana.rpc.async_api import AsyncClient

RPC_URL = "https://api.mainnet.solana.com"


def token_changes(tx, wallet):
    meta = tx.transaction.meta

    if meta is None:
        return []

    before = {}
    after = {}

    for item in meta.pre_token_balances or []:
        if item.owner and str(item.owner) == wallet:
            mint = str(item.mint)
            amount = float(item.ui_token_amount.ui_amount or 0)
            before[mint] = amount

    for item in meta.post_token_balances or []:
        if item.owner and str(item.owner) == wallet:
            mint = str(item.mint)
            amount = float(item.ui_token_amount.ui_amount or 0)
            after[mint] = amount

    changes = []

    for mint in set(before) | set(after):
        change = after.get(mint, 0) - before.get(mint, 0)

        if abs(change) > 0:
            changes.append({
                "mint": mint,
                "change": change
            })

    return changes


def sol_change(tx, wallet):
    meta = tx.transaction.meta

    if meta is None:
        return 0

    keys = tx.transaction.transaction.message.account_keys

    for index, account in enumerate(keys):
        try:
            address = str(account.pubkey)
        except AttributeError:
            address = str(account)

        if address == wallet:
            return (
                meta.post_balances[index]
                - meta.pre_balances[index]
            ) / 1_000_000_000

    return 0


def classify(sol, tokens):
    received = [x for x in tokens if x["change"] > 0]
    sent = [x for x in tokens if x["change"] < 0]

    # Stronger heuristic:
    # SOL down + token up = possible BUY
    if sol < 0 and received:
        return "POSSIBLE_BUY"

    # SOL up + token down = possible SELL
    if sol > 0 and sent:
        return "POSSIBLE_SELL"

    if received and not sent:
        return "TOKEN_RECEIVED"

    if sent and not received:
        return "TOKEN_SENT"

    return "OTHER"


async def inspect(signature, wallet):
    async with AsyncClient(RPC_URL) as client:

        tx_response = await client.get_transaction(
            Signature.from_string(signature),
            encoding="jsonParsed",
            commitment="finalized",
            max_supported_transaction_version=0
        )

        tx = tx_response.value

        if tx is None:
            print("Transaction not available.")
            return

        tokens = token_changes(tx, wallet)
        sol = sol_change(tx, wallet)

        action = classify(sol, tokens)

        print()
        print("=" * 70)
        print("                 LEGECY SWAP DETECTOR")
        print("=" * 70)

        print(f"Wallet: {wallet}")
        print(f"Transaction: {signature}")
        print(f"SOL change: {sol:+.9f}")
        print(f"Detected action: {action}")

        print()

        if tokens:
            print("TOKEN CHANGES:")

            for token in tokens:
                direction = (
                    "RECEIVED"
                    if token["change"] > 0
                    else "SENT"
                )

                print(
                    f"{direction}: "
                    f"{token['change']:+.6f} "
                    f"| Mint: {token['mint']}"
                )
        else:
            print("No token balance changes detected.")

        print("=" * 70)


async def main():

    wallet = input("Enter wallet address: ").strip()
    signature = input("Enter transaction signature: ").strip()

    try:
        Pubkey.from_string(wallet)
        Signature.from_string(signature)
    except Exception:
        print("Invalid wallet or transaction signature.")
        return

    await inspect(signature, wallet)


if __name__ == "__main__":
    asyncio.run(main())