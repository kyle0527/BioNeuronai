"""Convert signal JSONL training data into PyTorch tensor files.

Input JSONL row format:
    {"features": [[...1024], ...], "signal": [...512]}

Output:
    train.pt
    val.pt
    manifest.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _normalize_feature_seq(features: Any, seq_len: int) -> np.ndarray:
    feat = np.asarray(features, dtype=np.float32)
    if feat.ndim != 2:
        raise ValueError(f"features must be 2D, got shape={feat.shape}")
    if feat.shape[0] < seq_len:
        pad = np.zeros((seq_len - feat.shape[0], feat.shape[1]), dtype=np.float32)
        feat = np.concatenate([pad, feat], axis=0)
    else:
        feat = feat[-seq_len:]
    return feat


def load_jsonl(
    path: Path,
    *,
    seq_len: int,
    max_samples: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray]:
    features: List[np.ndarray] = []
    signals: List[np.ndarray] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            features.append(_normalize_feature_seq(obj["features"], seq_len))
            signals.append(np.asarray(obj["signal"], dtype=np.float32))
            if max_samples is not None and len(features) >= max_samples:
                break
    if not features:
        raise ValueError(f"no valid samples found in {path}")
    return np.stack(features), np.stack(signals)


def save_split(
    features: np.ndarray,
    signals: np.ndarray,
    *,
    output_dir: Path,
    val_ratio: float,
    seed: int,
) -> Dict[str, Any]:
    rng = random.Random(seed)
    indices = list(range(len(features)))
    rng.shuffle(indices)

    val_count = int(len(indices) * val_ratio)
    val_indices = indices[:val_count]
    train_indices = indices[val_count:]

    output_dir.mkdir(parents=True, exist_ok=True)
    train_path = output_dir / "signal_train.pt"
    val_path = output_dir / "signal_val.pt"

    torch.save(
        {
            "features": torch.from_numpy(features[train_indices]),
            "signals": torch.from_numpy(signals[train_indices]),
        },
        train_path,
    )
    torch.save(
        {
            "features": torch.from_numpy(features[val_indices]),
            "signals": torch.from_numpy(signals[val_indices]),
        },
        val_path,
    )
    return {
        "train_path": str(train_path),
        "val_path": str(val_path),
        "train_samples": len(train_indices),
        "val_samples": len(val_indices),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare tensor signal data for cloud training")
    parser.add_argument("--input", required=True, type=Path, help="input signal_history JSONL")
    parser.add_argument("--output-dir", default=Path("data/processed"), type=Path)
    parser.add_argument("--seq-len", default=16, type=int)
    parser.add_argument("--val-ratio", default=0.1, type=float)
    parser.add_argument("--max-samples", default=None, type=int)
    parser.add_argument("--seed", default=42, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    features, signals = load_jsonl(args.input, seq_len=args.seq_len, max_samples=args.max_samples)
    split = save_split(
        features,
        signals,
        output_dir=args.output_dir,
        val_ratio=args.val_ratio,
        seed=args.seed,
    )
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input": str(args.input),
        "input_sha256": _sha256_file(args.input),
        "input_size_bytes": args.input.stat().st_size,
        "seq_len": args.seq_len,
        "feature_dim": int(features.shape[-1]),
        "signal_dim": int(signals.shape[-1]),
        "total_samples": int(len(features)),
        "val_ratio": args.val_ratio,
        "seed": args.seed,
        **split,
    }
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with open(args.output_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
