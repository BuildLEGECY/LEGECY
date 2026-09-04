# LEGECY - Transaction Decoder
#
# Converts raw wallet transaction data into
# readable wallet activities.
#
# Supports both:
# 1. Normalized wallet-intelligence data
# 2. Legacy test transaction format


from protocol_registry import identify_programs


SWAP_LOG_PATTERNS = (
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


LIQUIDITY_LOG_PATTERNS = (
    "instruction: addliquidity",
    "instruction: add liquidity",
    "instruction: removeliquidity",
    "instruction: remove liquidity",
    "instruction: increaseliquidity",
    "instruction: increase liquidity",
    "instruction: decreaseliquidity",
    "instruction: decrease liquidity",
    "instruction: deposit",
    "instruction: withdraw",
    "instruction: openposition",
    "instruction: closeposition",
    "instruction: increaseposition",
    "instruction: decreaseposition",
)


def _normalize_logs(logs):
    return [
        str(log).lower()
        for log in (logs or [])
    ]


def _has_swap_log(logs):
    return any(
        pattern in log
        for log in logs
        for pattern in SWAP_LOG_PATTERNS
    )


def _has_liquidity_log(logs):
    return any(
        pattern in log
        for log in logs
        for pattern in LIQUIDITY_LOG_PATTERNS
    )


def _token_sent(token_changes):
    return any(
        token.get("direction") == "sent"
        for token in (token_changes or [])
        if isinstance(token, dict)
    )


def _token_received(token_changes):
    return any(
        token.get("direction") == "received"
        for token in (token_changes or [])
        if isinstance(token, dict)
    )


def _legacy_token_changes(transaction):
    """
    Convert the old test format into the same token-change
    structure used by wallet_intelligence.py.
    """

    meta = transaction.get("meta", {})

    pre_tokens = {}
    post_tokens = {}

    for token in meta.get("preTokenBalances", []) or []:

        mint = str(token.get("mint"))

        amount_data = token.get(
            "uiTokenAmount",
            {}
        )

        amount = amount_data.get(
            "uiAmount",
            0
        ) or 0

        pre_tokens[mint] = (
            pre_tokens.get(mint, 0)
            + float(amount)
        )

    for token in meta.get("postTokenBalances", []) or []:

        mint = str(token.get("mint"))

        amount_data = token.get(
            "uiTokenAmount",
            {}
        )

        amount = amount_data.get(
            "uiAmount",
            0
        ) or 0

        post_tokens[mint] = (
            post_tokens.get(mint, 0)
            + float(amount)
        )

    all_tokens = (
        set(pre_tokens.keys())
        | set(post_tokens.keys())
    )

    changes = []

    for mint in all_tokens:

        before = pre_tokens.get(
            mint,
            0
        )

        after = post_tokens.get(
            mint,
            0
        )

        change = after - before

        if change == 0:
            continue

        direction = (
            "received"
            if change > 0
            else "sent"
        )

        changes.append(
            {
                "mint": mint,
                "before": before,
                "after": after,
                "change": change,
                "direction": direction
            }
        )

    return changes


def _get_token_changes(transaction):
    """
    Return normalized token changes regardless of
    which transaction format was supplied.
    """

    if "token_changes" in transaction:
        return transaction.get(
            "token_changes",
            []
        )

    return _legacy_token_changes(
        transaction
    )


def _get_sol_change(transaction):
    """
    Return normalized SOL change.

    Supports the live wallet-intelligence format
    and the legacy test format.
    """

    if "wallet_sol_change" in transaction:

        try:
            return float(
                transaction.get(
                    "wallet_sol_change",
                    0
                )
            )
        except (TypeError, ValueError):
            return 0.0

    meta = transaction.get(
        "meta",
        {}
    )

    pre = meta.get(
        "preBalances",
        []
    )

    post = meta.get(
        "postBalances",
        []
    )

    if not pre or not post:
        return 0.0

    try:
        return (
            float(post[0])
            - float(pre[0])
        ) / 1_000_000_000

    except (TypeError, ValueError, IndexError):
        return 0.0


def _get_programs(transaction):
    return transaction.get(
        "programs",
        []
    )


def _get_protocols(programs):
    try:
        return identify_programs(
            programs or []
        )
    except Exception:
        return []


def _protocol_names(protocols):
    names = []

    for protocol in protocols:

        if isinstance(protocol, dict):
            name = protocol.get("name")
        else:
            name = str(protocol)

        if name:
            names.append(
                str(name)
            )

    return names


def _find_protocol(
    protocols,
    supported_action=None
):
    for protocol in protocols:

        if not isinstance(
            protocol,
            dict
        ):
            continue

        name = protocol.get(
            "name"
        )

        if not name:
            continue

        if supported_action is None:
            return name

        actions = protocol.get(
            "supports",
            protocol.get(
                "supported_actions",
                []
            )
        )

        if isinstance(
            actions,
            str
        ):
            actions = [actions]

        actions = [
            str(action).upper()
            for action in actions
        ]

        if supported_action.upper() in actions:
            return name

    return None


def _get_transaction_failed(transaction):
    """
    Determine whether a transaction failed.

    Primary source is transaction_failed from
    wallet_intelligence.py.

    Also supports common legacy representations.
    """

    if transaction.get(
        "transaction_failed",
        False
    ):
        return True

    if transaction.get(
        "failed",
        False
    ):
        return True

    meta = transaction.get(
        "meta"
    )

    if isinstance(
        meta,
        dict
    ):
        return meta.get(
            "err"
        ) is not None

    return False


def classify_transaction(transaction):
    """
    Classify a wallet transaction.

    Priority:

    1. Failed transaction
    2. Successful token-to-token swap
    3. Buy
    4. Sell
    5. Liquidity
    6. Token transfers
    7. SOL movement
    8. Unknown
    """

    if transaction is None:
        return {
            "event": "UNKNOWN",
            "confidence": 0.0,
            "reason": "Transaction data is missing",
            "protocols": []
        }

    logs = _normalize_logs(
        transaction.get(
            "logs",
            []
        )
    )

    programs = _get_programs(
        transaction
    )

    token_changes = _get_token_changes(
        transaction
    )

    sol_change = _get_sol_change(
        transaction
    )

    protocols = _get_protocols(
        programs
    )

    protocol_names = _protocol_names(
        protocols
    )

    protocol_text = (
        protocol_names[0]
        if protocol_names
        else "unknown protocol"
    )

    token_sent = _token_sent(
        token_changes
    )

    token_received = _token_received(
        token_changes
    )

    swap_log = _has_swap_log(
        logs
    )

    liquidity_log = _has_liquidity_log(
        logs
    )

    transaction_failed = _get_transaction_failed(
        transaction
    )

    # ---------------------------------------------------------
    # FAILED TRANSACTION
    # ---------------------------------------------------------

    if transaction_failed:

        if swap_log or token_sent or token_received:

            return {
                "event": "SWAP_FAILED",
                "confidence": 0.95,
                "reason": (
                    "Swap instruction was attempted but "
                    f"the transaction failed on "
                    f"{protocol_text}"
                ),
                "protocols": protocols
            }

        verified_swap_protocol = _find_protocol(
            protocols,
            "SWAP"
        )

        if verified_swap_protocol:

            return {
                "event": "SWAP_FAILED",
                "confidence": 0.90,
                "reason": (
                    "Transaction failed while interacting "
                    "with verified swap protocol "
                    f"{verified_swap_protocol}"
                ),
                "protocols": protocols
            }

        return {
            "event": "UNKNOWN",
            "confidence": 0.10,
            "reason": (
                "Transaction failed but no reliable "
                "activity pattern was detected"
            ),
            "protocols": protocols
        }

    # ---------------------------------------------------------
    # SUCCESSFUL TOKEN-TO-TOKEN SWAP
    # ---------------------------------------------------------

    if (
        token_sent
        and token_received
        and swap_log
    ):

        return {
            "event": "TOKEN_SWAP",
            "confidence": 0.90,
            "reason": (
                "Wallet sent one token and received "
                "another token; successful swap detected "
                f"on {protocol_text}"
            ),
            "protocols": protocols
        }

    if (
        token_sent
        and token_received
    ):

        verified_swap_protocol = _find_protocol(
            protocols,
            "SWAP"
        )

        if verified_swap_protocol:

            return {
                "event": "TOKEN_SWAP",
                "confidence": 0.85,
                "reason": (
                    "Wallet sent and received tokens "
                    "through verified swap protocol "
                    f"{verified_swap_protocol}"
                ),
                "protocols": protocols
            }

    # ---------------------------------------------------------
    # BUY
    # ---------------------------------------------------------

    if (
        token_received
        and sol_change < 0
        and not token_sent
    ):

        return {
            "event": "POSSIBLE_BUY",
            "confidence": 0.75,
            "reason": (
                "Wallet received tokens while "
                "SOL balance decreased"
            ),
            "protocols": protocols
        }

    # ---------------------------------------------------------
    # SELL
    # ---------------------------------------------------------

    if (
        token_sent
        and sol_change > 0
        and not token_received
    ):

        return {
            "event": "POSSIBLE_SELL",
            "confidence": 0.75,
            "reason": (
                "Wallet sent tokens while "
                "SOL balance increased"
            ),
            "protocols": protocols
        }

    # ---------------------------------------------------------
    # LIQUIDITY
    # ---------------------------------------------------------

    if liquidity_log:

        return {
            "event": "POSSIBLE_LIQUIDITY",
            "confidence": 0.80,
            "reason": (
                "Liquidity-related instruction detected"
                f" on {protocol_text}"
            ),
            "protocols": protocols
        }

    # ---------------------------------------------------------
    # TOKEN TRANSFERS
    # ---------------------------------------------------------

    if token_received and not token_sent:

        return {
            "event": "TRANSFER_RECEIVED",
            "confidence": 0.70,
            "reason": (
                "Wallet received tokens without "
                "a reliable swap pattern"
            ),
            "protocols": protocols
        }

    if token_sent and not token_received:

        return {
            "event": "TRANSFER_SENT",
            "confidence": 0.70,
            "reason": (
                "Wallet sent tokens without "
                "a reliable swap pattern"
            ),
            "protocols": protocols
        }

    # ---------------------------------------------------------
    # SOL TRANSFERS
    # ---------------------------------------------------------

    if sol_change > 0:

        return {
            "event": "SOL_RECEIVED",
            "confidence": 0.65,
            "reason": (
                "Wallet SOL balance increased"
            ),
            "protocols": protocols
        }

    if sol_change < 0:

        return {
            "event": "SOL_SENT",
            "confidence": 0.65,
            "reason": (
                "Wallet SOL balance decreased"
            ),
            "protocols": protocols
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
        "protocols": protocols
    }