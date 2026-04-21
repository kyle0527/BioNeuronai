"""
NLP (Natural Language Processing) Module
========================================
自然語言處理模組 - 包含 LLM 開發相關功能

主要模組：
- tiny_llm: 100M 參數小型語言模型
- chat_engine: 雙語交易對話引擎（中/英）
- rag_system: RAG 系統（已廢棄，請使用 src/rag/ 模組）
- tokenizers: BPE 和雙語分詞器
- quantization: 模型量化工具
- lora: LoRA 微調支持
- generation_utils: 文本生成工具
- inference_utils: 推理優化工具
- training: 訓練腳本（advanced_trainer, auto_evolve, data_manager 等）
"""

__version__ = "1.0.0"
__all__ = [
    "get_tiny_llm",
    "get_chat_engine",
    "get_create_chat_engine",
    "get_bpe_tokenizer",
    "get_bilingual_tokenizer",
]

# 延遲導入以避免循環依賴
def get_tiny_llm():
    from .tiny_llm import TinyLLM
    return TinyLLM

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

def get_rag_system():
    """取得 RAGSystem 類別（已廢棄，請使用 src/rag/ 模組）"""
    import warnings

    warnings.warn(
        "nlp.get_rag_system() 僅供舊版相容，請改用 src/rag/ 模組。",
        DeprecationWarning,
        stacklevel=2,
    )
    from .rag_system import RAGSystem
    return RAGSystem
