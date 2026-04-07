"""
規劃模組 - Planning Module
==========================

負責高階交易規劃與交易前檢查：
- 10 步驟交易計劃控制
- 市場環境分析
- 交易對篩選
- 單筆交易前檢查

此模組不負責實際訂單、帳戶、持倉或資金狀態事實。
"""

from .market_analyzer import MarketAnalyzer
from .pair_selector import PairSelector
from .plan_controller import TradingPlanController
from .pretrade_automation import PreTradeCheckSystem

__all__ = [
    "TradingPlanController",
    "MarketAnalyzer",
    "PairSelector",
    "PreTradeCheckSystem",
]


def get_trading_plan_controller() -> TradingPlanController:
    """回傳交易計劃控制器實例。"""
    return TradingPlanController()

