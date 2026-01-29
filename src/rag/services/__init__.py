# -*- coding: utf-8 -*-
"""
RAG Services 服務模塊

提供 RAG 系統的服務層組件:
- NewsAdapter: 新聞適配器，連接 CryptoNewsAnalyzer 與 RAG
- PreTradeCheckSystem: 交易前檢查系統 (從 trading 模組導入)

更新日期: 2026-01-25
"""

# 新聞適配器 (2026-01-25 新增)
try:
    from .news_adapter import NewsAdapter, NewsSearchResult, get_news_adapter
    NEWS_ADAPTER_AVAILABLE = True
except ImportError as e:
    NEWS_ADAPTER_AVAILABLE = False
    NewsAdapter = None
    NewsSearchResult = None
    get_news_adapter = None

# 從 bioneuronai.trading 導入
try:
    from bioneuronai.trading.pretrade_automation import PreTradeCheckSystem
except ImportError:
    PreTradeCheckSystem = None

__all__ = [
    # 新聞適配器
    'NewsAdapter',
    'NewsSearchResult',
    'get_news_adapter',
    # 交易前檢查
    'PreTradeCheckSystem',
]
