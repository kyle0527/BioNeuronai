# -*- coding: utf-8 -*-
from __future__ import annotations
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
   - 入庫服務 → services.news_adapter.ingest_news_analysis

架構:
    rag/
    ├── core/               # 核心組件
    │   ├── embeddings.py   # 向量嵌入
    │   └── retriever.py    # 統一檢索器
    ├── internal/           # 對內知識庫
    │   └── knowledge_base.py
    └── services/           # 外部數據橋接層
        └── news_adapter.py # Analysis → RAG 唯一入庫入口

    整合使用:
    - analysis.market_keywords → 505 個市場關鍵字（7 大類）
    - analysis.news_analyzer → CryptoPanic + RSS 新聞
    - services.news_adapter → ingest_news_analysis（B.3 唯一寫入入口）
"""

import logging
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)

# 核心組件
imported_embedding_service: Any = None
imported_embedding_model: Any = None
imported_embedding_result: Any = None
imported_unified_retriever: Any = None
imported_retrieval_result: Any = None
imported_retrieval_query: Any = None
imported_retrieval_source: Any = None
try:
    from .core.embeddings import (
        EmbeddingService as imported_embedding_service,
        EmbeddingModel as imported_embedding_model,
        EmbeddingResult as imported_embedding_result,
    )
    from .core.retriever import (
        UnifiedRetriever as imported_unified_retriever,
        RetrievalResult as imported_retrieval_result,
        RetrievalQuery as imported_retrieval_query,
        RetrievalSource as imported_retrieval_source,
    )
    CORE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAG 核心組件導入失敗: {e}")
    CORE_AVAILABLE = False

EmbeddingService: Any = imported_embedding_service
EmbeddingModel: Any = imported_embedding_model
EmbeddingResult: Any = imported_embedding_result
UnifiedRetriever: Any = imported_unified_retriever
RetrievalResult: Any = imported_retrieval_result
RetrievalQuery: Any = imported_retrieval_query
RetrievalSource: Any = imported_retrieval_source

# 對內 - 內部知識庫
imported_internal_knowledge_base: Any = None
imported_knowledge_document: Any = None
imported_document_type: Any = None
try:
    from .internal.knowledge_base import (
        InternalKnowledgeBase as imported_internal_knowledge_base,
        KnowledgeDocument as imported_knowledge_document,
        DocumentType as imported_document_type,
    )
    INTERNAL_KB_AVAILABLE = True
except ImportError as e:
    logger.warning(f"內部知識庫導入失敗: {e}")
    INTERNAL_KB_AVAILABLE = False

InternalKnowledgeBase: Any = imported_internal_knowledge_base
KnowledgeDocument: Any = imported_knowledge_document
DocumentType: Any = imported_document_type

# 整合現有分析模組 (對外功能 - 從 bioneuronai 導入)
imported_keyword_manager: Any = None
imported_keyword_match: Any = None
imported_get_keyword_manager: Optional[Callable[[], Any]] = None
imported_crypto_news_analyzer: Any = None
imported_news_article: Any = None
imported_get_news_analyzer: Optional[Callable[[], Any]] = None
try:
    from bioneuronai.analysis.keywords import (
        KeywordManager as imported_keyword_manager,
        KeywordMatch as imported_keyword_match,
        get_keyword_manager as imported_get_keyword_manager,
    )
    from bioneuronai.analysis.news import (
        CryptoNewsAnalyzer as imported_crypto_news_analyzer,
        NewsArticle as imported_news_article,
        get_news_analyzer as imported_get_news_analyzer,
    )
    ANALYSIS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"分析模組導入失敗: {e}")
    ANALYSIS_AVAILABLE = False

KeywordManager: Any = imported_keyword_manager
KeywordMatch: Any = imported_keyword_match
get_keyword_manager: Optional[Callable[[], Any]] = imported_get_keyword_manager
CryptoNewsAnalyzer: Any = imported_crypto_news_analyzer
NewsArticle: Any = imported_news_article
get_news_analyzer: Optional[Callable[[], Any]] = imported_get_news_analyzer

# 新聞適配器 - RAG 統一接口 (2026-01-25 新增)
imported_news_adapter: Any = None
imported_news_search_result: Any = None
imported_get_news_adapter: Optional[Callable[[], Any]] = None
imported_ingest_news_analysis: Optional[Callable[..., int]] = None
imported_ingest_news_analysis_with_status: Optional[Callable[..., Any]] = None
try:
    from .services.news_adapter import (
        NewsAdapter as imported_news_adapter,
        NewsSearchResult as imported_news_search_result,
        get_news_adapter as imported_get_news_adapter,
        ingest_news_analysis as imported_ingest_news_analysis,
        ingest_news_analysis_with_status as imported_ingest_news_analysis_with_status,
    )
    NEWS_ADAPTER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"新聞適配器導入失敗: {e}")
    NEWS_ADAPTER_AVAILABLE = False

NewsAdapter: Any = imported_news_adapter
NewsSearchResult: Any = imported_news_search_result
get_news_adapter: Optional[Callable[[], Any]] = imported_get_news_adapter
ingest_news_analysis: Optional[Callable[..., int]] = imported_ingest_news_analysis
ingest_news_analysis_with_status: Optional[Callable[..., Any]] = imported_ingest_news_analysis_with_status


def get_rag_status() -> dict:
    """獲取 RAG 模組狀態"""
    return {
        "core_available": CORE_AVAILABLE,
        "internal_kb_available": INTERNAL_KB_AVAILABLE,
        "analysis_available": ANALYSIS_AVAILABLE,
        "news_adapter_available": NEWS_ADAPTER_AVAILABLE,
        "components": {
            "EmbeddingService": EmbeddingService is not None,
            "InternalKnowledgeBase": InternalKnowledgeBase is not None,
            "KeywordManager": KeywordManager is not None,
            "CryptoNewsAnalyzer": CryptoNewsAnalyzer is not None,
            "NewsAdapter": NewsAdapter is not None,
            "ingest_news_analysis": ingest_news_analysis is not None,
        }
    }


def create_unified_retriever(
    embedding_service=None,
    knowledge_base=None,
    include_news: bool = True
) -> Any:
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
        internal_kb=knowledge_base,
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
    
    # 新聞適配器 + 入庫服務 (2026-01-25 新增 / 2026-04-02 補全入庫函數)
    'NewsAdapter',
    'NewsSearchResult',
    'get_news_adapter',
    'ingest_news_analysis',
    'ingest_news_analysis_with_status',

    # 工廠函數 (2026-01-27 新增)
    'create_unified_retriever',
    
    # 狀態檢查
    'get_rag_status',
    'CORE_AVAILABLE',
    'INTERNAL_KB_AVAILABLE',
    'ANALYSIS_AVAILABLE',
    'NEWS_ADAPTER_AVAILABLE',
]

__version__ = "2.1"
