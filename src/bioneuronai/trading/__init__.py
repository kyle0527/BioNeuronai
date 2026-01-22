"""
交易模組 - Trading Module
====================================

整合所有交易相關功能：
- 交易計劃制定（市場分析、策略選擇、風險管理）
- 交易前檢查自動化
- SOP 自動化流程
- 回測驗證

Author: BioNeuronai Team
Version: 2.0.0
Date: 2026-01-22
"""

# 交易計劃相關
from .market_analyzer import MarketAnalyzer
from .strategy_selector import StrategySelector  
from .risk_manager import RiskManager
from .pair_selector import PairSelector
from .plan_controller import TradingPlanController

# 自動化相關
from .pretrade_automation import PreTradeCheckSystem
from .trading_plan_system import TradingPlanGenerator

# 版本信息
__version__ = "2.0.0"
__author__ = "BioNeuronai Team"

# 導出主要類別
__all__ = [
    # 交易計劃
    "TradingPlanController",
    "MarketAnalyzer", 
    "StrategySelector",
    "RiskManager",
    "PairSelector",
    # 自動化
    "PreTradeCheckSystem",
    "TradingPlanGenerator",
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