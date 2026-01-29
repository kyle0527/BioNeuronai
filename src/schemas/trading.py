"""
BioNeuronai 交易信號模型

定義交易信號相關的 Pydantic 模型。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from .enums import SignalType, SignalStrength, RiskLevel


class TradingSignal(BaseModel):
    """交易信號模型"""
    
    symbol: str = Field(..., description="交易對符號")
    signal_type: SignalType = Field(..., description="信號類型 (BUY/SELL/HOLD)")
    strength: SignalStrength = Field(..., description="信號強度")
    confidence: float = Field(..., ge=0, le=1, description="信號置信度 (0-1)")
    timestamp: datetime = Field(default_factory=datetime.now, description="信號生成時間")
    
    # 價格相關
    entry_price: Optional[float] = Field(None, gt=0, description="建議進場價格")
    target_price: Optional[float] = Field(None, gt=0, description="目標價格")
    stop_loss: Optional[float] = Field(None, gt=0, description="止損價格")
    
    # 風險管理
    risk_level: RiskLevel = Field(default=RiskLevel.MEDIUM, description="風險等級")
    position_size: Optional[float] = Field(None, gt=0, le=1, description="建議倉位大小 (0-1)")
    
    # 策略相關
    strategy_name: Optional[str] = Field(None, description="生成信號的策略名稱")
    reason: Optional[str] = Field(None, description="信號產生原因")
    
    # 技術指標依據
    indicators: Optional[dict] = Field(None, description="相關技術指標數據")
    
    # 元數據
    metadata: Optional[dict] = Field(None, description="額外元數據")
    
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
