# Model assets

`config/active_model.json` is the single source of truth for the active model.

## Active architecture

- Name: `unified_v2_100m`
- Class: `nlp.tiny_llm_v2.TinyLLMv2`
- Parameters: 98,403,413
- Inputs: 16 x 64 numeric patches plus Chinese/English context tokens
- Outputs: 65-dimensional structured trade decision plus grounded language logits
- Current state: deterministic untrained initialization until `model/unified_v2_100m.pth` is trained

The runtime, chat engine, trading engine, autonomous operator, trainer, API, and frontend all resolve this same model. No component may load an independent text or trading checkpoint.

## Files kept here

- `tokenizer/vocab.json`: shared Chinese/English ByteLevel BPE tokenizer artifact (maximum 16,000 tokens)
- `unified_v2_100m.pth`: generated only after real paired v2 training data has been used

Legacy v1 checkpoints and model packages are isolated in `archived/legacy_v1_20260711/` and are offline migration references only.

## Runtime

```python
from bioneuronai.core.inference_engine import get_shared_inference_engine

engine = get_shared_inference_engine()
print(engine.get_stats())
```

When no trained checkpoint exists, the runtime reports `trained: false` and marks explanations as `UNTRAINED`. It remains executable for end-to-end verification but must not be interpreted as learned model quality. A tokenizer artifact and a trained checkpoint are one versioned unit: do not replace the tokenizer with a different vocabulary without retraining the model text embedding and output head.
