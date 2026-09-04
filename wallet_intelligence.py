import asyncio

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature

from transaction_decoder import classify_transaction
from wallet_statistics import calculate_wallet_statistics
from wallet_reputation import calculate_reputation_score


RPC_URL = "https://api.mainnet.solana.com"


async def get_wallet_transactions(client, wallet_address, limit=20):
    wallet = Pubkey.from_string(wallet_address)

    response = await client.get_signatures_for_address(
        wallet,
        limit=limit
    )

    if not response.value:
        return []

    return [
        item.signature
        for item in response.value
    ]


async def get_transaction_details(client, signature):
    try:
        response = await client.get_transaction(
            Signature.from_string(str(signature)),
            encoding="jsonParsed",
            max_supported_transaction_version=0
        )

        return response.value

    except Exception as exc:
        print(
            f"Transaction fetch failed: "
            f"{signature} -> {exc}"
        )
        return None


def get_transaction_meta(tx):
    try:
        return tx.transaction.meta
    except AttributeError:
        return None


def get_transaction_message(tx):
    try:
        return tx.transaction.transaction.message
    except AttributeError:
        return None


def find_wallet_index(message, wallet_address):
    try:
        account_keys = message.account_keys

        for index, account in enumerate(account_keys):
            try:
                pubkey = str(account.pubkey)
            except AttributeError:
                pubkey = str(account)

            if pubkey == wallet_address:
                return index

    except AttributeError:
        return None

    return None


def build_transaction_data(tx, wallet_address):
    if tx is None:
        return None

    meta = get_transaction_meta(tx)

    if meta is None:
        return None

    message = get_transaction_message(tx)

    if message is None:
        return None

    wallet_index = find_wallet_index(
        message,
        wallet_address
    )

    if wallet_index is None:
        return None

    # SOL movement
    pre_balances = meta.pre_balances
    post_balances = meta.post_balances

    if wallet_index >= len(pre_balances):
        return None

    if wallet_index >= len(post_balances):
        return None

    sol_change = (
        post_balances[wallet_index]
        - pre_balances[wallet_index]
    ) / 1_000_000_000

    # Token balances
    pre_tokens = {}
    post_tokens = {}

    for token in meta.pre_token_balances or []:
        owner = (
            str(token.owner)
            if token.owner
            else None
        )

        key = (
            token.account_index,
            str(token.mint)
        )

        try:
            amount = (
                int(token.ui_token_amount.amount)
                / (10 ** token.ui_token_amount.decimals)
            )
        except Exception:
            amount = (
                token.ui_token_amount.ui_amount
                or 0
            )

        pre_tokens[key] = {
            "amount": amount,
            "owner": owner,
            "account_index": token.account_index,
            "mint": str(token.mint)
        }

    for token in meta.post_token_balances or []:
        owner = (
            str(token.owner)
            if token.owner
            else None
        )

        key = (
            token.account_index,
            str(token.mint)
        )

        try:
            amount = (
                int(token.ui_token_amount.amount)
                / (10 ** token.ui_token_amount.decimals)
            )
        except Exception:
            amount = (
                token.ui_token_amount.ui_amount
                or 0
            )

        post_tokens[key] = {
            "amount": amount,
            "owner": owner,
            "account_index": token.account_index,
            "mint": str(token.mint)
        }

    # Work out which tokens actually moved.
    all_tokens = (
        set(pre_tokens.keys())
        | set(post_tokens.keys())
    )

    token_changes = []

    for key in all_tokens:
        before_data = pre_tokens.get(key)
        after_data = post_tokens.get(key)

        before = (
            before_data["amount"]
            if before_data
            else 0
        )

        after = (
            after_data["amount"]
            if after_data
            else 0
        )

        change = after - before

        if change == 0:
            continue

        owner = None

        if after_data and after_data.get("owner"):
            owner = after_data["owner"]
        elif before_data and before_data.get("owner"):
            owner = before_data["owner"]

        # If RPC gave us an owner, make sure it belongs
        # to the wallet we are analyzing.
        if owner is not None and owner != wallet_address:
            continue

        direction = "received"

        if change < 0:
            direction = "sent"

        token_changes.append(
            {
                "account_index": key[0],
                "mint": key[1],
                "before": before,
                "after": after,
                "change": change,
                "direction": direction,
                "owner": owner
            }
        )

    # Top-level programs
    programs = set()

    for instruction in message.instructions:
        try:
            programs.add(
                str(instruction.program_id)
            )
        except AttributeError:
            pass

    # Programs used by inner instructions
    for inner_group in meta.inner_instructions or []:
        for instruction in inner_group.instructions:
            try:
                programs.add(
                    str(instruction.program_id)
                )
            except AttributeError:
                pass

    # Transaction logs
    logs = [
        str(log)
        for log in (meta.log_messages or [])
    ]

    return {
        "wallet_address": wallet_address,
        "wallet_sol_change": sol_change,
        "token_changes": token_changes,
        "programs": list(programs),
        "logs": logs
    }


async def analyze_transaction(client, signature, wallet_address):
    tx = await get_transaction_details(
        client,
        signature
    )

    if tx is None:
        return None

    data = build_transaction_data(
        tx,
        wallet_address
    )

    if data is None:
        return None

    classification = classify_transaction(
        data
    )

    # Keep the protocol records exactly as they come
    # from the decoder. wallet_statistics.py uses them.
    protocols = classification.get(
        "protocols",
        []
    )

    return {
        "signature": str(signature),

        "event": classification.get(
            "event",
            "UNKNOWN"
        ),

        "confidence": classification.get(
            "confidence",
            0.0
        ),

        "reason": classification.get(
            "reason",
            ""
        ),

        "wallet_sol_change": data.get(
            "wallet_sol_change",
            0
        ),

        "token_changes": data.get(
            "token_changes",
            []
        ),

        "programs": data.get(
            "programs",
            []
        ),

        "protocols": protocols
    }


async def build_wallet_profile(wallet_address, limit=20):
    async with AsyncClient(RPC_URL) as client:

        signatures = await get_wallet_transactions(
            client,
            wallet_address,
            limit
        )

        activities = []
        unavailable = []

        for signature in signatures:

            analysis = await analyze_transaction(
                client,
                signature,
                wallet_address
            )

            if analysis is None:
                unavailable.append(
                    str(signature)
                )
                continue

            activities.append(analysis)

            print(
                f"Analyzing: {signature}"
            )

            print(
                f"Event: {analysis['event']}"
            )

            print(
                f"Confidence: {analysis['confidence']}"
            )

            print(
                f"Reason: {analysis['reason']}"
            )

            # Protocols are dictionaries internally,
            # so only convert them to names for display.
            if analysis["protocols"]:

                protocol_names = []

                for protocol in analysis["protocols"]:

                    if isinstance(protocol, dict):
                        name = protocol.get("name")

                        if name:
                            protocol_names.append(
                                str(name)
                            )

                    else:
                        protocol_names.append(
                            str(protocol)
                        )

                if protocol_names:
                    print(
                        "Protocols: "
                        + ", ".join(protocol_names)
                    )

            print()

        statistics = calculate_wallet_statistics(
            activities
        )

        reputation_score = calculate_reputation_score(
            statistics
        )

        statistics["reputation_score"] = (
            reputation_score
        )

        print("=" * 60)
        print("WALLET STATISTICS")
        print("=" * 60)

        print(
            f"Total activities: "
            f"{statistics.get('total_activities', 0)}"
        )

        print(
            f"Buys: "
            f"{statistics.get('buys', 0)}"
        )

        print(
            f"Sells: "
            f"{statistics.get('sells', 0)}"
        )

        print(
            f"Liquidity actions: "
            f"{statistics.get('liquidity_actions', 0)}"
        )

        print(
            f"Transfers received: "
            f"{statistics.get('transfers_received', 0)}"
        )

        print(
            f"Transfers sent: "
            f"{statistics.get('transfers_sent', 0)}"
        )

        print(
            f"Unknown: "
            f"{statistics.get('unknown', 0)}"
        )

        print(
            f"Unique tokens: "
            f"{statistics.get('unique_tokens', 0)}"
        )

        print(
            f"SOL spent: "
            f"{statistics.get('sol_spent', 0)}"
        )

        print(
            f"SOL received: "
            f"{statistics.get('sol_received', 0)}"
        )

        print(
            f"Reputation score: "
            f"{reputation_score}"
        )

        print("=" * 60)

        return {
            "wallet": wallet_address,

            "transactions": [
                str(signature)
                for signature in signatures
            ],

            "activities": activities,

            "unavailable": unavailable,

            "total_transactions": len(
                signatures
            ),

            "decoded_activities": len(
                activities
            ),

            "unavailable_transactions": len(
                unavailable
            ),

            "statistics": statistics
        }


if __name__ == "__main__":
    print(
        "wallet_intelligence.py loaded successfully."
    )