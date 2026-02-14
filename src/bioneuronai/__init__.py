"""
BioNeuronai - AI 
====================================

 v2.1:
- core:  (Battle Royale)
- analysis:  (RLHF)
- strategies: RL Meta-Agent 
- automation: SOP 
- services: 
- planning: 
- data_models: 
- connectors: API 
- risk_management: 
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

#  ()
try:
    from .core.self_improvement import (
        StrategyGene,
        EvolutionEngine,
        PopulationManager
    )
    GENETIC_ALGO_AVAILABLE = True
except ImportError:
    GENETIC_ALGO_AVAILABLE = False
    StrategyGene = None
    EvolutionEngine = None
    PopulationManager = None

# 
from .analysis import (
    CryptoNewsAnalyzer,
    NewsArticle,
    NewsAnalysisResult,
    get_news_analyzer,
    MarketKeywords,
    KeywordMatch
)

#  (RLHF)
try:
    from .analysis.news import (  # ✅ 修正：從 news 子模組導入
        NewsPredictionLoop
    )
    # 檢查是否有 NewsPrediction 類
    try:
        from .analysis.news.prediction_loop import NewsPrediction
    except (ImportError, AttributeError):
        NewsPrediction = None
    NEWS_PREDICTION_AVAILABLE = True
except ImportError:
    NEWS_PREDICTION_AVAILABLE = False
    NewsPrediction = None
    NewsPredictionLoop = None

# 
from .trading import (
    TradingPlanController,
    MarketAnalyzer,
    StrategySelector,
    PairSelector
)
# : SOPAutomationSystem, PreTradeCheckSystem, TradingPlanGenerator

#  RL Meta-Agent ()
try:
    from .strategies.rl_fusion_agent import (
        RLMetaAgent,
        StrategyFusionEnv
    )
    RL_FUSION_AVAILABLE = True
except ImportError:
    RL_FUSION_AVAILABLE = False
    RLMetaAgent = None
    StrategyFusionEnv = None

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
    
    #  ()
    "StrategyGene",
    "EvolutionEngine",
    "PopulationManager",
    "GENETIC_ALGO_AVAILABLE",
    
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
    
    #  RL Meta-Agent ()
    "RLMetaAgent",
    "StrategyFusionEnv",
    "RL_FUSION_AVAILABLE",
    
    # 
    "CryptoNewsAnalyzer",
    "NewsArticle",
    "NewsAnalysisResult",
    "get_news_analyzer",
    "MarketKeywords",
    "KeywordMatch",
    
    #  (RLHF)
    "NewsPrediction",
    "NewsPredictionLoop",
    "NEWS_PREDICTION_AVAILABLE",
    
    # 
    "TradingPlanController",
    "MarketAnalyzer",
    "StrategySelector",
    "PairSelector",
]

print(f"[BioNeuronai v{__version__}] ")
print(f": {len(__all__)} ")
print(": core | analysis | strategies | trading | data | risk_management")

# 
if GENETIC_ALGO_AVAILABLE:
    print("✅ ")
else:
    print("⚠️  (numpy)")

if RL_FUSION_AVAILABLE:
    print("✅ RL Meta-Agent ")
else:
    print("⚠️  RL Meta-Agent (stable-baselines3 + gymnasium)")

if NEWS_PREDICTION_AVAILABLE:
    print("✅ ")
else:
    print("⚠️  ")
