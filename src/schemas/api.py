"""
BioNeuronai API通信模型

專為幣安期貨API通信設計的 Pydantic 模型。
包含：
- 底層 Binance 通訊模型（ApiCredentials、ApiResponse、BinanceApiError…）
- REST API 入口層的 Request / Response / JobStatus 模型
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import Environment


class ApiCredentials(BaseModel):
    """API 憑證模型"""
    
    api_key: str = Field(..., description="API Key")
    secret_key: str = Field(..., description="Secret Key", repr=False)  # 不顯示在日誌中
    testnet: bool = Field(default=True, description="是否使用測試網")
    environment: Environment = Field(default=Environment.TESTNET, description="環境類型")
    
    # API 限制
    requests_per_minute: int = Field(default=1200, description="每分鐘請求限制")
    orders_per_second: int = Field(default=10, description="每秒訂單限制")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "api_key": "your_api_key_here",
                    "secret_key": "[HIDDEN]",
                    "testnet": True,
                    "environment": "testnet",
                    "requests_per_minute": 1200,
                    "orders_per_second": 10
                }
            ]
        }
    }


class ApiResponse(BaseModel):
    """API 響應基礎模型"""
    
    success: bool = Field(..., description="請求是否成功")
    status_code: int = Field(..., description="HTTP 狀態碼")
    message: Optional[str] = Field(None, description="響應消息")
    data: Optional[Dict[str, Any]] = Field(None, description="響應數據")
    
    # 請求信息
    request_id: Optional[str] = Field(None, description="請求ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="響應時間")
    
    # 限制信息
    rate_limit_used: Optional[int] = Field(None, description="已使用的請求次數")
    rate_limit_remaining: Optional[int] = Field(None, description="剩餘請求次數")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "status_code": 200,
                    "message": "請求成功",
                    "data": {"result": "success"},
                    "request_id": "req_123456",
                    "rate_limit_used": 10,
                    "rate_limit_remaining": 1190
                }
            ]
        }
    }


class BinanceApiError(BaseModel):
    """幣安API錯誤模型"""
    
    code: int = Field(..., description="錯誤代碼")
    msg: str = Field(..., description="錯誤消息")
    timestamp: datetime = Field(default_factory=datetime.now, description="錯誤時間")
    
    # 請求上下文
    endpoint: Optional[str] = Field(None, description="請求端點")
    method: Optional[str] = Field(None, description="請求方法")
    params: Optional[Dict[str, Any]] = Field(None, description="請求參數")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "code": -1021,
                    "msg": "Timestamp for this request was 1000ms ahead of the server's time.",
                    "endpoint": "/fapi/v1/order",
                    "method": "POST",
                    "params": {"symbol": "BTCUSDT", "side": "BUY"}
                }
            ]
        }
    }


class WebSocketMessage(BaseModel):
    """WebSocket 消息模型"""
    
    stream: str = Field(..., description="數據流名稱")
    data: Dict[str, Any] = Field(..., description="消息數據")
    timestamp: datetime = Field(default_factory=datetime.now, description="接收時間")
    
    # 消息類型
    event_type: Optional[str] = Field(None, description="事件類型")
    symbol: Optional[str] = Field(None, description="交易對符號")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "stream": "btcusdt@ticker",
                    "data": {
                        "e": "24hrTicker",
                        "s": "BTCUSDT",
                        "c": "50000.00",
                        "p": "1000.00"
                    },
                    "event_type": "24hrTicker",
                    "symbol": "BTCUSDT"
                }
            ]
        }
    }


class ApiStatusInfo(BaseModel):
    """API 狀態信息模型"""
    
    server_time: datetime = Field(..., description="服務器時間")
    
    # 連接信息
    ping: Optional[float] = Field(None, description="延遲 (毫秒)")
    last_request_time: Optional[datetime] = Field(None, description="最後請求時間")
    
    # 限制信息
    rate_limits: Dict[str, int] = Field(default_factory=dict, description="速率限制信息")
    
    # 錯誤統計
    error_count: int = Field(default=0, description="錯誤計數")
    last_error: Optional[BinanceApiError] = Field(None, description="最後一次錯誤")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "online",
                    "server_time": "2024-01-01T10:00:00Z",
                    "ping": 15.5,
                    "rate_limits": {
                        "requests_per_minute": 1200,
                        "orders_per_second": 10
                    },
                    "error_count": 0
                }
            ]
        }
    }


class ExchangeInfo(BaseModel):
    """交易所信息模型"""
    
    timezone: str = Field(..., description="時區")
    server_time: datetime = Field(..., description="服務器時間")
    
    # 限制信息
    rate_limits: list[Dict[str, Any]] = Field(..., description="速率限制")
    exchange_filters: list[Dict[str, Any]] = Field(..., description="交易所過濾器")
    
    # 交易對信息
    symbols: list[Dict[str, Any]] = Field(..., description="支持的交易對")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "timezone": "UTC",
                    "server_time": "2024-01-01T10:00:00Z",
                    "rate_limits": [
                        {
                            "rateLimitType": "REQUEST_WEIGHT",
                            "interval": "MINUTE",
                            "intervalNum": 1,
                            "limit": 1200
                        }
                    ],
                    "exchange_filters": [],
                    "symbols": [
                        {
                            "symbol": "BTCUSDT",
                            "status": "TRADING",
                            "baseAsset": "BTC",
                            "quoteAsset": "USDT"
                        }
                    ]
                }
            ]
        }
    }


# ── REST API Request Models ───────────────────────────────────────────────────


class NewsRequest(BaseModel):
    """新聞分析請求"""
    symbol: str = Field(default="BTCUSDT", description="交易對")
    max_items: int = Field(default=10, ge=1, le=50, description="最大新聞數量")


class PreTradeRequest(BaseModel):
    """進場前檢查請求"""
    symbol: str = Field(default="BTCUSDT", description="交易對")
    action: str = Field(default="long", pattern="^(long|short)$", description="交易方向")


class BacktestRequest(BaseModel):
    """回測請求"""
    symbol: str = Field(default="ETHUSDT", description="交易對")
    interval: str = Field(default="1h", description="K 線週期")
    start_date: Optional[str] = Field(default=None, description="起始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="結束日期 YYYY-MM-DD")
    balance: float = Field(default=10000.0, gt=0, description="初始資金")
    warmup_bars: int = Field(default=100, ge=0, description="預熱 K 線數量")


class SimulateRequest(BaseModel):
    """模擬交易請求"""
    symbol: str = Field(default="BTCUSDT", description="交易對")
    interval: str = Field(default="15m", description="K 線週期")
    balance: float = Field(default=100000.0, gt=0, description="模擬資金")
    bars: int = Field(default=200, ge=1, le=5000, description="模擬 K 線數量")
    start_date: Optional[str] = Field(default=None, description="起始日期")
    end_date: Optional[str] = Field(default=None, description="結束日期")


class TradeStartRequest(BaseModel):
    """啟動交易監控請求"""
    symbol: str = Field(default="BTCUSDT", description="交易對")
    testnet: bool = Field(default=True, description="使用測試網")
    # 選填：由 UI/CLI 注入使用者憑證；不填則 fallback 至環境變數
    api_key: Optional[str] = Field(default=None, description="Binance API Key（選填）")
    api_secret: Optional[str] = Field(default=None, description="Binance API Secret（選填）", repr=False)


class BinanceValidateRequest(BaseModel):
    """Binance 憑證驗證請求

    專用於 POST /api/v1/binance/validate，語意上只驗證憑證有效性，
    不綁定交易對（連線測試用固定 BTCUSDT）。
    """
    testnet: bool = Field(default=True, description="使用測試網")
    api_key: Optional[str] = Field(default=None, description="Binance API Key（選填，不填從環境變數讀取）")
    api_secret: Optional[str] = Field(default=None, description="Binance API Secret（選填）", repr=False)


# ── REST API Response / Status Models ────────────────────────────────────────


class RestApiResponse(BaseModel):
    """REST API 標準回應（薄入口層專用）

    與 ApiResponse（底層 Binance 通訊用）功能不同，此為 FastAPI 路由回傳格式。
    """
    success: bool
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ModuleStatus(BaseModel):
    """模組可用性狀態"""
    name: str
    available: bool
    error: Optional[str] = None


class StatusResponse(BaseModel):
    """系統健康狀態回應"""
    success: bool = True
    modules: List[ModuleStatus]
    version: Optional[str] = None
    all_ok: bool
    timestamp: datetime = Field(default_factory=datetime.now)


class JobStatus(BaseModel):
    """長時間背景任務狀態"""
    job_id: str
    status: str = Field(description="pending | running | completed | failed | not_found")
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class ChatMessage(BaseModel):
    """單條對話訊息"""
    role: str = Field(description="user | assistant | system")
    content: str


class ChatRequest(BaseModel):
    """對話請求"""
    message: str = Field(description="使用者訊息（中文或英文）")
    language: str = Field(default="auto", description="回應語言：auto | zh | en")
    symbol: Optional[str] = Field(default=None, description="交易對（選填），如 BTCUSDT，提供時自動注入即時市場資料")
    conversation_id: Optional[str] = Field(default=None, description="對話 ID，用於維持多輪對話（同 session 傳相同 ID）")
    history: Optional[List[ChatMessage]] = Field(default=None, description="前端傳入的對話歷史（選填，優先使用 conversation_id）")
    stream: bool = Field(default=False, description="是否啟用串流輸出（Server-Sent Events）")


class ChatResponse(BaseModel):
    """對話回應"""
    success: bool = True
    text: str = Field(description="AI 回應文字")
    language: str = Field(description="回應語言：zh | en | mixed")
    confidence: float = Field(default=1.0, description="模型信心值 0–1")
    market_context_used: bool = Field(default=False, description="是否注入了即時市場資料")
    stopped_reason: str = Field(default="", description="提前停止原因：'' | low_confidence | hallucination_detected | max_tokens")
    latency_ms: float = Field(default=0.0, description="生成耗時（毫秒）")
    conversation_id: Optional[str] = Field(default=None, description="對話 ID，供下一輪使用")
    timestamp: datetime = Field(default_factory=datetime.now)
