import asyncio
import os

from dotenv import load_dotenv
from solana.rpc.async_api import AsyncClient

from smart_money_engine import calculate_smart_money
from wallet_intelligence import (
    analyze_transaction,
    get_wallet_transactions,
)
from wallet_reputation import calculate_reputation_score
from wallet_statistics import calculate_wallet_statistics


load_dotenv()

RPC_CONCURRENCY = max(
    int(os.getenv("RPC_CONCURRENCY", "8")),
    1,
)


async def _analyze_signature_safe(
    client,
    semaphore,
    signature,
    wallet_address,
):
    """Analyze one signature without allowing one bad RPC result to stop the batch."""
    async with semaphore:
        try:
            return await analyze_transaction(
                client,
                signature,
                wallet_address,
            )
        except Exception as exc:
            print(
                f"Transaction analysis failed: "
                f"{signature} -> {exc}"
            )
            return None


async def build_wallet_profile(
    wallet_address,
    limit=20,
):
    """
    Build a wallet profile with bounded concurrent RPC transaction analysis.

    Signature discovery remains a single RPC request. Transaction details are
    then fetched concurrently with a semaphore so the RPC provider is not
    flooded. Results stay in the original signature order.
    """
    async with AsyncClient(
        os.getenv(
            "RPC_URL",
            "https://api.mainnet.solana.com",
        )
    ) as client:
        signatures = await get_wallet_transactions(
            client,
            wallet_address,
            limit,
        )

        semaphore = asyncio.Semaphore(RPC_CONCURRENCY)

        analyses = await asyncio.gather(
            *(
                _analyze_signature_safe(
                    client,
                    semaphore,
                    signature,
                    wallet_address,
                )
                for signature in signatures
            )
        )

        activities = []
        unavailable = []

        for signature, analysis in zip(signatures, analyses):
            if analysis is None:
                unavailable.append(str(signature))
                continue

            activities.append(analysis)

        statistics = calculate_wallet_statistics(
            activities
        )

        reputation_score = calculate_reputation_score(
            statistics
        )

        statistics["reputation_score"] = reputation_score

        smart_money = calculate_smart_money(
            statistics=statistics,
            behavior=None,
            reputation=reputation_score,
        )

        statistics["smart_money_score"] = smart_money.get(
            "score",
            0,
        )

        return {
            "wallet": wallet_address,
            "transactions": [
                str(signature)
                for signature in signatures
            ],
            "activities": activities,
            "unavailable": unavailable,
            "total_transactions": len(signatures),
            "decoded_activities": len(activities),
            "unavailable_transactions": len(unavailable),
            "requested_transactions": len(signatures),
            "statistics": statistics,
            "reputation_score": reputation_score,
            "smart_money": smart_money,
        }
