# Unified v2 model training

## Scope

BioNeuronai has one active 98.4M-parameter model: `unified_v2_100m`. Numeric market inference, Chinese/English context, structured trade decisions, chat, and explanations share one checkpoint and one backbone.

## Current state

`config/active_model.json` currently declares `deterministic_untrained` until a real v2 checkpoint is produced. The model can run end to end, but its outputs are not learned behavior.

## Required real data

Synthetic samples and old 512-dimensional model outputs are rejected. Every JSONL row contains `features` with shape `(16,64)`, `signal` with shape `(65,)`, non-empty `context_text`, non-empty bilingual `explanation`, and the measured `future_outcome`. The collector derives these values from future real K-lines rather than from the current model.

## Collect data

```powershell
python main.py collect-signal-data `
  --symbol BTCUSDT `
  --interval 1h `
  --future-horizon 12 `
  --output data/unified_v2_training.jsonl
```

Collect separate time ranges for train and validation to avoid leakage. Do not split adjacent rows randomly when their future horizons overlap.

## Train

```powershell
python -m nlp.training.unified_trainer `
  --signal-data data/unified_v2_training.jsonl `
  --signal-val-data data/unified_v2_validation.jsonl `
  --epochs 10 `
  --batch 2 `
  --grad-accum 8 `
  --output output/unified_v2_training
```

The trainer uses classification losses for direction/confidence/leverage/hold/regime, regression losses for size/SL/TP/timeframe/uncertainty, BCE for patterns, and language cross-entropy for the market-grounded explanation.

## Output and promotion

Successful training writes `model/unified_v2_100m.pth` and updates `config/active_model.json` to `trained_checkpoint`. API promotion accepts only the same model name and verifies that the checkpoint contains the TinyLLMv2 numeric encoder.

## Device guidance

The current CPU machine is suitable for inference and static/short data validation. Full training may be divided by date range or run on an external GPU, but it must use the same data contract and checkpoint format. Do not replace unavailable compute with mock data.
