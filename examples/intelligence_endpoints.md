# LEGECY Intelligence Endpoint Examples

These examples show what the major intelligence layers return after a wallet is supplied.

## 1. Wallet Profile

```text
GET /wallet/{wallet_address}
```

Returns the normalized wallet intelligence profile, including statistics, behavior, reputation, Smart Money signals, and data confidence.

## 2. Wallet Comparison

```text
GET /compare/{wallet_a}/{wallet_b}
```

Conceptually:

```text
Wallet A ──→ Profile A ──┐
                         ├──→ Comparison ──→ Metric winners + deltas + confidence
Wallet B ──→ Profile B ──┘
```

The comparison evaluates Smart Money, reputation, trading activity, token diversity, swap success/failure, and protocol diversity.

## 3. Smart Wallet Discovery

```text
GET /discover/{seed_wallet}
```

Conceptually:

```text
Seed Wallet
    ↓
Transaction History
    ↓
Repeated Co-signing / Interaction
    ↓
Candidate Wallets
    ↓
Candidate Intelligence
    ↓
Confidence-adjusted Discovery Score
```

A candidate with unavailable history is not treated as a high-quality discovery simply because it was observed once.

## 4. Smart Money Ranking

```text
GET /rank/{seed_wallet}
```

The ranking layer takes discovered wallets and applies a confidence-aware ranking process.

Example production QA result:

```text
Candidate wallet: E8MrQhcSKxeg9xSWWXycJaYjbiLMr17XNxxskWuDpump
Ranking score:    62.74
Smart Money:     63.30
Reputation:      64.00
Confidence:      60.00
```

The ranking score is a research signal, not a claim that the wallet will outperform in the future.

## 5. Watchlist

```text
POST   /watchlist
GET    /watchlist
DELETE /watchlist/{wallet_address}
```

Watchlist entries are stored persistently in SQLite in the normal production configuration.

## Design principle

Across all endpoints, LEGECY tries to preserve the same chain of evidence:

```text
Raw on-chain activity
        ↓
Decoded evidence
        ↓
Derived metrics
        ↓
Intelligence signals
        ↓
Confidence
        ↓
Decision-support output
```

This makes the system easier to inspect, test, and improve than a black-box score with no supporting evidence.
