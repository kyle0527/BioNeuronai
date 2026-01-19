"""
交易計劃模組 - Trading Plan Module
====================================

這個模組負責制定完整的每日交易計劃，包含：
- 市場環境分析
- 策略選擇與配置
- 風險管理參數制定
- 交易標的篩選
- 回測驗證
- 計劃最終確認

Author: BioNeuronai Team
Version: 1.0.0
Date: 2026-01-19
"""

from .market_analyzer import MarketAnalyzer
from .strategy_selector import StrategySelector  
from .risk_manager import RiskManager
from .pair_selector import PairSelector
from .backtest_validator import BacktestValidator
from .plan_controller import TradingPlanController

# 版本信息
__version__ = "1.0.0"
__author__ = "BioNeuronai Team"

# 導出主要類別
__all__ = [
    "TradingPlanController",
    "MarketAnalyzer", 
    "StrategySelector",
    "RiskManager",
    "PairSelector",
    "BacktestValidator"
]

# 模組初始化
def get_trading_plan_controller():
    """獲取交易計劃控制器實例"""
    return TradingPlanController()

# 快速使用函數
async def create_daily_trading_plan():
    """快速創建每日交易計劃"""
    controller = get_trading_plan_controller()
    return await controller.create_comprehensive_plan()