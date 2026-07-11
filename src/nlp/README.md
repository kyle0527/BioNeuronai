# NLP and unified multimodal model

The active NLP implementation is `tiny_llm_v2.py`. It is not a separate chat model: the same 98.4M-parameter checkpoint is shared by numeric market inference, Chinese/English context understanding, trade decisions, and explanations.

## Active modules

- `tiny_llm_v2.py`: unified 16 x 64 numeric and bilingual Transformer/MoE model
- `chat_engine.py`: conversational interface over the shared model instance
- `bilingual_tokenizer.py`: shared tokenizer
- `training/unified_trainer.py`: only supported training entrypoint
- `training/advanced_trainer.py`: optimizer, checkpoint, and multi-head loss loop used by the unified trainer

## Runtime usage

```python
from bioneuronai.core.inference_engine import get_shared_inference_engine
from nlp.chat_engine import create_chat_engine

inference = get_shared_inference_engine()
chat = create_chat_engine(language="zh")
assert chat.model is inference.model_loader.get_model()
```

## Training data contract

Every numeric training row must contain real historical features, a 65-dimensional target derived from future market outcomes, bilingual context, and a matching explanation. Legacy 512-dimensional model outputs and synthetic samples are rejected.

```bash
python main.py collect-signal-data --symbol BTCUSDT --interval 1h --output data/unified_v2_training.jsonl
python -m nlp.training.unified_trainer --signal-data data/unified_v2_training.jsonl
```

Pre-unification model and trainer files are under `archived/legacy_v1_20260711/` and must not be imported by active code.
