import asyncio
from types import SimpleNamespace

from smart_wallet_discovery import _discovery_score, _extract_signers, discover_smart_wallets


def test_extract_signers_excludes_seed_wallet():
    seed = "11111111111111111111111111111111"
    other = "So11111111111111111111111111111111111111112"
    message = SimpleNamespace(
        account_keys=[
            SimpleNamespace(pubkey=seed, signer=True),
            SimpleNamespace(pubkey=other, signer=True),
            SimpleNamespace(pubkey="11111111111111111111111111111111", signer=False),
        ]
    )
    transaction = SimpleNamespace(
        transaction=SimpleNamespace(
            transaction=SimpleNamespace(message=message)
        )
    )

    assert _extract_signers(transaction, seed) == [other]


def test_discovery_score_is_bounded():
    profile = {
        "wallet": "test",
        "smart_money": {"score": 100},
        "reputation": {"score": 100},
        "data_confidence": {"score": 100},
    }
    assert 0 <= _discovery_score(100, 100, profile) <= 100


def test_discovery_score_rewards_interactions():
    low = _discovery_score(1, 1, {
        "smart_money": {"score": 50},
        "reputation": {"score": 50},
        "data_confidence": {"score": 50},
    })
    high = _discovery_score(5, 5, {
        "smart_money": {"score": 50},
        "reputation": {"score": 50},
        "data_confidence": {"score": 50},
    })
    assert high > low


def test_discovery_rejects_invalid_wallet():
    async def run():
        try:
            await discover_smart_wallets("not-a-solana-wallet")
        except ValueError:
            return
        raise AssertionError("invalid wallet should raise ValueError")

    asyncio.run(run())
