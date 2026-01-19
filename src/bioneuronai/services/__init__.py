"""
外部服務模組
============
包含數據庫服務和匯率服務
"""

from .database import TradingDatabase
from .exchange_rate_service import (
    ExchangeRateService,
    ExchangeRateInfo,
    get_exchange_rate_service
)

__all__ = [
    'TradingDatabase',
    'ExchangeRateService',
    'ExchangeRateInfo',
    'get_exchange_rate_service',
]

# 向後兼容別名
Database = TradingDatabase
