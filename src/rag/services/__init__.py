# -*- coding: utf-8 -*-
"""
RAG Services 服務模塊

提供 RAG 系統的服務層組件:
- NewsAdapter: 新聞適配器，連接 CryptoNewsAnalyzer 與 RAG

更新日期: 2026-01-25
"""

from typing import Any, Callable, Optional

# 新聞適配器 (2026-01-25 新增)
imported_news_adapter: Any = None
imported_news_search_result: Any = None
imported_get_news_adapter: Optional[Callable[[], Any]] = None
imported_ingest_news_analysis: Optional[Callable[..., int]] = None
imported_ingest_news_analysis_with_status: Optional[Callable[..., Any]] = None
try:
    from .news_adapter import (
        NewsAdapter as imported_news_adapter,
        NewsSearchResult as imported_news_search_result,
        get_news_adapter as imported_get_news_adapter,
        ingest_news_analysis as imported_ingest_news_analysis,
        ingest_news_analysis_with_status as imported_ingest_news_analysis_with_status,
    )
    NEWS_ADAPTER_AVAILABLE = True
except ImportError:
    NEWS_ADAPTER_AVAILABLE = False

NewsAdapter: Any = imported_news_adapter
NewsSearchResult: Any = imported_news_search_result
get_news_adapter: Optional[Callable[[], Any]] = imported_get_news_adapter
ingest_news_analysis: Optional[Callable[..., int]] = imported_ingest_news_analysis
ingest_news_analysis_with_status: Optional[Callable[..., Any]] = imported_ingest_news_analysis_with_status

__all__ = [
    # 新聞適配器
    'NewsAdapter',
    'NewsSearchResult',
    'get_news_adapter',
    'ingest_news_analysis',
    'ingest_news_analysis_with_status',
]
