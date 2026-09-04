# LEGECY - Transaction Decoder

from protocol_registry import identify_programs


def classify_transaction(transaction):
    """
    Classify a Solana wallet transaction.

    Main events:

    TOKEN_SWAP
    SWAP_FAILED
    POSSIBLE_BUY
    POSSIBLE_SELL
    POSSIBLE_LIQUIDITY
    TRANSFER_RECEIVED
    TRANSFER_SENT
    SOL_RECEIVED
    SOL_SENT
    UNKNOWN
    """

    # ---------------------------------------------------------
    # Read wallet intelligence data
    # ---------------------------------------------------------

    wallet_sol_change = transaction.get(
        "wallet_sol_change"
    )

    token_changes = transaction.get(
        "token_changes",
        []
    )

    programs = transaction.get(
        "programs",
        []
    )

    logs = transaction.get(
        "logs",
        []
    )

    # ---------------------------------------------------------
    # Legacy compatibility
    # ---------------------------------------------------------

    if wallet_sol_change is None:

        meta = transaction.get("meta")

        if not meta:
            return {
                "event": "UNKNOWN",
                "confidence": 0.20,
                "reason": "Transaction metadata unavailable",
                "protocols": []
            }

        pre_balances = meta.get(
            "preBalances",
            []
        )

        post_balances = meta.get(
            "postBalances",
            []
        )

        if pre_balances and post_balances:
            wallet_sol_change = (
                post_balances[0]
                - pre_balances[0]
            ) / 1_000_000_000

        token_changes = []

        pre_tokens = meta.get(
            "preTokenBalances",
            []
        )

        post_tokens = meta.get(
            "postTokenBalances",
            []
        )

        for token in post_tokens:
            token_changes.append(
                {
                    "mint": token.get("mint"),
                    "change": 1,
                    "direction": "received"
                }
            )

        for token in pre_tokens:
            token_changes.append(
                {
                    "mint": token.get("mint"),
                    "change": -1,
                    "direction": "sent"
                }
            )

    # ---------------------------------------------------------
    # Normalize SOL movement
    # ---------------------------------------------------------

    if wallet_sol_change is None:
        wallet_sol_change = 0.0

    try:
        wallet_sol_change = float(
            wallet_sol_change
        )
    except (TypeError, ValueError):
        wallet_sol_change = 0.0

    # ---------------------------------------------------------
    # Token movement
    # ---------------------------------------------------------

    token_received = False
    token_sent = False

    received_mints = []
    sent_mints = []

    for token in token_changes:

        direction = str(
            token.get(
                "direction",
                ""
            )
        ).lower()

        change = token.get(
            "change",
            0
        )

        try:
            change = float(change)
        except (TypeError, ValueError):
            change = 0

        mint = token.get(
            "mint"
        )

        if direction in (
            "received",
            "receive",
            "in"
        ):
            token_received = True

            if mint:
                received_mints.append(
                    str(mint)
                )

        elif direction in (
            "sent",
            "send",
            "out"
        ):
            token_sent = True

            if mint:
                sent_mints.append(
                    str(mint)
                )

        elif change > 0:

            token_received = True

            if mint:
                received_mints.append(
                    str(mint)
                )

        elif change < 0:

            token_sent = True

            if mint:
                sent_mints.append(
                    str(mint)
                )

    # ---------------------------------------------------------
    # Verified protocols
    # ---------------------------------------------------------

    verified_protocols = identify_programs(
        programs
    )

    protocol_names = [
        protocol.get("name")
        for protocol in verified_protocols
        if isinstance(protocol, dict)
        and protocol.get("name")
    ]

    supports_swap = any(
        "SWAP" in protocol.get(
            "supports",
            []
        )
        for protocol in verified_protocols
        if isinstance(protocol, dict)
    )

    protocol_text = (
        ", ".join(protocol_names)
        if protocol_names
        else "unknown protocol"
    )

    # ---------------------------------------------------------
    # Logs
    # ---------------------------------------------------------

    log_text = " ".join(
        str(log).lower()
        for log in logs
    )

    # ---------------------------------------------------------
    # Detect swap instruction
    # ---------------------------------------------------------

    swap_patterns = (
        "instruction: swap",
        "instruction: swapv2",
        "instruction: exactinput",
        "instruction: exactoutput",
        "instruction: swapexactin",
        "instruction: swapexactout",
        "instruction: swap2",
        "instruction: swaps",
        "instruction: swapwith",
    )

    swap_in_log = any(
        pattern in log_text
        for pattern in swap_patterns
    )

    # Jupiter/OpenBook-style execution can use Fill.
    fill_in_log = (
        "instruction: fill" in log_text
    )

    # ---------------------------------------------------------
    # Detect liquidity instructions
    # ---------------------------------------------------------

    liquidity_patterns = (
        "instruction: addliquidity",
        "instruction: removeliquidity",
        "instruction: increase_liquidity",
        "instruction: decrease_liquidity",
        "instruction: add_liquidity",
        "instruction: remove_liquidity",
        "instruction: deposit",
        "instruction: withdraw",
        "instruction: openposition",
        "instruction: closeposition",
        "instruction: increaseposition",
        "instruction: decreaseposition",
    )

    liquidity_in_log = any(
        pattern in log_text
        for pattern in liquidity_patterns
    )

    # ---------------------------------------------------------
    # Detect failed transaction
    # ---------------------------------------------------------

    failure_patterns = (
        "program failed",
        "custom program error",
        "anchorerror",
        "error code:",
        "error number:",
        "error message:",
        "failed:",
    )

    transaction_failed = any(
        pattern in log_text
        for pattern in failure_patterns
    )

    # ---------------------------------------------------------
    # FAILED SWAP
    #
    # A swap was attempted but the transaction failed.
    #
    # We require:
    # - swap/fill evidence
    # - failure evidence
    # - no actual token movement
    #
    # This prevents failed swaps from being counted
    # as successful trades.
    # ---------------------------------------------------------

    if (
        (swap_in_log or fill_in_log)
        and transaction_failed
        and not token_received
        and not token_sent
    ):

        return {
            "event": "SWAP_FAILED",
            "confidence": 0.95,
            "reason": (
                "Swap instruction was attempted but "
                f"the transaction failed on "
                f"{protocol_text}"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # FAILED LIQUIDITY
    # ---------------------------------------------------------

    if (
        liquidity_in_log
        and transaction_failed
        and not token_received
        and not token_sent
    ):

        return {
            "event": "LIQUIDITY_FAILED",
            "confidence": 0.95,
            "reason": (
                "Liquidity instruction was attempted "
                f"but the transaction failed on "
                f"{protocol_text}"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # LIQUIDITY
    # ---------------------------------------------------------

    if (
        liquidity_in_log
        and token_received
        and token_sent
    ):

        return {
            "event": "POSSIBLE_LIQUIDITY",
            "confidence": 0.90,
            "reason": (
                "Token movements and liquidity "
                f"instruction detected on "
                f"{protocol_text}"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # TOKEN-TO-TOKEN SWAP
    # ---------------------------------------------------------

    if (
        token_sent
        and token_received
        and swap_in_log
        and not transaction_failed
    ):

        return {
            "event": "TOKEN_SWAP",
            "confidence": 0.90,
            "reason": (
                "Wallet sent one token and received "
                f"another token; successful swap "
                f"detected on {protocol_text}"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # TOKEN-TO-TOKEN SWAP
    #
    # Some protocols may not expose a standard Swap log.
    # Verified protocol + both token directions is enough.
    # ---------------------------------------------------------

    if (
        token_sent
        and token_received
        and supports_swap
        and not transaction_failed
    ):

        return {
            "event": "TOKEN_SWAP",
            "confidence": 0.85,
            "reason": (
                "Wallet sent and received tokens "
                f"through verified swap protocol "
                f"{protocol_text}"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # BUY
    #
    # SOL decreases and token increases.
    # No token was sent.
    # ---------------------------------------------------------

    if (
        token_received
        and not token_sent
        and wallet_sol_change < 0
        and not transaction_failed
    ):

        confidence = 0.50

        if (
            supports_swap
            or swap_in_log
            or fill_in_log
        ):
            confidence += 0.20

        return {
            "event": "POSSIBLE_BUY",
            "confidence": min(
                confidence,
                1.0
            ),
            "reason": (
                "Wallet spent SOL and received "
                f"a token; swap evidence: "
                f"{protocol_text}"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # SELL
    #
    # Token decreases and SOL increases.
    # No token was received.
    # ---------------------------------------------------------

    if (
        token_sent
        and not token_received
        and wallet_sol_change > 0
        and not transaction_failed
    ):

        confidence = 0.50

        if (
            supports_swap
            or swap_in_log
            or fill_in_log
        ):
            confidence += 0.20

        return {
            "event": "POSSIBLE_SELL",
            "confidence": min(
                confidence,
                1.0
            ),
            "reason": (
                "Wallet received SOL and sent "
                f"a token; swap evidence: "
                f"{protocol_text}"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # TOKEN TRANSFER RECEIVED
    # ---------------------------------------------------------

    if (
        token_received
        and not token_sent
        and wallet_sol_change >= 0
        and not transaction_failed
    ):

        return {
            "event": "TRANSFER_RECEIVED",
            "confidence": 0.85,
            "reason": (
                "Wallet received a token "
                "without spending SOL"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # TOKEN TRANSFER SENT
    # ---------------------------------------------------------

    if (
        token_sent
        and not token_received
        and wallet_sol_change <= 0
        and not transaction_failed
    ):

        return {
            "event": "TRANSFER_SENT",
            "confidence": 0.85,
            "reason": (
                "Wallet sent a token "
                "without receiving SOL"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # SOL RECEIVED
    # ---------------------------------------------------------

    if (
        wallet_sol_change > 0
        and not token_received
        and not token_sent
        and not swap_in_log
        and not fill_in_log
        and not liquidity_in_log
        and not transaction_failed
    ):

        return {
            "event": "SOL_RECEIVED",
            "confidence": 0.80,
            "reason": (
                "Wallet received SOL "
                "without token movement"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # SOL SENT
    # ---------------------------------------------------------

    if (
        wallet_sol_change < 0
        and not token_received
        and not token_sent
        and not swap_in_log
        and not fill_in_log
        and not liquidity_in_log
        and not transaction_failed
    ):

        return {
            "event": "SOL_SENT",
            "confidence": 0.80,
            "reason": (
                "Wallet sent SOL "
                "without token movement"
            ),
            "protocols": verified_protocols
        }

    # ---------------------------------------------------------
    # UNKNOWN
    # ---------------------------------------------------------

    return {
        "event": "UNKNOWN",
        "confidence": 0.20,
        "reason": (
            "No reliable transaction pattern detected"
        ),
        "protocols": verified_protocols
    }