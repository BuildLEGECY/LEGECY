# LEGECY - Solana Protocol Registry
#
# Only add programs after their identity has been verified.


PROTOCOLS = {

    # ---------------------------------------------------------
    # Orca Whirlpool
    # ---------------------------------------------------------

    "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc": {
        "name": "Orca Whirlpool",
        "category": "DEX",
        "supports": [
            "SWAP",
            "LIQUIDITY",
        ],
    },


    # ---------------------------------------------------------
    # Raydium AMM v4
    # ---------------------------------------------------------

    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": {
        "name": "Raydium AMM v4",
        "category": "DEX",
        "supports": [
            "SWAP",
            "LIQUIDITY",
        ],
    },


    # ---------------------------------------------------------
    # Jupiter Z / Order Engine
    # ---------------------------------------------------------

    "61DFfeTKM7trxYcPQCM78bJ794ddZprZpAwAnLiwTpYH": {
        "name": "Jupiter Z",
        "category": "SWAP_EXECUTION",
        "supports": [
            "SWAP",
        ],
    },


    # ---------------------------------------------------------
    # Meteora DLMM
    # ---------------------------------------------------------

    "LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo": {
        "name": "Meteora DLMM",
        "category": "DEX",
        "supports": [
            "SWAP",
            "LIQUIDITY",
        ],
    },


    # ---------------------------------------------------------
    # Raydium CLMM
    # ---------------------------------------------------------

    "CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK": {
        "name": "Raydium CLMM",
        "category": "DEX",
        "supports": [
            "SWAP",
            "LIQUIDITY",
        ],
    },
}


def identify_program(program_id):
    """
    Identify one known Solana program.
    """

    if not program_id:
        return None

    return PROTOCOLS.get(str(program_id))


def identify_programs(program_ids):
    """
    Identify all known programs from a transaction.
    """

    results = []

    for program_id in program_ids:

        protocol = identify_program(program_id)

        if protocol:

            results.append({
                "program_id": str(program_id),
                "name": protocol["name"],
                "category": protocol["category"],
                "supports": protocol["supports"],
            })

    return results