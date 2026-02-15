"""

================


1. 
2. 
3. 
4. 
5. 
6. 


- /
- 
- 15
-  Binance Futures API


1. TrendFollowingStrategy - 
2. SwingTradingStrategy -   
3. MeanReversionStrategy - 
4. BreakoutStrategy - 
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
