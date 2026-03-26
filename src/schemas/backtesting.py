"""
BioNeuronai 回測系統模型

定義策略回測相關的 Pydantic 模型。
支援完整的回測配置、執行和結果分析。

參考:
- 量化交易回測最佳實踐
- Walk-forward optimization
- Monte Carlo simulation

最後更新: 2026-02-14
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, computed_field

from .enums import (
    BacktestStatus,
    TimeFrame,
    OrderSide,
    PositionType,
    StrategyType,
)


class BacktestConfig(BaseModel):
    """回測配置模型
    
    定義回測的所有參數，包括時間範圍、資金、成本等。
    """
    
    # 回測識別
    backtest_id: UUID = Field(default_factory=uuid4, description="回測唯一 ID")
    name: str = Field(..., min_length=1, max_length=100, description="回測名稱")
    description: Optional[str] = Field(None, max_length=500, description="回測描述")
    
    # 時間範圍
    start_date: datetime = Field(..., description="回測開始日期")
    end_date: datetime = Field(..., description="回測結束日期")
    timeframe: TimeFrame = Field(default=TimeFrame.HOUR_1, description="K線時間框架")
    
    # 交易標的
    symbols: list[str] = Field(..., min_length=1, description="交易標的列表")
    
    # 資金配置
    initial_capital: Decimal = Field(..., gt=0, description="初始資金")
    base_currency: str = Field(default="USDT", description="基礎貨幣")
    
    # 交易成本
    commission_rate: Decimal = Field(
        default=Decimal("0.0004"), 
        ge=0, 
        le=Decimal("0.01"),
        description="手續費率 (如: 0.0004 = 0.04%)"
    )
    slippage: Decimal = Field(
        default=Decimal("0.0001"),
        ge=0,
        le=Decimal("0.01"),
        description="滑點估計 (如: 0.0001 = 0.01%)"
    )
    
    # 槓桿和保證金
    max_leverage: int = Field(default=1, ge=1, le=125, description="最大槓桿")
    margin_type: str = Field(default="cross", description="保證金類型")
    
    # 風險控制
    max_position_size: Decimal = Field(
        default=Decimal("0.2"),
        gt=0,
        le=1,
        description="單筆最大倉位比例"
    )
    max_drawdown_limit: Decimal = Field(
        default=Decimal("0.15"),
        gt=0,
        le=1,
        description="最大回撤限制"
    )
    stop_loss_pct: Optional[Decimal] = Field(
        None,
        gt=0,
        le=Decimal("0.5"),
        description="全局止損百分比"
    )
    
    # 策略配置
    strategy_type: StrategyType = Field(..., description="策略類型")
    strategy_params: dict[str, Any] = Field(
        default_factory=dict,
        description="策略參數"
    )
    
    # 回測選項
    use_realistic_fills: bool = Field(default=True, description="使用真實成交模擬")
    include_funding_rate: bool = Field(default=True, description="包含資金費率")
    warmup_period: int = Field(default=100, ge=0, description="預熱期 (K線數)")
    
    @field_validator("end_date")
    @classmethod
    def validate_end_date(cls, v: datetime, info) -> datetime:
        """驗證結束日期在開始日期之後"""
        if "start_date" in info.data:
            start = info.data["start_date"]
            if v <= start:
                raise ValueError("結束日期必須在開始日期之後")
            # 至少需要 1 天的數據
            if (v - start).days < 1:
                raise ValueError("回測期間至少需要 1 天")
        return v
    
    @computed_field
    @property
    def duration_days(self) -> int:
        """回測天數"""
        return (self.end_date - self.start_date).days
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "BTC趨勢策略回測",
                    "start_date": "2025-01-01T00:00:00Z",
                    "end_date": "2025-12-31T23:59:59Z",
                    "symbols": ["BTCUSDT"],
                    "initial_capital": "10000.00",
                    "commission_rate": "0.0004",
                    "strategy_type": "trend_following",
                    "strategy_params": {"fast_ma": 20, "slow_ma": 50},
                }
            ]
        }
    }


class TradeRecord(BaseModel):
    """交易記錄模型
    
    記錄回測中的每一筆交易。
    """
    
    # 交易識別
    trade_id: UUID = Field(default_factory=uuid4, description="交易唯一 ID")
    
    # 交易信息
    symbol: str = Field(..., description="交易對")
    side: OrderSide = Field(..., description="交易方向")
    position_type: PositionType = Field(..., description="倉位類型")
    
    # 進場信息
    entry_time: datetime = Field(..., description="進場時間")
    entry_price: Decimal = Field(..., gt=0, description="進場價格")
    entry_quantity: Decimal = Field(..., gt=0, description="進場數量")
    entry_value: Decimal = Field(..., gt=0, description="進場價值")
    
    # 出場信息
    exit_time: Optional[datetime] = Field(None, description="出場時間")
    exit_price: Optional[Decimal] = Field(None, gt=0, description="出場價格")
    exit_quantity: Optional[Decimal] = Field(None, gt=0, description="出場數量")
    exit_value: Optional[Decimal] = Field(None, gt=0, description="出場價值")
    
    # 盈虧
    gross_pnl: Decimal = Field(default=Decimal("0"), description="毛盈虧")
    commission: Decimal = Field(default=Decimal("0"), ge=0, description="手續費")
    slippage_cost: Decimal = Field(default=Decimal("0"), ge=0, description="滑點成本")
    net_pnl: Decimal = Field(default=Decimal("0"), description="淨盈虧")
    pnl_percentage: Decimal = Field(default=Decimal("0"), description="盈虧百分比")
    
    # 持倉時間
    holding_period: Optional[timedelta] = Field(None, description="持倉時間")
    holding_bars: Optional[int] = Field(None, ge=0, description="持倉 K 線數")
    
    # 風險指標
    max_favorable_excursion: Optional[Decimal] = Field(None, description="最大有利移動 (MFE)")
    max_adverse_excursion: Optional[Decimal] = Field(None, description="最大不利移動 (MAE)")
    
    # 策略信息
    strategy_name: Optional[str] = Field(None, description="策略名稱")
    signal_strength: Optional[str] = Field(None, description="信號強度")
    exit_reason: Optional[str] = Field(None, description="出場原因")
    
    @computed_field
    @property
    def is_winner(self) -> bool:
        """是否為盈利交易"""
        return self.net_pnl > 0
    
    @computed_field
    @property
    def is_closed(self) -> bool:
        """交易是否已平倉"""
        return self.exit_time is not None


class BacktestResult(BaseModel):
    """回測結果模型
    
    包含完整的回測統計數據。
    """
    
    # 識別
    backtest_id: UUID = Field(..., description="回測 ID")
    config: BacktestConfig = Field(..., description="回測配置")
    status: BacktestStatus = Field(..., description="回測狀態")
    
    # 執行時間
    started_at: datetime = Field(..., description="開始執行時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    execution_time_seconds: Optional[float] = Field(None, description="執行時間 (秒)")
    
    # 基本統計
    total_trades: int = Field(default=0, ge=0, description="總交易次數")
    winning_trades: int = Field(default=0, ge=0, description="盈利交易次數")
    losing_trades: int = Field(default=0, ge=0, description="虧損交易次數")
    break_even_trades: int = Field(default=0, ge=0, description="平手交易次數")
    
    # 收益指標
    initial_capital: Decimal = Field(..., gt=0, description="初始資金")
    final_capital: Decimal = Field(..., description="最終資金")
    total_return: Decimal = Field(default=Decimal("0"), description="總收益")
    total_return_pct: Decimal = Field(default=Decimal("0"), description="總收益率")
    annualized_return: Optional[Decimal] = Field(None, description="年化收益率")
    
    # 盈虧統計
    gross_profit: Decimal = Field(default=Decimal("0"), ge=0, description="總毛利")
    gross_loss: Decimal = Field(default=Decimal("0"), le=0, description="總毛損")
    net_profit: Decimal = Field(default=Decimal("0"), description="淨利潤")
    total_commission: Decimal = Field(default=Decimal("0"), ge=0, description="總手續費")
    
    # 勝率相關
    win_rate: Decimal = Field(default=Decimal("0"), ge=0, le=1, description="勝率")
    profit_factor: Optional[Decimal] = Field(None, description="盈虧比")
    average_win: Optional[Decimal] = Field(None, description="平均盈利")
    average_loss: Optional[Decimal] = Field(None, description="平均虧損")
    largest_win: Optional[Decimal] = Field(None, description="最大單筆盈利")
    largest_loss: Optional[Decimal] = Field(None, description="最大單筆虧損")
    
    # 風險指標
    max_drawdown: Decimal = Field(default=Decimal("0"), ge=0, description="最大回撤")
    max_drawdown_pct: Decimal = Field(default=Decimal("0"), ge=0, description="最大回撤百分比")
    max_drawdown_duration: Optional[timedelta] = Field(None, description="最大回撤持續時間")
    calmar_ratio: Optional[Decimal] = Field(None, description="卡爾馬比率")
    
    # 風險調整收益
    sharpe_ratio: Optional[float] = Field(None, description="夏普比率")
    sortino_ratio: Optional[float] = Field(None, description="索提諾比率")
    information_ratio: Optional[float] = Field(None, description="信息比率")
    
    # 交易統計
    average_holding_period: Optional[timedelta] = Field(None, description="平均持倉時間")
    trades_per_day: Optional[float] = Field(None, ge=0, description="日均交易次數")
    max_consecutive_wins: int = Field(default=0, ge=0, description="最大連勝次數")
    max_consecutive_losses: int = Field(default=0, ge=0, description="最大連敗次數")
    
    # 權益曲線
    equity_curve: list[dict[str, Any]] = Field(
        default_factory=list,
        description="權益曲線數據點"
    )
    
    # 交易記錄
    trades: list[TradeRecord] = Field(default_factory=list, description="交易記錄")
    
    # 錯誤信息
    error_message: Optional[str] = Field(None, description="錯誤信息")
    warnings: list[str] = Field(default_factory=list, description="警告信息")
    
    @computed_field
    @property
    def is_successful(self) -> bool:
        """回測是否成功完成"""
        return self.status == BacktestStatus.COMPLETED
    
    @computed_field
    @property
    def is_profitable(self) -> bool:
        """回測是否盈利"""
        return self.total_return > 0
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "COMPLETED",
                    "total_trades": 150,
                    "winning_trades": 90,
                    "losing_trades": 60,
                    "initial_capital": "10000.00",
                    "final_capital": "12500.00",
                    "total_return_pct": "25.00",
                    "win_rate": "0.60",
                    "sharpe_ratio": 1.85,
                    "max_drawdown_pct": "0.08",
                }
            ]
        }
    }


class WalkForwardResult(BaseModel):
    """Walk-Forward 優化結果"""
    
    # 基本信息
    total_windows: int = Field(..., ge=1, description="總窗口數")
    in_sample_ratio: Decimal = Field(..., gt=0, lt=1, description="樣本內比例")
    
    # 樣本內結果
    in_sample_results: list[BacktestResult] = Field(
        default_factory=list,
        description="樣本內回測結果"
    )
    
    # 樣本外結果
    out_of_sample_results: list[BacktestResult] = Field(
        default_factory=list,
        description="樣本外回測結果"
    )
    
    # 效率比
    walk_forward_efficiency: Optional[Decimal] = Field(
        None,
        description="Walk-Forward 效率 (樣本外/樣本內收益比)"
    )
    
    # 最佳參數
    best_params_per_window: list[dict[str, Any]] = Field(
        default_factory=list,
        description="每個窗口的最佳參數"
    )


class MonteCarloResult(BaseModel):
    """蒙特卡羅模擬結果"""
    
    # 模擬配置
    num_simulations: int = Field(..., ge=100, description="模擬次數")
    
    # 收益分布
    mean_return: Decimal = Field(..., description="平均收益")
    median_return: Decimal = Field(..., description="中位數收益")
    std_return: Decimal = Field(..., ge=0, description="收益標準差")
    
    # 置信區間
    return_5th_percentile: Decimal = Field(..., description="5% 分位數收益")
    return_25th_percentile: Decimal = Field(..., description="25% 分位數收益")
    return_75th_percentile: Decimal = Field(..., description="75% 分位數收益")
    return_95th_percentile: Decimal = Field(..., description="95% 分位數收益")
    
    # 風險指標
    probability_of_loss: Decimal = Field(
        ...,
        ge=0,
        le=1,
        description="虧損概率"
    )
    max_drawdown_95th: Decimal = Field(..., description="95% 置信區間最大回撤")
    
    # 破產風險
    risk_of_ruin: Decimal = Field(
        default=Decimal("0"),
        ge=0,
        le=1,
        description="破產風險"
    )


# =============================================================================
# 導出
# =============================================================================

__all__ = [
    "BacktestConfig",
    "TradeRecord",
    "BacktestResult",
    "WalkForwardResult",
    "MonteCarloResult",
]
