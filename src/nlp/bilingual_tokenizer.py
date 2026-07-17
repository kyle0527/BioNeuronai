"""中文與英文金融文本的正式 BPE tokenizer。

這個包裝維持專案既有 ``BilingualTokenizer`` 介面，但把舊的逐字／貪婪
切分實作替換為 Hugging Face ``tokenizers`` 的 ByteLevel BPE。詞彙表由真實
中英文新聞與訓練語料建立，並固定在 unified_v2_100m 的 16,000 token 上限內。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from tokenizers import Tokenizer, decoders, models, normalizers, pre_tokenizers, trainers


class BilingualTokenizer:
    """專案唯一的中英 BPE tokenizer。

    ByteLevel BPE 能把未見的幣名、機構名或事件名稱拆成可重用子詞／位元組，
    不需要為每個新關鍵字額外寫規則。模型與 tokenizer 的 vocabulary size 必須
    一致，因此正式訓練與推論都使用同一個儲存檔案。
    """

    DEFAULT_SPECIAL_TOKENS: Dict[str, str] = {
        "pad_token": "[PAD]",
        "unk_token": "[UNK]",
        "bos_token": "[BOS]",
        "eos_token": "[EOS]",
        "sep_token": "[SEP]",
        "cls_token": "[CLS]",
        "mask_token": "[MASK]",
    }

    def __init__(
        self,
        vocab_size: int = 16_000,
        special_tokens: Optional[Dict[str, str]] = None,
    ) -> None:
        self.vocab_size = vocab_size
        self.special_tokens = dict(special_tokens or self.DEFAULT_SPECIAL_TOKENS)
        self._tokenizer = self._new_backend()
        self.vocab: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        self.special_token_ids: Dict[str, int] = {}
        self._sync_metadata()

    def _new_backend(self) -> Tokenizer:
        tokenizer = Tokenizer(models.BPE(unk_token=self.special_tokens["unk_token"], byte_fallback=True))
        tokenizer.normalizer = normalizers.Sequence([normalizers.NFKC()])
        tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False)
        tokenizer.decoder = decoders.ByteLevel()
        tokenizer.add_special_tokens(list(self.special_tokens.values()))
        return tokenizer

    def _sync_metadata(self) -> None:
        self.vocab = self._tokenizer.get_vocab()
        self.id_to_token = {token_id: token for token, token_id in self.vocab.items()}
        self.special_token_ids = {
            key: token_id
            for key, token in self.special_tokens.items()
            if (token_id := self._tokenizer.token_to_id(token)) is not None
        }
        self.pad_token_id = self.special_token_ids.get("pad_token", 0)
        self.unk_token_id = self.special_token_ids.get("unk_token", 1)
        self.bos_token_id = self.special_token_ids.get("bos_token", 2)
        self.eos_token_id = self.special_token_ids.get("eos_token", 3)

    def build_vocab(self, texts: Iterable[str]) -> None:
        """以真實中英文文本訓練固定大小的 ByteLevel BPE 詞彙表。"""
        corpus = [text.strip() for text in texts if isinstance(text, str) and text.strip()]
        if not corpus:
            raise ValueError("建立 tokenizer 需要至少一筆真實中英文文本")

        trainer = trainers.BpeTrainer(
            vocab_size=self.vocab_size,
            min_frequency=2,
            max_token_length=24,
            special_tokens=list(self.special_tokens.values()),
            initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        )
        self._tokenizer = self._new_backend()
        self._tokenizer.train_from_iterator(corpus, trainer=trainer)
        self._sync_metadata()

        if len(self.vocab) > self.vocab_size:
            raise RuntimeError("BPE tokenizer 詞彙數超過設定上限")

    def encode(
        self,
        text: str,
        add_special_tokens: bool = True,
        max_length: Optional[int] = None,
        truncation: bool = False,
    ) -> List[int]:
        """把中英文本編碼成 token IDs。"""
        ids = list(self._tokenizer.encode(text).ids)
        if add_special_tokens:
            ids = [self.bos_token_id, *ids, self.eos_token_id]

        if truncation and max_length is not None and len(ids) > max_length:
            if add_special_tokens and max_length >= 2:
                return ids[: max_length - 1] + [self.eos_token_id]
            return ids[:max_length]
        return ids

    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        """由 token IDs 還原文本。"""
        values = ids
        if skip_special_tokens:
            special_ids = set(self.special_token_ids.values())
            values = [token_id for token_id in ids if token_id not in special_ids]
        return self._tokenizer.decode(values, skip_special_tokens=skip_special_tokens)

    def _tokenize(self, text: str) -> List[str]:
        """保留給既有診斷與使用端的 token 顯示介面。"""
        return list(self._tokenizer.encode(text).tokens)

    @property
    def version(self) -> str:
        """回傳 tokenizer 內容雜湊，供每小時決策快照記錄。"""
        return hashlib.sha256(self._tokenizer.to_str().encode("utf-8")).hexdigest()[:16]

    def save(self, path: str) -> None:
        """以 Hugging Face tokenizer.json 格式儲存。"""
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        self._tokenizer.save(str(path_obj))

    @classmethod
    def load(cls, path: str) -> "BilingualTokenizer":
        """讀取正式 BPE artifact；拒絕舊的自製詞典格式。"""
        path_obj = Path(path)
        with path_obj.open("r", encoding="utf-8") as file:
            payload = json.load(file)
        if "model" not in payload or "pre_tokenizer" not in payload:
            raise ValueError(
                f"{path_obj} 是舊版逐字詞典，不可用於正式 v2 tokenizer；"
                "請以真實新聞語料重新建立 BPE artifact。"
            )

        tokenizer = cls(vocab_size=16_000)
        tokenizer._tokenizer = Tokenizer.from_file(str(path_obj))
        tokenizer._sync_metadata()
        tokenizer.vocab_size = len(tokenizer.vocab)
        return tokenizer


def create_bilingual_tokenizer(vocab_size: int = 16_000) -> BilingualTokenizer:
    """建立尚未訓練的 tokenizer 實例；呼叫端必須提供真實語料後再使用。"""
    return BilingualTokenizer(vocab_size=vocab_size)
