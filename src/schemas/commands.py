"""
BioNeuronai 命令系統模型

基於 AIVA Common v6.3 標準的命令系統 Pydantic 模型。
"""

from datetime import datetime
from typing import Optional, Dict, Any, Union
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import CommandType, CommandStatus


class AICommand(BaseModel):
    """AI 命令模型 - AIVA Common v6.3 標準"""
    
    # 基本信息
    command_id: str = Field(default_factory=lambda: str(uuid4()), description="命令唯一ID")
    command_type: CommandType = Field(..., description="命令類型")
    action: str = Field(..., description="具體執行動作")
    
    # 目標和參數
    target: Optional[str] = Field(None, description="命令目標 (如交易對)")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="命令參數")
    
    # 執行控制
    priority: int = Field(default=5, ge=1, le=10, description="優先級 (1最高, 10最低)")
    timeout: Optional[int] = Field(None, description="超時時間 (秒)")
    retry_count: int = Field(default=0, description="重試次數")
    max_retries: int = Field(default=3, description="最大重試次數")
    
    # 狀態信息
    status: CommandStatus = Field(default=CommandStatus.PENDING, description="命令狀態")
    created_at: datetime = Field(default_factory=datetime.now, description="創建時間")
    started_at: Optional[datetime] = Field(None, description="開始執行時間")
    completed_at: Optional[datetime] = Field(None, description="完成時間")
    
    # 上下文信息
    user_id: Optional[str] = Field(None, description="用戶ID")
    session_id: Optional[str] = Field(None, description="會話ID")
    correlation_id: Optional[str] = Field(None, description="關聯ID")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "command_type": "trading",
                    "action": "place_order",
                    "target": "BTCUSDT",
                    "parameters": {
                        "side": "buy",
                        "type": "limit",
                        "quantity": "0.001",
                        "price": "50000.00"
                    },
                    "priority": 3,
                    "timeout": 30
                }
            ]
        }
    }


class AICommandResult(BaseModel):
    """AI 命令執行結果模型 - AIVA Common v6.3 標準"""
    
    # 關聯信息
    command_id: str = Field(..., description="對應的命令ID")
    correlation_id: Optional[str] = Field(None, description="關聯ID")
    
    # 執行結果
    success: bool = Field(..., description="執行是否成功")
    status: CommandStatus = Field(..., description="執行狀態")
    
    # 結果數據
    result: Optional[Dict[str, Any]] = Field(None, description="執行結果數據")
    error_message: Optional[str] = Field(None, description="錯誤信息")
    error_code: Optional[str] = Field(None, description="錯誤代碼")
    
    # 執行統計
    execution_time: Optional[float] = Field(None, description="執行耗時 (秒)")
    retry_count: int = Field(default=0, description="重試次數")
    
    # 時間信息
    started_at: datetime = Field(..., description="開始執行時間")
    completed_at: datetime = Field(default_factory=datetime.now, description="完成時間")
    
    # 額外信息
    metadata: Dict[str, Any] = Field(default_factory=dict, description="額外元數據")
    logs: list[str] = Field(default_factory=list, description="執行日誌")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "command_id": "cmd_123456",
                    "success": True,
                    "status": "completed",
                    "result": {
                        "order_id": 987654321,
                        "status": "filled",
                        "executed_qty": "0.001"
                    },
                    "execution_time": 1.5,
                    "started_at": "2024-01-01T10:00:00Z",
                    "completed_at": "2024-01-01T10:00:01Z"
                }
            ]
        }
    }


class TradingCommand(AICommand):
    """交易命令模型"""
    
    command_type: CommandType = Field(default=CommandType.TRADING, description="命令類型")
    
    # 交易特定參數
    symbol: str = Field(..., description="交易對符號")
    side: str = Field(..., description="買賣方向")
    order_type: str = Field(..., description="訂單類型")
    quantity: Union[str, float] = Field(..., description="訂單數量")
    price: Optional[Union[str, float]] = Field(None, description="訂單價格")
    
    # 風險控制
    stop_loss: Optional[Union[str, float]] = Field(None, description="止損價格")
    take_profit: Optional[Union[str, float]] = Field(None, description="止盈價格")
    reduce_only: bool = Field(default=False, description="僅減倉")
    

class AnalysisCommand(AICommand):
    """分析命令模型"""
    
    command_type: CommandType = Field(default=CommandType.ANALYSIS, description="命令類型")
    
    # 分析特定參數
    symbols: list[str] = Field(default_factory=list, description="分析的交易對列表")
    timeframe: str = Field(default="1h", description="時間框架")
    analysis_type: str = Field(..., description="分析類型 (technical/fundamental/sentiment)")
    
    # 分析選項
    indicators: list[str] = Field(default_factory=list, description="技術指標列表")
    lookback_period: int = Field(default=100, description="回顧期間")
    

class RiskManagementCommand(AICommand):
    """風險管理命令模型"""
    
    command_type: CommandType = Field(default=CommandType.RISK_MANAGEMENT, description="命令類型")
    
    # 風險管理特定參數
    portfolio_value: Union[str, float] = Field(..., description="組合總值")
    max_drawdown: float = Field(default=0.05, description="最大回撤限制")
    position_size_limit: float = Field(default=0.1, description="單筆倉位限制")
    
    # 風險評估
    risk_level: str = Field(default="medium", description="風險等級")
    var_confidence: float = Field(default=0.95, description="VaR 置信水平")


class SystemCommand(AICommand):
    """系統命令模型"""
    
    command_type: CommandType = Field(default=CommandType.SYSTEM, description="命令類型")
    
    # 系統特定參數
    service_name: Optional[str] = Field(None, description="服務名稱")
    operation: str = Field(..., description="操作類型 (start/stop/restart/status)")
    
    # 配置參數
    config_changes: Dict[str, Any] = Field(default_factory=dict, description="配置變更")
    force: bool = Field(default=False, description="強制執行")