from protocol_registry import identify_program


ORCA_WHIRLPOOL = "whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc"
RAYDIUM_AMM_V4 = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
JUPITER_Z = "61DFfeTKM7trxYcPQCM78bJ794ddZprZpAwAnLiwTpYH"


# ---------------------------------------------------------
# TEST 1 - ORCA
# ---------------------------------------------------------

result = identify_program(ORCA_WHIRLPOOL)

assert result is not None
assert result["name"] == "Orca Whirlpool"
assert result["category"] == "DEX"
assert "SWAP" in result["supports"]

print("TEST 1 - ORCA: PASS")


# ---------------------------------------------------------
# TEST 2 - RAYDIUM
# ---------------------------------------------------------

result = identify_program(RAYDIUM_AMM_V4)

assert result is not None
assert result["name"] == "Raydium AMM v4"
assert result["category"] == "DEX"
assert "SWAP" in result["supports"]

print("TEST 2 - RAYDIUM: PASS")


# ---------------------------------------------------------
# TEST 3 - JUPITER Z
# ---------------------------------------------------------

result = identify_program(JUPITER_Z)

assert result is not None
assert result["name"] == "Jupiter Z"
assert result["category"] == "SWAP_EXECUTION"
assert "SWAP" in result["supports"]

print("TEST 3 - JUPITER Z: PASS")


# ---------------------------------------------------------
# FINAL
# ---------------------------------------------------------

print()
print("ALL PROTOCOL REGISTRY TESTS PASSED")