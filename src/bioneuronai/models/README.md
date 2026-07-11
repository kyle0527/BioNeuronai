# bioneuronai.models

There is no active model implementation in this package. The single active model lives at `src/nlp/tiny_llm_v2.py`, and model loading is owned by `bioneuronai.core.inference_engine.ModelLoader`.

This directory remains only as a package boundary for compatibility with project imports. Legacy MLP code was moved to `archived/legacy_v1_20260711/legacy.py` and cannot be loaded by the active inference engine.

Use:

```python
from bioneuronai.core.inference_engine import get_shared_inference_engine
engine = get_shared_inference_engine()
```
