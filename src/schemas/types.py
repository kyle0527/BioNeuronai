"""
BioNeuronai 可重用類型定義

基於 Pydantic v2 Annotated 模式的可重用類型別名。
使用這些類型可以確保整個系統的類型一致性和驗證行為統一。

參考: https://docs.pydantic.dev/latest/concepts/fields/#the-annotated-pattern
最後更新: 2026-02-14
"""

from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID
from datetime import datetime

from pydantic import (
    Field,
    AfterValidator,
    BeforeValidator,
    PlainSerializer,
    StringConstraints,
)


# =============================================================================
# 版本控制
# =============================================================================

SCHEMA_VERSION = "2.1"
"""
Schema 版本號，遵循語義化版本控制 (SemVer)

版本歷史:
- 2.1 (2026-04-05): 將目前對外 schema 版本收斂為 2.1
- 2.3.0 (2026-02-14): 新增 types.py, events.py, backtesting.py, ml_models.py, alerts.py
- 2.0.0 (2026-01-25): 新增事件系統、市場分析 enums
- 1.0.0 (2025-01-22): 初始版本
"""


# =============================================================================
# 基礎數值類型
# =============================================================================

def _validate_positive(v: Decimal) -> Decimal:
    """驗證正數"""
    if v <= 0:
        raise ValueError("值必須為正數")
    return v


def _validate_non_negative(v: Decimal) -> Decimal:
    """驗證非負數"""
    if v < 0:
        raise ValueError("值不能為負數")
    return v


def _validate_percentage(v: float) -> float:
    """驗證百分比 (0-1)"""
    if not 0 <= v <= 1:
        raise ValueError("百分比必須在 0 到 1 之間")
    return v


def _validate_leverage(v: float) -> float:
    """驗證槓桿倍數 (1-125，符合幣安期貨規範)"""
    if not 1 <= v <= 125:
        raise ValueError("槓桿倍數必須在 1 到 125 之間")
    return v


def _validate_rsi(v: float) -> float:
    """驗證 RSI 值 (0-100)"""
    if not 0 <= v <= 100:
        raise ValueError("RSI 必須在 0 到 100 之間")
    return v


# 正數 Decimal
PositiveDecimal = Annotated[
    Decimal,
    AfterValidator(_validate_positive),
    Field(description="正數 Decimal 值"),
]

# 非負 Decimal
NonNegativeDecimal = Annotated[
    Decimal,
    AfterValidator(_validate_non_negative),
    Field(description="非負 Decimal 值"),
]

# 百分比 (0-1)
Percentage = Annotated[
    float,
    AfterValidator(_validate_percentage),
    Field(ge=0, le=1, description="百分比 (0-1)"),
]

# 槓桿倍數 (1-125，幣安期貨規範)
Leverage = Annotated[
    float,
    AfterValidator(_validate_leverage),
    Field(ge=1, le=125, description="槓桿倍數 (1-125)"),
]

# RSI 值 (0-100)
RSIValue = Annotated[
    float,
    AfterValidator(_validate_rsi),
    Field(ge=0, le=100, description="RSI 指標值 (0-100)"),
]

# 置信度 (0-1)
Confidence = Annotated[
    float,
    Field(ge=0, le=1, description="置信度 (0-1)"),
]


# =============================================================================
# 幣安交易對類型
# =============================================================================

def _validate_binance_symbol(v: str) -> str:
    """
    驗證幣安交易對符號
    
    規則:
    - 必須為大寫
    - 必須以 USDT, BUSD, BTC, ETH 結尾 (期貨常用)
    - 長度 6-12 字元
    """
    v = v.upper().strip()
    
    valid_suffixes = ("USDT", "BUSD", "BTC", "ETH")
    if not any(v.endswith(suffix) for suffix in valid_suffixes):
        raise ValueError(f"交易對必須以 {valid_suffixes} 結尾")
    
    if not 6 <= len(v) <= 12:
        raise ValueError("交易對符號長度必須在 6-12 字元之間")
    
    if not v.isalnum():
        raise ValueError("交易對符號只能包含字母和數字")
    
    return v


BinanceSymbol = Annotated[
    str,
    BeforeValidator(lambda v: v.upper().strip() if isinstance(v, str) else v),
    AfterValidator(_validate_binance_symbol),
    Field(description="幣安交易對符號 (如: BTCUSDT)"),
]


# USDT 專用交易對 (僅 USDT 保證金合約)
def _validate_usdt_symbol(v: str) -> str:
    """驗證 USDT 保證金交易對"""
    v = v.upper().strip()
    if not v.endswith("USDT"):
        raise ValueError("僅支援 USDT 保證金交易對")
    return v


USDTSymbol = Annotated[
    str,
    BeforeValidator(lambda v: v.upper().strip() if isinstance(v, str) else v),
    AfterValidator(_validate_usdt_symbol),
    Field(description="USDT 保證金交易對符號"),
]


# =============================================================================
# UUID 和 ID 類型
# =============================================================================

# 標準 UUID
StandardUUID = Annotated[
    UUID,
    Field(description="UUID v4 唯一識別碼"),
]

# 訂單 ID (幣安使用 int64)
BinanceOrderId = Annotated[
    int,
    Field(gt=0, description="幣安訂單 ID"),
]

# 客戶端訂單 ID
ClientOrderId = Annotated[
    str,
    StringConstraints(min_length=1, max_length=36),
    Field(description="客戶端自定義訂單 ID"),
]


# =============================================================================
# 時間戳類型
# =============================================================================

def _serialize_timestamp(dt: datetime) -> str:
    """序列化時間戳為 ISO 格式"""
    return dt.isoformat()


Timestamp = Annotated[
    datetime,
    PlainSerializer(_serialize_timestamp, return_type=str),
    Field(description="時間戳 (ISO 8601 格式)"),
]

# 毫秒時間戳 (幣安 API 使用)
BinanceTimestamp = Annotated[
    int,
    Field(ge=0, description="幣安毫秒時間戳"),
]


# =============================================================================
# 價格和數量類型
# =============================================================================

# 價格 (正數 Decimal)
Price = Annotated[
    Decimal,
    AfterValidator(_validate_positive),
    Field(description="價格"),
]

# 數量 (正數 Decimal)
Quantity = Annotated[
    Decimal,
    AfterValidator(_validate_positive),
    Field(description="數量"),
]

# 名義價值
NotionalValue = Annotated[
    Decimal,
    AfterValidator(_validate_positive),
    Field(description="名義價值"),
]

# 保證金
Margin = Annotated[
    Decimal,
    AfterValidator(_validate_non_negative),
    Field(description="保證金"),
]


# =============================================================================
# 盈虧類型
# =============================================================================

# 盈虧 (可正可負)
PnL = Annotated[
    Decimal,
    Field(description="盈虧金額"),
]

# 盈虧百分比 (可正可負)
PnLPercentage = Annotated[
    float,
    Field(description="盈虧百分比"),
]


# =============================================================================
# 策略相關類型
# =============================================================================

# 策略名稱
StrategyName = Annotated[
    str,
    StringConstraints(min_length=1, max_length=50),
    Field(description="策略名稱"),
]

# 策略描述
StrategyDescription = Annotated[
    str,
    StringConstraints(max_length=500),
    Field(description="策略描述"),
]


# =============================================================================
# JSON 相關類型
# =============================================================================

# JSON 可序列化字典
JsonDict = Annotated[
    dict[str, Any],
    Field(default_factory=dict, description="JSON 可序列化字典"),
]

# JSON 數組
JsonList = Annotated[
    list[Any],
    Field(default_factory=list, description="JSON 可序列化數組"),
]


# =============================================================================
# 導出
# =============================================================================

__all__ = [
    # 版本
    "SCHEMA_VERSION",
    # 數值類型
    "PositiveDecimal",
    "NonNegativeDecimal",
    "Percentage",
    "Leverage",
    "RSIValue",
    "Confidence",
    # 交易對
    "BinanceSymbol",
    "USDTSymbol",
    # ID 類型
    "StandardUUID",
    "BinanceOrderId",
    "ClientOrderId",
    # 時間
    "Timestamp",
    "BinanceTimestamp",
    # 價格和數量
    "Price",
    "Quantity",
    "NotionalValue",
    "Margin",
    # 盈虧
    "PnL",
    "PnLPercentage",
    # 策略
    "StrategyName",
    "StrategyDescription",
    # JSON
    "JsonDict",
    "JsonList",
]
