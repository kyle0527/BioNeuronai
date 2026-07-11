# Legacy v1 archive

This directory contains the pre-unification model, trainers, packaging helper,
deprecated NLP RAG bridge, and checkpoints removed from active runtime on
2026-07-11.

Active runtime must use:

- `src/nlp/tiny_llm_v2.py`
- `src/bioneuronai/core/inference_engine.py`
- `src/nlp/training/unified_trainer.py`
- `config/active_model.json`

The archived files are offline migration references only. They must not be
imported, loaded, promoted, or used as training ground truth.
