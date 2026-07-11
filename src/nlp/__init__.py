"""
NLP (Natural Language Processing) Module
========================================
自然語言處理模組 - 包含 LLM 開發相關功能

主要模組：
- tiny_llm_v2: 約 100M 參數的統一數值與中英文字模型
- chat_engine: 雙語交易對話引擎（中/英）
- tokenizers: BPE 和雙語分詞器
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
    from .bpe_tokenizer import BPETokenizer
    return BPETokenizer

def get_bilingual_tokenizer():
    from .bilingual_tokenizer import BilingualTokenizer
    return BilingualTokenizer
