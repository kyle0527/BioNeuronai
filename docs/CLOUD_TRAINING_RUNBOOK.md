# Cloud Training Runbook

This runbook describes the safe path for running BioNeuronAI model training on a cloud GPU.

## Goals

- Do not overwrite `model/my_100m_model.pth` during cloud experiments.
- Train from versioned datasets and checkpoints.
- Save resumable checkpoints and a `run_manifest.json`.
- Promote a trained model only after operational and backtest validation.

## 1. Prepare Signal Data

Collect signal data from replay/backtest:

```bash
python -m bioneuronai.cli.main collect-signal-data \
  --symbol BTCUSDT \
  --interval 1h \
  --output data/signal_history.jsonl
```

Convert JSONL into tensor files:

```bash
python tools/training/prepare_signal_tensors.py \
  --input data/signal_history.jsonl \
  --output-dir data/processed \
  --seq-len 16 \
  --val-ratio 0.1
```

Expected outputs:

- `data/processed/signal_train.pt`
- `data/processed/signal_val.pt`
- `data/processed/manifest.json`

Upload these files to cloud storage or mount them into the cloud VM/container.

## 2. Local Dry Run

Use a tiny real-data subset before spending GPU time:

```bash
python -m nlp.training.unified_trainer \
  --sig-only \
  --signal-data data/signal_history.jsonl \
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
- `model/my_100m_model.pth` is not modified.

## 3. Build Training Image

```bash
docker build -f Dockerfile.train -t bioneuronai-train:latest .
```

## 4. Run Cloud Training

Example with mounted local paths:

```bash
docker run --gpus all --rm \
  -v "$PWD/data:/workspace/data" \
  -v "$PWD/model:/workspace/model" \
  -v "$PWD/output:/outputs" \
  bioneuronai-train:latest \
  --sig-only \
  --signal-data /workspace/data/processed/signal_train.pt \
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

## 7. Promotion Gate

Do not copy a cloud-trained checkpoint into `model/my_100m_model.pth` until it passes:

- chat sanity check if language mode is affected,
- signal shape and inference check,
- replay/backtest validation,
- walk-forward OOS validation,
- API status and pretrade operational validation,
- latency measurement on target hardware.

Promotion should be a separate explicit step, not part of training.
