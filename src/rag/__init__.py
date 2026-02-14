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

# 整合現有分析模組 (對外功能 - 從 bioneuronai 導入)
try:
    from bioneuronai.analysis.keywords import KeywordManager, KeywordMatch, get_keyword_manager
    from bioneuronai.analysis.news import CryptoNewsAnalyzer, NewsArticle, get_news_analyzer
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

# 整合交易前檢查 (從 bioneuronai.trading 導入)
try:
    from bioneuronai.trading.pretrade_automation import PreTradeCheckSystem
    PRETRADE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"交易前檢查模組導入失敗: {e}")
    PRETRADE_AVAILABLE = False
    PreTradeCheckSystem = None

# 新聞適配器 - RAG 統一接口 (2026-01-25 新增)
try:
    from .services.news_adapter import NewsAdapter, NewsSearchResult, get_news_adapter
    NEWS_ADAPTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"新聞適配器導入失敗: {e}")
    NEWS_ADAPTER_AVAILABLE = False
    NewsAdapter = None
    NewsSearchResult = None
    get_news_adapter = None


def get_rag_status() -> dict:
    """獲取 RAG 模組狀態"""
    return {
        "core_available": CORE_AVAILABLE,
        "internal_kb_available": INTERNAL_KB_AVAILABLE,
        "analysis_available": ANALYSIS_AVAILABLE,
        "pretrade_available": PRETRADE_AVAILABLE,
        "news_adapter_available": NEWS_ADAPTER_AVAILABLE,
        "components": {
            "EmbeddingService": EmbeddingService is not None,
            "InternalKnowledgeBase": InternalKnowledgeBase is not None,
            "KeywordManager": KeywordManager is not None,
            "CryptoNewsAnalyzer": CryptoNewsAnalyzer is not None,
            "PreTradeCheckSystem": PreTradeCheckSystem is not None,
            "NewsAdapter": NewsAdapter is not None,
        }
    }


def create_unified_retriever(
    embedding_service=None,
    knowledge_base=None,
    include_news: bool = True
):
    """
    創建預設配置的 UnifiedRetriever
    
    自動連接 NewsAdapter（如果可用）以提供新聞搜索功能。
    
    Args:
        embedding_service: 可選的 EmbeddingService 實例
        knowledge_base: 可選的 InternalKnowledgeBase 實例
        include_news: 是否包含新聞來源（預設 True）
    
    Returns:
        UnifiedRetriever: 配置好的檢索器實例
    
    使用範例:
        from rag import create_unified_retriever
        retriever = create_unified_retriever()
        results = retriever.retrieve("BTC 最新消息")
    """
    if not CORE_AVAILABLE or UnifiedRetriever is None:
        raise ImportError("RAG 核心組件不可用，請確認 sentence-transformers 已安裝")
    
    # 準備組件
    news_api = None
    if include_news and NEWS_ADAPTER_AVAILABLE and get_news_adapter is not None:
        try:
            news_api = get_news_adapter()
            logger.info("✅ NewsAdapter 已連接到 UnifiedRetriever")
        except Exception as e:
            logger.warning(f"NewsAdapter 初始化失敗: {e}")
    
    # 創建檢索器
    return UnifiedRetriever(
        embedding_service=embedding_service,
        knowledge_base=knowledge_base,
        news_api=news_api
    )


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
    
    # 新聞適配器 (2026-01-25 新增)
    'NewsAdapter',
    'NewsSearchResult',
    'get_news_adapter',
    
    # 交易前檢查 (整合 trading 模組)
    'PreTradeCheckSystem',
    
    # 工廠函數 (2026-01-27 新增)
    'create_unified_retriever',
    
    # 狀態檢查
    'get_rag_status',
    'CORE_AVAILABLE',
    'INTERNAL_KB_AVAILABLE',
    'ANALYSIS_AVAILABLE',
    'PRETRADE_AVAILABLE',
    'NEWS_ADAPTER_AVAILABLE',
]

__version__ = "2.0.0"
