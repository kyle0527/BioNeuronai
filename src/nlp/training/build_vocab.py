"""
詞彙建立腳本 (build_vocab.py)
==============================
從 trading_dialogue_data.py 的訓練語料建立 BilingualTokenizer 詞彙，
並儲存至 model/tokenizer/vocab.json。

執行方式：
    python -m nlp.training.build_vocab
    python -m nlp.training.build_vocab --vocab-size 30000
    python -m nlp.training.build_vocab --output model/tokenizer/vocab.json

輸出後 ChatEngine / unified_trainer 均可自動從該路徑載入詞彙。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[4]   # BioNeuronai/
_SRC  = _ROOT / "src"
for p in [str(_SRC), str(_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from nlp.bilingual_tokenizer import BilingualTokenizer
from nlp.training.trading_dialogue_data import ALL_TRADING_DATA


def build_vocab(vocab_size: int = 30000, output: Path | None = None) -> Path:
    """
    從 ALL_TRADING_DATA 建立詞彙並儲存。

    Args:
        vocab_size: 詞彙表大小上限（含特殊 tokens）
        output:     儲存路徑（None 時使用 model/tokenizer/vocab.json）

    Returns:
        實際儲存路徑
    """
    dest = output or (_ROOT / "model" / "tokenizer" / "vocab.json")
    dest = Path(dest)

    # 收集所有訓練文本
    texts: list[str] = []
    for item in ALL_TRADING_DATA:
        if item.get("input"):
            texts.append(item["input"])
        if item.get("output"):
            texts.append(item["output"])

    print(f"[build_vocab] 語料共 {len(texts)} 段文字（來自 {len(ALL_TRADING_DATA)} 筆 QA 對）")

    tokenizer = BilingualTokenizer(vocab_size=vocab_size)
    tokenizer.build_vocab(texts)

    dest.parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(dest))

    print(f"[build_vocab] 詞彙表大小: {len(tokenizer.vocab)} tokens")
    print(f"[build_vocab] 已儲存至: {dest}")
    return dest


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="BioNeuronai Tokenizer Vocab Builder")
    p.add_argument(
        "--vocab-size", type=int, default=30000,
        help="詞彙表大小上限（預設 30000）"
    )
    p.add_argument(
        "--output", type=str, default=None,
        help="輸出路徑（預設: model/tokenizer/vocab.json）"
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    build_vocab(
        vocab_size=args.vocab_size,
        output=Path(args.output) if args.output else None,
    )
