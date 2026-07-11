# Core runtime

`core` owns the single active AI runtime and the single order execution engine.

## InferenceEngine

- Active model name: `unified_v2_100m`
- Architecture: `nlp.tiny_llm_v2.TinyLLMv2`
- Parameters: 98,403,413
- Feature SSOT: `FeaturePipeline` builds 1024 existing features and `to_v2_patch()` maps them to 16 x 64
- Output: 65-dimensional structured decision
- Text: Chinese/English context conditions the numeric decision; the same backbone produces explanation logits
- Lifecycle: `get_shared_inference_engine()` returns the process-wide shared instance

```python
from bioneuronai.core.inference_engine import get_shared_inference_engine
engine = get_shared_inference_engine()
signal = engine.predict("BTCUSDT", current_price, klines, context_text=news_context)
```

When no trained checkpoint exists, the model is deterministically initialized, `trained` is false, and output is only an end-to-end runtime check.

## TradingEngine

`TradingEngine` owns the connector, strategy fusion, shared inference service, order execution, ActionRecord lifecycle, EpisodicMemory, OnlineLearner, and AdaptiveLearningHub.

Autonomous planning does not create another production connector. Prepared autonomous paper orders are delegated to `TradingEngine.execute_prepared_order()`, and the shared close callback writes both TradingEngine learning state and the autonomous decision ledger.

## Model loading

Only TinyLLMv2 checkpoints are accepted. Legacy v1 and MLP files are stored under `archived/legacy_v1_20260711/` and the active loader rejects them. `config/active_model.json` is the only model configuration source.
