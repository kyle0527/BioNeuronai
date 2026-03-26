"""
策略選擇器內部類型 - Strategy Selector Internal Types

此檔案只包含 **模組專屬** 的內部定義。
通用型別請從 schemas/ 導入。

遵循 CODE_FIX_GUIDE.md:
- 通用枚舉: schemas/enums.py
- 通用模型: schemas/strategy.py
- 此處僅放模組專屬的內部結構

Created: 2026-01-25
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Any

# 從 schemas 導入通用型別 (Single Source of Truth)
from schemas.enums import (
    StrategyType,
    MarketRegime,
    Complexity,
    RiskLevel,
)
from schemas.strategy import (
    StrategyRecommendation,
    STRATEGY_MARKET_FIT,
)


@dataclass
class StrategyConfigTemplate:
    """
    策略配置模板 - 模組專屬
    
    用於定義策略的**預設配置模板**，包括：
    - 入場/出場條件
    - 風險參數
    - 預期績效指標
    - 適合的市場環境
    
    注意：這與 schemas/strategy.py 的 StrategyConfig 不同：
    - 此類是策略的「配置模板」（靜態定義）
    - schemas 的是策略的「運行實例」（動態狀態）
    """
    strategy_type: StrategyType
    name: str
    description: str
    entry_conditions: Dict[str, Any]
    exit_conditions: Dict[str, Any]
    risk_parameters: Dict[str, Any]
    timeframe: str
    min_capital: float
    expected_return: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    suitable_markets: List[MarketRegime]
    complexity: Complexity = Complexity.MEDIUM


@dataclass
class StrategySelectionResult:
    """
    策略選擇結果 - 模組專屬 (內部使用)
    
    用於 async select_optimal_strategy() 的返回值。
    包含詳細的選擇結果，使用 StrategyConfigTemplate。
    
    注意：對外 API 建議使用 schemas/strategy.py 的 StrategyRecommendation
    """
    timestamp: datetime = field(default_factory=datetime.now)
    primary_strategy: Optional[StrategyConfigTemplate] = None
    backup_strategies: List[StrategyConfigTemplate] = field(default_factory=list)
    strategy_mix: Dict[str, float] = field(default_factory=dict)
    confidence_score: float = 0.5
    market_match_score: float = 0.5
    reasoning: str = ""
    risk_assessment: Dict[str, Any] = field(default_factory=dict)
    expected_performance: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InternalPerformanceMetrics:
    """
    內部績效指標 - 模組專屬
    
    用於 evaluator.py 的內部績效追蹤。
    對外 API 建議使用 schemas/strategy.py 的 StrategyPerformanceMetrics
    """
    strategy_name: str
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 1.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    total_return: float = 0.0
    avg_trade_duration: float = 0.0  # 小時
    market_conditions_performance: Dict[str, float] = field(default_factory=dict)


# 重新導出 schemas 的型別，方便模組內使用
__all__ = [
    # 從 schemas 導入的通用型別
    "StrategyType",
    "MarketRegime",
    "Complexity",
    "RiskLevel",
    "StrategyRecommendation",
    "STRATEGY_MARKET_FIT",
    # 模組專屬型別
    "StrategyConfigTemplate",
    "StrategySelectionResult",
    "InternalPerformanceMetrics",
]
