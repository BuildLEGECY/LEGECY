import asyncio

import wallet_intelligence_fast as fast


def test_parallel_signature_analysis_is_bounded(monkeypatch):
    active = 0
    max_active = 0

    async def fake_analyze_transaction(client, signature, wallet_address):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return {"signature": str(signature)}

    monkeypatch.setattr(
        fast,
        "analyze_transaction",
        fake_analyze_transaction,
    )

    async def run():
        semaphore = asyncio.Semaphore(2)
        return await asyncio.gather(
            *(
                fast._analyze_signature_safe(
                    object(),
                    semaphore,
                    f"sig-{index}",
                    "wallet",
                )
                for index in range(6)
            )
        )

    results = asyncio.run(run())

    assert len(results) == 6
    assert [item["signature"] for item in results] == [
        f"sig-{index}" for index in range(6)
    ]
    assert max_active <= 2


def test_failed_transaction_analysis_becomes_none(monkeypatch):
    async def fake_analyze_transaction(client, signature, wallet_address):
        raise RuntimeError("RPC failure")

    monkeypatch.setattr(
        fast,
        "analyze_transaction",
        fake_analyze_transaction,
    )

    async def run():
        semaphore = asyncio.Semaphore(1)
        return await fast._analyze_signature_safe(
            object(),
            semaphore,
            "bad-signature",
            "wallet",
        )

    assert asyncio.run(run()) is None
