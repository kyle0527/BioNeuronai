"""
統一訓練入口腳本 (Unified Trainer)
====================================
同一個 TinyLLL v2 訓練流程，同時支援數值決策與中英文說明：

  任務 A（語言）  ：用 trading_dialogue_data.py 的 QA 對進行 next-token 預測
  任務 B（訊號）  ：用回測歷史中的 (feature_seq, signal_label) 進行序列回歸

執行方式：
    python -m nlp.training.unified_trainer              # 預設多任務訓練
    python -m nlp.training.unified_trainer --lm-only    # 純語言訓練
    python -m nlp.training.unified_trainer --sig-only   # 純訊號訓練

輸出：
    model/unified_v2_100m.pth   ← 正式統一 checkpoint 輸出位置
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

# ── 路徑設定 ─────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parents[3]   # BioNeuronai/
_SRC  = _ROOT / "src"
for p in [str(_SRC), str(_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from bioneuronai.core.inference_engine import FeaturePipeline
from bioneuronai.data.cloud_storage import materialize_uri, upload_path
from nlp.bilingual_tokenizer import BilingualTokenizer
from nlp.tiny_llm_v2 import TinyLLMv2, TinyLLMv2Config
from nlp.training.advanced_trainer import Trainer, TrainingConfig
from nlp.training.build_vocab import collect_real_news_corpus
from nlp.training.trading_dialogue_data import ALL_TRADING_DATA

# ============================================================================
# 資料集：語言任務
# ============================================================================

class DialogueDataset(Dataset):
    """
    把 trading_dialogue_data 的 QA 對轉換成 next-token 語言模型格式。
    格式：[BOS] input [SEP] output [EOS]  → 預測每個位置的下一個 token
    """

    def __init__(
        self,
        data: List[dict],
        tokenizer: BilingualTokenizer,
        max_length: int = 256,
    ) -> None:
        self.tokenizer = tokenizer
        self.max_length = max_length
        self.samples: List[List[int]] = []

        bos = tokenizer.special_token_ids.get("bos_token", 1)
        sep = tokenizer.special_token_ids.get("sep_token", 4)
        eos = tokenizer.special_token_ids.get("eos_token", 2)
        pad = tokenizer.pad_token_id

        for item in data:
            inp = item.get("input", "")
            out = item.get("output", "")
            ids_in  = tokenizer.encode(inp,  add_special_tokens=False)
            ids_out = tokenizer.encode(out,  add_special_tokens=False)
            ids = [bos] + ids_in + [sep] + ids_out + [eos]
            # 截斷
            ids = ids[:max_length]
            # 填充至 max_length
            ids = ids + [pad] * (max_length - len(ids))
            self.samples.append(ids)

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        ids = torch.tensor(self.samples[idx], dtype=torch.long)
        return {"input_ids": ids, "labels": ids}


# ============================================================================
# 資料集：訊號任務
# ============================================================================

class SignalDataset(Dataset):
    """
    從回測資料庫讀取 (feature_seq, signal_label) 對。

    JSONL 格式（每行一筆）：
    {
        "features": [[f1, f2, ..., f1024], ...],   # shape (T, 1024)
        "signal":   [s1, s2, ..., s65],             # v2 結構化目標
        "context_text": "中英文市場脈絡",
        "explanation": "與 signal 一致的交易說明"
    }
    """

    def __init__(
        self,
        tokenizer: BilingualTokenizer,
        data_path: Optional[Path] = None,
        seq_len: int = 16,
        max_samples: Optional[int] = None,
    ) -> None:
        self.tokenizer = tokenizer
        self.seq_len = seq_len
        self.samples: List[Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]] = []

        if data_path and data_path.exists():
            if data_path.suffix.lower() == ".pt":
                self._load_tensor_file(data_path, max_samples=max_samples)
            else:
                self._load_jsonl(data_path, max_samples=max_samples)
            if not self.samples:
                raise ValueError(f"訊號資料檔為空或沒有有效樣本: {data_path}")
        else:
            target = str(data_path) if data_path else "未指定 --signal-data"
            raise FileNotFoundError(
                f"找不到真實訊號資料: {target}。"
                " 統一訓練器禁止合成資料，請提供帶未來結果與雙語說明的 v2 資料。"
            )

    def _prepare_sample(
        self,
        features: np.ndarray,
        signal: np.ndarray,
        context_text: str,
        explanation: str,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        if features.ndim != 2:
            raise ValueError(f"features 必須為二維，收到 {features.shape}")
        if features.shape[-1] == FeaturePipeline.TOTAL_FEATURES:
            features = FeaturePipeline.to_v2_patch(features)
        if features.shape[-1] != 64:
            raise ValueError(f"features 最後一維必須是 64 或 1024，收到 {features.shape}")
        if signal.shape != (65,):
            raise ValueError(
                f"signal 必須是 v2 的 65 維真實目標，收到 {signal.shape}；"
                "舊 512 維模型輸出禁止作為 ground truth"
            )
        if not context_text.strip() or not explanation.strip():
            raise ValueError("每筆 v2 訓練資料都必須包含 context_text 與 explanation")

        if features.shape[0] < self.seq_len:
            first = features[:1]
            padding = np.repeat(first, self.seq_len - features.shape[0], axis=0)
            features = np.concatenate([padding, features], axis=0)
        else:
            features = features[-self.seq_len:]

        context_ids = self.tokenizer.encode(
            context_text, max_length=128, truncation=True, add_special_tokens=True
        )
        eos = self.tokenizer.eos_token_id
        sep = self.tokenizer.special_token_ids.get("sep_token", 4)
        explanation_tokens = self.tokenizer.encode(
            explanation, add_special_tokens=False
        )
        sequence = (context_ids[:-1] + [sep] + explanation_tokens + [eos])[:128]
        prompt_length = min(len(context_ids), len(sequence))
        labels = [-100] * prompt_length + sequence[prompt_length:]
        pad_count = 128 - len(sequence)
        sequence = sequence + [self.tokenizer.pad_token_id] * pad_count
        labels = labels + [-100] * pad_count
        context_ids = context_ids[:128] + [self.tokenizer.pad_token_id] * (128 - len(context_ids[:128]))
        return (
            features.astype(np.float32),
            signal.astype(np.float32),
            np.asarray(context_ids, dtype=np.int64),
            np.asarray(sequence, dtype=np.int64),
            np.asarray(labels, dtype=np.int64),
        )

    def _load_jsonl(self, path: Path, max_samples: Optional[int] = None) -> None:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                feat = np.array(obj["features"], dtype=np.float32)
                sig = np.array(obj["signal"], dtype=np.float32)
                self.samples.append(
                    self._prepare_sample(
                        feat,
                        sig,
                        str(obj.get("context_text") or ""),
                        str(obj.get("explanation") or ""),
                    )
                )
                if max_samples is not None and len(self.samples) >= max_samples:
                    break

    def _load_tensor_file(self, path: Path, max_samples: Optional[int] = None) -> None:
        payload = torch.load(path, map_location="cpu", weights_only=False)
        features = payload["features"]
        signals = payload["signals"]
        contexts = payload.get("contexts")
        explanations = payload.get("explanations")
        if contexts is None or explanations is None:
            raise ValueError("v2 .pt 資料必須包含 contexts 與 explanations")
        if isinstance(features, torch.Tensor):
            features = features.numpy()
        if isinstance(signals, torch.Tensor):
            signals = signals.numpy()
        limit = len(features) if max_samples is None else min(len(features), max_samples)
        for idx in range(limit):
            feat = np.asarray(features[idx], dtype=np.float32)
            sig = np.asarray(signals[idx], dtype=np.float32)
            self.samples.append(
                self._prepare_sample(feat, sig, str(contexts[idx]), str(explanations[idx]))
            )

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        feat, sig, context_ids, explanation_ids, explanation_labels = self.samples[idx]
        return {
            "feature_seq": torch.from_numpy(feat),
            "signal_labels": torch.from_numpy(sig),
            "context_ids": torch.from_numpy(context_ids),
            "explanation_ids": torch.from_numpy(explanation_ids),
            "explanation_labels": torch.from_numpy(explanation_labels),
        }


# ============================================================================
# DataLoader 工廠
# ============================================================================

class _WrappedLoader:
    """使 DataLoader 輸出符合 Trainer 期待的 dict 格式"""
    def __init__(self, dl: DataLoader) -> None:
        self._dl = dl
    def __iter__(self):
        return iter(self._dl)
    def __len__(self) -> int:
        return len(self._dl)


def build_lm_dataloader(
    tokenizer: BilingualTokenizer,
    batch_size: int = 8,
    max_length: int = 256,
    val_ratio: float = 0.1,
) -> Tuple[_WrappedLoader, Optional[_WrappedLoader]]:
    random.shuffle(ALL_TRADING_DATA)
    split = max(1, int(len(ALL_TRADING_DATA) * (1 - val_ratio)))
    train_data = ALL_TRADING_DATA[:split]
    val_data   = ALL_TRADING_DATA[split:]

    train_ds = DialogueDataset(train_data, tokenizer, max_length)
    val_ds   = DialogueDataset(val_data,   tokenizer, max_length) if val_data else None

    train_dl = _WrappedLoader(DataLoader(train_ds, batch_size=batch_size, shuffle=True,  num_workers=0))
    val_dl   = _WrappedLoader(DataLoader(val_ds,   batch_size=batch_size, shuffle=False, num_workers=0)) if val_ds else None

    return train_dl, val_dl


def build_signal_dataloader(
    data_path: Optional[Path],
    tokenizer: BilingualTokenizer,
    seq_len: int = 16,
    batch_size: int = 8,
    max_samples: Optional[int] = None,
) -> _WrappedLoader:
    ds = SignalDataset(
        tokenizer,
        data_path,
        seq_len=seq_len,
        max_samples=max_samples,
    )
    return _WrappedLoader(DataLoader(ds, batch_size=batch_size, shuffle=True, num_workers=0))


def set_training_seed(seed: int) -> None:
    """固定常見亂數來源，讓雲端 dry run 與短訓練較容易重現。"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True


def _sha256_file(path: Optional[Path]) -> Optional[str]:
    if path is None or not path.exists() or not path.is_file():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_commit() -> Optional[str]:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(_ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return None


def _file_info(path: Optional[Path], include_hash: bool = True) -> Dict[str, Any]:
    if path is None:
        return {"path": None, "exists": False}
    info: Dict[str, Any] = {
        "path": str(path),
        "exists": path.exists(),
    }
    if path.exists() and path.is_file():
        info["size_bytes"] = path.stat().st_size
        if include_hash:
            info["sha256"] = _sha256_file(path)
    return info


def _write_run_manifest(
    output_dir: Path,
    *,
    args: Dict[str, Any],
    signal_data_path: Optional[Path],
    base_model_path: Optional[Path],
    status: str,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "platform": {
            "python": sys.version,
            "system": platform.platform(),
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "torch": torch.__version__,
        },
        "arguments": args,
        "artifacts": {
            "signal_data": _file_info(signal_data_path),
            "base_model": _file_info(base_model_path),
            "output_dir": str(output_dir),
            "final_model": str(output_dir / "final_model" / "model.pth"),
            "best_model": str(output_dir / "best_model" / "model.pth"),
            "checkpoint_latest": str(output_dir / "checkpoint_latest" / "model.pth"),
        },
        "environment": {
            "TRAINING_JOB_ID": os.getenv("TRAINING_JOB_ID"),
            "CUDA_VISIBLE_DEVICES": os.getenv("CUDA_VISIBLE_DEVICES"),
            "TRAINING_OUTPUT_URI": os.getenv("TRAINING_OUTPUT_URI"),
        },
    }
    with open(output_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


# ============================================================================
# Tokenizer 工具
# ============================================================================

def _build_and_save_vocab(tokenizer: BilingualTokenizer, dest: Path) -> None:
    """從正式中英文新聞快照建立 tokenizer，禁止使用合成示例語料。"""
    texts = collect_real_news_corpus()
    tokenizer.build_vocab(texts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(dest))
    print(f"[unified_trainer] tokenizer 已建立並儲存至 {dest}  ({len(tokenizer.vocab)} tokens)")


# ============================================================================
# 主訓練流程
# ============================================================================

def build_model(model_path: Optional[Path] = None) -> Tuple[TinyLLMv2, BilingualTokenizer]:
    """建立或載入模型與分詞器"""
    tokenizer = BilingualTokenizer(vocab_size=16000)

    # 嘗試載入已有詞彙；若不存在則從訓練語料自動建立
    tok_file = _ROOT / "model" / "tokenizer" / "vocab.json"
    if tok_file.exists():
        try:
            tokenizer = BilingualTokenizer.load(str(tok_file))
            print(f"[unified_trainer] tokenizer 載入自 {tok_file}")
        except Exception as e:
            print(f"[unified_trainer] tokenizer 載入失敗，重新建立: {e}")
            _build_and_save_vocab(tokenizer, tok_file)
    else:
        print("[unified_trainer] 未找到 tokenizer，從訓練語料建立詞彙...")
        _build_and_save_vocab(tokenizer, tok_file)

    max_token_id = max(tokenizer.id_to_token, default=0)
    active_path = _ROOT / "config" / "active_model.json"
    active = json.loads(active_path.read_text(encoding="utf-8"))
    cfg = TinyLLMv2Config.from_dict(active.get("config") or {})
    if max_token_id >= cfg.vocab_size:
        raise ValueError(
            f"tokenizer 最大 token id {max_token_id} 超過統一詞表 {cfg.vocab_size}"
        )
    model = TinyLLMv2(cfg)

    # 嘗試載入已有權重
    configured_path = active.get("model_path")
    ckpt = model_path or ((_ROOT / configured_path) if configured_path else None)
    if ckpt is not None and ckpt.exists():
        try:
            checkpoint = torch.load(str(ckpt), map_location="cpu", weights_only=True)
            # 支援新格式 {'state_dict':..., 'config':...} 及舊格式（純 OrderedDict）
            if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                state = checkpoint["state_dict"]
            else:
                state = checkpoint
            model.load_state_dict(state, strict=True)
            setattr(model, "is_trained", True)
            print(f"[unified_trainer] 統一 v2 權重載入自 {ckpt}（完整載入）")
        except Exception as e:
            raise RuntimeError(f"基礎權重不是相容的統一 v2 checkpoint: {ckpt}") from e
    else:
        setattr(model, "is_trained", False)
        print("[unified_trainer] 尚無 v2 checkpoint，依 active_model 設定初始化")

    total = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"[unified_trainer] 模型參數量: {total:.1f}M")
    return model, tokenizer


def train(
    lm_only: bool = False,
    sig_only: bool = False,
    epochs: int = 10,
    batch_size: int = 8,
    lr: float = 3e-4,
    signal_data_path: Optional[Union[str, Path]] = None,
    signal_val_data_path: Optional[Union[str, Path]] = None,
    output_dir: str = "./output/unified",
    save_to_model: bool = True,
    base_model_path: Optional[Union[str, Path]] = None,
    resume_from: Optional[Union[str, Path]] = None,
    max_signal_samples: Optional[int] = None,
    seed: int = 42,
    save_steps: int = 500,
    gradient_accumulation_steps: int = 4,
    cloud_output_uri: Optional[str] = None,
) -> None:
    """
    執行訓練。

    Args:
        lm_only:           只訓練語言任務（不啟用多任務）
        sig_only:          只訓練訊號任務（不啟用語言任務）
        epochs:            訓練輪數
        batch_size:        批次大小
        lr:                學習率
        signal_data_path:  訊號任務 JSONL 資料路徑
        output_dir:        檢查點輸出目錄
        save_to_model:     訓練完成後是否寫入 model/unified_v2_100m.pth
    """
    set_training_seed(seed)
    original_signal_data_path = str(signal_data_path) if signal_data_path else None
    original_signal_val_data_path = str(signal_val_data_path) if signal_val_data_path else None
    original_base_model_path = str(base_model_path) if base_model_path else None
    original_resume_from = str(resume_from) if resume_from else None

    resolved_signal_data_path = materialize_uri(signal_data_path) if signal_data_path else None
    resolved_signal_val_data_path = materialize_uri(signal_val_data_path) if signal_val_data_path else None
    resolved_base_model_path = materialize_uri(base_model_path) if base_model_path else None
    resolved_resume_from = materialize_uri(resume_from) if resume_from else None

    model, tokenizer = build_model(resolved_base_model_path)
    output_path = Path(output_dir)
    cloud_output_uri = cloud_output_uri or os.getenv("TRAINING_OUTPUT_URI") or os.getenv("GCS_OUTPUT_URI")
    manifest_args = {
        "lm_only": lm_only,
        "sig_only": sig_only,
        "epochs": epochs,
        "batch_size": batch_size,
        "learning_rate": lr,
        "signal_data_path": original_signal_data_path,
        "signal_val_data_path": original_signal_val_data_path,
        "resolved_signal_data_path": str(resolved_signal_data_path) if resolved_signal_data_path else None,
        "resolved_signal_val_data_path": str(resolved_signal_val_data_path) if resolved_signal_val_data_path else None,
        "output_dir": output_dir,
        "cloud_output_uri": cloud_output_uri,
        "save_to_model": save_to_model,
        "base_model_path": original_base_model_path,
        "resolved_base_model_path": str(resolved_base_model_path) if resolved_base_model_path else None,
        "resume_from": original_resume_from,
        "resolved_resume_from": str(resolved_resume_from) if resolved_resume_from else None,
        "max_signal_samples": max_signal_samples,
        "seed": seed,
        "save_steps": save_steps,
        "gradient_accumulation_steps": gradient_accumulation_steps,
    }
    _write_run_manifest(
        output_path,
        args=manifest_args,
        signal_data_path=resolved_signal_data_path,
        base_model_path=resolved_base_model_path,
        status="started",
    )

    multitask = (not lm_only) and (not sig_only)

    if not lm_only and resolved_signal_data_path is None:
        raise ValueError(
            "signal 任務需要真實 v2 配對資料，請使用 --signal-data 指定 JSONL/.pt。"
        )

    cfg = TrainingConfig(
        batch_size=batch_size,
        gradient_accumulation_steps=gradient_accumulation_steps,
        max_epochs=epochs,
        learning_rate=lr,
        warmup_steps=200,
        lr_scheduler_type="cosine",
        use_amp=torch.cuda.is_available(),
        eval_steps=500,
        save_steps=save_steps,
        logging_steps=50,
        output_dir=output_dir,
        multitask=multitask,
        signal_loss_weight=0.5,
        signal_seq_len=16,
    )

    # ── 語言任務資料 ─────────────────────────────────────────────────────────
    train_dl: Optional[_WrappedLoader] = None
    val_dl: Optional[_WrappedLoader] = None
    if not sig_only:
        train_dl, val_dl = build_lm_dataloader(tokenizer, batch_size=batch_size)
        print(f"[unified_trainer] 語言任務: {len(train_dl)} batches")

    # ── 訊號任務資料 ─────────────────────────────────────────────────────────
    signal_dl = None
    if not lm_only:
        signal_dl = build_signal_dataloader(
            resolved_signal_data_path,
            tokenizer,
            seq_len=cfg.signal_seq_len,
            batch_size=batch_size,
            max_samples=max_signal_samples,
        )
        print(f"[unified_trainer] 訊號與說明聯合任務: {len(signal_dl)} batches")

    # ── sig_only 時把 signal_dl 當作主 dataloader ──────────────────────────
    if sig_only and signal_dl is not None:
        train_dl = signal_dl
        cfg.multitask = False   # 關掉多任務，只計算訊號 loss
        if resolved_signal_val_data_path is not None:
            val_dl = build_signal_dataloader(
                resolved_signal_val_data_path,
                tokenizer,
                seq_len=cfg.signal_seq_len,
                batch_size=batch_size,
            )
            print(f"[unified_trainer] 訊號驗證集: {len(val_dl)} batches")

    if train_dl is None:
        raise RuntimeError("沒有可用的真實訓練資料")

    trainer = Trainer(
        model=model,
        train_config=cfg,
        train_dataloader=train_dl,
        eval_dataloader=val_dl,
        signal_dataloader=signal_dl if multitask else None,
        resume_from=resolved_resume_from,
    )

    # sig_only 模式：覆寫 _train_epoch 使用訊號 loss
    if sig_only:
        trainer._run_sig_only = True  # type: ignore[attr-defined]

    trainer.train()

    # ── 儲存最終權重 ──────────────────────────────────────────────────────────
    if save_to_model:
        dest = _ROOT / "model" / "unified_v2_100m.pth"
        dest.parent.mkdir(exist_ok=True)
        torch.save(
            {
                "architecture": "TinyLLMv2",
                "state_dict": model.state_dict(),
                "config": model.config.to_dict(),
                "trained": True,
            },
            str(dest),
        )
        active_path = _ROOT / "config" / "active_model.json"
        active = json.loads(active_path.read_text(encoding="utf-8"))
        active.update(
            {
                "model_name": "unified_v2_100m",
                "architecture": "TinyLLMv2",
                "model_path": "model/unified_v2_100m.pth",
                "materialized_path": "model/unified_v2_100m.pth",
                "initialization": "trained_checkpoint",
                "trained": True,
                "promoted_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        active_path.write_text(
            json.dumps(active, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"\n[unified_trainer] 權重已儲存至 {dest}")
        print("  InferenceEngine 與 ChatEngine 下次啟動時將自動載入此權重。")
    else:
        print(f"\n[unified_trainer] 訓練完成，檢查點在 {output_dir}/")

    _write_run_manifest(
        output_path,
        args=manifest_args,
        signal_data_path=resolved_signal_data_path,
        base_model_path=resolved_base_model_path,
        status="completed",
    )
    print(f"[unified_trainer] run manifest 已寫入 {output_path / 'run_manifest.json'}")
    if cloud_output_uri:
        upload_path(output_path, cloud_output_uri)
        print(f"[unified_trainer] artifacts 已同步至 {cloud_output_uri}")


# ============================================================================
# CLI 入口
# ============================================================================

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="BioNeuronai Unified Trainer")
    p.add_argument("--lm-only",  action="store_true", help="只訓練語言任務")
    p.add_argument("--sig-only", action="store_true", help="只訓練訊號任務")
    p.add_argument("--epochs",   type=int,   default=10,    help="訓練輪數")
    p.add_argument("--batch",    type=int,   default=8,     help="批次大小")
    p.add_argument("--lr",       type=float, default=3e-4,  help="學習率")
    p.add_argument(
        "--signal-data", type=str, default=None,
        help="訊號任務 JSONL 路徑"
    )
    p.add_argument(
        "--signal-val-data", type=str, default=None,
        help="訊號任務驗證集 .pt / JSONL 路徑（sig-only 模式使用，對應 signal_val.pt）"
    )
    p.add_argument("--base-model", type=str, default=None, help="基礎 checkpoint 路徑")
    p.add_argument("--resume", type=str, default=None, help="從 checkpoint 目錄恢復訓練")
    p.add_argument("--max-signal-samples", type=int, default=None, help="最多讀取幾筆 signal 樣本")
    p.add_argument("--seed", type=int, default=42, help="訓練亂數種子")
    p.add_argument("--save-steps", type=int, default=500, help="每幾個 optimizer step 保存 checkpoint")
    p.add_argument("--grad-accum", type=int, default=4, help="梯度累積步數")
    p.add_argument("--output",   type=str,   default="./output/unified", help="檢查點輸出目錄")
    p.add_argument(
        "--cloud-output-uri",
        type=str,
        default=None,
        help="訓練完成後同步 output 目錄到 gs://bucket/prefix（也可用 TRAINING_OUTPUT_URI）",
    )
    p.add_argument(
        "--no-save", action="store_true", help="不寫入 model/unified_v2_100m.pth"
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    train(
        lm_only=args.lm_only,
        sig_only=args.sig_only,
        epochs=args.epochs,
        batch_size=args.batch,
        lr=args.lr,
        signal_data_path=args.signal_data,
        signal_val_data_path=args.signal_val_data,
        output_dir=args.output,
        save_to_model=not args.no_save,
        base_model_path=args.base_model,
        resume_from=args.resume,
        max_signal_samples=args.max_signal_samples,
        seed=args.seed,
        save_steps=args.save_steps,
        gradient_accumulation_steps=args.grad_accum,
        cloud_output_uri=args.cloud_output_uri,
    )
