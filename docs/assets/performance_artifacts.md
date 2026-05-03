# Performance Artifact Template

Use this file to track the exact evidence behind README performance claims.

## Backtest Run

| Field | Value |
|---|---|
| Commit SHA | `f88d5c9b2b859ec4e21e7bb31868bcf7cdb9c0d1` |
| Dataset | BTCUSDT 1h 2022-01-01 to 2022-12-31 |
| Validation method | Walk-forward out-of-sample backtest |
| Command | `python main.py backtest --symbol BTCUSDT --interval 1h --start-date 2022-01-01 --end-date 2022-12-31 --balance 10000 --data-dir backtest/data/binance_historical` |
| Output directory | `backtest/runtime/20260503_010914_f3f0bbd4/` |
| Generated date | 2026-05-03 |
| Fee calibration | maker=0.022% taker=0.055% (Binance Futures VIP0 actual: 0.02%/0.05%; conservative buffer +10%) |

## Metrics

| Metric | Value |
|---|---:|
| Total return | -6.60% |
| Annualized Sharpe | -4.37 |
| Max drawdown | 14.29% |
| Win rate | 27.80% |
| Profit factor | 1.05 |
| Calmar ratio | -0.46 |
| Average holding time | 6.4 bars (6.4 h) |
| Inference latency | N/A (rule-based strategy, no model inference) |
| Total commission | 1,016.13 USDT (at corrected 0.055% taker) |
| Gross PnL | +358.82 USDT |
| Net PnL | -657.31 USDT |

## Figures

| Figure | File |
|---|---|
| Equity curve | `docs/assets/equity_curve.png` |
| Drawdown | `docs/assets/drawdown.png` |
| Signal vs price | `docs/assets/signal_vs_price.png` |
| Trade distribution | `docs/assets/trade_distribution.png` |

Only move a metric from TODO to README after the artifact file exists and the run command is documented.
