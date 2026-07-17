"""
NLP (Natural Language Processing) Module
========================================
自然語言處理模組 - 包含 LLM 開發相關功能

主要模組：
- tiny_llm_v2: 約 100M 參數的統一數值與中英文字模型
- chat_engine: 雙語交易對話引擎（中/英）
- bilingual_tokenizer: 統一的中英 ByteLevel BPE tokenizer
- quantization: 模型量化工具
- lora: LoRA 微調支持
- generation_utils: 文本生成工具
- inference_utils: 推理優化工具
- training: 統一 v2 多任務訓練與資料管理
"""

__version__ = "2.1"
__all__ = [
    "get_tiny_llm",
    "get_chat_engine",
    "get_create_chat_engine",
    "get_bpe_tokenizer",
    "get_bilingual_tokenizer",
]

# 延遲導入以避免循環依賴
def get_tiny_llm():
    from .tiny_llm_v2 import TinyLLMv2
    return TinyLLMv2

def get_chat_engine():
    from .chat_engine import ChatEngine
    return ChatEngine

def get_create_chat_engine():
    from .chat_engine import create_chat_engine
    return create_chat_engine

def get_bpe_tokenizer():
    """相容入口：回傳正式的統一中英 BPE tokenizer。

    舊版 ``BPETokenizer`` 是未接入 v2 模型的手寫實作。正式執行路徑、
    訓練與推論都必須使用同一個 ``BilingualTokenizer``，避免兩套詞彙
    與 token id 空間混用。
    """
    return get_bilingual_tokenizer()

def get_bilingual_tokenizer():
    from .bilingual_tokenizer import BilingualTokenizer
    return BilingualTokenizer
