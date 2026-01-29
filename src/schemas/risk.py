"""
BioNeuronai 風險管理模型

定義風險管理相關的 Pydantic 模型。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from .enums import RiskLevel, PositionType


class RiskParameters(BaseModel):
    """風險參數模型"""
    
    max_position_size: float = Field(..., gt=0, le=1, description="單筆最大倉位比例 (0-1)")
    max_total_exposure: float = Field(..., gt=0, le=1, description="總倉位上限 (0-1)")
    max_drawdown: float = Field(..., gt=0, le=1, description="最大回撤限制 (0-1)")
    stop_loss_pct: float = Field(..., gt=0, le=1, description="止損百分比 (0-1)")
    take_profit_pct: float = Field(..., gt=0, description="止盈百分比")
    risk_per_trade: float = Field(..., gt=0, le=0.1, description="單筆交易風險比例 (0-0.1)")
    
    # 槓桿設定
    max_leverage: float = Field(default=1.0, ge=1, le=125, description="最大槓桿倍數 (1-125)")
    
    # 風險等級閾值
    risk_level_thresholds: dict = Field(
        default={
            "low": 0.02,
            "medium": 0.05,
            "high": 0.10,
            "critical": 0.15,
        },
        description="風險等級閾值設定",
    )
    
    @field_validator("max_position_size")
    @classmethod
    def validate_max_position_size(cls, v: float) -> float:
        """驗證最大倉位不超過 50%"""
        if v > 0.5:
            raise ValueError("單筆最大倉位不應超過 50%")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "max_position_size": 0.2,
                    "max_total_exposure": 0.8,
                    "max_drawdown": 0.15,
                    "stop_loss_pct": 0.02,
                    "take_profit_pct": 0.05,
                    "risk_per_trade": 0.01,
                    "max_leverage": 3.0,
                }
            ]
        }
    }


class PositionSizing(BaseModel):
    """倉位大小計算模型"""
    
    symbol: str = Field(..., description="交易對符號")
    position_type: PositionType = Field(..., description="倉位類型 (LONG/SHORT)")
    entry_price: float = Field(..., gt=0, description="進場價格")
    current_price: float = Field(..., gt=0, description="當前價格")
    quantity: float = Field(..., gt=0, description="數量")
    leverage: float = Field(default=1.0, ge=1, le=125, description="槓桿倍數")
    
    # 計算屬性
    notional_value: Optional[float] = Field(None, gt=0, description="名義價值")
    unrealized_pnl: Optional[float] = Field(None, description="未實現盈虧")
    unrealized_pnl_pct: Optional[float] = Field(None, description="未實現盈虧百分比")
    
    def calculate_metrics(self, account_balance: float) -> dict:
        """計算倉位相關指標"""
        notional = self.quantity * self.current_price
        margin = notional / self.leverage
        
        if self.position_type == PositionType.LONG:
            pnl = (self.current_price - self.entry_price) * self.quantity
        else:  # SHORT
            pnl = (self.entry_price - self.current_price) * self.quantity
        
        pnl_pct = pnl / (self.entry_price * self.quantity)
        
        return {
            "notional_value": notional,
            "margin_used": margin,
            "unrealized_pnl": pnl,
            "unrealized_pnl_pct": pnl_pct,
            "position_size_pct": margin / account_balance,
        }
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "position_type": "long",
                    "entry_price": 50000.0,
                    "current_price": 51000.0,
                    "quantity": 0.1,
                    "leverage": 2.0,
                }
            ]
        }
    }


class PortfolioRisk(BaseModel):
    """投資組合風險模型"""
    
    total_equity: float = Field(..., gt=0, description="總權益")
    total_margin: float = Field(..., ge=0, description="已使用保證金")
    available_margin: float = Field(..., ge=0, description="可用保證金")
    total_unrealized_pnl: float = Field(default=0.0, description="總未實現盈虧")
    
    # 風險指標
    margin_ratio: float = Field(..., ge=0, le=1, description="保證金比率")
    effective_leverage: float = Field(..., ge=0, description="有效槓桿")
    portfolio_var: Optional[float] = Field(None, description="投資組合風險價值 (VaR)")
    
    # 風險狀態
    risk_level: RiskLevel = Field(..., description="當前風險等級")
    is_margin_call: bool = Field(default=False, description="是否觸發保證金追繳")
    
    timestamp: datetime = Field(default_factory=datetime.now, description="計算時間")
    
    @field_validator("margin_ratio")
    @classmethod
    def validate_margin_ratio(cls, v: float) -> float:
        """驗證保證金比率"""
        if v > 0.9:
            raise ValueError("保證金比率過高，接近強平風險")
        return v
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_equity": 10000.0,
                    "total_margin": 3000.0,
                    "available_margin": 7000.0,
                    "total_unrealized_pnl": 500.0,
                    "margin_ratio": 0.3,
                    "effective_leverage": 1.5,
                    "risk_level": "medium",
                    "is_margin_call": False,
                }
            ]
        }
    }


class RiskAlert(BaseModel):
    """風險警報模型"""
    
    alert_id: str = Field(..., description="警報 ID")
    risk_level: RiskLevel = Field(..., description="風險等級")
    alert_type: str = Field(..., description="警報類型")
    message: str = Field(..., description="警報訊息")
    
    # 相關數據
    symbol: Optional[str] = Field(None, description="相關交易對")
    current_value: Optional[float] = Field(None, description="當前值")
    threshold_value: Optional[float] = Field(None, description="閾值")
    
    # 建議動作
    recommended_action: Optional[str] = Field(None, description="建議採取的動作")
    
    # 時間戳
    timestamp: datetime = Field(default_factory=datetime.now, description="警報時間")
    acknowledged: bool = Field(default=False, description="是否已確認")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "alert_id": "RISK_2025_01_22_001",
                    "risk_level": "high",
                    "alert_type": "margin_warning",
                    "message": "保證金使用率超過 80%",
                    "symbol": "BTCUSDT",
                    "current_value": 0.85,
                    "threshold_value": 0.80,
                    "recommended_action": "考慮減少倉位或增加保證金",
                    "acknowledged": False,
                }
            ]
        }
    }
