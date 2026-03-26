# -*- coding: utf-8 -*-
"""
RAG Services 服務模塊

提供 RAG 系統的服務層組件:
- NewsAdapter: 新聞適配器，連接 CryptoNewsAnalyzer 與 RAG
- PreTradeCheckSystem: 交易前檢查系統 (從 trading 模組導入)

更新日期: 2026-01-25
"""

from typing import Any, Callable, Optional

# 新聞適配器 (2026-01-25 新增)
imported_news_adapter: Any = None
imported_news_search_result: Any = None
imported_get_news_adapter: Optional[Callable[[], Any]] = None
try:
    from .news_adapter import (
        NewsAdapter as imported_news_adapter,
        NewsSearchResult as imported_news_search_result,
        get_news_adapter as imported_get_news_adapter,
    )
    NEWS_ADAPTER_AVAILABLE = True
except ImportError:
    NEWS_ADAPTER_AVAILABLE = False

NewsAdapter: Any = imported_news_adapter
NewsSearchResult: Any = imported_news_search_result
get_news_adapter: Optional[Callable[[], Any]] = imported_get_news_adapter

# 從 bioneuronai.trading 導入
imported_pretrade_check_system: Any = None
try:
    from bioneuronai.trading.pretrade_automation import PreTradeCheckSystem as imported_pretrade_check_system
except ImportError:
    imported_pretrade_check_system = None

PreTradeCheckSystem: Any = imported_pretrade_check_system

__all__ = [
    # 新聞適配器
    'NewsAdapter',
    'NewsSearchResult',
    'get_news_adapter',
    # 交易前檢查
    'PreTradeCheckSystem',
]
