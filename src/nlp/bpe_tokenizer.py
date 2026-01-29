"""
BPE Tokenizer (Byte Pair Encoding)
==================================
高效的子詞分詞器，適用於多語言文本
"""

import json
import regex as re
from typing import List, Dict, Optional, Tuple, Set
from pathlib import Path
from collections import defaultdict, Counter
import pickle


class BPETokenizer:
    """BPE (Byte Pair Encoding) 分詞器
    
    特點：
    - 子詞分詞，處理 OOV（未見詞）問題
    - 支持中英文混合
    - 可訓練和保存
    - 高效編碼/解碼
    """
    
    def __init__(
        self,
        vocab: Optional[Dict[str, int]] = None,
        merges: Optional[List[Tuple[str, str]]] = None,
        vocab_size: int = 50257,
        special_tokens: Optional[Dict[str, str]] = None
    ):
        """初始化 BPE Tokenizer
        
        Args:
            vocab: 詞彙表 {token: id}
            merges: BPE 合併規則列表
            vocab_size: 詞彙表大小
            special_tokens: 特殊 token
        """
        self.vocab_size = vocab_size
        
        # 特殊 token
        self.special_tokens = special_tokens or {
            'pad_token': '<|pad|>',
            'unk_token': '<|unk|>',
            'bos_token': '<|startoftext|>',
            'eos_token': '<|endoftext|>',
            'sep_token': '<|sep|>',
        }
        
        # 初始化詞彙表和合併規則
        if vocab is not None and merges is not None:
            self.vocab = vocab
            self.merges = merges
            self.inverse_vocab = {v: k for k, v in vocab.items()}
        else:
            self.vocab = {}
            self.merges = []
            self.inverse_vocab = {}
            self._initialize_vocab()
        
        # 編譯正則表達式用於分詞
        # GPT-2 風格的正則表達式
        self.pattern = re.compile(
            r"""'s|'t|'re|'ve|'m|'ll|'d| ?\p{L}+| ?\p{N}+| ?[^\s\p{L}\p{N}]+|\s+(?!\S)|\s+""",
            re.IGNORECASE
        )
        
        # 緩存
        self.cache = {}
    
    def _initialize_vocab(self):
        """初始化基礎詞彙表"""
        # 添加特殊 token
        idx = 0
        for token in self.special_tokens.values():
            self.vocab[token] = idx
            idx += 1
        
        # 添加所有可能的字節（256個）
        for i in range(256):
            byte_token = chr(i)
            if byte_token not in self.vocab:
                self.vocab[byte_token] = idx
                idx += 1
        
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
    
    @property
    def pad_token_id(self) -> int:
        return self.vocab[self.special_tokens['pad_token']]
    
    @property
    def unk_token_id(self) -> int:
        return self.vocab[self.special_tokens['unk_token']]
    
    @property
    def bos_token_id(self) -> int:
        return self.vocab[self.special_tokens['bos_token']]
    
    @property
    def eos_token_id(self) -> int:
        return self.vocab[self.special_tokens['eos_token']]
    
    def train(self, texts: List[str], vocab_size: Optional[int] = None):
        """訓練 BPE tokenizer
        
        Args:
            texts: 訓練文本列表
            vocab_size: 目標詞彙表大小
        """
        if vocab_size is not None:
            self.vocab_size = vocab_size
        
        print(f"開始訓練 BPE Tokenizer...")
        print(f"訓練文本數: {len(texts)}")
        print(f"目標詞彙表大小: {self.vocab_size}")
        
        # 重新初始化
        self._initialize_vocab()
        current_vocab_size = len(self.vocab)
        
        # 收集所有詞
        word_freqs = Counter()
        for text in texts:
            words = self.pattern.findall(text)
            for word in words:
                word_freqs[word] += 1
        
        print(f"不同詞數: {len(word_freqs)}")
        
        # 將詞拆分為字符
        splits = {}
        for word in word_freqs:
            splits[word] = list(word)
        
        # 迭代合併
        num_merges = self.vocab_size - current_vocab_size
        print(f"需要進行 {num_merges} 次合併")
        
        for i in range(num_merges):
            if (i + 1) % 100 == 0:
                print(f"  進度: {i + 1}/{num_merges}")
            
            # 計算所有配對的頻率
            pair_freqs = defaultdict(int)
            for word, freq in word_freqs.items():
                split = splits[word]
                if len(split) == 1:
                    continue
                for j in range(len(split) - 1):
                    pair = (split[j], split[j + 1])
                    pair_freqs[pair] += freq
            
            if not pair_freqs:
                break
            
            # 找到最頻繁的配對
            best_pair = max(pair_freqs, key=lambda x: pair_freqs[x])
            
            # 記錄合併規則
            self.merges.append(best_pair)
            
            # 添加到詞彙表
            new_token = best_pair[0] + best_pair[1]
            self.vocab[new_token] = current_vocab_size
            current_vocab_size += 1
            
            # 更新所有詞的拆分
            for word in word_freqs:
                split = splits[word]
                if len(split) == 1:
                    continue
                
                new_split = []
                j = 0
                while j < len(split):
                    if j < len(split) - 1 and (split[j], split[j + 1]) == best_pair:
                        new_split.append(new_token)
                        j += 2
                    else:
                        new_split.append(split[j])
                        j += 1
                
                splits[word] = new_split
        
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
        print(f"訓練完成! 最終詞彙表大小: {len(self.vocab)}")
    
    def _tokenize_word(self, word: str) -> List[str]:
        """對單個詞進行 BPE 分詞"""
        if word in self.cache:
            return self.cache[word]
        
        # 拆分為字符
        tokens = list(word)
        
        # 應用合併規則
        for merge in self.merges:
            new_tokens = []
            i = 0
            while i < len(tokens):
                if i < len(tokens) - 1 and (tokens[i], tokens[i + 1]) == merge:
                    new_tokens.append(merge[0] + merge[1])
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            tokens = new_tokens
        
        # 緩存結果
        self.cache[word] = tokens
        return tokens
    
    def encode(
        self,
        text: str,
        add_special_tokens: bool = True,
        max_length: Optional[int] = None,
        padding: bool = False,
        truncation: bool = False
    ) -> List[int]:
        """編碼文本為 token IDs
        
        Args:
            text: 輸入文本
            add_special_tokens: 是否添加特殊 token
            max_length: 最大長度
            padding: 是否填充
            truncation: 是否截斷
        
        Returns:
            token IDs 列表
        """
        # 分詞
        words = self.pattern.findall(text)
        
        # BPE 編碼
        tokens = []
        for word in words:
            word_tokens = self._tokenize_word(word)
            tokens.extend(word_tokens)
        
        # 轉換為 ID
        ids = []
        if add_special_tokens:
            ids.append(self.bos_token_id)
        
        for token in tokens:
            if token in self.vocab:
                ids.append(self.vocab[token])
            else:
                # 未知 token - 分解為字節
                for char in token:
                    if char in self.vocab:
                        ids.append(self.vocab[char])
                    else:
                        ids.append(self.unk_token_id)
        
        if add_special_tokens:
            ids.append(self.eos_token_id)
        
        # 截斷
        if truncation and max_length is not None and len(ids) > max_length:
            ids = ids[:max_length]
            if add_special_tokens:
                ids[-1] = self.eos_token_id
        
        # 填充
        if padding and max_length is not None:
            while len(ids) < max_length:
                ids.append(self.pad_token_id)
        
        return ids
    
    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        """解碼 token IDs 為文本
        
        Args:
            ids: token IDs
            skip_special_tokens: 是否跳過特殊 token
        
        Returns:
            解碼後的文本
        """
        tokens = []
        special_ids = {v for v in self.special_tokens.values() if v in self.vocab}
        
        for idx in ids:
            if idx in self.inverse_vocab:
                token = self.inverse_vocab[idx]
                if skip_special_tokens and token in special_ids:
                    continue
                tokens.append(token)
        
        text = ''.join(tokens)
        return text
    
    def batch_encode(
        self,
        texts: List[str],
        add_special_tokens: bool = True,
        max_length: Optional[int] = None,
        padding: bool = True,
        truncation: bool = True
    ) -> Dict[str, List[List[int]]]:
        """批量編碼
        
        Args:
            texts: 文本列表
            add_special_tokens: 是否添加特殊 token
            max_length: 最大長度
            padding: 是否填充
            truncation: 是否截斷
        
        Returns:
            {'input_ids': [[...], ...], 'attention_mask': [[...], ...]}
        """
        all_ids = []
        all_masks = []
        
        # 先編碼所有文本
        encoded = [
            self.encode(text, add_special_tokens, max_length, False, truncation)
            for text in texts
        ]
        
        # 計算最大長度
        if max_length is None:
            max_len = max(len(ids) for ids in encoded)
        else:
            max_len = max_length
        
        # 填充
        for ids in encoded:
            # Attention mask
            mask = [1] * len(ids)
            
            # 填充
            if padding:
                pad_len = max_len - len(ids)
                ids = ids + [self.pad_token_id] * pad_len
                mask = mask + [0] * pad_len
            
            all_ids.append(ids)
            all_masks.append(mask)
        
        return {
            'input_ids': all_ids,
            'attention_mask': all_masks
        }
    
    def save(self, save_directory: str):
        """保存 tokenizer
        
        Args:
            save_directory: 保存目錄
        """
        save_dir = Path(save_directory)
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存詞彙表
        with open(save_dir / 'vocab.json', 'w', encoding='utf-8') as f:
            json.dump(self.vocab, f, ensure_ascii=False, indent=2)
        
        # 保存合併規則
        with open(save_dir / 'merges.txt', 'w', encoding='utf-8') as f:
            for pair in self.merges:
                f.write(f"{pair[0]} {pair[1]}\n")
        
        # 保存配置
        config = {
            'vocab_size': self.vocab_size,
            'special_tokens': self.special_tokens
        }
        with open(save_dir / 'tokenizer_config.json', 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Tokenizer 已保存至: {save_dir}")
    
    @classmethod
    def load(cls, load_directory: str) -> 'BPETokenizer':
        """加載 tokenizer
        
        Args:
            load_directory: 加載目錄
        
        Returns:
            BPETokenizer 實例
        """
        load_dir = Path(load_directory)
        
        # 加載詞彙表
        with open(load_dir / 'vocab.json', 'r', encoding='utf-8') as f:
            vocab = json.load(f)
        
        # 加載合併規則
        merges = []
        with open(load_dir / 'merges.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    pair = tuple(line.strip().split(' '))
                    merges.append(pair)
        
        # 加載配置
        with open(load_dir / 'tokenizer_config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        tokenizer = cls(
            vocab=vocab,
            merges=merges,
            vocab_size=config['vocab_size'],
            special_tokens=config['special_tokens']
        )
        
        print(f"✓ Tokenizer 已從 {load_dir} 加載")
        return tokenizer
    
    def __len__(self) -> int:
        """詞彙表大小"""
        return len(self.vocab)
    
    def __repr__(self) -> str:
        return f"BPETokenizer(vocab_size={len(self.vocab)}, merges={len(self.merges)})"


def train_tokenizer_from_files(
    file_paths: List[str],
    vocab_size: int = 50257,
    save_directory: Optional[str] = None
) -> BPETokenizer:
    """從文件訓練 tokenizer
    
    Args:
        file_paths: 訓練文本文件路徑列表
        vocab_size: 詞彙表大小
        save_directory: 保存目錄
    
    Returns:
        訓練好的 tokenizer
    """
    # 讀取所有文本
    texts = []
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as f:
            texts.extend([line.strip() for line in f if line.strip()])
    
    # 訓練
    tokenizer = BPETokenizer(vocab_size=vocab_size)
    tokenizer.train(texts, vocab_size)
    
    # 保存
    if save_directory:
        tokenizer.save(save_directory)
    
    return tokenizer
