# Walk-Forward IS/OOS: Engineering Against Backtest Illusions

Backtests are easy to make impressive and hard to make trustworthy. The main problem is leakage: strategy parameters can accidentally learn the entire dataset, then look strong on data they already influenced.

## The Decision

BioNeuronAI should report strategy quality using walk-forward validation:

- train or tune on an in-sample period,
- evaluate on a later out-of-sample period,
- roll the window forward,
- aggregate results across folds.

This is more work than a single full-period backtest, but it gives reviewers a better signal about whether the strategy survives changing market regimes.

## Why Retail Backtests Often Mislead

Common failure modes:

- tuning indicators on the same period used for final reporting,
- ignoring fees and slippage,
- using future data in feature engineering,
- reporting only total return while hiding drawdown,
- evaluating one lucky symbol and timeframe,
- changing code after seeing results without preserving run metadata.

## Engineering Requirements

A credible walk-forward result should include:

- commit SHA,
- dataset source and time range,
- symbol and interval,
- fee and slippage assumptions,
- fold definitions,
- generated equity and drawdown curves,
- raw run output,
- exact command used to reproduce.

The template in `docs/assets/performance_artifacts.md` exists for that reason.

## Reporting Standard

README performance claims should only use numbers that can be reproduced from checked-in commands or attached artifacts. If a number is a target, label it as a target. If a number is measured, link the evidence.
