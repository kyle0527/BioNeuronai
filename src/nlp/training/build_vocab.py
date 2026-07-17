"""
詞彙建立腳本 (build_vocab.py)
==============================
從正式新聞快照的真實中英文文本建立 BPE tokenizer，並儲存至
``model/tokenizer/vocab.json``。

執行方式：
    python -m nlp.training.build_vocab
    python -m nlp.training.build_vocab --vocab-size 16000
    python -m nlp.training.build_vocab --output model/tokenizer/vocab.json

輸出後 ChatEngine / unified_trainer 均可自動從該路徑載入詞彙。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]   # BioNeuronai/
_SRC  = _ROOT / "src"
for p in [str(_SRC), str(_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from nlp.bilingual_tokenizer import BilingualTokenizer  # noqa: E402

OFFICIAL_NEWS_SOURCE_IDS = {"coindesk", "google_news_macro"}
SUPPORTED_LANGUAGES = {"zh", "en"}


def collect_real_news_corpus(records_path: Path | None = None) -> list[str]:
    """從既有新聞記錄收集正式來源的真實中英文原文與摘要。"""
    path = records_path or (_ROOT / "src" / "data" / "bioneuronai" / "trading" / "sop" / "news_records.json")
    if not path.exists():
        raise FileNotFoundError(f"找不到正式新聞記錄：{path}")

    records = json.loads(path.read_text(encoding="utf-8"))
    corpus: list[str] = []
    for record in records:
        if record.get("source_id") not in OFFICIAL_NEWS_SOURCE_IDS:
            continue
        if record.get("language") not in SUPPORTED_LANGUAGES:
            continue
        title = str(record.get("title") or "").strip()
        summary = str(record.get("summary") or "").strip()
        text = "\n".join(part for part in (title, summary) if part)
        if text:
            corpus.append(text)

    if not corpus:
        raise ValueError(
            "尚無可用的正式中英文新聞語料。請先完成至少一輪 CoinDesk 與 "
            "Google News（en-US、zh-TW）成功抓取，再建立 tokenizer。"
        )
    return corpus


def build_vocab(vocab_size: int = 16_000, output: Path | None = None) -> Path:
    """
    從正式新聞快照建立詞彙並儲存。

    Args:
        vocab_size: 詞彙表大小上限（含特殊 tokens）
        output:     儲存路徑（None 時使用 model/tokenizer/vocab.json）

    Returns:
        實際儲存路徑
    """
    dest = output or (_ROOT / "model" / "tokenizer" / "vocab.json")
    dest = Path(dest)

    texts = collect_real_news_corpus()
    print(f"[build_vocab] 語料共 {len(texts)} 段真實中英文新聞文本")

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
        "--vocab-size", type=int, default=16_000,
        help="詞彙表大小上限（預設 16000，須與 unified_v2_100m 一致）"
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
