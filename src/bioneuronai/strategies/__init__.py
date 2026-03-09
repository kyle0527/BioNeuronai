"""
策略模組
================

BioNeuronAI 交易策略集合：
1. 基礎策略基類與數據模型
2. 趨勢跟隨策略
3. 波段交易策略
4. 均值回歸策略
5. 突破交易策略
6. 方向變化策略（DC 算法）
7. 配對交易策略（統計套利）

架構：
- 全策略繼承 BaseStrategy 抽象基類
- 支援遺傳算法競技場（strategy_arena）
- 支援 AI 多策略融合（strategy_fusion）
- 支援 9 階段市場路由（phase_router）
- 整合 Binance Futures API
"""

from .base_strategy import (
    BaseStrategy,
    StrategyState,
    TradeSetup,
    TradeExecution,
    PositionManagement,
    RiskParameters,
    StrategyPerformance,
)

from .trend_following import TrendFollowingStrategy
from .swing_trading import SwingTradingStrategy
from .mean_reversion import MeanReversionStrategy
from .breakout_trading import BreakoutTradingStrategy
from .direction_change_strategy import DirectionChangeStrategy
from .pair_trading_strategy import PairTradingStrategy
from .strategy_fusion import AIStrategyFusion, FusionMethod, FusionSignal, MarketRegime

# 階段路由模組 (2026-02-15 AI 策略編排)
from .phase_router import (
    TradingPhaseRouter,
    TradingPhase,
    TradeActionPhase,
    PhaseConfig,
    PhaseState,
    StrategyPerformanceRecord,
)

# 策略選擇器模組 (2026-01-25 新增)
from .selector import (
    StrategySelector,
    StrategyType,
    StrategyConfigTemplate,
    StrategySelectionResult,
    StrategyRecommendation,
    MarketEvaluator,
    get_recommended_strategy,
)

__all__ = [
    # 基礎類
    'BaseStrategy',
    'StrategyState',
    'TradeSetup',
    'TradeExecution',
    'PositionManagement',
    'RiskParameters',
    'StrategyPerformance',
    
    # 策略實現
    'TrendFollowingStrategy',
    'SwingTradingStrategy',
    'MeanReversionStrategy',
    'BreakoutTradingStrategy',
    'DirectionChangeStrategy',
    'PairTradingStrategy',
    
    # AI 融合
    'AIStrategyFusion',
    'FusionMethod',
    'FusionSignal',
    'MarketRegime',
    
    # 階段路由 (2026-02-15 AI 策略編排)
    'TradingPhaseRouter',
    'TradingPhase',
    'TradeActionPhase',
    'PhaseConfig',
    'PhaseState',
    'StrategyPerformanceRecord',
    
    # 策略選擇器 (2026-01-25 新增)
    'StrategySelector',
    'StrategyType',
    'StrategyConfigTemplate',
    'StrategySelectionResult',
    'StrategyRecommendation',
    'MarketEvaluator',
    'get_recommended_strategy',
]
