# -*- coding: utf-8 -*-
"""
BioNeuronai 數據層模組

整合連接器和服務：
- binance_futures: Binance 期貨 API 連接器
- database: [已棄用] 管理 trading_pairs/strategy_weights/account_snapshots 獨特表，
             使用獨立 DB 檔案 (trading_pairs.db)，尚未合併至 database_manager
- database_manager: 數據庫管理器（統一數據持久化接口）→ 優先使用此模組
- exchange_rate_service: 匯率服務
"""

from .binance_futures import BinanceFuturesConnector
from .exchange_rate_service import ExchangeRateService
from .database_manager import DatabaseManager, get_database_manager

__all__ = [
    'BinanceFuturesConnector',
    'ExchangeRateService',
    'DatabaseManager',
    'get_database_manager',
]
