"""
BioNeuronai 市場數據模型

定義市場數據相關的 Pydantic 模型。
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class MarketData(BaseModel):
    """市場數據模型"""

    symbol: str = Field(..., description="交易對符號")
    timestamp: datetime = Field(..., description="時間戳")
    open: float = Field(..., gt=0, description="開盤價")
    high: float = Field(..., gt=0, description="最高價")
    low: float = Field(..., gt=0, description="最低價")
    close: float = Field(..., gt=0, description="收盤價")
    volume: float = Field(..., ge=0, description="成交量")

    # 即時行情欄位（ticker data — 期貨連接器使用）
    bid: Optional[float] = Field(None, gt=0, description="買一價（最佳買入報價）")
    ask: Optional[float] = Field(None, gt=0, description="賣一價（最佳賣出報價）")
    funding_rate: float = Field(default=0.0, description="資金費率（期貨合約，每8小時結算）")
    open_interest: float = Field(default=0.0, ge=0, description="未平倉合約數量")

    # 技術指標
    sma_20: Optional[float] = Field(default=None, description="20 期簡單移動平均線")
    sma_50: Optional[float] = Field(default=None, description="50 期簡單移動平均線")
    ema_12: Optional[float] = Field(default=None, description="12 期指數移動平均線")
    ema_26: Optional[float] = Field(default=None, description="26 期指數移動平均線")
    rsi: Optional[float] = Field(default=None, ge=0, le=100, description="相對強弱指標")
    macd: Optional[float] = Field(default=None, description="MACD 指標")
    macd_signal: Optional[float] = Field(default=None, description="MACD 信號線")

    # 波動率指標
    atr: Optional[float] = Field(default=None, ge=0, description="平均真實範圍")
    bollinger_upper: Optional[float] = Field(default=None, description="布林帶上軌")
    bollinger_middle: Optional[float] = Field(default=None, description="布林帶中軌")
    bollinger_lower: Optional[float] = Field(default=None, description="布林帶下軌")

    @property
    def price(self) -> float:
        """當前市場價（等同於收盤價，供 ticker/connector 相容使用）"""
        return self.close

    @field_validator("high")
    @classmethod
    def validate_high(cls, v: float, info) -> float:
        """驗證最高價不低於開盤價和收盤價"""
        if "open" in info.data and v < info.data["open"]:
            raise ValueError("最高價不能低於開盤價")
        if "close" in info.data and v < info.data["close"]:
            raise ValueError("最高價不能低於收盤價")
        return v

    @field_validator("low")
    @classmethod
    def validate_low(cls, v: float, info) -> float:
        """驗證最低價不高於開盤價和收盤價"""
        if "open" in info.data and v > info.data["open"]:
            raise ValueError("最低價不能高於開盤價")
        if "close" in info.data and v > info.data["close"]:
            raise ValueError("最低價不能高於收盤價")
        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "timestamp": "2025-01-22T10:00:00Z",
                    "open": 50000.0,
                    "high": 51000.0,
                    "low": 49500.0,
                    "close": 50500.0,
                    "volume": 1234.56,
                    "rsi": 65.5,
                    "macd": 150.25,
                }
            ]
        }
    }


class MarketDataHealth(BaseModel):
    """可供決策守門層使用的市場資料完整性與新鮮度紀錄。"""

    source: str = Field(..., description="資料來源，例如 historical 或 binance_rest")
    symbol: str = Field(..., description="交易對符號")
    interval: str = Field(..., description="K 線週期")
    received_at: datetime = Field(
        default_factory=datetime.now,
        description="本程序收到並檢查資料的時間",
    )
    latest_open_time: Optional[datetime] = Field(
        default=None,
        description="最新已採用 K 線的開盤時間",
    )
    latest_close_time: Optional[datetime] = Field(
        default=None,
        description="最新已採用 K 線的收盤時間",
    )
    age_seconds: Optional[float] = Field(
        default=None,
        ge=0,
        description="收到資料時距離最新已收 K 線收盤的秒數",
    )
    is_complete: bool = Field(..., description="最新採用的 K 線是否已收盤")
    is_fresh: bool = Field(..., description="資料是否在允許的新鮮度範圍內")
    reason: Optional[str] = Field(default=None, description="資料不適用時的原因")

    @field_validator("symbol")
    @classmethod
    def validate_health_symbol(cls, value: str) -> str:
        """統一交易對格式以便 ledger 與資料來源比對。"""
        normalized = value.upper().strip()
        if not normalized or not normalized.isalnum():
            raise ValueError("交易對必須是非空英數字字串")
        return normalized

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source": "binance_rest",
                    "symbol": "BTCUSDT",
                    "interval": "1h",
                    "latest_open_time": "2026-07-19T09:00:00",
                    "latest_close_time": "2026-07-19T09:59:59.999000",
                    "age_seconds": 11.2,
                    "is_complete": True,
                    "is_fresh": True,
                }
            ]
        }
    }
