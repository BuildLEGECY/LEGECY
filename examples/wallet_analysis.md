# Real Wallet Analysis Example

This example shows the intended LEGECY flow from a Solana wallet address to wallet intelligence.

## Input

```text
Wallet: BC2JZCGY6sXbQdXoqNzxm7JZxf9Q1bue8Ue9rAgbdwA7
Transaction history requested: 20
```

## Processing

```text
Solana Wallet
      ↓
Transaction History
      ↓
Transaction Decoder
      ↓
Protocol Detection
      ↓
Swap / Trade Extraction
      ↓
Wallet Statistics
      ↓
Behavior Analysis
      ↓
Reputation Engine
      ↓
Smart Money Engine
      ↓
Final Wallet Profile
```

## Example result

The following values are from a production dashboard analysis captured during LEGECY QA. They demonstrate the shape and meaning of the intelligence output; they are not a prediction of future wallet performance.

| Signal | Result |
|---|---:|
| Reputation | 64 / 100 |
| Reputation rating | MODERATE |
| Data confidence | 50% coverage |
| Smart Money score | 63.3 / 100 |
| Smart Money rating | MODERATE |
| Protocol observed | Raydium AMM v4 |
| Open positions | None |

## What the output means

LEGECY does not stop at returning raw transactions. It converts transaction activity into multiple intelligence layers:

- **Statistics** describe measurable wallet activity.
- **Behavior** describes trading style and patterns.
- **Reputation** summarizes wallet-level trust/risk signals.
- **Data confidence** shows how much of the requested history was successfully analyzed.
- **Smart Money** combines these signals into a confidence-aware classification.

The important distinction is that a score is only as reliable as the underlying data. LEGECY therefore exposes coverage and confidence instead of hiding incomplete analysis.

## API form

A wallet analysis is available through:

```text
GET /wallet/{wallet_address}
```

Production API:

```text
https://legecy-production.up.railway.app
```

See the main README for the full endpoint list and local setup instructions.
