"""
BioNeuronai 交易信號模型

定義交易信號相關的 Pydantic 模型。
包含完整的業務邏輯驗證，確保信號的一致性和合理性。

最後更新: 2026-02-14
"""

from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field, computed_field, field_validator, model_validator

from .enums import SignalType, SignalStrength, RiskLevel


class TradingSignal(BaseModel):
    """交易信號模型
    
    包含完整的業務邏輯驗證，確保：
    - 止損價格符合交易方向
    - 目標價格符合交易方向
    - 風險報酬比合理
    """
    
    symbol: str = Field(..., description="交易對符號")
    signal_type: SignalType = Field(..., description="信號類型 (BUY/SELL/HOLD)")
    strength: SignalStrength = Field(default=SignalStrength.MODERATE, description="信號強度")
    confidence: float = Field(..., ge=0, le=1, description="信號置信度 (0-1)")
    timestamp: datetime = Field(default_factory=datetime.now, description="信號生成時間")
    
    # 價格相關
    entry_price: Optional[float] = Field(default=None, gt=0, description="建議進場價格")
    target_price: Optional[float] = Field(default=None, gt=0, description="目標價格")
    stop_loss: Optional[float] = Field(default=None, gt=0, description="止損價格")
    take_profit: Optional[float] = Field(default=None, gt=0, description="止盈價格")
    
    # 風險管理
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="風險等級")
    position_size: Optional[float] = Field(default=None, gt=0, le=1, description="建議倉位大小 (0-1)")
    
    # 策略相關
    strategy_name: Optional[str] = Field(default=None, description="生成信號的策略名稱")
    reason: Optional[str] = Field(default=None, description="信號產生原因")
    
    # 技術指標依據
    indicators: Optional[dict[str, Any]] = Field(default=None, description="相關技術指標數據")
    
    # 元數據
    metadata: Optional[dict[str, Any]] = Field(default=None, description="額外元數據")
    
    @computed_field
    @property
    def action(self) -> str:
        """便捷屬性：返回大寫 action 字串 (BUY/SELL/HOLD)，供日誌與比較使用"""
        return self.signal_type.value.upper()

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        """驗證交易對符號格式"""
        v = v.upper().strip()
        if len(v) < 6 or len(v) > 12:
            raise ValueError("交易對符號長度必須在 6-12 字元之間")
        if not v.isalnum():
            raise ValueError("交易對符號只能包含字母和數字")
        return v
    
    @field_validator("stop_loss")
    @classmethod
    def validate_stop_loss(cls, v: Optional[float], info) -> Optional[float]:
        """
        驗證止損價格符合交易方向
        
        - BUY 信號：止損應低於進場價
        - SELL 信號：止損應高於進場價
        """
        if v is None:
            return None
        
        data = info.data
        entry_price = data.get("entry_price")
        signal_type = data.get("signal_type")
        
        if entry_price is None or signal_type is None:
            return v
        
        if signal_type == SignalType.BUY and v >= entry_price:
            raise ValueError(
                f"買入信號的止損價格 ({v}) 必須低於進場價格 ({entry_price})"
            )
        
        if signal_type == SignalType.SELL and v <= entry_price:
            raise ValueError(
                f"賣出信號的止損價格 ({v}) 必須高於進場價格 ({entry_price})"
            )
        
        return v
    
    @field_validator("target_price")
    @classmethod
    def validate_target_price(cls, v: Optional[float], info) -> Optional[float]:
        """
        驗證目標價格符合交易方向
        
        - BUY 信號：目標應高於進場價
        - SELL 信號：目標應低於進場價
        """
        if v is None:
            return None
        
        data = info.data
        entry_price = data.get("entry_price")
        signal_type = data.get("signal_type")
        
        if entry_price is None or signal_type is None:
            return v
        
        if signal_type == SignalType.BUY and v <= entry_price:
            raise ValueError(
                f"買入信號的目標價格 ({v}) 必須高於進場價格 ({entry_price})"
            )
        
        if signal_type == SignalType.SELL and v >= entry_price:
            raise ValueError(
                f"賣出信號的目標價格 ({v}) 必須低於進場價格 ({entry_price})"
            )
        
        return v
    
    @model_validator(mode="after")
    def validate_risk_reward(self) -> "TradingSignal":
        """
        驗證風險報酬比
        
        - 對於高置信度信號 (>0.8)，風險報酬比應至少 1:1.5
        - 對於中等置信度信號 (0.5-0.8)，風險報酬比應至少 1:1
        """
        # HOLD 信號不需要驗證風險報酬
        if self.signal_type == SignalType.HOLD:
            return self
        
        # 如果缺少價格信息，跳過驗證
        if self.entry_price is None or self.stop_loss is None or self.target_price is None:
            return self
        
        # 計算風險和報酬
        if self.signal_type == SignalType.BUY:
            risk = self.entry_price - self.stop_loss
            reward = self.target_price - self.entry_price
        else:  # SELL
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.target_price
        
        # 風險不能為零或負
        if risk <= 0:
            raise ValueError("風險值必須為正數")
        
        risk_reward_ratio = reward / risk
        
        # 高置信度信號需要更好的風險報酬比
        if self.confidence > 0.8:
            min_ratio = 1.5
            if risk_reward_ratio < min_ratio:
                raise ValueError(
                    f"高置信度信號 ({self.confidence:.0%}) 的風險報酬比 "
                    f"({risk_reward_ratio:.2f}) 低於最小要求 ({min_ratio})"
                )
        elif self.confidence >= 0.5:
            min_ratio = 1.0
            if risk_reward_ratio < min_ratio:
                raise ValueError(
                    f"中等置信度信號的風險報酬比 ({risk_reward_ratio:.2f}) "
                    f"低於最小要求 ({min_ratio})"
                )
        
        return self
    
    def calculate_risk_reward_ratio(self) -> Optional[float]:
        """計算風險報酬比"""
        if self.entry_price is None or self.stop_loss is None or self.target_price is None:
            return None
        
        if self.signal_type == SignalType.BUY:
            risk = self.entry_price - self.stop_loss
            reward = self.target_price - self.entry_price
        elif self.signal_type == SignalType.SELL:
            risk = self.stop_loss - self.entry_price
            reward = self.entry_price - self.target_price
        else:
            return None
        
        if risk <= 0:
            return None
        
        return reward / risk
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "signal_type": "buy",
                    "strength": "strong",
                    "confidence": 0.85,
                    "entry_price": 50000.0,
                    "target_price": 52000.0,
                    "stop_loss": 48000.0,
                    "risk_level": "medium",
                    "position_size": 0.1,
                    "strategy_name": "trend_following",
                    "reason": "突破關鍵阻力位，RSI 顯示超買",
                    "indicators": {
                        "rsi": 68.5,
                        "macd": 250.0,
                        "volume_ratio": 1.5,
                    },
                }
            ]
        }
    }
