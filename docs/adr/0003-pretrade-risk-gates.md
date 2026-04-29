# 0003 - Gate Trade Execution Through Pretrade Risk Checks

## Status

Accepted

## Context

Trading systems can produce technically valid signals that should still be rejected because of account state, liquidity, drawdown, event risk, or unresolved market context.

## Decision

Trade execution should pass through pretrade checks and risk sizing before reaching execution connectors.

## Consequences

- Strategy confidence alone is not enough to place a trade.
- Kelly sizing, drawdown limits, account availability, and RAG/news context become first-class deployment checks.
- Operational validation should keep the pretrade chain executable through Docker, CLI, or API flows.
