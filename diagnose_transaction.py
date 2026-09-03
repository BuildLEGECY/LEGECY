import asyncio

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature


RPC_URL = "https://api.mainnet.solana.com"

WALLET = "MfDuWeqSHEqTFVYZ7LoexgAK9dxk7cy4DFJWjWMGVWa"


async def main():

    print("=" * 70)
    print("LEGECY - TRANSACTION RPC DIAGNOSTIC")
    print("=" * 70)

    async with AsyncClient(RPC_URL) as client:

        print()
        print("Getting latest signature...")

        signatures = await client.get_signatures_for_address(
            Pubkey.from_string(WALLET),
            limit=1
        )

        if not signatures.value:
            print("NO SIGNATURE FOUND")
            return

        signature = signatures.value[0].signature

        print()
        print("Signature:")
        print(signature)

        print()
        print("Requesting transaction...")

        response = await client.get_transaction(
            Signature.from_string(str(signature)),
            encoding="jsonParsed",
            max_supported_transaction_version=0
        )

        print()
        print("=" * 70)
        print("RESPONSE DIAGNOSTIC")
        print("=" * 70)

        print()
        print("Response type:")
        print(type(response))

        print()
        print("Response value:")
        print(response.value)

        if response.value is None:

            print()
            print("RESULT: RPC RETURNED NONE")
            print("The public RPC did not return transaction data.")
            return

        tx = response.value

        print()
        print("Transaction object type:")
        print(type(tx))

        print()
        print("Top-level attributes:")

        print(
            [
                name
                for name in dir(tx)
                if not name.startswith("_")
            ]
        )

        print()
        print("=" * 70)
        print("CHECKING METADATA LOCATIONS")
        print("=" * 70)

        # Possible location 1
        try:

            print()
            print("tx.meta:")
            print(tx.meta)

        except Exception as error:

            print()
            print("tx.meta unavailable:")
            print(error)

        # Possible location 2
        try:

            print()
            print("tx.transaction.meta:")
            print(tx.transaction.meta)

        except Exception as error:

            print()
            print("tx.transaction.meta unavailable:")
            print(error)

        # Possible location 3
        try:

            print()
            print("tx.transaction:")
            print(tx.transaction)

        except Exception as error:

            print()
            print("tx.transaction unavailable:")
            print(error)

        print()
        print("=" * 70)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())