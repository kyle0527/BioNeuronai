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

__version__ = "2.1"
__author__ = "BioNeuronai Team"

import logging  # noqa: E402 (imports after sys.path setup are intentional)
from typing import Any

# 套件層級 logger — 不在 import 時強制設定 root logger 或建立 FileHandler
# FileHandler 由 CLI 入口 (cli/main.py) 或應用程式自行配置
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# 核心模組（依賴 torch，若未安裝則優雅降級）
try:
    from .core import TradingEngine, SelfImprovementSystem
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
    from .core.inference_engine import TradingSignal as AITradingSignal
    TORCH_AVAILABLE = True
except (ImportError, AttributeError) as _torch_err:
    TORCH_AVAILABLE = False
    TradingEngine = None          # type: ignore[assignment,misc]
    SelfImprovementSystem = None  # type: ignore[assignment,misc]
    InferenceEngine = None        # type: ignore[assignment,misc]
    ModelLoader = None            # type: ignore[assignment,misc]
    FeaturePipeline = None        # type: ignore[assignment,misc]
    Predictor = None              # type: ignore[assignment,misc]
    SignalInterpreter = None      # type: ignore[assignment,misc]
    SignalType = None             # type: ignore[assignment,misc]
    RiskLevel = None              # type: ignore[assignment,misc]
    AITradingSignal = None        # type: ignore[assignment,misc]
    create_inference_engine = None  # type: ignore[assignment,misc]
    logging.getLogger(__name__).warning(
        "torch 未安裝，TradingEngine / InferenceEngine 不可用。"
        " 執行 pip install torch 以啟用 AI 功能。"
    )

from schemas.market import MarketData  # noqa: E402
from schemas.trading import TradingSignal  # noqa: E402
from .data import BinanceFuturesConnector, ExchangeRateService  # noqa: E402
from .risk_management import RiskManager, RiskParameters  # noqa: E402
from .strategies import AIStrategyFusion, StrategySelector  # noqa: E402

#  ()
imported_strategy_gene: Any = None
imported_evolution_engine: Any = None
imported_population_manager: Any = None
try:
    from .core.self_improvement import (
        StrategyGene as imported_strategy_gene,
        EvolutionEngine as imported_evolution_engine,
        PopulationManager as imported_population_manager,
    )
    GENETIC_ALGO_AVAILABLE = True
except ImportError:
    GENETIC_ALGO_AVAILABLE = False

StrategyGene: Any = imported_strategy_gene
EvolutionEngine: Any = imported_evolution_engine
PopulationManager: Any = imported_population_manager

# 
from .analysis import (  # noqa: E402
    CryptoNewsAnalyzer,
    NewsArticle,
    NewsAnalysisResult,
    get_news_analyzer,
    MarketKeywords,
    KeywordMatch
)

#  (RLHF)
imported_news_prediction: Any = None
imported_news_prediction_loop: Any = None
try:
    from .analysis.news import (  # ✅ 修正：從 news 子模組導入
        NewsPredictionLoop as imported_news_prediction_loop,
    )
    # 檢查是否有 NewsPrediction 類
    try:
        from .analysis.news.prediction_loop import NewsPrediction as imported_news_prediction
    except (ImportError, AttributeError):
        imported_news_prediction = None
    NEWS_PREDICTION_AVAILABLE = True
except ImportError:
    NEWS_PREDICTION_AVAILABLE = False
    imported_news_prediction = None
    imported_news_prediction_loop = None

NewsPrediction: Any = imported_news_prediction
NewsPredictionLoop: Any = imported_news_prediction_loop

# 
from .planning import (  # noqa: E402
    TradingPlanController,
    MarketAnalyzer,
    PairSelector
)
# : SOPAutomationSystem, PreTradeCheckSystem

#  RL Meta-Agent ()
imported_rl_meta_agent: Any = None
imported_strategy_fusion_env: Any = None
try:
    from .strategies.rl_fusion_agent import (
        RLMetaAgent as imported_rl_meta_agent,
        StrategyFusionEnv as imported_strategy_fusion_env,
    )
    RL_FUSION_AVAILABLE = True
except ImportError:
    RL_FUSION_AVAILABLE = False

RLMetaAgent: Any = imported_rl_meta_agent
StrategyFusionEnv: Any = imported_strategy_fusion_env

# CLI 統一入口
from .cli import cli_main  # noqa: E402

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
    
    # 策略融合
    "AIStrategyFusion",
    
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

    # CLI 統一入口
    "cli_main",
]

logger.debug("[BioNeuronai v%s] 已載入 %d 個公開符號", __version__, len(__all__))
logger.debug("模組: core | analysis | strategies | trading | data | risk_management")

if GENETIC_ALGO_AVAILABLE:
    logger.debug("遺傳演算法模組已啟用")
else:
    logger.debug("遺傳演算法模組不可用 (需要 numpy)")

if RL_FUSION_AVAILABLE:
    logger.debug("RL Meta-Agent 已啟用")
else:
    logger.debug("RL Meta-Agent 不可用 (需要 stable-baselines3 + gymnasium)")

if NEWS_PREDICTION_AVAILABLE:
    logger.debug("新聞預測模組已啟用")
else:
    logger.debug("新聞預測模組不可用")
