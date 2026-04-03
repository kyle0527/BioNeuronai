"""
英中雙語 Tokenizer
=================
專為英文和中文設計的簡單 tokenizer
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional


class BilingualTokenizer:
    """英中雙語 Tokenizer
    
    特點:
    - 支持英文和中文
    - 使用 BPE (Byte Pair Encoding)
    - 詞彙表大小可配置
    """
    
    def __init__(
        self,
        vocab_size: int = 30000,
        special_tokens: Optional[Dict[str, str]] = None
    ):
        self.vocab_size = vocab_size
        
        # 特殊 tokens
        if special_tokens is None:
            special_tokens = {
                "pad_token": "[PAD]",
                "unk_token": "[UNK]",
                "bos_token": "[BOS]",
                "eos_token": "[EOS]",
                "sep_token": "[SEP]",
                "cls_token": "[CLS]",
                "mask_token": "[MASK]",
            }
        
        self.special_tokens = special_tokens
        self.special_token_ids: Dict[str, int] = {}
        
        # 詞彙表
        self.vocab: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        
        # 初始化特殊 tokens
        self._init_special_tokens()
    
    def _init_special_tokens(self):
        """初始化特殊 tokens"""
        idx = 0
        for key, token in self.special_tokens.items():
            self.vocab[token] = idx
            self.id_to_token[idx] = token
            self.special_token_ids[key] = idx
            idx += 1
        
        self.pad_token_id = self.special_token_ids.get("pad_token", 0)
        self.unk_token_id = self.special_token_ids.get("unk_token", 1)
        self.bos_token_id = self.special_token_ids.get("bos_token", 2)
        self.eos_token_id = self.special_token_ids.get("eos_token", 3)
    
    def build_vocab(self, texts: List[str]):
        """從文本構建詞彙表"""
        print("構建英中雙語詞彙表...")
        
        # 基礎字符集（英文字母、數字、中文常用字符）
        base_chars = set()
        
        for text in texts:
            # 英文單詞
            words = re.findall(r'[a-zA-Z]+', text)
            for word in words:
                base_chars.update(list(word.lower()))
            
            # 中文字符
            chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
            base_chars.update(chinese_chars)
            
            # 數字和標點
            others = re.findall(r'[0-9\s\.,!?;:\-]', text)
            base_chars.update(others)
        
        # 添加基礎字符到詞彙表
        current_id = len(self.vocab)
        for char in sorted(base_chars):
            if char not in self.vocab:
                self.vocab[char] = current_id
                self.id_to_token[current_id] = char
                current_id += 1
        
        # 添加常用英文詞和中文詞
        common_words = self._get_common_words(texts)
        for word in common_words[:self.vocab_size - current_id]:
            if word not in self.vocab:
                self.vocab[word] = current_id
                self.id_to_token[current_id] = word
                current_id += 1
        
        print(f"✅ 詞彙表已構建: {len(self.vocab)} tokens")
    
    def _get_common_words(self, texts: List[str]) -> List[str]:
        """獲取常用詞"""
        word_counts: Dict[str, int] = {}
        
        for text in texts:
            # 英文單詞
            words = re.findall(r'[a-zA-Z]+', text.lower())
            for word in words:
                word_counts[word] = word_counts.get(word, 0) + 1
            
            # 中文詞（2-4字）
            chinese_text = re.sub(r'[^\u4e00-\u9fff]', '', text)
            for length in [2, 3, 4]:
                for i in range(len(chinese_text) - length + 1):
                    word = chinese_text[i:i+length]
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # 按頻率排序
        sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words]
    
    def encode(self, text: str, add_special_tokens: bool = True) -> List[int]:
        """編碼文本為 token IDs"""
        tokens = self._tokenize(text)
        ids = []
        
        if add_special_tokens:
            ids.append(self.bos_token_id)
        
        for token in tokens:
            ids.append(self.vocab.get(token, self.unk_token_id))
        
        if add_special_tokens:
            ids.append(self.eos_token_id)
        
        return ids
    
    def decode(self, ids: List[int], skip_special_tokens: bool = True) -> str:
        """解碼 token IDs 為文本"""
        tokens = []
        
        for id in ids:
            if skip_special_tokens and id in self.special_token_ids.values():
                continue
            tokens.append(self.id_to_token.get(id, self.special_tokens["unk_token"]))
        
        # 合併 tokens
        text = ""
        for token in tokens:
            # 中文字符直接連接
            if re.match(r'[\u4e00-\u9fff]', token):
                text += token
            # 英文單詞用空格分隔
            elif re.match(r'[a-zA-Z]', token):
                if text and not re.match(r'[\u4e00-\u9fff]', text[-1]):
                    text += " "
                text += token
            else:
                text += token
        
        return text.strip()
    
    def _tokenize(self, text: str) -> List[str]:
        """分詞"""
        tokens = []
        
        # 先按空格和標點分割
        parts = re.split(r'(\s+|[.,!?;:\-])', text)
        
        for part in parts:
            if not part or part.isspace():
                continue
            
            # 中文字符逐字分割
            if re.match(r'[\u4e00-\u9fff]', part):
                # 先嘗試找多字詞
                i = 0
                while i < len(part):
                    matched = False
                    for length in [4, 3, 2]:
                        if i + length <= len(part):
                            word = part[i:i+length]
                            if word in self.vocab:
                                tokens.append(word)
                                i += length
                                matched = True
                                break
                    if not matched:
                        tokens.append(part[i])
                        i += 1
            else:
                # 英文單詞
                word = part.lower()
                if word in self.vocab:
                    tokens.append(word)
                else:
                    # 分解為字符
                    tokens.extend(list(word))
        
        return tokens
    
    def save(self, path: str):
        """保存 tokenizer"""
        path_obj = Path(path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)

        # JSON 不支援整數鍵，將 id_to_token 的 key 轉為字串
        data = {
            "vocab": self.vocab,
            "id_to_token": {str(k): v for k, v in self.id_to_token.items()},
            "special_tokens": self.special_tokens,
            "special_token_ids": self.special_token_ids,
            "vocab_size": self.vocab_size,
        }

        with open(path_obj, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"✅ Tokenizer 已保存: {path}")

    @classmethod
    def load(cls, path: str) -> 'BilingualTokenizer':
        """載入 tokenizer"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        tokenizer = cls(vocab_size=data["vocab_size"])
        tokenizer.vocab = data["vocab"]
        # JSON 鍵為字串，還原為整數
        tokenizer.id_to_token = {int(k): v for k, v in data["id_to_token"].items()}
        tokenizer.special_tokens = data["special_tokens"]
        tokenizer.special_token_ids = data["special_token_ids"]

        tokenizer.pad_token_id = tokenizer.special_token_ids.get("pad_token", 0)
        tokenizer.unk_token_id = tokenizer.special_token_ids.get("unk_token", 1)
        tokenizer.bos_token_id = tokenizer.special_token_ids.get("bos_token", 2)
        tokenizer.eos_token_id = tokenizer.special_token_ids.get("eos_token", 3)

        return tokenizer


def create_bilingual_tokenizer(vocab_size: int = 30000) -> BilingualTokenizer:
    """創建英中雙語 tokenizer"""
    
    # 示例訓練數據（英文 + 中文）
    training_texts = [
        "Hello, how are you today?",
        "你好，今天過得怎麼樣？",
        "This is a machine learning model.",
        "這是一個機器學習模型。",
        "I love programming and artificial intelligence.",
        "我喜歡編程和人工智慧。",
        "The weather is nice today.",
        "今天天氣很好。",
        "Let's learn together!",
        "讓我們一起學習！",
        "Python is a great programming language.",
        "Python 是一個很棒的編程語言。",
        "Welcome to the future of AI.",
        "歡迎來到人工智慧的未來。",
    ] * 10  # 重複增加樣本
    
    tokenizer = BilingualTokenizer(vocab_size=vocab_size)
    tokenizer.build_vocab(training_texts)
    
    return tokenizer


if __name__ == "__main__":
    print("=" * 70)
    print("🌏 創建英中雙語 Tokenizer")
    print("=" * 70)
    
    # 創建 tokenizer
    tokenizer = create_bilingual_tokenizer(vocab_size=30000)
    
    # 測試編碼和解碼
    print("\n📝 測試編碼和解碼:")
    test_texts = [
        "Hello world!",
        "你好世界！",
        "I love AI and machine learning.",
        "我愛人工智慧和機器學習。",
    ]
    
    for text in test_texts:
        print(f"\n原文: {text}")
        ids = tokenizer.encode(text)
        decoded = tokenizer.decode(ids)
        print(f"IDs: {ids[:20]}..." if len(ids) > 20 else f"IDs: {ids}")
        print(f"解碼: {decoded}")
    
    # 保存
    save_path = "tokenizer/bilingual_tokenizer.pkl"
    tokenizer.save(save_path)
    
    print("\n✅ 完成!")
