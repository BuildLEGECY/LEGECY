# LEGECY

> An on-chain wallet intelligence system for Solana, built in public.

LEGECY started as a simple wallet monitor. It has grown into a full wallet-intelligence pipeline that decodes Solana activity, identifies swaps and protocols, reconstructs trading behavior, calculates wallet statistics and reputation, scores smart-money signals, compares wallets, discovers related wallets, ranks candidates, and exposes the intelligence through an API and dashboard.

The project is being built openly: progress, bugs, failed experiments, decisions, and milestones are part of the journey.

**Important:** LEGECY is an intelligence and research system. Scores are signals, not financial advice or guarantees of profit.

---

## What LEGECY does today

The current system focuses on **Solana wallet intelligence**.

Given a wallet address, LEGECY can:

- fetch and analyze transaction history
- decode transaction activity
- detect protocols and program interactions
- detect token swaps
- identify failed swaps
- normalize SOL/WSOL activity
- extract trade data
- reconstruct trades with FIFO accounting
- calculate trading statistics and P/L foundations
- analyze wallet behavior
- calculate a wallet reputation score
- calculate a Smart Money score with confidence
- calculate data confidence based on analyzed coverage
- build a normalized wallet profile
- compare two wallets
- discover wallets repeatedly interacting with a seed wallet
- rank discovered wallets using confidence-adjusted intelligence
- maintain a persistent wallet watchlist
- expose the system through a FastAPI API
- serve a production dashboard

---

## Real end-to-end proof

LEGECY is designed to be understood from **input → processing → evidence → intelligence**, not just from a list of features.

### Example: enter a wallet, get intelligence

**Input**

```text
Wallet: BC2JZCGY6sXbQdXoqNzxm7JZxf9Q1bue8Ue9rAgbdwA7
Transaction history requested: 20
```

**Pipeline**

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

**Production QA result**

| Signal | Result |
|---|---:|
| Reputation | 64 / 100 |
| Reputation rating | MODERATE |
| Data confidence | 50% coverage |
| Smart Money score | 63.3 / 100 |
| Smart Money rating | MODERATE |
| Protocol observed | Raydium AMM v4 |
| Open positions | None |

These values demonstrate the actual output shape and intelligence flow captured during production QA. They are not predictions of future performance.

### The important part: confidence is visible

LEGECY does not hide incomplete data. A wallet profile tracks requested, analyzed, and unavailable transactions and exposes coverage/confidence alongside the intelligence. Smart Money scoring uses that confidence so incomplete data cannot simply look like strong intelligence.

For more concrete endpoint examples, see [`examples/wallet_analysis.md`](examples/wallet_analysis.md) and [`examples/intelligence_endpoints.md`](examples/intelligence_endpoints.md).

---

## Architecture

The current architecture is intentionally modular so individual intelligence layers can be improved without rewriting the whole system.

```text
                         ┌──────────────────────────┐
                         │        Solana RPC        │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │   Transaction History    │
                         │      + Wallet Data       │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │ Transaction Intelligence │
                         │  Decoder + Classification│
                         └────────────┬─────────────┘
                                      │
                         ┌────────────┼────────────┐
                         ▼            ▼            ▼
                   Protocols       Swaps        Balances
                         │            │            │
                         └────────────┼────────────┘
                                      ▼
                         ┌──────────────────────────┐
                         │       Trade Engine       │
                         │     FIFO / P&L Data      │
                         └────────────┬─────────────┘
                                      │
                         ┌────────────┼─────────────┐
                         ▼            ▼             ▼
                    Statistics     Behavior     Reputation
                         │            │             │
                         └────────────┼─────────────┘
                                      ▼
                         ┌──────────────────────────┐
                         │    Data Confidence       │
                         │   + Smart Money Engine   │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │     Wallet Profile       │
                         └────────────┬─────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
              Comparison        Discovery          Ranking
                    │                 │                 │
                    └─────────────────┼─────────────────┘
                                      ▼
                         ┌──────────────────────────┐
                         │       FastAPI API        │
                         │       + Watchlist        │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │       Web Dashboard      │
                         └──────────────────────────┘
```

---

## Core modules

| Module | Responsibility |
|---|---|
| `transaction_decoder.py` | Decode and classify transaction activity |
| `protocol_registry.py` | Identify known Solana protocols/programs |
| `swap_detector.py` | Detect successful and failed swaps |
| `trade_engine.py` | Extract trades and reconstruct FIFO positions/P&L |
| `wallet_statistics.py` | Trading and wallet-level statistics |
| `wallet_behavior.py` | Behavioral and trading-style signals |
| `wallet_reputation.py` | Reputation scoring and signals |
| `wallet_profile.py` | Normalize, summarize, save, and load wallet profiles |
| `smart_money_engine.py` | Smart Money scoring, ratings, and confidence |
| `wallet_intelligence_fast.py` | Concurrent wallet analysis for API workloads |
| `wallet_comparison.py` | Comparative wallet intelligence |
| `smart_wallet_discovery.py` | Discover repeatedly interacting wallets |
| `smart_money_ranking.py` | Confidence-adjusted wallet ranking |
| `watchlist.py` | Persistent wallet watchlist storage |
| `watchlist_api.py` | Watchlist REST endpoints |
| `api.py` | FastAPI application and production API |
| `dashboard/` | Web interface for wallet intelligence |

---

## API

Production API:

`https://legecy-production.up.railway.app`

### Main endpoints

| Endpoint | Purpose |
|---|---|
| `GET /` | Production dashboard |
| `GET /api` | API information |
| `GET /health` | Health check |
| `GET /metrics` | Runtime metrics |
| `GET /wallet/{wallet_address}` | Analyze a Solana wallet |
| `GET /compare/{wallet_a}/{wallet_b}` | Compare two wallets |
| `GET /discover/{seed_wallet}` | Discover related wallets |
| `GET /rank/{seed_wallet}` | Rank discovered wallets |

### Watchlist endpoints

The watchlist API supports persistent wallet tracking with add, list, remove, and lookup operations.

The default production storage is SQLite at `data/watchlist.db`. A Railway persistent volume should be mounted at `/app/data` so the database survives deployments and restarts.

---

## Data confidence

LEGECY does not treat an incomplete transaction sample as complete truth.

The wallet profile tracks:

- requested transactions
- analyzed transactions
- unavailable transactions
- coverage percentage
- confidence level

Smart Money scoring uses this confidence information so a wallet with weak or unavailable data cannot appear artificially strong simply because the sample is incomplete.

This is an important design principle of LEGECY: **the system should know when it does not know enough.**

---

## Smart Money intelligence

The Smart Money Engine combines multiple wallet signals rather than relying on a single metric.

Current signals include:

- trading activity
- token diversity
- protocol diversity
- swap reliability
- wallet reputation
- behavioral signals
- data confidence

The result includes a score from 0–100, a rating, confidence, positive signals, risk signals, and supporting metrics.

Ratings currently use:

- **STRONG** — 80+
- **GOOD** — 65+
- **MODERATE** — 50+
- **WEAK** — 35+
- **LOW** — below 35

These are analytical classifications, not predictions of future returns.

---

## Wallet comparison

LEGECY can compare two wallet profiles across multiple dimensions, including:

- Smart Money score
- reputation
- trading activity
- token diversity
- swap success
- swap failure rate
- protocol diversity

The comparison returns per-metric winners, score deltas, an overall winner, and a confidence value limited by the less-confident wallet.

The composite result is explicitly treated as a **comparative signal, not a financial prediction**.

---

## Smart wallet discovery

Discovery starts with a seed wallet and looks for wallets that repeatedly co-sign or interact within the seed wallet's transaction history.

Candidates are then analyzed separately. Discovery quality is adjusted by the candidate's data confidence so a candidate with little usable transaction data does not receive an inflated discovery score.

---

## Watchlist persistence

The watchlist uses SQLite for the normal configuration and retains compatibility with the older JSON storage mode.

SQLite provides:

- persistent storage
- duplicate prevention through a wallet primary key
- safe concurrent access settings
- migration support from legacy JSON storage

For Railway production, the database should live on a persistent volume mounted at `/app/data`.

---

## Security and reliability

Current production hardening includes:

- Solana wallet-address validation
- request rate limiting
- bounded RPC concurrency
- transaction-level failure isolation
- response caching
- request metrics
- explicit API error schemas
- restricted CORS configuration
- security response headers
- production HSTS
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- strict referrer policy
- restrictive permissions policy

Automated tests run through GitHub Actions on the main branch.

---

## Running locally

### 1. Clone the repository

```bash
git clone https://github.com/BuildLEGECY/LEGECY.git
cd LEGECY
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and provide the required Solana RPC configuration.

### 5. Run the API

```powershell
uvicorn api:app --host 0.0.0.0 --port 8000
```

Then open:

`http://localhost:8000`

---

## Tests

Run the full test suite with:

```powershell
pytest -q
```

The test suite covers transaction classification, decoding, protocol detection, wallet intelligence, statistics, reputation, profiles, trade processing, behavior, API behavior, wallet comparison, discovery, ranking, and watchlist persistence.

---

## Project status

### Completed

- [x] Solana wallet monitoring foundation
- [x] Transaction decoding and classification
- [x] Protocol registry
- [x] Swap detection
- [x] Failed swap detection
- [x] Trade extraction
- [x] SOL/WSOL normalization
- [x] FIFO trade engine foundation
- [x] Wallet statistics
- [x] Wallet behavior intelligence
- [x] Wallet reputation engine
- [x] Wallet profiles
- [x] Data confidence
- [x] Smart Money Engine
- [x] Concurrent API wallet analysis
- [x] Production FastAPI service
- [x] Production dashboard
- [x] Wallet comparison
- [x] Smart wallet discovery
- [x] Smart Money ranking
- [x] Persistent watchlist code
- [x] API security hardening
- [x] Automated regression testing
- [x] Railway production deployment
- [x] Real end-to-end proof examples

### In progress / next evolution

- [ ] Finalize production persistent-volume setup
- [ ] Continue performance tuning with real workload measurements
- [ ] Expand protocol and transaction coverage
- [ ] Improve trade reconstruction for more complex activity
- [ ] Build deeper token intelligence
- [ ] Add broader market and social intelligence
- [ ] Backtest intelligence signals
- [ ] Strengthen risk management
- [ ] Evaluate autonomous decision-making only after sufficient testing

---

## Long-term vision

LEGECY is not intended to remain a wallet dashboard.

The long-term direction is to connect multiple intelligence sources:

```text
Wallet Activity
      ↓
On-chain Intelligence
      ↓
Token Intelligence
      ↓
Market Context
      ↓
Social / Narrative Signals
      ↓
Research & Reasoning
      ↓
Reputation + Risk
      ↓
Opportunity Score
      ↓
Decision Engine
      ↓
Backtesting / Evaluation
      ↓
Controlled Execution
```

The important part is the order. **Intelligence and risk come before autonomous trading.**

---

## Build philosophy

LEGECY is being built from scratch and in public.

That means the project is not only about the final result. Bugs, failed assumptions, incomplete data, performance problems, design decisions, experiments, and lessons are all part of the project history.

The goal is simple:

> **Build an intelligence system that can inspect on-chain reality instead of guessing from surface-level signals.**

---

## Disclaimer

LEGECY is an experimental software project for blockchain data analysis and research. Scores and classifications are not financial advice, investment recommendations, or guarantees of performance. Any future trading functionality should be isolated, tested, risk-controlled, and evaluated independently before real capital is used.
