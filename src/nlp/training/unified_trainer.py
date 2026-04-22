"""
統一訓練入口腳本 (Unified Trainer)
====================================
同一個 TinyLLM 訓練流程，同時支援兩個任務：

  任務 A（語言）  ：用 trading_dialogue_data.py 的 QA 對進行 next-token 預測
  任務 B（訊號）  ：用回測歷史中的 (feature_seq, signal_label) 進行序列回歸

執行方式：
    python -m nlp.training.unified_trainer              # 預設多任務訓練
    python -m nlp.training.unified_trainer --lm-only    # 純語言訓練
    python -m nlp.training.unified_trainer --sig-only   # 純訊號訓練

輸出：
    model/my_100m_model.pth   ← 正式交易 checkpoint 輸出位置
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path
from typing import List, Optional, Tuple

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

from nlp.tiny_llm import TinyLLM, TinyLLMConfig
from nlp.bilingual_tokenizer import BilingualTokenizer
from nlp.training.advanced_trainer import Trainer, TrainingConfig
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

    預設必須提供真實 JSONL；只有顯式 allow_synthetic=True 時才允許產生合成資料供 smoke test。

    JSONL 格式（每行一筆）：
    {
        "features": [[f1, f2, ..., f1024], ...],   # shape (T, 1024)
        "signal":   [s1, s2, ..., s512]             # shape (512,)
    }
    """

    _SYNTH_FEATURES = 1024
    _SYNTH_OUTPUT   = 512
    _SYNTH_SEQ_LEN  = 16

    def __init__(
        self,
        data_path: Optional[Path] = None,
        seq_len: int = 16,
        n_synthetic: int = 1000,
        allow_synthetic: bool = False,
    ) -> None:
        self.seq_len = seq_len
        self.samples: List[Tuple[np.ndarray, np.ndarray]] = []

        if data_path and data_path.exists():
            self._load_jsonl(data_path)
            if not self.samples:
                raise ValueError(f"訊號資料檔為空或沒有有效樣本: {data_path}")
        elif allow_synthetic:
            print("[unified_trainer] 警告：使用合成 signal 資料，僅適用於 smoke test，不應作為正式訓練資料。")
            self._generate_synthetic(n_synthetic)
        else:
            target = str(data_path) if data_path else "未指定 --signal-data"
            raise FileNotFoundError(
                f"找不到真實訊號資料: {target}。"
                " 請先執行 backtest.service.collect_signal_training_data 收集 JSONL，"
                "或顯式使用 --allow-synthetic-signal-data 進行 smoke test。"
            )

    def _load_jsonl(self, path: Path) -> None:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                feat = np.array(obj["features"], dtype=np.float32)  # (T, 1024)
                sig  = np.array(obj["signal"],   dtype=np.float32)  # (512,)
                # 若 T != seq_len，截斷或補零
                if feat.shape[0] < self.seq_len:
                    pad = np.zeros((self.seq_len - feat.shape[0], feat.shape[1]), dtype=np.float32)
                    feat = np.concatenate([pad, feat], axis=0)
                else:
                    feat = feat[-self.seq_len:]
                self.samples.append((feat, sig))

    def _generate_synthetic(self, n: int) -> None:
        """生成隨機合成資料，僅用於系統驗證，不代表真實訓練品質"""
        rng = np.random.default_rng(42)
        for _ in range(n):
            feat = rng.standard_normal((self.seq_len, self._SYNTH_FEATURES)).astype(np.float32)
            sig  = rng.standard_normal(self._SYNTH_OUTPUT).astype(np.float32)
            self.samples.append((feat, sig))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int):
        feat, sig = self.samples[idx]
        return {
            "feature_seq":    torch.from_numpy(feat),   # (T, 1024)
            "signal_labels":  torch.from_numpy(sig),    # (512,)
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
    seq_len: int = 16,
    batch_size: int = 8,
    n_synthetic: int = 1000,
    allow_synthetic: bool = False,
) -> _WrappedLoader:
    ds = SignalDataset(
        data_path,
        seq_len=seq_len,
        n_synthetic=n_synthetic,
        allow_synthetic=allow_synthetic,
    )
    return _WrappedLoader(DataLoader(ds, batch_size=batch_size, shuffle=True, num_workers=0))


# ============================================================================
# Tokenizer 工具
# ============================================================================

def _build_and_save_vocab(tokenizer: BilingualTokenizer, dest: Path) -> None:
    """從 ALL_TRADING_DATA 抽取所有文本，建立詞彙並儲存至 dest。"""
    texts = []
    for item in ALL_TRADING_DATA:
        if item.get("input"):
            texts.append(item["input"])
        if item.get("output"):
            texts.append(item["output"])
    tokenizer.build_vocab(texts)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(dest))
    print(f"[unified_trainer] tokenizer 已建立並儲存至 {dest}  ({len(tokenizer.vocab)} tokens)")


# ============================================================================
# 主訓練流程
# ============================================================================

def build_model(model_path: Optional[Path] = None) -> Tuple[TinyLLM, BilingualTokenizer]:
    """建立或載入模型與分詞器"""
    tokenizer = BilingualTokenizer(vocab_size=30000)

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

    cfg = TinyLLMConfig(
        vocab_size=tokenizer.vocab_size,
        use_numeric_mode=True,
        numeric_input_dim=1024,
        signal_output_dim=512,
        numeric_seq_len=16,
    )
    model = TinyLLM(cfg)

    # 嘗試載入已有權重
    ckpt = model_path or (_ROOT / "model" / "my_100m_model.pth")
    if ckpt.exists():
        try:
            checkpoint = torch.load(str(ckpt), map_location="cpu", weights_only=True)
            # 支援新格式 {'state_dict':..., 'config':...} 及舊格式（純 OrderedDict）
            if isinstance(checkpoint, dict) and "state_dict" in checkpoint:
                state = checkpoint["state_dict"]
            else:
                state = checkpoint
            loaded = model.load_state_dict(state, strict=False)
            missing = loaded.missing_keys
            unexpected = loaded.unexpected_keys
            if missing or unexpected:
                print(
                    f"[unified_trainer] 部分層未對齊 — missing={len(missing)}, "
                    f"unexpected={len(unexpected)}（通常因詞彙表大小不符，embedding 已重新初始化）"
                )
            else:
                print(f"[unified_trainer] 權重載入自 {ckpt}（完整載入）")
        except Exception as e:
            print(f"[unified_trainer] 權重載入失敗，從隨機初始化開始: {e}")
    else:
        print(f"[unified_trainer] 未找到 {ckpt}，從隨機初始化開始")

    total = sum(p.numel() for p in model.parameters()) / 1e6
    print(f"[unified_trainer] 模型參數量: {total:.1f}M")
    return model, tokenizer


def train(
    lm_only: bool = False,
    sig_only: bool = False,
    epochs: int = 10,
    batch_size: int = 8,
    lr: float = 3e-4,
    signal_data_path: Optional[Path] = None,
    output_dir: str = "./output/unified",
    save_to_model: bool = True,
    allow_synthetic_signal_data: bool = False,
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
        save_to_model:     訓練完成後是否直接覆寫 model/my_100m_model.pth
        allow_synthetic_signal_data:
                          允許用合成 signal 資料做 smoke test；正式訓練請保持 False
    """
    model, tokenizer = build_model()

    multitask = (not lm_only) and (not sig_only)

    if not lm_only and signal_data_path is None and not allow_synthetic_signal_data:
        raise ValueError(
            "signal 任務需要真實資料。請使用 --signal-data 指定 JSONL，"
            "或顯式傳入 --allow-synthetic-signal-data 僅做 smoke test。"
        )

    cfg = TrainingConfig(
        batch_size=batch_size,
        gradient_accumulation_steps=4,
        max_epochs=epochs,
        learning_rate=lr,
        warmup_steps=200,
        lr_scheduler_type="cosine",
        use_amp=torch.cuda.is_available(),
        eval_steps=500,
        save_steps=500,
        logging_steps=50,
        output_dir=output_dir,
        multitask=multitask,
        signal_loss_weight=0.5,
        signal_seq_len=16,
    )

    # ── 語言任務資料 ─────────────────────────────────────────────────────────
    if not sig_only:
        train_dl, val_dl = build_lm_dataloader(tokenizer, batch_size=batch_size)
        print(f"[unified_trainer] 語言任務: {len(train_dl)} batches")
    else:
        # sig_only 模式：用一個空的假 dataloader 佔位
        # Trainer 仍需要 train_dataloader，這裡傳空 Dataset
        empty_dl = _WrappedLoader(DataLoader(DialogueDataset([], tokenizer), batch_size=1))
        train_dl, val_dl = empty_dl, None

    # ── 訊號任務資料 ─────────────────────────────────────────────────────────
    signal_dl = None
    if not lm_only:
        signal_dl = build_signal_dataloader(
            signal_data_path,
            seq_len=cfg.signal_seq_len,
            batch_size=batch_size,
            allow_synthetic=allow_synthetic_signal_data,
        )
        print(f"[unified_trainer] 訊號任務: {len(signal_dl)} batches"
              f"{'（合成資料）' if allow_synthetic_signal_data and signal_data_path is None else ''}")

    # ── sig_only 時把 signal_dl 當作主 dataloader ──────────────────────────
    if sig_only and signal_dl is not None:
        # 包裝成語言任務格式讓 Trainer 能跑主 loop
        # 實際語言 loss 計算中 logits 形狀對不上時為 0，不影響訊號 loss
        train_dl = signal_dl
        cfg.multitask = False   # 關掉多任務，只計算訊號 loss

    trainer = Trainer(
        model=model,
        train_config=cfg,
        train_dataloader=train_dl,
        eval_dataloader=val_dl,
        signal_dataloader=signal_dl if multitask else None,
    )

    # sig_only 模式：覆寫 _train_epoch 使用訊號 loss
    if sig_only:
        trainer._run_sig_only = True  # type: ignore[attr-defined]

    trainer.train()

    # ── 儲存最終權重 ──────────────────────────────────────────────────────────
    if save_to_model:
        dest = _ROOT / "model" / "my_100m_model.pth"
        dest.parent.mkdir(exist_ok=True)
        # 使用 load_llm() 相容格式，讓 auto_evolve.py 可直接載入
        torch.save({"state_dict": model.state_dict(), "config": model.config.__dict__}, str(dest))
        print(f"\n[unified_trainer] 權重已儲存至 {dest}")
        print("  InferenceEngine 與 ChatEngine 下次啟動時將自動載入此權重。")
    else:
        print(f"\n[unified_trainer] 訓練完成，檢查點在 {output_dir}/")


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
        "--allow-synthetic-signal-data",
        action="store_true",
        help="允許在未提供真實 signal JSONL 時使用合成資料進行 smoke test",
    )
    p.add_argument("--output",   type=str,   default="./output/unified", help="檢查點輸出目錄")
    p.add_argument("--no-save",  action="store_true", help="不覆寫 model/my_100m_model.pth")
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    train(
        lm_only=args.lm_only,
        sig_only=args.sig_only,
        epochs=args.epochs,
        batch_size=args.batch,
        lr=args.lr,
        signal_data_path=Path(args.signal_data) if args.signal_data else None,
        output_dir=args.output,
        save_to_model=not args.no_save,
        allow_synthetic_signal_data=args.allow_synthetic_signal_data,
    )
