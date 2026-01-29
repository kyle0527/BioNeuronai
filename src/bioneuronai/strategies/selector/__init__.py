"""
策略選擇器模組 - Strategy Selector Module

整合 v1 和 v2 的完整功能，提供統一的策略選擇介面。

使用方式:
    from bioneuronai.strategies.selector import StrategySelector
    
    # 基本使用
    selector = StrategySelector(timeframe="1h")
    recommendation = selector.recommend_strategy(ohlcv_data)
    
    # 使用 AI Fusion
    selector = StrategySelector(enable_ai_fusion=True)
    recommendation = selector.recommend_strategy(
        ohlcv_data,
        event_score=event_score,
        event_context=event_context
    )
    
    # 詳細選擇 (async)
    selection = await selector.select_optimal_strategy(ohlcv_data)

Created: 2026-01-25
Replaces: trading/strategy_selector.py, trading/strategy_selector_v2.py
"""

# 類型定義
from .types import (
    StrategyType,
    MarketRegime,
    Complexity,
    StrategyConfigTemplate,
    StrategySelectionResult,
    StrategyRecommendation,
    InternalPerformanceMetrics,
    STRATEGY_MARKET_FIT,
)

# 策略配置
from .configs import (
    get_default_strategy_configs,
    get_strategy_by_type,
    STRATEGY_ALIASES,
)

# 市場評估器
from .evaluator import MarketEvaluator

# 核心選擇器
from .core import (
    StrategySelector,
    get_recommended_strategy,
)


__all__ = [
    # 核心類
    "StrategySelector",
    "MarketEvaluator",
    
    # 類型
    "StrategyType",
    "MarketRegime",
    "Complexity",
    "StrategyConfigTemplate",
    "StrategySelectionResult",
    "StrategyRecommendation",
    "InternalPerformanceMetrics",
    
    # 配置
    "get_default_strategy_configs",
    "get_strategy_by_type",
    "STRATEGY_ALIASES",
    "STRATEGY_MARKET_FIT",
    
    # 便捷函數
    "get_recommended_strategy",
]
