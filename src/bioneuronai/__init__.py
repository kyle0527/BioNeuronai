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

import importlib
import logging  # noqa: E402 (imports after sys.path setup are intentional)
from typing import Any

# 套件層級 logger — 不在 import 時強制設定 root logger 或建立 FileHandler
# FileHandler 由 CLI 入口 (cli/main.py) 或應用程式自行配置
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

_EXPORTS: dict[str, tuple[str, str]] = {
    "TradingEngine": ("bioneuronai.core", "TradingEngine"),
    "CryptoFuturesTrader": ("bioneuronai.core", "TradingEngine"),
    "SelfImprovementSystem": ("bioneuronai.core", "SelfImprovementSystem"),
    "InferenceEngine": ("bioneuronai.core", "InferenceEngine"),
    "ModelLoader": ("bioneuronai.core", "ModelLoader"),
    "FeaturePipeline": ("bioneuronai.core", "FeaturePipeline"),
    "Predictor": ("bioneuronai.core", "Predictor"),
    "SignalInterpreter": ("bioneuronai.core", "SignalInterpreter"),
    "SignalType": ("bioneuronai.core", "SignalType"),
    "RiskLevel": ("bioneuronai.core", "RiskLevel"),
    "AITradingSignal": ("bioneuronai.core.inference_engine", "TradingSignal"),
    "create_inference_engine": ("bioneuronai.core", "create_inference_engine"),
    "StrategyGene": ("bioneuronai.core.self_improvement", "StrategyGene"),
    "EvolutionEngine": ("bioneuronai.core.self_improvement", "EvolutionEngine"),
    "PopulationManager": ("bioneuronai.core.self_improvement", "PopulationManager"),
    "MarketData": ("schemas.market", "MarketData"),
    "TradingSignal": ("schemas.trading", "TradingSignal"),
    "BinanceFuturesConnector": ("bioneuronai.data", "BinanceFuturesConnector"),
    "ExchangeRateService": ("bioneuronai.data", "ExchangeRateService"),
    "RiskManager": ("bioneuronai.risk_management", "RiskManager"),
    "RiskParameters": ("bioneuronai.risk_management", "RiskParameters"),
    "AIStrategyFusion": ("bioneuronai.strategies", "AIStrategyFusion"),
    "StrategySelector": ("bioneuronai.strategies", "StrategySelector"),
    "RLMetaAgent": ("bioneuronai.strategies.rl_fusion_agent", "RLMetaAgent"),
    "StrategyFusionEnv": ("bioneuronai.strategies.rl_fusion_agent", "StrategyFusionEnv"),
    "CryptoNewsAnalyzer": ("bioneuronai.analysis", "CryptoNewsAnalyzer"),
    "NewsArticle": ("bioneuronai.analysis", "NewsArticle"),
    "NewsAnalysisResult": ("bioneuronai.analysis", "NewsAnalysisResult"),
    "get_news_analyzer": ("bioneuronai.analysis", "get_news_analyzer"),
    "MarketKeywords": ("bioneuronai.analysis", "MarketKeywords"),
    "KeywordMatch": ("bioneuronai.analysis", "KeywordMatch"),
    "NewsPrediction": ("bioneuronai.analysis.news.prediction_loop", "NewsPrediction"),
    "NewsPredictionLoop": ("bioneuronai.analysis.news", "NewsPredictionLoop"),
    "TradingPlanController": ("bioneuronai.planning", "TradingPlanController"),
    "MarketAnalyzer": ("bioneuronai.planning", "MarketAnalyzer"),
    "PairSelector": ("bioneuronai.planning", "PairSelector"),
    "cli_main": ("bioneuronai.cli", "cli_main"),
}


def __getattr__(name: str) -> Any:
    """Lazy public export loader.

    The package itself stays importable so API status/readiness can report
    runtime problems. Accessing core AI/trading symbols still imports the real
    module and raises the original error when the runtime is not ready.
    """
    if name in {
        "TORCH_AVAILABLE",
        "STRATEGIES_AVAILABLE",
        "GENETIC_ALGO_AVAILABLE",
        "RL_FUSION_AVAILABLE",
        "NEWS_PREDICTION_AVAILABLE",
    }:
        return _check_export_available(name)
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module_name, attr_name = target
    module = importlib.import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value


def _check_export_available(name: str) -> bool:
    groups = {
        "TORCH_AVAILABLE": ("bioneuronai.core", "TradingEngine"),
        "STRATEGIES_AVAILABLE": ("bioneuronai.strategies", "StrategySelector"),
        "GENETIC_ALGO_AVAILABLE": ("bioneuronai.core.self_improvement", "StrategyGene"),
        "RL_FUSION_AVAILABLE": ("bioneuronai.strategies.rl_fusion_agent", "RLMetaAgent"),
        "NEWS_PREDICTION_AVAILABLE": ("bioneuronai.analysis.news", "NewsPredictionLoop"),
    }
    module_name, attr_name = groups[name]
    try:
        module = importlib.import_module(module_name)
        getattr(module, attr_name)
        return True
    except Exception:
        return False

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
