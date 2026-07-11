# Cloud Training Runbook

This runbook describes the unified v2 training path on a cloud GPU. The runtime can execute an untrained deterministic baseline, but no trained `unified_v2_100m` checkpoint is currently promoted.

## 📑 目錄

- [Goals](#goals)
- [1. Prepare Signal Data](#1-prepare-signal-data)
- [2. Local Real-Data Short Run](#2-local-real-data-short-run)
- [3. Build Training Image](#3-build-training-image)
- [4. Run Cloud Training](#4-run-cloud-training)
- [5. Resume Interrupted Training](#5-resume-interrupted-training)
- [6. Required Artifacts](#6-required-artifacts)
- [7. Promotion Gate](#7-promotion-gate)

---

## Goals

- Do not overwrite `model/unified_v2_100m.pth` during cloud experiments; promote through `config/active_model.json` only after validation.
- Train from versioned datasets and checkpoints.
- Save resumable checkpoints and a `run_manifest.json`.
- Promote a trained model only after operational and backtest validation.

## 1. Prepare Signal Data

Collect signal data from replay/backtest:

```bash
python main.py collect-signal-data \
  --symbol BTCUSDT \
  --interval 1h \
  --future-horizon 12 \
  --output data/unified_v2_training.jsonl
```

Convert JSONL into tensor files:

```bash
python tools/training/prepare_signal_tensors.py \
  --input data/unified_v2_training.jsonl \
  --output-dir data/processed \
  --seq-len 16 \
  --val-ratio 0.1
```

Expected outputs:

- `data/processed/signal_train.pt`
- `data/processed/signal_val.pt`
- `data/processed/manifest.json`

Current project status verified on 2026-07-11: `config/active_model.json` points to the deterministic untrained unified v2 architecture. `data/processed/` is git-ignored; training tensors must be uploaded to a cloud bucket or mounted into the cloud VM/container before a new cloud job starts.

Example GCS upload:

```bash
gcloud storage cp data/processed/signal_train.pt gs://YOUR_BUCKET/bioneuronai/data/processed/signal_train.pt
gcloud storage cp data/processed/signal_val.pt gs://YOUR_BUCKET/bioneuronai/data/processed/signal_val.pt
gcloud storage cp data/processed/manifest.json gs://YOUR_BUCKET/bioneuronai/data/processed/manifest.json
```

## 2. Local Real-Data Short Run

Use a tiny real-data subset before spending GPU time. This is an operational rehearsal of the real training entrypoint, not a smoke test file:

```bash
python -m nlp.training.unified_trainer \
  --sig-only \
  --signal-data data/unified_v2_training.jsonl \
  --max-signal-samples 4 \
  --epochs 1 \
  --batch 2 \
  --grad-accum 1 \
  --save-steps 1 \
  --output output/cloud_dryrun \
  --no-save
```

Pass criteria:

- loss prints without shape errors,
- `output/cloud_dryrun/final_model/model.pth` exists,
- `output/cloud_dryrun/checkpoint_latest/model.pth` exists,
- `output/cloud_dryrun/run_manifest.json` exists,
- `model/unified_v2_100m.pth` is not modified.
- `config/active_model.json` is changed only by an explicit promote step.

## 3. Build Training Image

```bash
docker build --target training -t bioneuronai-train:latest .
```

## 4. Run Cloud Training

Example with GCS inputs and output artifact sync:

```bash
docker run --gpus all --rm \
  -e GOOGLE_APPLICATION_CREDENTIALS=/secrets/gcp-sa.json \
  -e TRAINING_OUTPUT_URI=gs://YOUR_BUCKET/bioneuronai/training-runs/sig_run_001 \
  -v "$PWD/secrets:/secrets:ro" \
  bioneuronai-train:latest \
  --sig-only \
  --signal-data gs://YOUR_BUCKET/bioneuronai/data/processed/signal_train.pt \
  --signal-val-data gs://YOUR_BUCKET/bioneuronai/data/processed/signal_val.pt \
  --epochs 10 \
  --batch 8 \
  --grad-accum 4 \
  --save-steps 500 \
  --output /outputs/sig_run_001 \
  --no-save
```

The trainer downloads `gs://` inputs to `BIONEURONAI_CLOUD_CACHE` and uploads the completed output directory to `TRAINING_OUTPUT_URI`.

Example with mounted local paths:

```bash
docker run --gpus all --rm \
  -v "$PWD/data:/workspace/data" \
  -v "$PWD/model:/workspace/model" \
  -v "$PWD/output:/outputs" \
  bioneuronai-train:latest \
  --sig-only \
  --signal-data /workspace/data/processed/signal_train.pt \
  --signal-val-data /workspace/data/processed/signal_val.pt \
  --epochs 10 \
  --batch 8 \
  --grad-accum 4 \
  --save-steps 500 \
  --output /outputs/sig_run_001 \
  --no-save
```

## 5. Resume Interrupted Training

```bash
docker run --gpus all --rm \
  -v "$PWD/data:/workspace/data" \
  -v "$PWD/model:/workspace/model" \
  -v "$PWD/output:/outputs" \
  bioneuronai-train:latest \
  --sig-only \
  --signal-data /workspace/data/processed/signal_train.pt \
  --signal-val-data /workspace/data/processed/signal_val.pt \
  --epochs 10 \
  --batch 8 \
  --grad-accum 4 \
  --save-steps 500 \
  --output /outputs/sig_run_001 \
  --resume /outputs/sig_run_001/checkpoint_latest \
  --no-save
```

## 6. Required Artifacts

Keep these files for every run:

- `run_manifest.json`
- `training_history.json`
- `final_model/model.pth`
- `final_model/training_state.pth`
- `best_model/model.pth` if validation loss is available
- `checkpoint_latest/model.pth`
- dataset `manifest.json`

When running in a stateless container, set `TRAINING_OUTPUT_URI=gs://...` or pass `--cloud-output-uri gs://...`; otherwise checkpoints and logs remain inside the container filesystem and may be lost when the job exits.

## 7. Promotion Gate

Do not promote a cloud-trained checkpoint through `config/active_model.json` until it passes:

- chat sanity check if language mode is affected,
- signal shape and inference check,
- replay/backtest validation,
- walk-forward OOS validation,
- API status and pretrade operational validation,
- latency measurement on target hardware.

Promotion is a separate explicit step. A checkpoint must identify `TinyLLMv2`, contain the numeric encoder and 65-dimensional signal head, and pass the gates above before becoming active.

For inference after promotion, point the runtime to the promoted model with one of:

```bash
MODEL_PATH=gs://YOUR_BUCKET/bioneuronai/models/unified_v2_100m.pth
MODEL_DIR=gs://YOUR_BUCKET/bioneuronai/models
```
