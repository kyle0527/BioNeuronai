# 0002 - Use Walk-Forward Validation for Public Performance Claims

## Status

Accepted

## Context

Static backtests can overstate strategy quality when parameters are tuned on the same data used for reporting.

## Decision

Public performance claims must come from reproducible walk-forward IS/OOS runs or be labeled as design targets.

## Consequences

- README metrics remain conservative until artifact files exist.
- Backtest charts should include command, dataset range, commit SHA, and generated output location.
- New strategy claims need evidence in `docs/assets/performance_artifacts.md`.
