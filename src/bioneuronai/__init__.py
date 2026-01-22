"""
BioNeuronai - AI 
====================================

 v2.1:
- core: 
- analysis: 
- automation: SOP 
- services: 
- planning: 
- data_models: 
- connectors: API 
- risk_management: 
- strategies: 
"""

__version__ = "2.1.0"
__author__ = "BioNeuronai Team"

import logging

# 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# 
from .core import TradingEngine, SelfImprovementSystem
from .trading_strategies import MarketData, TradingSignal, StrategyFusion
from .data import BinanceFuturesConnector, ExchangeRateService
from .risk_management import RiskManager, RiskParameters

#  ()
from .core import (
    InferenceEngine,
    ModelLoader,
    FeaturePipeline,
    Predictor,
    SignalInterpreter,
    SignalType,
    RiskLevel,
    create_inference_engine,
)
#  AI 
from .core.inference_engine import TradingSignal as AITradingSignal

# 
from .analysis import (
    CryptoNewsAnalyzer,
    NewsArticle,
    NewsAnalysisResult,
    get_news_analyzer,
    MarketKeywords,
    KeywordMatch
)

# 
from .trading import (
    TradingPlanController,
    MarketAnalyzer,
    StrategySelector,
    PairSelector
)
# : SOPAutomationSystem, PreTradeCheckSystem, TradingPlanGenerator

# 
CryptoFuturesTrader = TradingEngine

__all__ = [
    # 
    "TradingEngine",
    "CryptoFuturesTrader",  # 
    "SelfImprovementSystem",
    
    #  ()
    "InferenceEngine",
    "ModelLoader",
    "FeaturePipeline",
    "Predictor",
    "SignalInterpreter",
    "SignalType",
    "RiskLevel",
    "AITradingSignal",
    "create_inference_engine",
    
    # 
    "MarketData",
    "TradingSignal",
    
    # 
    "BinanceFuturesConnector",
    "ExchangeRateService",
    
    # 
    "RiskManager",
    "RiskParameters",
    
    # 
    "StrategyFusion",
    
    # 
    "CryptoNewsAnalyzer",
    "NewsArticle",
    "NewsAnalysisResult",
    "get_news_analyzer",
    "MarketKeywords",
    "KeywordMatch",
    
    # 
    "TradingPlanController",
    "MarketAnalyzer",
    "StrategySelector",
    "PairSelector",
]

print(f"[BioNeuronai v{__version__}] ")
print(f": {len(__all__)} ")
print(": core | analysis | strategies | trading | data | risk_management")
