# -*- coding: utf-8 -*-
"""
BioNeuronai 數據層模組

整合連接器和服務：
- binance_futures: Binance 期貨 API 連接器
- paper_binance: 主網行情 + 本地虛擬成交的 paper-live 連接器
- database: [已棄用] 管理 trading_pairs/strategy_weights/account_snapshots 獨特表，
             使用獨立 DB 檔案 (trading_pairs.db)，尚未合併至 database_manager
- database_manager: 數據庫管理器（統一數據持久化接口）→ 優先使用此模組
- exchange_rate_service: 匯率服務
- news_data_fetcher: 新聞數據抓取器（同步）— CryptoPanic + RSS
- sync_external_fetcher: 同步外部市場數據抓取器 — Fear&Greed + Yahoo Finance + Binance Spot

採 PEP 562 延遲載入：不因 import 本套件就被迫載入 websocket/交易所
連接器等重依賴（cloud_storage 等輕量模組的使用者不需要它們）。
"""

from typing import TYPE_CHECKING

__all__ = [
    'BinanceFuturesConnector',
    'PaperBinanceFuturesConnector',
    'ExchangeRateService',
    'DatabaseManager',
    'get_database_manager',
    'NewsDataFetcher',
    'SyncExternalDataFetcher',
]

_LAZY_IMPORTS = {
    'BinanceFuturesConnector': ('bioneuronai.data.binance_futures', 'BinanceFuturesConnector'),
    'PaperBinanceFuturesConnector': ('bioneuronai.data.paper_binance', 'PaperBinanceFuturesConnector'),
    'ExchangeRateService': ('bioneuronai.data.exchange_rate_service', 'ExchangeRateService'),
    'DatabaseManager': ('bioneuronai.data.database_manager', 'DatabaseManager'),
    'get_database_manager': ('bioneuronai.data.database_manager', 'get_database_manager'),
    'NewsDataFetcher': ('bioneuronai.data.news_data_fetcher', 'NewsDataFetcher'),
    'SyncExternalDataFetcher': ('bioneuronai.data.sync_external_fetcher', 'SyncExternalDataFetcher'),
}

if TYPE_CHECKING:  # pragma: no cover - 僅供型別檢查
    from .binance_futures import BinanceFuturesConnector as BinanceFuturesConnector
    from .database_manager import (  # noqa: F401
        DatabaseManager,
        get_database_manager,
    )
    from .exchange_rate_service import ExchangeRateService as ExchangeRateService
    from .news_data_fetcher import NewsDataFetcher as NewsDataFetcher
    from .paper_binance import PaperBinanceFuturesConnector as PaperBinanceFuturesConnector
    from .sync_external_fetcher import SyncExternalDataFetcher as SyncExternalDataFetcher


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        import importlib
        module_name, attr = _LAZY_IMPORTS[name]
        value = getattr(importlib.import_module(module_name), attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
