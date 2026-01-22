# -*- coding: utf-8 -*-
"""
BioNeuronai RAG 模塊 (Retrieval-Augmented Generation)
====================================================

提供檢索增強生成系統，整合現有的分析模組：

🔹 對內功能 (Internal Knowledge)
   - 內部知識庫 (knowledge_base.py)
   - 向量嵌入 (embeddings.py)
   - 統一檢索 (retriever.py)

🔹 對外功能 (External - 使用 analysis 模組)
   - 關鍵字系統 → analysis.market_keywords.KeywordManager
   - 新聞分析 → analysis.news_analyzer.CryptoNewsAnalyzer
   - 交易前檢查 → trading.pretrade_automation.PreTradeCheckSystem

架構:
    rag/
    ├── core/               # 核心組件
    │   ├── embeddings.py   # 向量嵌入
    │   └── retriever.py    # 統一檢索器
    └── internal/           # 對內知識庫
        └── knowledge_base.py
        
    整合使用:
    - analysis.market_keywords → 181 個市場關鍵字
    - analysis.news_analyzer → CryptoPanic + RSS 新聞
    - trading.pretrade_automation → 完整 SOP 檢查流程
"""

import logging

logger = logging.getLogger(__name__)

# 核心組件
try:
    from .core.embeddings import EmbeddingService, EmbeddingModel, EmbeddingResult
    from .core.retriever import UnifiedRetriever, RetrievalResult, RetrievalQuery, RetrievalSource
    CORE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAG 核心組件導入失敗: {e}")
    CORE_AVAILABLE = False
    EmbeddingService = None
    EmbeddingModel = None
    EmbeddingResult = None
    UnifiedRetriever = None
    RetrievalResult = None
    RetrievalQuery = None
    RetrievalSource = None

# 對內 - 內部知識庫
try:
    from .internal.knowledge_base import InternalKnowledgeBase, KnowledgeDocument, DocumentType
    INTERNAL_KB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"內部知識庫導入失敗: {e}")
    INTERNAL_KB_AVAILABLE = False
    InternalKnowledgeBase = None
    KnowledgeDocument = None
    DocumentType = None

# 整合現有分析模組 (對外功能)
try:
    from ..analysis.market_keywords import KeywordManager, KeywordMatch, get_keyword_manager
    from ..analysis.news_analyzer import CryptoNewsAnalyzer, NewsArticle, get_news_analyzer
    ANALYSIS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"分析模組導入失敗: {e}")
    ANALYSIS_AVAILABLE = False
    KeywordManager = None
    KeywordMatch = None
    get_keyword_manager = None
    CryptoNewsAnalyzer = None
    NewsArticle = None
    get_news_analyzer = None

# 整合交易前檢查 (使用現有的 trading 模組)
try:
    from ..trading.pretrade_automation import PreTradeCheckSystem
    PRETRADE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"交易前檢查模組導入失敗: {e}")
    PRETRADE_AVAILABLE = False
    PreTradeCheckSystem = None


def get_rag_status() -> dict:
    """獲取 RAG 模組狀態"""
    return {
        "core_available": CORE_AVAILABLE,
        "internal_kb_available": INTERNAL_KB_AVAILABLE,
        "analysis_available": ANALYSIS_AVAILABLE,
        "pretrade_available": PRETRADE_AVAILABLE,
        "components": {
            "EmbeddingService": EmbeddingService is not None,
            "InternalKnowledgeBase": InternalKnowledgeBase is not None,
            "KeywordManager": KeywordManager is not None,
            "CryptoNewsAnalyzer": CryptoNewsAnalyzer is not None,
            "PreTradeCheckSystem": PreTradeCheckSystem is not None,
        }
    }


__all__ = [
    # 核心
    'EmbeddingService',
    'EmbeddingModel',
    'EmbeddingResult',
    'UnifiedRetriever',
    'RetrievalResult',
    'RetrievalQuery',
    'RetrievalSource',
    
    # 對內
    'InternalKnowledgeBase',
    'KnowledgeDocument',
    'DocumentType',
    
    # 對外 (整合 analysis 模組)
    'KeywordManager',
    'KeywordMatch',
    'get_keyword_manager',
    'CryptoNewsAnalyzer',
    'NewsArticle',
    'get_news_analyzer',
    
    # 交易前檢查 (整合 trading 模組)
    'PreTradeCheckSystem',
    
    # 狀態檢查
    'get_rag_status',
    'CORE_AVAILABLE',
    'INTERNAL_KB_AVAILABLE',
    'ANALYSIS_AVAILABLE',
    'PRETRADE_AVAILABLE',
]

__version__ = "2.0.0"
