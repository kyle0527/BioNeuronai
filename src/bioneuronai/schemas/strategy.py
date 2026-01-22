"""
BioNeuronai 策略配置模型

定義策略配置相關的 Pydantic 模型。
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from bioneuronai.schemas.enums import (
    StrategyType,
    StrategyState,
    MarketRegime,
    MarketCondition,
    SignalStrength,
)


class StrategyConfig(BaseModel):
    """策略配置模型"""
    
    strategy_id: str = Field(..., description="策略唯一識別碼")
    strategy_name: str = Field(..., description="策略名稱")
    strategy_type: StrategyType = Field(..., description="策略類型")
    
    # 策略狀態
    state: StrategyState = Field(default=StrategyState.INACTIVE, description="策略狀態")
    
    # 適用條件
    applicable_market_regimes: list[MarketRegime] = Field(
        default_factory=list,
        description="適用的市場狀態",
    )
    applicable_symbols: list[str] = Field(
        default_factory=list,
        description="適用的交易對列表",
    )
    
    # 策略參數
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="策略特定參數",
    )
    
    # 權重配置
    weight: float = Field(default=1.0, ge=0, le=1, description="策略權重 (0-1)")
    min_confidence: float = Field(default=0.6, ge=0, le=1, description="最低信號置信度")
    
    # 時間控制
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新時間")
    
    # 性能追蹤
    total_signals: int = Field(default=0, ge=0, description="總信號數")
    successful_trades: int = Field(default=0, ge=0, description="成功交易數")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "strategy_id": "trend_follow_001",
                    "strategy_name": "趨勢跟蹤策略 v1",
                    "strategy_type": "trend_following",
                    "state": "active",
                    "applicable_market_regimes": ["bull", "bear"],
                    "applicable_symbols": ["BTCUSDT", "ETHUSDT"],
                    "parameters": {
                        "fast_ma_period": 12,
                        "slow_ma_period": 26,
                        "signal_period": 9,
                    },
                    "weight": 0.8,
                    "min_confidence": 0.7,
                }
            ]
        }
    }


class StrategySelection(BaseModel):
    """策略選擇模型"""
    
    selected_strategy: str = Field(..., description="選中的策略 ID")
    selection_time: datetime = Field(default_factory=datetime.now, description="選擇時間")
    
    # 選擇原因
    market_regime: MarketRegime = Field(..., description="當前市場狀態")
    market_conditions: list[MarketCondition] = Field(
        default_factory=list,
        description="當前市場條件",
    )
    
    # 備選策略
    alternative_strategies: list[str] = Field(
        default_factory=list,
        description="備選策略列表",
    )
    
    # 選擇依據
    selection_score: float = Field(..., ge=0, le=1, description="選擇分數 (0-1)")
    confidence: float = Field(..., ge=0, le=1, description="選擇置信度 (0-1)")
    
    # 元數據
    metadata: Optional[Dict[str, Any]] = Field(None, description="額外元數據")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "selected_strategy": "trend_follow_001",
                    "market_regime": "bull",
                    "market_conditions": ["trending_up", "high_volatility"],
                    "alternative_strategies": ["breakout_001", "swing_001"],
                    "selection_score": 0.85,
                    "confidence": 0.78,
                }
            ]
        }
    }


class StrategyPerformanceMetrics(BaseModel):
    """策略性能指標模型"""
    
    strategy_id: str = Field(..., description="策略 ID")
    
    # 基本指標
    total_trades: int = Field(default=0, ge=0, description="總交易次數")
    winning_trades: int = Field(default=0, ge=0, description="獲利交易次數")
    losing_trades: int = Field(default=0, ge=0, description="虧損交易次數")
    
    # 盈虧指標
    total_pnl: float = Field(default=0.0, description="總盈虧")
    total_pnl_pct: float = Field(default=0.0, description="總盈虧百分比")
    average_win: float = Field(default=0.0, description="平均獲利")
    average_loss: float = Field(default=0.0, description="平均虧損")
    
    # 風險指標
    max_drawdown: float = Field(default=0.0, ge=0, le=1, description="最大回撤")
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    sortino_ratio: Optional[float] = Field(None, description="索提諾比率")
    
    # 勝率指標
    win_rate: float = Field(default=0.0, ge=0, le=1, description="勝率 (0-1)")
    profit_factor: Optional[float] = Field(None, ge=0, description="盈利因子")
    
    # 時間範圍
    start_date: Optional[datetime] = Field(None, description="開始日期")
    end_date: Optional[datetime] = Field(None, description="結束日期")
    
    # 更新時間
    last_updated: datetime = Field(default_factory=datetime.now, description="最後更新時間")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "strategy_id": "trend_follow_001",
                    "total_trades": 100,
                    "winning_trades": 65,
                    "losing_trades": 35,
                    "total_pnl": 5000.0,
                    "total_pnl_pct": 0.25,
                    "average_win": 120.0,
                    "average_loss": -60.0,
                    "max_drawdown": 0.12,
                    "sharpe_ratio": 1.8,
                    "win_rate": 0.65,
                    "profit_factor": 2.0,
                }
            ]
        }
    }


class TradeSetup(BaseModel):
    """交易設置模型"""
    
    symbol: str = Field(..., description="交易對符號")
    strategy_id: str = Field(..., description="策略 ID")
    
    # 入場設置
    entry_condition: MarketCondition = Field(..., description="入場條件")
    entry_price_target: float = Field(..., gt=0, description="目標入場價格")
    entry_signal_strength: SignalStrength = Field(..., description="入場信號強度")
    
    # 出場設置
    exit_conditions: list[MarketCondition] = Field(
        default_factory=list,
        description="出場條件列表",
    )
    take_profit_targets: list[float] = Field(
        default_factory=list,
        description="止盈目標列表",
    )
    stop_loss_price: float = Field(..., gt=0, description="止損價格")
    
    # 倉位管理
    position_size: float = Field(..., gt=0, le=1, description="倉位大小 (0-1)")
    max_holding_time: Optional[int] = Field(None, gt=0, description="最大持倉時間(分鐘)")
    
    # 附加信息
    notes: Optional[str] = Field(None, description="備註說明")
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "strategy_id": "trend_follow_001",
                    "entry_condition": "breakout",
                    "entry_price_target": 50000.0,
                    "entry_signal_strength": "strong",
                    "exit_conditions": ["reversal", "high_volatility"],
                    "take_profit_targets": [52000.0, 54000.0],
                    "stop_loss_price": 48000.0,
                    "position_size": 0.1,
                    "max_holding_time": 1440,
                }
            ]
        }
    }
