# BioNeuronAI Local Review Batches

Date: 2026-07-06

## Current Baseline

- Branch: `main`
- Remote: `origin/main`
- Commit parity: `ahead 0 / behind 0`
- Current commit: `af16557 chore: integrate WIP with origin/main baseline`
- Git conflict files: none
- `git diff --check`: passed
- `python -m compileall -q src/bioneuronai`: passed
- `python main.py status`: passes after restoring `bioneuronai.risk_management` package exports.

## Batch 1 - Must Review Before Any Deletion Commit

These deletions affect import/package/runtime behavior and should be handled first.

- `src/bioneuronai/risk_management/__init__.py`
  - Current impact: restored as the package export surface for `RiskManager`, `RiskParameters`, `RiskLevel`, and related traditional risk symbols.
  - Duplicate review folder result: no exact-content match found in `C:\D\待審查_重複檔案`; restored from the existing `position_manager.py` definitions rather than adding duplicate classes.
- `src/nlp/py.typed`
- `src/rag/py.typed`
- `src/schemas/py.typed`
- `tools/data_download/requirements.txt`

## Batch 2 - Frontend Tree Deletions

These are large tracked deletions. They should be reviewed as a group because they look like removed generated/frontend project trees.

- `frontend/devops-d/` deleted tracked files: 59
- `frontend/trading/` deleted tracked files: 47

Exact matches found in duplicate review folder:

- `frontend/devops-d/src/lib/utils.ts` -> `C:\D\待審查_重複檔案\utils.ts`
- `frontend/devops-d/theme.json` -> `C:\D\待審查_重複檔案\theme.json`
- `frontend/trading/src/lib/utils.ts` -> `C:\D\待審查_重複檔案\utils.ts`
- `frontend/trading/theme.json` -> `C:\D\待審查_重複檔案\theme.json`

No same-relative-path copies were found under `C:\D\待審查_重複檔案`.

## Batch 3 - Model Artifact Deletions

- `model/tiny_llm_en_zh_trained/config.json`
- `model/tiny_llm_en_zh_trained/special_tokens_map.json`
- `model/tiny_llm_en_zh_trained/tokenizer.pkl`
- `model/tiny_llm_en_zh_trained/tokenizer_config.json`
- `model/tiny_llm_en_zh_trained/vocab.json`

Exact match found in duplicate review folder:

- `model/tiny_llm_en_zh_trained/tokenizer.pkl` -> `C:\D\待審查_重複檔案\tokenizer.pkl`

## Batch 4 - Small Code Cleanups

These are small tracked modifications, not deletions.

- `src/bioneuronai/analysis/feature_engineering.py`
- `src/bioneuronai/data/binance_futures.py`
- `src/bioneuronai/risk_management/confidence_calibrator.py`
- `src/bioneuronai/strategies/base_strategy.py`

## Batch 5 - New Untracked Material

- `critical_errors_summary.md`
- `src/bioneuronai/mcps/` untracked files: 95
- `src/bioneuronai/terminals/` untracked files: 9

No same-relative-path copies were found under `C:\D\待審查_重複檔案`.

## Suggested Order

1. Review the remaining Batch 1 deletions (`py.typed` files and `tools/data_download/requirements.txt`) before any deletion commit.
2. Review Batch 4 small source edits after the runtime export fix, because they are low-volume and likely intentional lint cleanup.
3. Decide whether Batch 2 frontend trees are intended to stay deleted.
4. Decide whether Batch 3 model artifacts should stay deleted or be restored.
5. Decide whether Batch 5 untracked MCP/terminal files should be committed, ignored, or moved out.
