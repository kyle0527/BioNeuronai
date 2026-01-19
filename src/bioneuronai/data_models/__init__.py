"""
數據模型定義
包含所有核心數據結構
"""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class MarketData:
    """市場數據"""
    symbol: str
    price: float
    timestamp: int
    volume: float = 0.0
    bid_price: float = 0.0
    ask_price: float = 0.0
    funding_rate: float = 0.0
    open_interest: float = 0.0


@dataclass
class TradingSignal:
    """交易信號"""
    action: str  # BUY, SELL, HOLD
    symbol: str
    confidence: float
    reason: str
    target_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class Position:
    """持倉信息"""
    symbol: str
    side: str  # LONG, SHORT
    quantity: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    leverage: int = 1


@dataclass
class OrderResult:
    """訂單結果"""
    order_id: Optional[str]
    symbol: str
    side: str
    quantity: float
    price: Optional[float]
    status: str
    error: Optional[str] = None