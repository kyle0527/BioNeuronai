"""
規劃模組 - Planning Module
==========================

負責高階交易規劃與交易前檢查：
- 10 步驟交易計劃控制
- 市場環境分析
- 交易對篩選
- 單筆交易前檢查
- 自主運行編排與自適應控制

此模組不負責實際訂單、帳戶、持倉或資金狀態事實。
"""

from typing import TYPE_CHECKING

__all__ = [
    "TradingPlanController",
    "AutonomousOperator",
    "AutonomousOperatorConfig",
    "AdaptationController",
    "DecisionLedger",
    "MarketAnalyzer",
    "PairSelector",
    "PreTradeCheckSystem",
    "GoalConfig",
    "GoalReport",
    "GoalTracker",
]

# PEP 562 延遲載入：輕量模組（adaptation_controller / decision_ledger /
# autonomous_operator）不因 import 本套件而載入計劃/檢查系統的完整依賴鏈。
_LAZY_IMPORTS = {
    "GoalConfig": ("bioneuronai.planning.goal_manager", "GoalConfig"),
    "GoalReport": ("bioneuronai.planning.goal_manager", "GoalReport"),
    "GoalTracker": ("bioneuronai.planning.goal_manager", "GoalTracker"),
    "AdaptationController": ("bioneuronai.planning.adaptation_controller", "AdaptationController"),
    "AutonomousOperator": ("bioneuronai.planning.autonomous_operator", "AutonomousOperator"),
    "AutonomousOperatorConfig": ("bioneuronai.planning.autonomous_operator", "AutonomousOperatorConfig"),
    "DecisionLedger": ("bioneuronai.planning.decision_ledger", "DecisionLedger"),
    "MarketAnalyzer": ("bioneuronai.planning.market_analyzer", "MarketAnalyzer"),
    "PairSelector": ("bioneuronai.planning.pair_selector", "PairSelector"),
    "TradingPlanController": ("bioneuronai.planning.plan_controller", "TradingPlanController"),
    "PreTradeCheckSystem": ("bioneuronai.planning.pretrade_automation", "PreTradeCheckSystem"),
}

if TYPE_CHECKING:  # pragma: no cover - 僅供型別檢查
    from .adaptation_controller import AdaptationController as AdaptationController
    from .autonomous_operator import (  # noqa: F401
        AutonomousOperator,
        AutonomousOperatorConfig,
    )
    from .decision_ledger import DecisionLedger as DecisionLedger
    from .market_analyzer import MarketAnalyzer as MarketAnalyzer
    from .pair_selector import PairSelector as PairSelector
    from .plan_controller import TradingPlanController as TradingPlanController
    from .pretrade_automation import PreTradeCheckSystem as PreTradeCheckSystem


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        import importlib
        module_name, attr = _LAZY_IMPORTS[name]
        value = getattr(importlib.import_module(module_name), attr)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def get_trading_plan_controller():
    """回傳交易計劃控制器實例。"""
    from .plan_controller import TradingPlanController
    return TradingPlanController()
