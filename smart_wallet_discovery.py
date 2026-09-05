import asyncio
from collections import Counter
import os

from solders.pubkey import Pubkey
from solders.signature import Signature
from solana.rpc.async_api import AsyncClient

from wallet_intelligence_fast import build_wallet_profile
from wallet_profile import build_profile_summary

RPC_URL = os.getenv("RPC_URL", "https://api.mainnet.solana.com")
DISCOVERY_CONCURRENCY = max(int(os.getenv("DISCOVERY_CONCURRENCY", "8")), 1)


async def _get_recent_signatures(client, wallet, limit):
    result = await client.get_signatures_for_address(
        Pubkey.from_string(wallet),
        limit=limit,
        commitment="finalized",
    )
    return [str(item.signature) for item in result.value]


async def _fetch_transaction(client, semaphore, signature):
    async with semaphore:
        try:
            result = await client.get_transaction(
                Signature.from_string(signature),
                encoding="jsonParsed",
                commitment="finalized",
                max_supported_transaction_version=0,
            )
            return result.value
        except Exception:
            return None


def _extract_signers(transaction, seed_wallet):
    if transaction is None:
        return []

    try:
        account_keys = transaction.transaction.transaction.message.account_keys
    except AttributeError:
        return []

    candidates = []
    for account in account_keys:
        address = str(getattr(account, "pubkey", account))
        if address == seed_wallet:
            continue
        if bool(getattr(account, "signer", False)):
            try:
                Pubkey.from_string(address)
                candidates.append(address)
            except (ValueError, TypeError):
                pass
    return candidates


def _discovery_score(interactions, candidate_count, profile):
    normalized = build_profile_summary(profile)
    smart_money = normalized.get("smart_money", {})
    reputation = normalized.get("reputation", {})
    data_confidence = normalized.get("data_confidence", {})

    smart_score = float(smart_money.get("score", 0) or 0)
    reputation_score = reputation.get("score", 0)
    if isinstance(reputation_score, dict):
        reputation_score = reputation_score.get("score", 0)
    reputation_score = float(reputation_score or 0)
    confidence = float(data_confidence.get("score", 0) or 0)

    interaction_signal = min(interactions * 10, 30)
    intelligence_signal = smart_score * 0.45 + reputation_score * 0.25 + confidence * 0.10
    diversity_signal = min(candidate_count * 5, 15)
    return round(min(100, interaction_signal + intelligence_signal + diversity_signal), 2)


async def discover_smart_wallets(
    seed_wallet: str,
    seed_history_limit: int = 10,
    candidate_limit: int = 5,
    candidate_history_limit: int = 10,
):
    """Discover and rank wallets that repeatedly co-signed seed-wallet transactions."""
    Pubkey.from_string(seed_wallet)
    seed_history_limit = max(1, min(int(seed_history_limit), 50))
    candidate_limit = max(1, min(int(candidate_limit), 10))
    candidate_history_limit = max(1, min(int(candidate_history_limit), 20))

    async with AsyncClient(RPC_URL) as client:
        signatures = await _get_recent_signatures(client, seed_wallet, seed_history_limit)
        semaphore = asyncio.Semaphore(DISCOVERY_CONCURRENCY)
        transactions = await asyncio.gather(
            *(_fetch_transaction(client, semaphore, signature) for signature in signatures)
        )

        interactions = Counter()
        for transaction in transactions:
            interactions.update(_extract_signers(transaction, seed_wallet))

        ranked = interactions.most_common(candidate_limit * 2)
        ranked = [item for item in ranked if item[0] != seed_wallet][:candidate_limit]

    async def analyze_candidate(address):
        try:
            profile = await build_wallet_profile(address, limit=candidate_history_limit)
            return address, profile
        except Exception:
            return address, None

    candidates = await asyncio.gather(*(analyze_candidate(address) for address, _ in ranked))

    results = []
    for address, profile in candidates:
        if profile is None:
            continue
        interactions_count = interactions[address]
        normalized = build_profile_summary(profile)
        score = _discovery_score(interactions_count, len(interactions), profile)
        results.append({
            "wallet": address,
            "discovery_score": score,
            "interactions": interactions_count,
            "smart_money": normalized.get("smart_money", {}),
            "reputation": normalized.get("reputation", {}),
            "data_confidence": normalized.get("data_confidence", {}),
            "behavior": normalized.get("behavior", {}),
        })

    results.sort(key=lambda item: item["discovery_score"], reverse=True)
    return {
        "seed_wallet": seed_wallet,
        "history_scanned": len(signatures),
        "candidates": results,
        "discovery": {
            "method": "Repeated co-signing wallet discovery",
            "candidate_count": len(results),
            "candidate_history_limit": candidate_history_limit,
            "read_only": True,
        },
    }
