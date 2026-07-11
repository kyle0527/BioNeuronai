# 0001 - Keep Dual-Modal TinyLLM as an Architecture Path

## Status

Accepted

## Context

The project needs numeric market reasoning, Chinese/English context understanding, a structured trade action, and an explanation under an approximately 100M-parameter hardware budget. Separate trading and chat checkpoints created divergent behavior and violated the single-source-of-truth requirement.

## Decision

Use `unified_v2_100m` as the only active architecture and checkpoint identity. TradingEngine, ChatEngine, and AutonomousOperator obtain the same process-wide InferenceEngine model. Legacy v1 weights and loaders are archived and rejected by the active loader.

## Consequences

- Runtime operability can be verified before training, but must report `trained=false` and cannot be treated as trading-quality evidence.
- Training data must contain real market features, a 65-dimensional target derived from future bars, bilingual context, and a grounded explanation.
- Promotion requires signal, language, backtest, walk-forward, latency, and operational validation of one checkpoint.
