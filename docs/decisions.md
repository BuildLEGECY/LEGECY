# Architecture Decisions

## Decision 001 — Read-only wallet monitoring

### Decision

LEGECY will initially monitor public wallets without controlling their funds.

### Why

The first priority is understanding market behavior.

Execution should come later.

---

## Decision 002 — No private keys in the repository

### Decision

Private keys and seed phrases will never be stored in the repository.

### Why

A public repository must not contain trading credentials.

---

## Decision 003 — Transaction classification must be evidence-based

### Decision

LEGECY should not classify a transaction as BUY or SELL from token balance
changes alone.

### Why

Token transfers, airdrops, liquidity operations and swaps can produce
similar balance changes.

The system should inspect transaction instructions and context.

---

## Decision 004 — Build before live trading

### Decision

No live trading during the initial intelligence-building phase.

### Why

The system needs to be tested before real funds are exposed.
