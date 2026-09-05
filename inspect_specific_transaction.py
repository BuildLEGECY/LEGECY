import asyncio
import sys

from solana.rpc.async_api import AsyncClient
from solders.signature import Signature


RPC_URL = "https://api.mainnet.solana.com"


async def main():

    print("=" * 70)
    print("LEGECY - SPECIFIC TRANSACTION INSPECTION")
    print("=" * 70)

    # ---------------------------------------------------------
    # Get transaction signature from command line
    # ---------------------------------------------------------

    if len(sys.argv) < 2:

        print()
        print("Usage:")
        print(
            "python inspect_specific_transaction.py "
            "<transaction_signature>"
        )
        print()

        return

    signature_text = sys.argv[1]

    print()
    print("Signature:")
    print(signature_text)

    # Convert string into Signature object.
    signature = Signature.from_string(
        signature_text
    )

    async with AsyncClient(RPC_URL) as client:

        response = await client.get_transaction(
            signature,
            encoding="jsonParsed",
            max_supported_transaction_version=0,
        )

        tx = response.value

        if tx is None:

            print()
            print("Transaction not found.")
            return

        meta = tx.transaction.meta
        message = tx.transaction.transaction.message

        # -----------------------------------------------------
        # PROGRAMS
        # -----------------------------------------------------

        print()
        print("=" * 70)
        print("PROGRAMS USED")
        print("=" * 70)

        programs = set()

        for instruction in message.instructions:

            program_id = getattr(
                instruction,
                "program_id",
                None,
            )

            if program_id:
                programs.add(
                    str(program_id)
                )

        if meta and meta.inner_instructions:

            for inner in meta.inner_instructions:

                for instruction in inner.instructions:

                    program_id = getattr(
                        instruction,
                        "program_id",
                        None,
                    )

                    if program_id:
                        programs.add(
                            str(program_id)
                        )

        for program in sorted(programs):
            print(program)

        # -----------------------------------------------------
        # SOL BALANCE CHANGE
        # -----------------------------------------------------

        print()
        print("=" * 70)
        print("SOL BALANCES")
        print("=" * 70)

        if meta:

            pre_balances = meta.pre_balances
            post_balances = meta.post_balances

            if pre_balances and post_balances:

                print(
                    f"Account 0 before: "
                    f"{pre_balances[0] / 1_000_000_000}"
                )

                print(
                    f"Account 0 after:  "
                    f"{post_balances[0] / 1_000_000_000}"
                )

                sol_change = (
                    post_balances[0]
                    - pre_balances[0]
                ) / 1_000_000_000

                print(
                    f"SOL change:       "
                    f"{sol_change}"
                )

        # -----------------------------------------------------
        # TOKEN BALANCES
        # -----------------------------------------------------

        print()
        print("=" * 70)
        print("TOKEN BALANCES")
        print("=" * 70)

        if meta:

            print()
            print("PRE TOKEN BALANCES")
            print("-" * 70)

            if meta.pre_token_balances:

                for token in meta.pre_token_balances:

                    owner = getattr(
                        token,
                        "owner",
                        None
                    )

                    mint = getattr(
                        token,
                        "mint",
                        None
                    )

                    amount = token.ui_token_amount

                    print(
                        f"Account Index: "
                        f"{token.account_index}"
                    )

                    print(
                        f"Owner: {owner}"
                    )

                    print(
                        f"Mint: {mint}"
                    )

                    print(
                        f"Amount: "
                        f"{amount.ui_amount}"
                    )

                    print()

            else:
                print("No pre-token balances.")

            print()
            print("POST TOKEN BALANCES")
            print("-" * 70)

            if meta.post_token_balances:

                for token in meta.post_token_balances:

                    owner = getattr(
                        token,
                        "owner",
                        None
                    )

                    mint = getattr(
                        token,
                        "mint",
                        None
                    )

                    amount = token.ui_token_amount

                    print(
                        f"Account Index: "
                        f"{token.account_index}"
                    )

                    print(
                        f"Owner: {owner}"
                    )

                    print(
                        f"Mint: {mint}"
                    )

                    print(
                        f"Amount: "
                        f"{amount.ui_amount}"
                    )

                    print()

            else:
                print("No post-token balances.")

        # -----------------------------------------------------
        # LOGS
        # -----------------------------------------------------

        print()
        print("=" * 70)
        print("LOGS")
        print("=" * 70)

        if meta and meta.log_messages:

            for log in meta.log_messages:
                print(log)

        else:
            print("No logs available.")

        print()
        print("=" * 70)
        print("INSPECTION COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())