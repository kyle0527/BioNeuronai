"""
BioNeuronai 策略配置模型

定義策略配置相關的 Pydantic 模型。
"""

from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from .enums import (
    StrategyType,
    StrategyState,
    MarketRegime,
    MarketCondition,
    SignalStrength,
    RiskLevel,
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


class StrategyRecommendation(BaseModel):
    """
    策略推薦模型 - 完整版本
    
    包含策略選擇的完整資訊：權重分配、推理說明、風險設定、事件調整等。
    
    2026-01-25 新增
    """
    
    # 時間戳
    timestamp: datetime = Field(default_factory=datetime.now, description="推薦時間")
    
    # 主要推薦
    primary_strategy: StrategyType = Field(
        default=StrategyType.TREND_FOLLOWING,
        description="主要推薦策略類型"
    )
    primary_confidence: float = Field(
        default=0.5, ge=0, le=1, 
        description="主要策略置信度 (0-1)"
    )
    
    # 市場狀態
    market_regime: MarketRegime = Field(
        default=MarketRegime.SIDEWAYS,
        description="當前市場體制"
    )
    market_condition: MarketCondition = Field(
        default=MarketCondition.RANGING,
        description="當前市場條件"
    )
    
    # 策略權重分配
    strategy_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="各策略的權重分配 (策略名稱 -> 權重)"
    )
    
    # 推理說明
    reasoning: list[str] = Field(
        default_factory=list,
        description="策略選擇的推理說明列表"
    )
    
    # 風險設定
    risk_level: RiskLevel = Field(
        default=RiskLevel.MEDIUM,
        description="風險等級"
    )
    suggested_position_size: float = Field(
        default=0.02, ge=0, le=1,
        description="建議倉位大小 (0-1)"
    )
    
    # 需避免的策略
    avoid_strategies: list[StrategyType] = Field(
        default_factory=list,
        description="建議避免使用的策略列表"
    )
    
    # 備選策略
    alternative_strategies: list[StrategyType] = Field(
        default_factory=list,
        description="備選策略列表"
    )
    
    # 事件驅動調整 (整合 EventContext)
    has_event_adjustment: bool = Field(
        default=False,
        description="是否有事件驅動調整"
    )
    event_score: float = Field(
        default=0.0, ge=-10, le=10,
        description="事件評分 (-10 到 +10)"
    )
    event_type: Optional[str] = Field(
        default=None,
        description="事件類型 (如 HACK, REGULATION 等)"
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "primary_strategy": "trend_following",
                    "primary_confidence": 0.75,
                    "market_regime": "trending_bull",
                    "market_condition": "trending_up",
                    "strategy_weights": {
                        "trend_following": 0.4,
                        "momentum": 0.3,
                        "breakout": 0.2,
                        "swing_trading": 0.1
                    },
                    "reasoning": [
                        "市場體制: trending_bull",
                        "趨勢跟隨策略在牛市表現最佳",
                        "風險等級: medium"
                    ],
                    "risk_level": "medium",
                    "suggested_position_size": 0.02,
                    "avoid_strategies": ["mean_reversion", "grid_trading"],
                    "has_event_adjustment": False,
                    "event_score": 0.0,
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


def _get_strategy_market_fit() -> Dict[StrategyType, Dict[str, list[MarketRegime]]]:
    """
    策略與市場體制的適配關係表
    
    Returns:
        Dict 包含:
        - best: 該策略最適合的市場體制
        - good: 該策略表現尚可的市場體制
        - avoid: 該策略應避免的市場體制
    
    Added: 2026-01-25
    """
    return {
    StrategyType.TREND_FOLLOWING: {
        'best': [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
        'good': [MarketRegime.BREAKOUT_POTENTIAL],
        'avoid': [MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.VOLATILE_UNCERTAIN],
    },
    StrategyType.SWING_TRADING: {
        'best': [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
        'good': [MarketRegime.SIDEWAYS_HIGH_VOL],
        'avoid': [],
    },
    StrategyType.MEAN_REVERSION: {
        'best': [MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL],
        'good': [],
        'avoid': [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
    },
    StrategyType.BREAKOUT: {
        'best': [MarketRegime.BREAKOUT_POTENTIAL, MarketRegime.SIDEWAYS_LOW_VOL],
        'good': [],
        'avoid': [MarketRegime.VOLATILE_UNCERTAIN],
    },
    StrategyType.MOMENTUM: {
        'best': [MarketRegime.TRENDING_BULL],
        'good': [MarketRegime.BREAKOUT_POTENTIAL],
        'avoid': [MarketRegime.SIDEWAYS_LOW_VOL],
    },
    StrategyType.SCALPING: {
        'best': [MarketRegime.SIDEWAYS_LOW_VOL],
        'good': [],
        'avoid': [MarketRegime.VOLATILE_UNCERTAIN, MarketRegime.TRENDING_BEAR],
    },
    StrategyType.GRID_TRADING: {
        'best': [MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL],
        'good': [],
        'avoid': [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
    },
    StrategyType.VOLATILITY_TRADING: {
        'best': [MarketRegime.VOLATILE_UNCERTAIN, MarketRegime.SIDEWAYS_HIGH_VOL],
        'good': [],
        'avoid': [MarketRegime.SIDEWAYS_LOW_VOL],
    },
    StrategyType.NEWS_TRADING: {
        'best': [MarketRegime.VOLATILE_UNCERTAIN],
        'good': [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
        'avoid': [MarketRegime.SIDEWAYS_LOW_VOL],
    },
    StrategyType.ARBITRAGE: {
        'best': [MarketRegime.SIDEWAYS_LOW_VOL],
        'good': [MarketRegime.SIDEWAYS_HIGH_VOL],
        'avoid': [MarketRegime.VOLATILE_UNCERTAIN],
    },
    StrategyType.AI_FUSION: {
        'best': [],  # AI 適應所有市場
        'good': [
            MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR,
            MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL,
            MarketRegime.VOLATILE_UNCERTAIN, MarketRegime.BREAKOUT_POTENTIAL
        ],
        'avoid': [],
    },
}


# 導出常數
STRATEGY_MARKET_FIT = _get_strategy_market_fit()
