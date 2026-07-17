"""
BioNeuronai 回測系統 - 模組初始化

提供回測相關的所有組件：
- HistoricalBacktest: 歷史數據回測引擎
- WalkForwardTester: Walk-Forward 測試框架
- TradingCostCalculator: 交易成本計算器

注意：
- `backtesting/` 主要用於離線研究、成本分析與 walk-forward 驗證
- 正式 replay / mock exchange 主路徑請使用 repo 根目錄的 `backtest/`

最後更新: 2026-02-15
"""

from .historical_backtest import HistoricalBacktest, HistoricalDataLoader
from .cost_calculator import TradingCostCalculator, TradingCost
from .walk_forward import (
    WalkForwardTester,
    WalkForwardConfig,
    WalkForwardResult,
    WalkForwardWindow,
    WindowResult,
)

__all__ = [
    "HistoricalBacktest",
    "HistoricalDataLoader",
    "TradingCostCalculator",
    "TradingCost",
    "WalkForwardTester",
    "WalkForwardConfig",
    "WalkForwardResult",
    "WalkForwardWindow",
    "WindowResult",
]
