import asyncio

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature

from transaction_decoder import classify_transaction


RPC_URL = "https://api.mainnet.solana.com"

REQUEST_DELAY = 0.8
MAX_RETRIES = 5


# =========================================================
# GET WALLET TRANSACTIONS
# =========================================================

async def get_wallet_transactions(wallet_address, limit=20):

    async with AsyncClient(RPC_URL) as client:

        await asyncio.sleep(REQUEST_DELAY)

        response = await client.get_signatures_for_address(
            Pubkey.from_string(wallet_address),
            limit=limit
        )

        return response.value


# =========================================================
# GET TRANSACTION DETAILS
# =========================================================

async def get_transaction_details(client, signature):

    for attempt in range(MAX_RETRIES):

        try:

            await asyncio.sleep(REQUEST_DELAY)

            response = await client.get_transaction(
                Signature.from_string(str(signature)),
                encoding="jsonParsed",
                max_supported_transaction_version=0
            )

            if response.value is None:
                return None

            return response.value

        except Exception as error:

            error_text = str(error)

            if (
                "429" in error_text
                or "Too Many Requests" in error_text
            ):

                wait_time = 2 ** attempt

                print(
                    f"RPC rate limit hit. "
                    f"Retrying in {wait_time}s..."
                )

                await asyncio.sleep(wait_time)

            else:

                print(
                    f"Transaction fetch failed: {error}"
                )

                return None

    return None


# =========================================================
# GET TRANSACTION METADATA
# =========================================================

def get_transaction_meta(tx):

    if tx is None:
        return None

    try:

        meta = tx.transaction.meta

        if meta is not None:
            return meta

    except AttributeError:
        pass

    return None


# =========================================================
# GET TRANSACTION MESSAGE
# =========================================================

def get_transaction_message(tx):

    if tx is None:
        return None

    try:

        return tx.transaction.transaction.message

    except AttributeError:

        return None


# =========================================================
# FIND WALLET INDEX
# =========================================================

def find_wallet_index(message, wallet_address):

    if message is None:
        return None

    for index, account in enumerate(message.account_keys):

        try:

            address = str(account.pubkey)

        except AttributeError:

            address = str(account)

        if address == wallet_address:

            return index

    return None


# =========================================================
# BUILD TRANSACTION INTELLIGENCE DATA
# =========================================================

def build_transaction_data(tx, wallet_address):

    if tx is None:
        return None

    # -----------------------------------------------------
    # Metadata
    # -----------------------------------------------------

    meta = get_transaction_meta(tx)

    if meta is None:
        return None

    # -----------------------------------------------------
    # Message
    # -----------------------------------------------------

    message = get_transaction_message(tx)

    if message is None:
        return None

    # -----------------------------------------------------
    # Wallet index
    # -----------------------------------------------------

    wallet_index = find_wallet_index(
        message,
        wallet_address
    )

    if wallet_index is None:
        return None

    # -----------------------------------------------------
    # SOL balance change
    # -----------------------------------------------------

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

    # -----------------------------------------------------
    # Token balances BEFORE
    # -----------------------------------------------------

    pre_tokens = {}

    for token in meta.pre_token_balances or []:

        owner = (
            str(token.owner)
            if token.owner
            else ""
        )

        if owner != wallet_address:
            continue

        key = (
            token.account_index,
            str(token.mint)
        )

        amount = (
            token.ui_token_amount.ui_amount
            or 0
        )

        pre_tokens[key] = amount

    # -----------------------------------------------------
    # Token balances AFTER
    # -----------------------------------------------------

    post_tokens = {}

    for token in meta.post_token_balances or []:

        owner = (
            str(token.owner)
            if token.owner
            else ""
        )

        if owner != wallet_address:
            continue

        key = (
            token.account_index,
            str(token.mint)
        )

        amount = (
            token.ui_token_amount.ui_amount
            or 0
        )

        post_tokens[key] = amount

    # -----------------------------------------------------
    # Calculate token movements
    # -----------------------------------------------------

    all_tokens = (
        set(pre_tokens.keys())
        | set(post_tokens.keys())
    )

    token_changes = []

    for key in all_tokens:

        before = pre_tokens.get(
            key,
            0
        )

        after = post_tokens.get(
            key,
            0
        )

        change = after - before

        if change == 0:
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
                "direction": direction
            }
        )

    # -----------------------------------------------------
    # Program IDs
    # -----------------------------------------------------

    programs = set()

    for instruction in message.instructions:

        try:

            programs.add(
                str(instruction.program_id)
            )

        except AttributeError:

            pass

    # -----------------------------------------------------
    # Inner program IDs
    # -----------------------------------------------------

    for inner_group in meta.inner_instructions or []:

        for instruction in inner_group.instructions:

            try:

                programs.add(
                    str(instruction.program_id)
                )

            except AttributeError:

                pass

    # -----------------------------------------------------
    # Logs
    # -----------------------------------------------------

    logs = []

    for log in meta.log_messages or []:

        logs.append(
            str(log)
        )

    # -----------------------------------------------------
    # Return intelligence data
    # -----------------------------------------------------

    return {

        "wallet_address": wallet_address,

        "wallet_sol_change": sol_change,

        "token_changes": token_changes,

        "programs": list(programs),

        "logs": logs
    }


# =========================================================
# ANALYZE ONE TRANSACTION
# =========================================================

async def analyze_transaction(
    client,
    signature,
    wallet_address
):

    tx = await get_transaction_details(
        client,
        signature
    )

    if tx is None:

        return {
            "signature": str(signature),
            "event": "UNAVAILABLE",
            "confidence": 0.0,
            "reason": "Transaction data unavailable"
        }

    data = build_transaction_data(
        tx,
        wallet_address
    )

    if data is None:

        return {
            "signature": str(signature),
            "event": "UNAVAILABLE",
            "confidence": 0.0,
            "reason": "Could not extract wallet transaction data"
        }

    # -----------------------------------------------------
    # Decode transaction
    # -----------------------------------------------------

    result = classify_transaction(
        data
    )

    # -----------------------------------------------------
    # Preserve protocol information
    # -----------------------------------------------------

    protocols = result.get(
        "protocols",
        []
    )

    # -----------------------------------------------------
    # Return complete wallet activity
    # -----------------------------------------------------

    return {

        "signature": str(signature),

        "event": result.get(
            "event",
            "UNKNOWN"
        ),

        "confidence": result.get(
            "confidence",
            0.0
        ),

        "reason": result.get(
            "reason",
            "No reason provided"
        ),

        "protocols": protocols,

        "wallet_sol_change": data.get(
            "wallet_sol_change",
            0.0
        ),

        "token_changes": data.get(
            "token_changes",
            []
        ),

        "programs": data.get(
            "programs",
            []
        )
    }


# =========================================================
# BUILD WALLET PROFILE
# =========================================================

async def build_wallet_profile(
    wallet_address,
    limit=20
):

    signatures = await get_wallet_transactions(
        wallet_address,
        limit=limit
    )

    activities = []

    unavailable = []

    async with AsyncClient(RPC_URL) as client:

        for item in signatures:

            signature = item.signature

            print()
            print(
                f"Analyzing: {signature}"
            )

            result = await analyze_transaction(
                client,
                signature,
                wallet_address
            )

            print(
                f"Event: {result['event']}"
            )

            print(
                f"Confidence: "
                f"{result['confidence']}"
            )

            print(
                f"Reason: "
                f"{result['reason']}"
            )

            # -------------------------------------------------
            # Print recognized protocols
            # -------------------------------------------------

            if result.get("protocols"):

                protocol_names = [
                    protocol["name"]
                    for protocol in result["protocols"]
                ]

                print(
                    f"Protocols: "
                    f"{', '.join(protocol_names)}"
                )

            # -------------------------------------------------
            # Store unavailable transactions separately
            # -------------------------------------------------

            if result["event"] == "UNAVAILABLE":

                unavailable.append(
                    result
                )

            else:

                activities.append(
                    result
                )

    # =====================================================
    # WALLET PROFILE
    # =====================================================

    return {

        "wallet": wallet_address,

        "transactions": [
            str(item.signature)
            for item in signatures
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
        )
    }