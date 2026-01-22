"""
BioNeuronai 資料庫模型

專為資料庫操作設計的 Pydantic 模型。
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from decimal import Decimal

from pydantic import BaseModel, Field

from bioneuronai.schemas.enums import DatabaseOperation, DatabaseStatus


class DatabaseConfig(BaseModel):
    """資料庫配置模型"""
    
    # 連接信息
    host: str = Field(..., description="資料庫主機")
    port: int = Field(..., description="資料庫端口")
    database: str = Field(..., description="資料庫名稱")
    username: str = Field(..., description="用戶名")
    password: str = Field(..., description="密碼", repr=False)  # 不顯示在日誌中
    
    # 連接池配置
    pool_size: int = Field(default=10, description="連接池大小")
    max_connections: int = Field(default=20, description="最大連接數")
    connection_timeout: int = Field(default=30, description="連接超時 (秒)")
    
    # SSL 配置
    ssl_enabled: bool = Field(default=False, description="是否啟用 SSL")
    ssl_cert_path: Optional[str] = Field(None, description="SSL 證書路徑")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "host": "localhost",
                    "port": 5432,
                    "database": "bioneuronai",
                    "username": "admin",
                    "password": "[HIDDEN]",
                    "pool_size": 10,
                    "max_connections": 20,
                    "connection_timeout": 30,
                    "ssl_enabled": False
                }
            ]
        }
    }


class DatabaseQuery(BaseModel):
    """資料庫查詢模型"""
    
    # 查詢基本信息
    query_id: str = Field(..., description="查詢唯一ID")
    operation: DatabaseOperation = Field(..., description="操作類型")
    table_name: str = Field(..., description="表名")
    
    # SQL 查詢
    sql: Optional[str] = Field(None, description="SQL 語句")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="查詢參數")
    
    # 執行控制
    timeout: Optional[int] = Field(None, description="查詢超時 (秒)")
    limit: Optional[int] = Field(None, description="結果限制")
    offset: Optional[int] = Field(None, description="結果偏移")
    
    # 時間信息
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query_id": "query_123456",
                    "operation": "read",
                    "table_name": "trading_signals",
                    "sql": "SELECT * FROM trading_signals WHERE symbol = :symbol",
                    "parameters": {"symbol": "BTCUSDT"},
                    "timeout": 30,
                    "limit": 100
                }
            ]
        }
    }


class DatabaseResult(BaseModel):
    """資料庫查詢結果模型"""
    
    # 關聯信息
    query_id: str = Field(..., description="對應的查詢ID")
    
    # 執行結果
    success: bool = Field(..., description="執行是否成功")
    rows_affected: int = Field(default=0, description="影響的列數")
    data: Optional[List[Dict[str, Any]]] = Field(None, description="查詢結果數據")
    
    # 錯誤信息
    error_message: Optional[str] = Field(None, description="錯誤信息")
    error_code: Optional[str] = Field(None, description="錯誤代碼")
    
    # 性能信息
    execution_time: float = Field(..., description="執行時間 (秒)")
    memory_usage: Optional[int] = Field(None, description="內存使用 (bytes)")
    
    # 時間信息
    started_at: datetime = Field(..., description="開始執行時間")
    completed_at: datetime = Field(default_factory=datetime.now, description="完成時間")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "query_id": "query_123456",
                    "success": True,
                    "rows_affected": 5,
                    "data": [
                        {"id": 1, "symbol": "BTCUSDT", "signal": "buy"},
                        {"id": 2, "symbol": "ETHUSDT", "signal": "sell"}
                    ],
                    "execution_time": 0.15,
                    "started_at": "2024-01-01T10:00:00Z",
                    "completed_at": "2024-01-01T10:00:01Z"
                }
            ]
        }
    }


class DatabaseConnection(BaseModel):
    """資料庫連接模型"""
    
    # 連接信息
    connection_id: str = Field(..., description="連接唯一ID")
    host: str = Field(..., description="資料庫主機")
    database: str = Field(..., description="資料庫名稱")
    
    # 狀態信息
    status: DatabaseStatus = Field(..., description="連接狀態")
    connected_at: Optional[datetime] = Field(None, description="連接時間")
    last_activity: Optional[datetime] = Field(None, description="最後活動時間")
    
    # 統計信息
    queries_executed: int = Field(default=0, description="已執行查詢數")
    total_execution_time: float = Field(default=0.0, description="總執行時間 (秒)")
    
    # 錯誤信息
    error_count: int = Field(default=0, description="錯誤計數")
    last_error: Optional[str] = Field(None, description="最後一次錯誤")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "connection_id": "conn_abc123",
                    "host": "localhost",
                    "database": "bioneuronai",
                    "status": "connected",
                    "connected_at": "2024-01-01T09:00:00Z",
                    "last_activity": "2024-01-01T10:00:00Z",
                    "queries_executed": 150,
                    "total_execution_time": 45.67,
                    "error_count": 2
                }
            ]
        }
    }


class TradingDataRecord(BaseModel):
    """交易數據記錄模型 (資料庫存儲用)"""
    
    # 主鍵
    id: Optional[int] = Field(None, description="記錄主鍵")
    
    # 基本信息
    symbol: str = Field(..., description="交易對符號")
    timestamp: datetime = Field(..., description="時間戳")
    
    # 價格數據
    open_price: Decimal = Field(..., description="開盤價")
    high_price: Decimal = Field(..., description="最高價")
    low_price: Decimal = Field(..., description="最低價")
    close_price: Decimal = Field(..., description="收盤價")
    volume: Decimal = Field(..., description="成交量")
    
    # 技術指標 (JSON 存儲)
    indicators: Optional[Dict[str, Decimal]] = Field(None, description="技術指標數據")
    
    # 交易信號
    signal_type: Optional[str] = Field(None, description="交易信號類型")
    signal_strength: Optional[str] = Field(None, description="信號強度")
    confidence: Optional[Decimal] = Field(None, description="信號置信度")
    
    # 元數據
    created_at: datetime = Field(default_factory=datetime.now, description="記錄創建時間")
    updated_at: Optional[datetime] = Field(None, description="記錄更新時間")
    source: str = Field(default="binance", description="數據來源")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "symbol": "BTCUSDT",
                    "timestamp": "2024-01-01T10:00:00Z",
                    "open_price": "50000.00",
                    "high_price": "50500.00",
                    "low_price": "49800.00",
                    "close_price": "50250.00",
                    "volume": "125.45",
                    "indicators": {
                        "rsi": "65.5",
                        "macd": "125.8",
                        "sma_20": "49950.0"
                    },
                    "signal_type": "buy",
                    "signal_strength": "strong",
                    "confidence": "0.85",
                    "source": "binance"
                }
            ]
        }
    }


# 為了向後兼容性，創建 DatabaseService 類
class DatabaseService(BaseModel):
    """資料庫服務模型 (向後兼容)"""
    
    config: DatabaseConfig = Field(..., description="資料庫配置")
    connection: Optional[DatabaseConnection] = Field(None, description="當前連接")
    status: DatabaseStatus = Field(default=DatabaseStatus.DISCONNECTED, description="服務狀態")
    
    # 統計信息
    total_queries: int = Field(default=0, description="總查詢數")
    success_queries: int = Field(default=0, description="成功查詢數")
    error_queries: int = Field(default=0, description="錯誤查詢數")
    
    # 時間信息
    service_started_at: datetime = Field(default_factory=datetime.now, description="服務啟動時間")
    last_query_at: Optional[datetime] = Field(None, description="最後查詢時間")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "config": {
                        "host": "localhost",
                        "port": 5432,
                        "database": "bioneuronai",
                        "username": "admin",
                        "password": "[HIDDEN]"
                    },
                    "status": "connected",
                    "total_queries": 1250,
                    "success_queries": 1200,
                    "error_queries": 50
                }
            ]
        }
    }