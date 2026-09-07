from typing import Any, Dict, Iterable, List


class _DeferredSeedRanking:
    """Awaitable compatibility wrapper for the public seed-wallet ranking route."""

    def __init__(self, seed_wallet: str, history_limit: int, max_candidates: int, candidate_history_limit: int, min_confidence: float):
        self.seed_wallet = seed_wallet
        self.history_limit = history_limit
        self.max_candidates = max_candidates
        self.candidate_history_limit = candidate_history_limit
        self.min_confidence = min_confidence

    def __await__(self):
        async def _run():
            from smart_wallet_discovery import discover_smart_wallets

            discovery = await discover_smart_wallets(
                self.seed_wallet,
                seed_history_limit=self.history_limit,
                candidate_limit=self.max_candidates,
                candidate_history_limit=self.candidate_history_limit,
            )
            candidates = discovery.get("candidates", [])
            ranked = rank_smart_wallets(
                candidates,
                min_confidence=self.min_confidence,
            )
            return {
                "seed_wallet": self.seed_wallet,
                "history_scanned": discovery.get("history_scanned", 0),
                "ranked_wallets": ranked,
                "ranking": {
                    "method": "Confidence-adjusted Smart Money ranking",
                    "candidate_count": len(candidates),
                    "minimum_confidence": self.min_confidence,
                    "read_only": True,
                },
            }

        return _run().__await__()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _confidence(profile: Dict[str, Any]) -> float:
    value = profile.get("data_confidence", {})
    if not isinstance(value, dict):
        return 0.0
    return max(0.0, min(100.0, _number(value.get("score"))))


def _smart_money_score(profile: Dict[str, Any]) -> float:
    value = profile.get("smart_money", {})
    if not isinstance(value, dict):
        return 0.0
    return max(0.0, min(100.0, _number(value.get("score"))))


def rank_smart_wallets(
    profiles: Iterable[Dict[str, Any]] | str,
    min_confidence: float = 0.0,
    history_limit: int = 10,
    max_candidates: int = 5,
    candidate_history_limit: int = 10,
):
    """Rank wallet profiles, or return an awaitable seed-wallet ranking job.

    The profile form remains synchronous for existing callers and tests. The
    seed-wallet form provides compatibility with the production API route,
    which awaits the ranking operation after discovering candidate wallets.
    """
    if isinstance(profiles, str):
        return _DeferredSeedRanking(
            profiles,
            history_limit,
            max_candidates,
            candidate_history_limit,
            min_confidence,
        )

    minimum = max(0.0, min(100.0, _number(min_confidence)))
    ranked = []

    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        confidence = _confidence(profile)
        if confidence < minimum:
            continue

        smart_score = _smart_money_score(profile)
        reputation = profile.get("reputation", {})
        reputation_score = _number(reputation.get("score")) if isinstance(reputation, dict) else 0.0
        behavior = profile.get("behavior", {})
        activity = _number(behavior.get("trading_frequency_score")) if isinstance(behavior, dict) else 0.0

        # Keep smart-money as the primary signal, then reward reputation and
        # evidence quality. Confidence can never create intelligence; it only
        # determines how much of the observed score is trusted.
        ranking_score = (
            smart_score * 0.65
            + reputation_score * 0.15
            + confidence * 0.20
        )

        ranked.append({
            "wallet": profile.get("wallet"),
            "ranking_score": round(min(100.0, max(0.0, ranking_score)), 2),
            "smart_money_score": round(smart_score, 2),
            "reputation_score": round(reputation_score, 2),
            "confidence": round(confidence, 2),
            "smart_money": profile.get("smart_money", {}),
            "reputation": profile.get("reputation", {}),
            "behavior": profile.get("behavior", {}),
        })

    ranked.sort(
        key=lambda item: (
            item["ranking_score"],
            item["smart_money_score"],
            item["confidence"],
        ),
        reverse=True,
    )

    for index, item in enumerate(ranked, start=1):
        item["rank"] = index

    return ranked
