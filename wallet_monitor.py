import asyncio
from datetime import datetime

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

from transaction_decoder import classify_transaction


WALLET = "7W8nmmbkwA1VFhzFjg3BU57ZwtS3XXCq9MwM61EN7USE"
RPC_URL = "https://api.mainnet.solana.com"

CHECK_INTERVAL = 10


def build_transaction_data(tx):
    """
    Convert a Solana RPC transaction into the format
    expected by LEGECY's transaction decoder.
    """

    meta = tx.transaction.meta

    if not meta:
        return None

    programs = set()

    # Top-level instructions
    instructions = tx.transaction.transaction.message.instructions

    for instruction in instructions:
        program_id = getattr(instruction, "program_id", None)

        if program_id:
            programs.add(str(program_id))

    # Inner instructions
    inner_instructions = meta.inner_instructions or []

    for group in inner_instructions:

        for instruction in group.instructions:
            program_id = getattr(instruction, "program_id", None)

            if program_id:
                programs.add(str(program_id))

    # Token balances
    pre_tokens = []
    post_tokens = []

    for token in meta.pre_token_balances or []:
        pre_tokens.append(
            {
                "accountIndex": token.account_index,
                "mint": token.mint,
                "uiTokenAmount": {
                    "uiAmount": token.ui_token_amount.ui_amount
                }
            }
        )

    for token in meta.post_token_balances or []:
        post_tokens.append(
            {
                "accountIndex": token.account_index,
                "mint": token.mint,
                "uiTokenAmount": {
                    "uiAmount": token.ui_token_amount.ui_amount
                }
            }
        )

    return {
        "meta": {
            "preBalances": meta.pre_balances,
            "postBalances": meta.post_balances,
            "preTokenBalances": pre_tokens,
            "postTokenBalances": post_tokens,
        },
        "programs": list(programs),
    }


async def analyze_transaction(client, signature):

    try:

        response = await client.get_transaction(
            signature,
            encoding="jsonParsed",
            max_supported_transaction_version=0
        )

        if not response.value:
            print("       Transaction details unavailable.")
            return

        transaction_data = build_transaction_data(
            response.value
        )

        if not transaction_data:
            print("       Transaction metadata unavailable.")
            return

        result = classify_transaction(
            transaction_data
        )

        print()
        print("       🧠 LEGECY ANALYSIS")
        print("       " + "-" * 40)
        print(f"       Event:      {result['event']}")
        print(f"       Confidence: {result['confidence']}")
        print(f"       Reason:     {result['reason']}")

        if result.get("tokens_received"):
            print("       Tokens received:")

            for token in result["tokens_received"]:
                print(
                    f"         {token['amount']} "
                    f"{token['mint']}"
                )

        if result.get("tokens_sent"):
            print("       Tokens sent:")

            for token in result["tokens_sent"]:
                print(
                    f"         {token['amount']} "
                    f"{token['mint']}"
                )

    except Exception as error:
        print(f"       Decoder error: {error}")


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
            print("Solana connection failed.")
            return

        print("Connected to Solana Mainnet")

        previous_balance = await get_balance(
            client,
            wallet
        )

        previous_signatures = set()

        print(
            f"Starting balance: "
            f"{previous_balance:.9f} SOL"
        )

        print()
        print("LEGECY is now watching...")
        print("Press CTRL+C to stop.")
        print("-" * 60)

        while True:

            try:

                current_balance = await get_balance(
                    client,
                    wallet
                )

                response = await client.get_signatures_for_address(
                    wallet,
                    limit=10
                )

                signatures = {
                    item.signature
                    for item in response.value
                }

                new_transactions = (
                    signatures - previous_signatures
                )

                now = datetime.now().strftime("%H:%M:%S")

                if current_balance != previous_balance:

                    change = (
                        current_balance
                        - previous_balance
                    )

                    print(
                        f"[{now}] Balance changed: "
                        f"{change:+.9f} SOL"
                    )

                    print(
                        f"       New balance: "
                        f"{current_balance:.9f} SOL"
                    )

                    previous_balance = current_balance

                if new_transactions:

                    print(
                        f"[{now}] "
                        f"{len(new_transactions)} "
                        f"new transaction(s)"
                    )

                    for signature in new_transactions:

                        print(
                            f"       TX: {signature}"
                        )

                        await analyze_transaction(
                            client,
                            signature
                        )

                if not previous_signatures:

                    previous_signatures = signatures

                else:

                    previous_signatures.update(
                        signatures
                    )

                await asyncio.sleep(
                    CHECK_INTERVAL
                )

            except KeyboardInterrupt:

                print()
                print("LEGECY stopped.")
                break

            except Exception as error:

                print(f"[ERROR] {error}")

                await asyncio.sleep(
                    CHECK_INTERVAL
                )


if __name__ == "__main__":
    asyncio.run(main())