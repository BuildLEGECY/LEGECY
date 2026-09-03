# LEGECY 🧠

> An autonomous crypto intelligence agent built in public.

LEGECY is an experimental system I'm building to understand crypto markets through
on-chain activity, wallet behavior, social signals, token data, and market narratives.

The long-term goal is to build an agent that can observe, reason, learn from previous
events, manage risk, and eventually make its own trading decisions.

This project is being built from scratch and documented publicly.

There are no promises of profit.
There are no fake results.
If something breaks, it becomes part of the build log.

---

## 🧠 What LEGECY is trying to become

LEGECY is designed around several intelligence layers:

- 👛 Wallet Intelligence
- 🪙 Token Intelligence
- ⛓️ On-chain Intelligence
- 𝕏 Social Intelligence
- 📈 Market Intelligence
- 🧠 Research & Reasoning
- 🛡️ Risk Management
- 🤖 Autonomous Decision Making
- 💰 Trading Execution

The system will eventually connect these signals instead of looking at them separately.

Example:

Wallet activity
↓
Transaction decoding
↓
Token identification
↓
Market context
↓
Social/narrative signals
↓
Wallet reputation
↓
Risk analysis
↓
Opportunity score
↓
Decision

---

## 🚧 Current Status

LEGECY is in early development.

### Currently working on

- Solana wallet monitoring
- Detecting new wallet transactions
- Remembering previously processed transactions
- Transaction inspection
- Token/SOL balance change analysis
- Building the first transaction classification system

### Current limitation

A token appearing in a wallet does NOT automatically mean the wallet bought it.

It could be:

- transfer
- airdrop
- liquidity interaction
- token account operation
- swap
- another program interaction

So LEGECY is being built to inspect the actual transaction instead of making
simple assumptions.

---

## 🗺️ Roadmap

### Phase 1 — Foundation
- [x] Project repository
- [x] Solana connection
- [x] Wallet monitoring
- [x] Transaction memory
- [ ] Reliable transaction decoder

### Phase 2 — Wallet Intelligence
- [ ] Wallet profiles
- [ ] Trading history
- [ ] Entry/exit analysis
- [ ] Win/loss statistics
- [ ] Wallet reputation score
- [ ] Smart-wallet discovery

### Phase 3 — Token Intelligence
- [ ] Token metadata
- [ ] Liquidity analysis
- [ ] Holder distribution
- [ ] Volume analysis
- [ ] Token age
- [ ] Developer wallet analysis
- [ ] Risk signals

### Phase 4 — Social Intelligence
- [ ] X account monitoring
- [ ] Influencer tracking
- [ ] Token mentions
- [ ] Narrative detection
- [ ] Engagement analysis
- [ ] Social signal scoring

### Phase 5 — Master Intelligence
- [ ] Combine wallet + token + social signals
- [ ] Opportunity scoring
- [ ] Confidence scoring
- [ ] Risk engine
- [ ] Decision history
- [ ] Continuous thesis monitoring

### Phase 6 — Trading
- [ ] Backtesting
- [ ] Historical evaluation
- [ ] Execution engine
- [ ] Isolated trading wallet
- [ ] Small-scale live testing

Live trading will only be considered after the intelligence and risk systems
have been tested properly.

---

## 🏗️ Architecture

LEGECY is being designed as a multi-agent system.

```text
                    ┌─────────────────┐
                    │     LEGECY      │
                    │   Master Brain  │
                    └────────┬────────┘
                             │
        ┌────────────┬───────┼───────┬────────────┐
        ↓            ↓       ↓       ↓            ↓
     Wallet        Token     X      Research     Risk
     Agent         Agent   Agent     Agent       Agent
        │            │       │         │           │
        └────────────┴───────┴─────────┴───────────┘
                             │
                             ↓
                    Intelligence Layer
                             │
                             ↓
                       Decision Engine
                             │
                             ↓
                       Execution Layer
