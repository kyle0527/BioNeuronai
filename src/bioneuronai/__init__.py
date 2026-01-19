"""
BioNeuronai - AI 交易與深度學習框架
====================================

模組化架構 v2.1:
- core: 核心交易引擎與自我改進系統
- analysis: 新聞分析與市場關鍵字識別
- automation: SOP 自動化與交易前自動化
- services: 數據庫與匯率服務
- planning: 交易計劃生成系統
- data_models: 交易數據模型
- connectors: API 連接器
- risk_management: 風險管理系統
- strategies: 交易策略系統
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

# 核心模組
from .core import TradingEngine, SelfImprovementSystem
from .data_models import MarketData, TradingSignal, Position, OrderResult
from .connectors import BinanceFuturesConnector
from .risk_management import RiskManager, RiskParameters
from .trading_strategies import StrategyFusion

# 分析模組
from .analysis import (
    CryptoNewsAnalyzer,
    NewsArticle,
    NewsAnalysisResult,
    get_news_analyzer,
    MarketKeywords,
    KeywordMatch
)

# 自動化模組
from .automation import SOPAutomation, PreTradeAutomation

# 服務模組
from .services import (
    Database,
    ExchangeRateService,
    ExchangeRateInfo,
    get_exchange_rate_service
)

# 計劃模組
from .planning import (
    TradingPlanGenerator,
    MarketConditionAnalysis,
    StrategyPerformanceMetrics,
)

# 向後兼容別名
CryptoFuturesTrader = TradingEngine

__all__ = [
    # 核心引擎
    "TradingEngine",
    "CryptoFuturesTrader",  # 向後兼容
    "SelfImprovementSystem",
    
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
    
    # 分析服務
    "CryptoNewsAnalyzer",
    "NewsArticle",
    "NewsAnalysisResult",
    "get_news_analyzer",
    "MarketKeywords",
    "KeywordMatch",
    
    # 自動化
    "SOPAutomation",
    "PreTradeAutomation",
    
    # 服務
    "Database",
    "ExchangeRateService",
    "ExchangeRateInfo",
    "get_exchange_rate_service",
    
    # 計劃
    "TradingPlanGenerator",
    "MarketConditionAnalysis",
    "StrategyPerformanceMetrics",
]

print(f"🚀 BioNeuronai v{__version__} 模組化交易系統已載入")
print(f"📦 可用模組: {len(__all__)} 個")
print(f"🏗️  新架構: core | analysis | automation | services | planning")
