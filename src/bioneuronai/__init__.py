"""
BioNeuronai - AI 交易與深度學習框架
====================================

核心模組:
- trading_engine: 虛擬貨幣期貨交易引擎
- trading_strategies: 多策略融合系統
- data_models: 交易數據模型
- connectors: Binance Futures API 連接器
- risk_management: 風險管理系統
- market_analyzer: 市場分析工具
"""

__version__ = "2.1.0"
__author__ = "BioNeuronai Team"

import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 交易系統核心模組
from .trading_engine import TradingEngine
from .data_models import MarketData, TradingSignal, Position, OrderResult
from .connectors import BinanceFuturesConnector
from .risk_management import RiskManager, RiskParameters
from .trading_strategies import StrategyFusion

# 向後兼容別名
CryptoFuturesTrader = TradingEngine

__all__ = [
    # 主引擎
    "TradingEngine",
    "CryptoFuturesTrader",  # 向後兼容
    
    # 數據模型
    "MarketData",
    "TradingSignal",
    "Position",
    "OrderResult",
    
    # 連接器
    "BinanceFuturesConnector",
    
    # 風險管理
    "RiskManager",
    "RiskParameters",
    
    # 策略
    "StrategyFusion",
]

print(f"🚀 BioNeuronai v{__version__} 交易系統已載入")
print(f"📦 可用模組: {len(__all__)} 個")
