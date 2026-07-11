"""核心模組

採 PEP 562 延遲載入：輕量模組（reward / adaptive_hub / action_record /
online_learner）不應因為 import 本套件就被迫載入 TradingEngine 的完整
依賴鏈（新聞排程、交易所連接器等）。
"""

from typing import TYPE_CHECKING

__all__ = [
    'TradingEngine',
    'SelfImprovementSystem',
    'CryptoFuturesTrader',
    'InferenceEngine',
    'ModelLoader',
    'FeaturePipeline',
    'Predictor',
    'SignalInterpreter',
    'TradingSignal',
    'SignalType',
    'RiskLevel',
    'create_inference_engine',
    'AdaptiveLearningHub',
    'OnlineLearner',
    'ActionRecord',
    'compute_reward',
    'RewardConfig',
]

_LAZY_IMPORTS = {
    'TradingEngine': ('bioneuronai.core.trading_engine', 'TradingEngine'),
    'CryptoFuturesTrader': ('bioneuronai.core.trading_engine', 'TradingEngine'),
    'SelfImprovementSystem': ('bioneuronai.core.self_improvement', 'SelfImprovementSystem'),
    'InferenceEngine': ('bioneuronai.core.inference_engine', 'InferenceEngine'),
    'ModelLoader': ('bioneuronai.core.inference_engine', 'ModelLoader'),
    'FeaturePipeline': ('bioneuronai.core.inference_engine', 'FeaturePipeline'),
    'Predictor': ('bioneuronai.core.inference_engine', 'Predictor'),
    'SignalInterpreter': ('bioneuronai.core.inference_engine', 'SignalInterpreter'),
    'TradingSignal': ('bioneuronai.core.inference_engine', 'TradingSignal'),
    'SignalType': ('bioneuronai.core.inference_engine', 'SignalType'),
    'RiskLevel': ('bioneuronai.core.inference_engine', 'RiskLevel'),
    'create_inference_engine': ('bioneuronai.core.inference_engine', 'create_inference_engine'),
    'AdaptiveLearningHub': ('bioneuronai.core.adaptive_hub', 'AdaptiveLearningHub'),
    'OnlineLearner': ('bioneuronai.core.online_learner', 'OnlineLearner'),
    'ActionRecord': ('bioneuronai.core.action_record', 'ActionRecord'),
    'compute_reward': ('bioneuronai.core.reward', 'compute_reward'),
    'RewardConfig': ('bioneuronai.core.reward', 'RewardConfig'),
}

if TYPE_CHECKING:  # pragma: no cover - 僅供型別檢查
    from .action_record import ActionRecord as ActionRecord
    from .adaptive_hub import AdaptiveLearningHub as AdaptiveLearningHub
    from .inference_engine import (  # noqa: F401
        FeaturePipeline,
        InferenceEngine,
        ModelLoader,
        Predictor,
        RiskLevel,
        SignalInterpreter,
        SignalType,
        TradingSignal,
        create_inference_engine,
    )
    from .online_learner import OnlineLearner as OnlineLearner
    from .reward import RewardConfig as RewardConfig
    from .reward import compute_reward as compute_reward
    from .self_improvement import SelfImprovementSystem as SelfImprovementSystem
    from .trading_engine import TradingEngine as CryptoFuturesTrader
    from .trading_engine import TradingEngine as TradingEngine


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        import importlib
        module_name, attr = _LAZY_IMPORTS[name]
        module = importlib.import_module(module_name)
        value = getattr(module, attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
