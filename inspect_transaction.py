import asyncio

from solana.rpc.async_api import AsyncClient
from solders.signature import Signature


RPC_URL = "https://api.mainnet.solana.com"

SIGNATURE = (
    "3UifLq45eZc4gRtnJuaMLwgNS54Edywph4mMDnHbonJ2Jwb7JSEERUNueZnXvvby"
    "ESEB5CP6nctuGgYZC48z8uLY"
)


async def main():

    async with AsyncClient(RPC_URL) as client:

        signature = Signature.from_string(SIGNATURE)

        response = await client.get_transaction(
            signature,
            encoding="jsonParsed",
            max_supported_transaction_version=0
        )

        if not response.value:
            print("Transaction could not be loaded.")
            return

        tx = response.value
        meta = tx.transaction.meta

        print("=" * 60)
        print("LEGECY - ASSET MOVEMENT ANALYSIS")
        print("=" * 60)
        print()

        # -------------------------
        # SOL movement
        # -------------------------

        pre_sol = meta.pre_balances[0] / 1_000_000_000
        post_sol = meta.post_balances[0] / 1_000_000_000

        sol_change = post_sol - pre_sol

        print("SOL MOVEMENT")
        print("-" * 60)
        print(f"Before: {pre_sol:.9f} SOL")
        print(f"After:  {post_sol:.9f} SOL")
        print(f"Change: {sol_change:+.9f} SOL")
        print()

        # -------------------------
        # Token movement
        # -------------------------

        pre_tokens = meta.pre_token_balances or []
        post_tokens = meta.post_token_balances or []

        pre_map = {}

        for token in pre_tokens:
            key = (token.account_index, token.mint)
            amount = token.ui_token_amount.ui_amount or 0
            pre_map[key] = amount

        post_map = {}

        for token in post_tokens:
            key = (token.account_index, token.mint)
            amount = token.ui_token_amount.ui_amount or 0
            post_map[key] = amount

        all_tokens = set(pre_map) | set(post_map)

        print("TOKEN MOVEMENTS")
        print("-" * 60)

        if not all_tokens:
            print("No token balance changes found.")
        else:
            for account, mint in sorted(all_tokens):

                before = pre_map.get((account, mint), 0)
                after = post_map.get((account, mint), 0)

                change = after - before

                if change != 0:

                    print(f"Mint:   {mint}")
                    print(f"Before: {before}")
                    print(f"After:  {after}")
                    print(f"Change: {change:+}")
                    print()

        print("=" * 60)
        print("ASSET ANALYSIS COMPLETE")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())