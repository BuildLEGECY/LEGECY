import asyncio

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature


RPC_URL = "https://api.mainnet.solana.com"

WALLET = "MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa"


async def main():

    print("=" * 70)
    print("LEGECY - REAL WALLET TRANSACTION INSPECTOR")
    print("=" * 70)

    async with AsyncClient(RPC_URL) as client:

        response = await client.get_signatures_for_address(
            Pubkey.from_string(WALLET),
            limit=1
        )

        if not response.value:
            print("No transactions found.")
            return

        signature = response.value[0].signature

        print()
        print("Transaction:")
        print(signature)

        print()
        print("Fetching transaction...")

        tx_response = await client.get_transaction(
            Signature.from_string(str(signature)),
            encoding="jsonParsed",
            max_supported_transaction_version=0
        )

        tx = tx_response.value

        if tx is None:
            print("Transaction details unavailable.")
            return

        meta = tx.transaction.meta
        message = tx.transaction.transaction.message

        print()
        print("=" * 70)
        print("WALLET ACCOUNT")
        print("=" * 70)

        wallet_index = None

        for index, account in enumerate(message.account_keys):

            try:
                address = str(account.pubkey)
            except AttributeError:
                address = str(account)

            if address == WALLET:
                wallet_index = index
                break

        print("Wallet index:", wallet_index)

        if wallet_index is not None:

            pre_sol = meta.pre_balances[wallet_index]
            post_sol = meta.post_balances[wallet_index]

            print(
                "SOL before:",
                pre_sol / 1_000_000_000
            )

            print(
                "SOL after:",
                post_sol / 1_000_000_000
            )

            print(
                "SOL change:",
                (post_sol - pre_sol) / 1_000_000_000
            )

        print()
        print("=" * 70)
        print("TOKEN BALANCE CHANGES")
        print("=" * 70)

        pre_tokens = {}

        for token in meta.pre_token_balances or []:

            owner = str(getattr(token, "owner", ""))

            if owner == WALLET:

                key = (
                    token.account_index,
                    str(token.mint)
                )

                amount = (
                    token.ui_token_amount.ui_amount or 0
                )

                pre_tokens[key] = amount

        post_tokens = {}

        for token in meta.post_token_balances or []:

            owner = str(getattr(token, "owner", ""))

            if owner == WALLET:

                key = (
                    token.account_index,
                    str(token.mint)
                )

                amount = (
                    token.ui_token_amount.ui_amount or 0
                )

                post_tokens[key] = amount

        all_tokens = set(pre_tokens) | set(post_tokens)

        if not all_tokens:
            print("No wallet-owned token balance changes found.")

        for key in all_tokens:

            before = pre_tokens.get(key, 0)
            after = post_tokens.get(key, 0)
            change = after - before

            if change != 0:

                print()
                print("Mint:", key[1])
                print("Before:", before)
                print("After:", after)
                print("Change:", change)

        print()
        print("=" * 70)
        print("PROGRAMS USED")
        print("=" * 70)

        programs = set()

        for instruction in message.instructions:

            try:
                programs.add(str(instruction.program_id))
            except AttributeError:
                pass

        for inner_group in meta.inner_instructions or []:

            for instruction in inner_group.instructions:

                try:
                    programs.add(str(instruction.program_id))
                except AttributeError:
                    pass

        for program in programs:
            print(program)

        print()
        print("=" * 70)
        print("LOGS")
        print("=" * 70)

        for log in meta.log_messages or []:
            print(log)

        print()
        print("=" * 70)
        print("INSPECTION COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())