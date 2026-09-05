from typing import Any, Dict, Iterable, List


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


def rank_smart_wallets(profiles: Iterable[Dict[str, Any]], min_confidence: float = 0.0) -> List[Dict[str, Any]]:
    """Rank wallet profiles by smart-money quality with an evidence-confidence adjustment."""
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

    ranked.sort(key=lambda item: (item["ranking_score"], item["smart_money_score"], item["confidence"]), reverse=True)

    for index, item in enumerate(ranked, start=1):
        item["rank"] = index

    return ranked
