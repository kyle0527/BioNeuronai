# 16-Step Rolling Attention vs Single-Point Prediction

Single-point prediction asks the model to make a decision from the latest feature vector. That is convenient, but trading is rarely a one-tick problem. Breakouts, failed breakouts, momentum decay, and liquidity shifts are temporal patterns.

## The Decision

BioNeuronAI maintains a rolling feature window before inference. The window length is 16 by default. Each step carries engineered market features, and the transformer can attend across the window instead of seeing only the newest point.

## Why It Matters

A single feature vector can tell the model what the market looks like now. A rolling window lets the model compare:

- whether volatility is expanding or contracting,
- whether momentum is accelerating or fading,
- whether volume confirms price movement,
- whether recent states contradict the current candle,
- whether a signal is early, late, or already exhausted.

Attention is useful here because the important comparison is not always between adjacent candles. A candle can matter because it set a local high, marked a liquidity sweep, or started a regime change several steps earlier.

## Engineering Tradeoff

The rolling window adds state. That means the inference engine must handle warmup periods, missing data, and deterministic replay. The benefit is that the same production path can be used in live mode and backtest mode, reducing the gap between research and deployment.

## What To Measure

The correct test is not whether the architecture sounds more advanced. The project should compare:

- single-step vs 16-step walk-forward results,
- max drawdown,
- signal churn,
- latency,
- calibration of confidence,
- behavior during volatile regimes.

Until those comparisons are generated from reproducible runs, the 16-step design should be described as an implemented architecture choice, not as proven alpha.
