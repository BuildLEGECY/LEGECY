import asyncio

from solana.rpc.async_api import AsyncClient
from solders.signature import Signature


RPC_URL = "https://api.mainnet.solana.com"

SIGNATURE = (
    "5wCFu7woCWcv3nJU6LoXhDniYSqhvTUdqZ7j7DPoAHqySJr8zLgyyPzYZh9u1KkbJDhqL1YEWBF5a2B4zWHkNZDP"
)


async def main():

    print("=" * 70)
    print("LEGECY - SPECIFIC TRANSACTION INSPECTION")
    print("=" * 70)

    print()
    print("Signature:")
    print(SIGNATURE)

    # Convert string into the Signature type required
    # by the installed Solana Python library.
    signature = Signature.from_string(SIGNATURE)

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

        print()
        print("=" * 70)
        print("PROGRAMS USED")
        print("=" * 70)

        programs = set()

        message = tx.transaction.transaction.message

        for instruction in message.instructions:

            program_id = getattr(
                instruction,
                "program_id",
                None,
            )

            if program_id:
                programs.add(str(program_id))

        meta = tx.transaction.meta

        if meta and meta.inner_instructions:

            for inner in meta.inner_instructions:

                for instruction in inner.instructions:

                    program_id = getattr(
                        instruction,
                        "program_id",
                        None,
                    )

                    if program_id:
                        programs.add(str(program_id))

        for program in sorted(programs):
            print(program)

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