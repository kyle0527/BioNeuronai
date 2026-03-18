# -*- coding: utf-8 -*-
"""
API Request / Response Models
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Request Models ────────────────────────────────────────────────────────────


class NewsRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="交易對")
    max_items: int = Field(default=10, ge=1, le=50, description="最大新聞數量")


class PreTradeRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="交易對")
    action: str = Field(default="long", pattern="^(long|short)$", description="交易方向")


class BacktestRequest(BaseModel):
    symbol: str = Field(default="ETHUSDT", description="交易對")
    interval: str = Field(default="1h", description="K 線週期")
    start_date: Optional[str] = Field(default=None, description="起始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="結束日期 YYYY-MM-DD")
    balance: float = Field(default=10000.0, gt=0, description="初始資金")


class SimulateRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="交易對")
    interval: str = Field(default="15m", description="K 線週期")
    balance: float = Field(default=100000.0, gt=0, description="模擬資金")
    bars: int = Field(default=200, ge=1, le=5000, description="模擬 K 線數量")
    start_date: Optional[str] = Field(default=None, description="起始日期")
    end_date: Optional[str] = Field(default=None, description="結束日期")


class TradeStartRequest(BaseModel):
    symbol: str = Field(default="BTCUSDT", description="交易對")
    testnet: bool = Field(default=True, description="使用測試網")


# ── Response Models ───────────────────────────────────────────────────────────


class ApiResponse(BaseModel):
    """標準 API 回應"""
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ModuleStatus(BaseModel):
    name: str
    available: bool
    error: Optional[str] = None


class StatusResponse(BaseModel):
    success: bool = True
    modules: List[ModuleStatus]
    version: Optional[str] = None
    all_ok: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class JobStatus(BaseModel):
    """長時間任務的狀態"""
    job_id: str
    status: str = Field(description="pending | running | completed | failed")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
