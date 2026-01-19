"""
核心引擎模組
============
包含交易引擎和自我改進系統
"""

from .trading_engine import TradingEngine
from .self_improvement import SelfImprovementSystem

__all__ = [
    'TradingEngine',
    'SelfImprovementSystem',
]

# 向後兼容別名
CryptoFuturesTrader = TradingEngine
