from typing import Any, Dict


def _number(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _score(profile: Dict[str, Any], section: str, *keys: str) -> float:
    data = profile.get(section, {})
    if not isinstance(data, dict):
        return 0.0
    for key in keys:
        if key in data:
            return _number(data.get(key))
    return 0.0


def _confidence(profile: Dict[str, Any]) -> float:
    data = profile.get("data_confidence", {})
    return _number(data.get("score"), 0.0) if isinstance(data, dict) else 0.0


def _label(value: float) -> str:
    return "A" if value > 0 else "B" if value < 0 else "TIE"


def compare_wallet_profiles(profile_a: Dict[str, Any], profile_b: Dict[str, Any]) -> Dict[str, Any]:
    """Compare two normalized LEGECY wallet profiles without inventing missing data."""
    a = profile_a if isinstance(profile_a, dict) else {}
    b = profile_b if isinstance(profile_b, dict) else {}

    metrics = {
        "smart_money": (_score(a, "smart_money", "score"), _score(b, "smart_money", "score")),
        "reputation": (_score(a, "reputation", "score"), _score(b, "reputation", "score")),
        "trading_activity": (_score(a, "trading", "trading_activity"), _score(b, "trading", "trading_activity")),
        "unique_tokens": (_score(a, "trading", "unique_tokens"), _score(b, "trading", "unique_tokens")),
        "swap_success": (
            _score(a, "swap_metrics", "successful_swaps"),
            _score(b, "swap_metrics", "successful_swaps"),
        ),
        "swap_failure_rate": (
            _score(a, "swap_metrics", "swap_failure_rate"),
            _score(b, "swap_metrics", "swap_failure_rate"),
        ),
        "protocol_diversity": (
            len(a.get("protocols", {})) if isinstance(a.get("protocols"), dict) else 0,
            len(b.get("protocols", {})) if isinstance(b.get("protocols"), dict) else 0,
        ),
    }

    results = {}
    wins_a = wins_b = ties = 0
    for name, (value_a, value_b) in metrics.items():
        # Lower failure rate is better; all other metrics are higher-is-better.
        delta = value_a - value_b
        if name == "swap_failure_rate":
            delta = value_b - value_a
        winner = _label(delta)
        if winner == "A":
            wins_a += 1
        elif winner == "B":
            wins_b += 1
        else:
            ties += 1
        results[name] = {
            "wallet_a": round(value_a, 2),
            "wallet_b": round(value_b, 2),
            "winner": winner,
            "delta": round(abs(delta), 2),
        }

    weighted = {
        "smart_money": 0.30,
        "reputation": 0.20,
        "trading_activity": 0.10,
        "unique_tokens": 0.08,
        "swap_success": 0.10,
        "swap_failure_rate": 0.12,
        "protocol_diversity": 0.10,
    }
    composite_a = composite_b = 0.0
    for name, weight in weighted.items():
        va, vb = metrics[name]
        if name == "swap_failure_rate":
            va, vb = -va, -vb
        composite_a += va * weight
        composite_b += vb * weight

    winner = "A" if composite_a > composite_b else "B" if composite_b > composite_a else "TIE"
    winner_wallet = a.get("wallet") if winner == "A" else b.get("wallet") if winner == "B" else None

    return {
        "wallet_a": a.get("wallet"),
        "wallet_b": b.get("wallet"),
        "winner": {
            "side": winner,
            "wallet": winner_wallet,
            "wins": {"wallet_a": wins_a, "wallet_b": wins_b, "ties": ties},
        },
        "composite": {
            "wallet_a": round(composite_a, 2),
            "wallet_b": round(composite_b, 2),
            "note": "Composite is a comparative signal, not a financial prediction.",
        },
        "metrics": results,
        "confidence": {
            "wallet_a": round(_confidence(a), 2),
            "wallet_b": round(_confidence(b), 2),
            "comparison": round(min(_confidence(a), _confidence(b)), 2),
            "rule": "Comparison confidence is limited by the lower-confidence wallet.",
        },
    }
