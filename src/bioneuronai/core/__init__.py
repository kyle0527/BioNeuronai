"""

============

"""

try:
    from .trading_engine import TradingEngine
    from .self_improvement import SelfImprovementSystem
    from .inference_engine import (
        InferenceEngine,
        ModelLoader,
        FeaturePipeline,
        Predictor,
        SignalInterpreter,
        TradingSignal,
        SignalType,
        RiskLevel,
        create_inference_engine,
    )
except (ImportError, AttributeError):
    # torch 未安裝時的優雅降級
    TradingEngine = None          # type: ignore[assignment,misc]
    SelfImprovementSystem = None  # type: ignore[assignment,misc]
    InferenceEngine = None        # type: ignore[assignment,misc]
    ModelLoader = None            # type: ignore[assignment,misc]
    FeaturePipeline = None        # type: ignore[assignment,misc]
    Predictor = None              # type: ignore[assignment,misc]
    SignalInterpreter = None      # type: ignore[assignment,misc]
    TradingSignal = None          # type: ignore[assignment,misc]
    SignalType = None             # type: ignore[assignment,misc]
    RiskLevel = None              # type: ignore[assignment,misc]
    create_inference_engine = None  # type: ignore[assignment,misc]

__all__ = [
    # 
    'TradingEngine',
    'SelfImprovementSystem',
    
    # 
    'InferenceEngine',
    'ModelLoader',
    'FeaturePipeline',
    'Predictor',
    'SignalInterpreter',
    'TradingSignal',
    'SignalType',
    'RiskLevel',
    'create_inference_engine',
]

# 
CryptoFuturesTrader = TradingEngine
