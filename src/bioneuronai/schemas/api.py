"""
BioNeuronai API通信模型

專為幣安期貨API通信設計的 Pydantic 模型。
"""

from datetime import datetime
from typing import Optional, Dict, Any, Union
from decimal import Decimal

from pydantic import BaseModel, Field

from bioneuronai.schemas.enums import Environment


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