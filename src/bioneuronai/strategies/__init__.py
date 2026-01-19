"""
完整交易策略模組
================

每個策略都是一個完整的交易流程，包含：
1. 市場分析與確認條件
2. 進場規則（多重確認）
3. 出場規則（停損、停利、追蹤止損、時間止損）
4. 部位管理（分批進場、分批出場）
5. 風險控制（動態調整）
6. 交易管理（加碼、減碼決策）

策略設計原則：
- 不使用剝頭皮/高頻交易
- 適合零售交易者使用
- 使用15分鐘以上時間框架
- 整合 Binance Futures API

策略列表：
1. TrendFollowingStrategy - 趨勢跟隨策略
2. SwingTradingStrategy - 波段交易策略  
3. MeanReversionStrategy - 均值回歸策略
4. BreakoutStrategy - 突破交易策略
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

__all__ = [
    # 基礎類別
    'BaseStrategy',
    'StrategyState',
    'TradeSetup',
    'TradeExecution',
    'PositionManagement',
    'RiskParameters',
    'StrategyPerformance',
    
    # 完整策略
    'TrendFollowingStrategy',
    'SwingTradingStrategy',
    'MeanReversionStrategy',
    'BreakoutTradingStrategy',
    
    # AI 融合系統
    'AIStrategyFusion',
    'FusionMethod',
    'FusionSignal',
    'MarketRegime',
]
