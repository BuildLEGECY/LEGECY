"""
Basic tests for LEGECY transaction classification.

These tests intentionally cover simple, deterministic cases first.
"""

from dataclasses import dataclass


@dataclass
class TransactionEvent:
    sol_change: float
    token_change: float


def classify_transaction(event: TransactionEvent) -> str:
    """
    Simple first-pass classifier.

    This is NOT the final LEGECY transaction decoder.
    It is only a deterministic baseline for testing.
    """

    if event.sol_change < 0 and event.token_change > 0:
        return "POSSIBLE_BUY"

    if event.sol_change > 0 and event.token_change < 0:
        return "POSSIBLE_SELL"

    if event.token_change > 0 and event.sol_change == 0:
        return "TOKEN_RECEIVED"

    if event.token_change < 0 and event.sol_change == 0:
        return "TOKEN_SENT"

    return "OTHER"


def test_possible_buy():
    event = TransactionEvent(
        sol_change=-1.0,
        token_change=1000.0,
    )

    assert classify_transaction(event) == "POSSIBLE_BUY"


def test_possible_sell():
    event = TransactionEvent(
        sol_change=1.0,
        token_change=-1000.0,
    )

    assert classify_transaction(event) == "POSSIBLE_SELL"


def test_token_received():
    event = TransactionEvent(
        sol_change=0.0,
        token_change=500.0,
    )

    assert classify_transaction(event) == "TOKEN_RECEIVED"


def test_token_sent():
    event = TransactionEvent(
        sol_change=0.0,
        token_change=-500.0,
    )

    assert classify_transaction(event) == "TOKEN_SENT"


def test_other_transaction():
    event = TransactionEvent(
        sol_change=0.0,
        token_change=0.0,
    )

    assert classify_transaction(event) == "OTHER"
