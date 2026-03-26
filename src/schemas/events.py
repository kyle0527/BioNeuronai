"""
BioNeuronai Event Sourcing 模型

實現交易系統的事件溯源 (Event Sourcing) 模式。
所有交易相關操作都會生成不可變事件，用於審計追蹤和狀態重建。

參考：
- Event Sourcing Pattern: https://martinfowler.com/eaaDev/EventSourcing.html
- CQRS Pattern: https://martinfowler.com/bliki/CQRS.html

最後更新: 2026-02-14
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, computed_field

from .enums import (
    TradeEventType,
    OrderSide,
    OrderType,
    OrderStatus,
    PositionType,
    RiskLevel,
)

# 常量定義 - 避免重複字符串
EVENT_ID_DESC = "事件唯一 ID"
EVENT_METADATA_DESC = "事件元數據"


class EventMetadata(BaseModel):
    """事件元數據
    
    包含事件的追蹤和審計信息。
    """
    
    source: str = Field(..., description="事件來源 (如: trading_engine, risk_manager)")
    version: str = Field(default="1.0", description="事件版本")
    correlation_id: Optional[UUID] = Field(None, description="關聯 ID，用於追蹤相關事件")
    causation_id: Optional[UUID] = Field(None, description="因果 ID，追蹤事件因果關係")
    user_id: Optional[str] = Field(None, description="觸發事件的用戶 ID")
    session_id: Optional[str] = Field(None, description="會話 ID")
    ip_address: Optional[str] = Field(None, description="來源 IP")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source": "trading_engine",
                    "version": "1.0",
                    "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
                    "user_id": "system",
                }
            ]
        }
    }


class TradeEvent(BaseModel):
    """交易事件基類
    
    所有交易相關事件的基類，實現 Event Sourcing 模式。
    事件一旦創建就不可變，用於完整的審計追蹤。
    """
    
    # 事件識別
    event_id: UUID = Field(default_factory=uuid4, description=EVENT_ID_DESC)
    event_type: TradeEventType = Field(..., description="事件類型")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件發生時間")
    
    # 聚合根識別 (相關的訂單/倉位)
    aggregate_id: str = Field(..., description="聚合根 ID (訂單 ID 或倉位標識)")
    aggregate_type: str = Field(..., description="聚合類型 (order/position/account)")
    
    # 事件內容
    payload: dict[str, Any] = Field(default_factory=dict, description="事件有效載荷")
    
    # 元數據
    metadata: EventMetadata = Field(..., description=EVENT_METADATA_DESC)
    
    # 序列號 (用於事件排序)
    sequence_number: Optional[int] = Field(None, description="事件序列號")
    
    @computed_field
    @property
    def event_key(self) -> str:
        """生成事件唯一鍵"""
        return f"{self.aggregate_type}:{self.aggregate_id}:{self.event_id}"
    
    model_config = {
        "frozen": True,  # 事件不可變
        "json_schema_extra": {
            "examples": [
                {
                    "event_type": "ORDER_PLACED",
                    "aggregate_id": "123456789",
                    "aggregate_type": "order",
                    "payload": {
                        "symbol": "BTCUSDT",
                        "side": "BUY",
                        "quantity": "0.001",
                    },
                    "metadata": {
                        "source": "trading_engine",
                        "version": "1.0",
                    },
                }
            ]
        }
    }


class OrderEvent(BaseModel):
    """訂單事件
    
    記錄訂單生命週期中的所有事件。
    """
    
    event_id: UUID = Field(default_factory=uuid4, description=EVENT_ID_DESC)
    event_type: TradeEventType = Field(..., description="事件類型")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件時間")
    
    # 訂單信息
    order_id: str = Field(..., description="訂單 ID")
    client_order_id: Optional[str] = Field(None, description="客戶端訂單 ID")
    symbol: str = Field(..., description="交易對")
    side: OrderSide = Field(..., description="訂單方向")
    order_type: OrderType = Field(..., description="訂單類型")
    status: OrderStatus = Field(..., description="訂單狀態")
    
    # 價格和數量
    price: Optional[Decimal] = Field(None, gt=0, description="訂單價格")
    quantity: Decimal = Field(..., gt=0, description="訂單數量")
    filled_quantity: Decimal = Field(default=Decimal("0"), ge=0, description="已成交數量")
    avg_price: Optional[Decimal] = Field(None, ge=0, description="平均成交價")
    
    # 費用
    commission: Decimal = Field(default=Decimal("0"), ge=0, description="手續費")
    commission_asset: Optional[str] = Field(None, description="手續費資產")
    
    # 追蹤
    metadata: EventMetadata = Field(..., description=EVENT_METADATA_DESC)
    
    model_config = {
        "frozen": True,
        "json_schema_extra": {
            "examples": [
                {
                    "event_type": "ORDER_FILLED",
                    "order_id": "123456789",
                    "symbol": "BTCUSDT",
                    "side": "BUY",
                    "order_type": "MARKET",
                    "status": "FILLED",
                    "quantity": "0.001",
                    "filled_quantity": "0.001",
                    "avg_price": "50000.00",
                    "commission": "0.00005",
                    "commission_asset": "BTC",
                    "metadata": {"source": "binance_api", "version": "1.0"},
                }
            ]
        }
    }


class PositionEvent(BaseModel):
    """倉位事件
    
    記錄倉位變化的所有事件。
    """
    
    event_id: UUID = Field(default_factory=uuid4, description=EVENT_ID_DESC)
    event_type: TradeEventType = Field(..., description="事件類型")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件時間")
    
    # 倉位信息
    position_id: str = Field(..., description="倉位標識 (symbol:side)")
    symbol: str = Field(..., description="交易對")
    position_side: PositionType = Field(..., description="倉位方向")
    
    # 倉位變化
    previous_quantity: Decimal = Field(..., description="變化前數量")
    new_quantity: Decimal = Field(..., description="變化後數量")
    delta_quantity: Decimal = Field(..., description="數量變化")
    
    # 價格信息
    entry_price: Decimal = Field(..., gt=0, description="進場價格")
    mark_price: Decimal = Field(..., gt=0, description="標記價格")
    liquidation_price: Optional[Decimal] = Field(None, description="強平價格")
    
    # 盈虧
    realized_pnl: Decimal = Field(default=Decimal("0"), description="已實現盈虧")
    unrealized_pnl: Decimal = Field(default=Decimal("0"), description="未實現盈虧")
    
    # 槓桿
    leverage: int = Field(default=1, ge=1, le=125, description="槓桿倍數")
    margin_type: str = Field(default="cross", description="保證金類型")
    
    # 相關訂單
    trigger_order_id: Optional[str] = Field(None, description="觸發此事件的訂單 ID")
    
    # 追蹤
    metadata: EventMetadata = Field(..., description=EVENT_METADATA_DESC)
    
    model_config = {
        "frozen": True,
        "json_schema_extra": {
            "examples": [
                {
                    "event_type": "POSITION_OPENED",
                    "position_id": "BTCUSDT:LONG",
                    "symbol": "BTCUSDT",
                    "position_side": "long",
                    "previous_quantity": "0",
                    "new_quantity": "0.001",
                    "delta_quantity": "0.001",
                    "entry_price": "50000.00",
                    "mark_price": "50050.00",
                    "leverage": 10,
                    "metadata": {"source": "trading_engine", "version": "1.0"},
                }
            ]
        }
    }


class RiskEvent(BaseModel):
    """風險事件
    
    記錄風險相關事件，用於風險監控和審計。
    """
    
    event_id: UUID = Field(default_factory=uuid4, description=EVENT_ID_DESC)
    event_type: TradeEventType = Field(..., description="事件類型")
    timestamp: datetime = Field(default_factory=datetime.now, description="事件時間")
    
    # 風險信息
    risk_level: RiskLevel = Field(..., description="風險等級")
    risk_type: str = Field(..., description="風險類型")
    description: str = Field(..., description="風險描述")
    
    # 相關實體
    affected_positions: list[str] = Field(default_factory=list, description="受影響的倉位")
    affected_orders: list[str] = Field(default_factory=list, description="受影響的訂單")
    
    # 風險指標
    current_value: Optional[float] = Field(None, description="當前值")
    threshold_value: Optional[float] = Field(None, description="閾值")
    breach_percentage: Optional[float] = Field(None, description="超出百分比")
    
    # 採取的行動
    action_taken: Optional[str] = Field(None, description="採取的行動")
    action_result: Optional[str] = Field(None, description="行動結果")
    
    # 追蹤
    metadata: EventMetadata = Field(..., description=EVENT_METADATA_DESC)
    
    model_config = {
        "frozen": True,
        "json_schema_extra": {
            "examples": [
                {
                    "event_type": "RISK_LIMIT_REACHED",
                    "risk_level": "high",
                    "risk_type": "DRAWDOWN",
                    "description": "日內回撤達到 5%",
                    "affected_positions": ["BTCUSDT:LONG", "ETHUSDT:SHORT"],
                    "current_value": 0.05,
                    "threshold_value": 0.05,
                    "action_taken": "REDUCE_POSITIONS",
                    "metadata": {"source": "risk_manager", "version": "1.0"},
                }
            ]
        }
    }


class EventStore(BaseModel):
    """事件存儲模型
    
    用於事件的批量存儲和查詢。
    """
    
    # 存儲信息
    stream_id: str = Field(..., description="事件流 ID")
    stream_type: str = Field(..., description="事件流類型")
    
    # 事件列表
    events: list[TradeEvent] = Field(default_factory=list, description="事件列表")
    
    # 快照
    snapshot_version: Optional[int] = Field(None, description="最新快照版本")
    last_event_sequence: int = Field(default=0, description="最後事件序列號")
    
    # 時間範圍
    start_time: Optional[datetime] = Field(None, description="事件流開始時間")
    end_time: Optional[datetime] = Field(None, description="事件流結束時間")
    
    def append_event(self, event: TradeEvent) -> "EventStore":
        """添加事件到流中"""
        new_events = self.events.copy()
        new_events.append(event)
        return EventStore(
            stream_id=self.stream_id,
            stream_type=self.stream_type,
            events=new_events,
            snapshot_version=self.snapshot_version,
            last_event_sequence=self.last_event_sequence + 1,
            start_time=self.start_time or event.timestamp,
            end_time=event.timestamp,
        )
    
    def get_events_after(self, sequence: int) -> list[TradeEvent]:
        """獲取指定序列號之後的事件"""
        return [
            e for e in self.events 
            if e.sequence_number is not None and e.sequence_number > sequence
        ]


class EventQuery(BaseModel):
    """事件查詢模型"""
    
    # 查詢條件
    aggregate_id: Optional[str] = Field(None, description="聚合根 ID")
    aggregate_type: Optional[str] = Field(None, description="聚合類型")
    event_types: Optional[list[TradeEventType]] = Field(None, description="事件類型過濾")
    
    # 時間範圍
    start_time: Optional[datetime] = Field(None, description="開始時間")
    end_time: Optional[datetime] = Field(None, description="結束時間")
    
    # 分頁
    limit: int = Field(default=100, ge=1, le=1000, description="查詢限制")
    offset: int = Field(default=0, ge=0, description="偏移量")
    
    # 排序
    ascending: bool = Field(default=True, description="升序排列")


# =============================================================================
# 導出
# =============================================================================

__all__ = [
    "EventMetadata",
    "TradeEvent",
    "OrderEvent",
    "PositionEvent",
    "RiskEvent",
    "EventStore",
    "EventQuery",
]
