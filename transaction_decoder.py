# LEGECY - Transaction Decoder
# Uses wallet-specific changes + verified protocol registry

from protocol_registry import identify_programs


def classify_transaction(transaction):
    """
    Classify a Solana transaction.

    Supports:
    1. Legacy test input using transaction["meta"]
    2. Wallet Intelligence input using:
       wallet_sol_change
       token_changes
       programs
       logs
    """

    # ---------------------------------------------------------
    # 1. Read wallet intelligence input
    # ---------------------------------------------------------

    wallet_sol_change = transaction.get("wallet_sol_change")
    token_changes = transaction.get("token_changes", [])
    programs = transaction.get("programs", [])
    logs = transaction.get("logs", [])

    # ---------------------------------------------------------
    # 2. Backward compatibility with old decoder tests
    # ---------------------------------------------------------

    if wallet_sol_change is None:
        meta = transaction.get("meta")

        if not meta:
            return {
                "event": "UNKNOWN",
                "confidence": 0.20,
                "reason": "Transaction metadata unavailable",
            }

        pre_balances = meta.get("preBalances", [])
        post_balances = meta.get("postBalances", [])

        if pre_balances and post_balances:
            wallet_sol_change = (
                post_balances[0] - pre_balances[0]
            ) / 1_000_000_000

        token_changes = []

        pre_tokens = meta.get("preTokenBalances", [])
        post_tokens = meta.get("postTokenBalances", [])

        for token in post_tokens:
            token_changes.append({
                "mint": token.get("mint"),
                "change": 1,
                "direction": "received",
            })

        for token in pre_tokens:
            token_changes.append({
                "mint": token.get("mint"),
                "change": -1,
                "direction": "sent",
            })

        programs = transaction.get("programs", [])
        logs = transaction.get("logs", [])

    # ---------------------------------------------------------
    # 3. Normalize values
    # ---------------------------------------------------------

    if wallet_sol_change is None:
        wallet_sol_change = 0.0

    try:
        wallet_sol_change = float(wallet_sol_change)
    except (TypeError, ValueError):
        wallet_sol_change = 0.0

    # ---------------------------------------------------------
    # 4. Determine token movement
    # ---------------------------------------------------------

    token_received = False
    token_sent = False

    for token in token_changes:
        direction = str(token.get("direction", "")).lower()

        change = token.get("change", 0)

        try:
            change = float(change)
        except (TypeError, ValueError):
            change = 0

        if direction in ("received", "receive", "in"):
            token_received = True

        elif direction in ("sent", "send", "out"):
            token_sent = True

        elif change > 0:
            token_received = True

        elif change < 0:
            token_sent = True

    # ---------------------------------------------------------
    # 5. Identify verified protocols
    # ---------------------------------------------------------

    verified_protocols = identify_programs(programs)

    protocol_names = [
        protocol["name"]
        for protocol in verified_protocols
    ]

    supports_swap = any(
        "SWAP" in protocol.get("supports", [])
        for protocol in verified_protocols
    )

    supports_liquidity = any(
        "LIQUIDITY" in protocol.get("supports", [])
        for protocol in verified_protocols
    )

    # ---------------------------------------------------------
    # 6. Inspect logs for swap/liquidity instructions
    # ---------------------------------------------------------

    log_text = " ".join(
        str(log).lower()
        for log in logs
    )

    swap_in_log = "instruction: swap" in log_text
    liquidity_in_log = (
        "instruction: addliquidity" in log_text
        or "instruction: removeliquidity" in log_text
        or "instruction: increase_liquidity" in log_text
        or "instruction: decrease_liquidity" in log_text
    )

    # ---------------------------------------------------------
    # 7. LIQUIDITY detection
    # ---------------------------------------------------------

    if (
        (supports_liquidity or liquidity_in_log)
        and token_received
        and token_sent
    ):
        protocol_text = (
            ", ".join(protocol_names)
            if protocol_names
            else "known liquidity protocol"
        )

        return {
            "event": "POSSIBLE_LIQUIDITY",
            "confidence": 0.80,
            "reason": (
                f"Token movement matches liquidity activity "
                f"on {protocol_text}"
            ),
            "protocols": verified_protocols,
        }

    # ---------------------------------------------------------
    # 8. SWAP / BUY detection
    # ---------------------------------------------------------

    if token_received and wallet_sol_change < 0:
        confidence = 0.50

        if supports_swap or swap_in_log:
            confidence += 0.20

        protocol_text = (
            ", ".join(protocol_names)
            if protocol_names
            else "unknown protocol"
        )

        return {
            "event": "POSSIBLE_BUY",
            "confidence": min(confidence, 1.0),
            "reason": (
                f"Wallet spent SOL and received a token; "
                f"swap evidence: {protocol_text}"
            ),
            "protocols": verified_protocols,
        }

    # ---------------------------------------------------------
    # 9. SWAP / SELL detection
    # ---------------------------------------------------------

    if token_sent and wallet_sol_change > 0:
        confidence = 0.50

        if supports_swap or swap_in_log:
            confidence += 0.20

        protocol_text = (
            ", ".join(protocol_names)
            if protocol_names
            else "unknown protocol"
        )

        return {
            "event": "POSSIBLE_SELL",
            "confidence": min(confidence, 1.0),
            "reason": (
                f"Wallet received SOL and sent a token; "
                f"swap evidence: {protocol_text}"
            ),
            "protocols": verified_protocols,
        }

    # ---------------------------------------------------------
    # 10. Token transfer received
    # ---------------------------------------------------------

    if token_received and wallet_sol_change >= 0:
        return {
            "event": "TRANSFER_RECEIVED",
            "confidence": 0.85,
            "reason": "Wallet received a token without spending SOL",
            "protocols": verified_protocols,
        }

    # ---------------------------------------------------------
    # 11. Token transfer sent
    # ---------------------------------------------------------

    if token_sent and wallet_sol_change <= 0:
        return {
            "event": "TRANSFER_SENT",
            "confidence": 0.85,
            "reason": "Wallet sent a token without receiving SOL",
            "protocols": verified_protocols,
        }

    # ---------------------------------------------------------
    # 12. Unknown
    # ---------------------------------------------------------

    return {
        "event": "UNKNOWN",
        "confidence": 0.20,
        "reason": "No reliable transaction pattern detected",
        "protocols": verified_protocols,
    }