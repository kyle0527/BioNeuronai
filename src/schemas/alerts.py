"""
BioNeuronai 警報系統 Schema

定義警報規則、事件和通知的 Pydantic 模型。
支援價格警報、技術指標警報、風險警報和系統警報。

最後更新: 2026-02-14
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Literal, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from .enums import (
    AlertSeverity,
    AlertType,
    NotificationChannel,
    OrderSide,
)


class AlertCondition(BaseModel):
    """警報觸發條件
    
    定義觸發警報的具體條件。
    """
    
    # 條件類型
    condition_type: Literal[
        "crosses_above",      # 向上穿越
        "crosses_below",      # 向下穿越
        "greater_than",       # 大於
        "less_than",          # 小於
        "equals",             # 等於
        "change_pct_up",      # 上漲百分比
        "change_pct_down",    # 下跌百分比
        "in_range",           # 區間內
        "out_of_range",       # 區間外
        "custom",             # 自定義
    ] = Field(..., description="條件類型")
    
    # 目標值
    target_value: Optional[float] = Field(None, description="目標值")
    target_value_2: Optional[float] = Field(None, description="第二目標值 (範圍條件)")
    
    # 時間窗口
    time_window_minutes: Optional[int] = Field(
        None, 
        ge=1, 
        description="時間窗口 (分鐘)"
    )
    
    # 自定義表達式
    custom_expression: Optional[str] = Field(
        None,
        max_length=500,
        description="自定義條件表達式"
    )
    
    @model_validator(mode="after")
    def validate_condition(self) -> "AlertCondition":
        """驗證條件邏輯"""
        if self.condition_type == "in_range" or self.condition_type == "out_of_range":
            if self.target_value is None or self.target_value_2 is None:
                raise ValueError(
                    f"{self.condition_type} 條件需要兩個目標值"
                )
            if self.target_value >= self.target_value_2:
                raise ValueError("target_value 必須小於 target_value_2")
        elif self.condition_type == "custom":
            if not self.custom_expression:
                raise ValueError("自定義條件需要 custom_expression")
        elif self.condition_type != "custom" and self.target_value is None:
            raise ValueError(f"{self.condition_type} 條件需要 target_value")
        
        return self


class AlertRule(BaseModel):
    """警報規則
    
    定義完整的警報規則配置。
    """
    
    # 規則識別
    rule_id: UUID = Field(default_factory=uuid4, description="規則唯一 ID")
    name: str = Field(..., min_length=1, max_length=100, description="規則名稱")
    description: Optional[str] = Field(None, max_length=500, description="規則描述")
    
    # 警報類型
    alert_type: AlertType = Field(..., description="警報類型")
    severity: AlertSeverity = Field(
        default=AlertSeverity.INFO,
        description="警報嚴重性"
    )
    
    # 監控目標
    symbol: Optional[str] = Field(None, description="監控標的 (價格相關)")
    metric_name: str = Field(..., description="監控指標名稱")
    
    # 觸發條件
    condition: AlertCondition = Field(..., description="觸發條件")
    
    # 通知配置
    notification_channels: list[NotificationChannel] = Field(
        default_factory=lambda: [NotificationChannel.IN_APP],
        min_length=1,
        description="通知渠道"
    )
    
    # 狀態
    is_enabled: bool = Field(default=True, description="是否啟用")
    is_one_time: bool = Field(default=False, description="是否一次性")
    cooldown_minutes: int = Field(
        default=5,
        ge=0,
        description="冷卻時間 (分鐘)"
    )
    
    # 有效期
    valid_from: Optional[datetime] = Field(None, description="生效開始時間")
    valid_until: Optional[datetime] = Field(None, description="生效結束時間")
    
    # 元數據
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="創建時間"
    )
    last_triggered_at: Optional[datetime] = Field(
        None,
        description="最後觸發時間"
    )
    trigger_count: int = Field(default=0, ge=0, description="觸發次數")
    
    # 標籤
    tags: list[str] = Field(default_factory=list, description="標籤")
    
    @model_validator(mode="after")
    def validate_rule(self) -> "AlertRule":
        """驗證規則配置"""
        # 價格類警報需要 symbol
        price_alerts = [
            AlertType.PRICE_ABOVE,
            AlertType.PRICE_BELOW,
            AlertType.PRICE_CHANGE_PCT,
        ]
        if self.alert_type in price_alerts and not self.symbol:
            raise ValueError("價格警報需要指定 symbol")
        
        # 驗證生效時間
        if self.valid_from and self.valid_until:
            if self.valid_from >= self.valid_until:
                raise ValueError("valid_from 必須早於 valid_until")
        
        return self


class AlertEvent(BaseModel):
    """警報事件
    
    記錄一次警報觸發的完整信息。
    """
    
    # 事件識別
    event_id: UUID = Field(default_factory=uuid4, description="事件唯一 ID")
    rule_id: UUID = Field(..., description="規則 ID")
    rule_name: str = Field(..., description="規則名稱")
    
    # 警報信息
    alert_type: AlertType = Field(..., description="警報類型")
    severity: AlertSeverity = Field(..., description="警報嚴重性")
    
    # 觸發信息
    triggered_at: datetime = Field(
        default_factory=datetime.now,
        description="觸發時間"
    )
    trigger_value: float = Field(..., description="觸發時的值")
    threshold_value: float = Field(..., description="閾值")
    
    # 上下文
    symbol: Optional[str] = Field(None, description="相關標的")
    metric_name: str = Field(..., description="指標名稱")
    additional_context: dict[str, Any] = Field(
        default_factory=dict,
        description="附加上下文"
    )
    
    # 消息
    title: str = Field(..., description="警報標題")
    message: str = Field(..., description="警報消息")
    
    # 通知狀態
    notifications_sent: list[NotificationChannel] = Field(
        default_factory=list,
        description="已發送的通知"
    )
    
    # 確認
    is_acknowledged: bool = Field(default=False, description="是否已確認")
    acknowledged_at: Optional[datetime] = Field(None, description="確認時間")
    acknowledged_by: Optional[str] = Field(None, description="確認人")
    
    # 解決
    is_resolved: bool = Field(default=False, description="是否已解決")
    resolved_at: Optional[datetime] = Field(None, description="解決時間")
    resolution_note: Optional[str] = Field(None, description="解決備註")
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "event_id": "550e8400-e29b-41d4-a716-446655440000",
                    "rule_id": "550e8400-e29b-41d4-a716-446655440001",
                    "rule_name": "BTC 價格突破",
                    "alert_type": "PRICE_ABOVE",
                    "severity": "WARNING",
                    "triggered_at": "2026-02-14T10:30:00Z",
                    "trigger_value": 105000.0,
                    "threshold_value": 100000.0,
                    "symbol": "BTCUSDT",
                    "metric_name": "mark_price",
                    "title": "BTC 突破 10 萬美元",
                    "message": "BTCUSDT 價格達到 105000，已突破 100000 閾值"
                }
            ]
        }
    }


class NotificationConfig(BaseModel):
    """通知配置
    
    配置各通知渠道的詳細設置。
    """
    
    # 渠道
    channel: NotificationChannel = Field(..., description="通知渠道")
    is_enabled: bool = Field(default=True, description="是否啟用")
    
    # EMAIL 配置
    email_address: Optional[str] = Field(None, description="郵箱地址")
    
    # SMS 配置
    phone_number: Optional[str] = Field(None, description="手機號碼")
    
    # TELEGRAM 配置
    telegram_chat_id: Optional[str] = Field(None, description="Telegram Chat ID")
    telegram_bot_token: Optional[str] = Field(None, description="Telegram Bot Token")
    
    # DISCORD 配置
    discord_webhook_url: Optional[str] = Field(None, description="Discord Webhook URL")
    discord_channel_id: Optional[str] = Field(None, description="Discord Channel ID")
    
    # WEBHOOK 配置
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    webhook_secret: Optional[str] = Field(None, description="Webhook 密鑰")
    webhook_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Webhook Headers"
    )
    
    # 通用配置
    format_template: Optional[str] = Field(None, description="消息格式模板")
    severity_filter: list[AlertSeverity] = Field(
        default_factory=lambda: list(AlertSeverity),
        description="嚴重性過濾"
    )
    
    @model_validator(mode="after")
    def validate_config(self) -> "NotificationConfig":
        """驗證通知配置完整性"""
        if not self.is_enabled:
            return self
        
        # 驗證必需字段
        self._validate_required_fields()
        return self
    
    def _validate_required_fields(self) -> None:
        """私有方法：驗證各渠道的必需字段"""
        validators = {
            NotificationChannel.EMAIL: lambda: self._check_field("email_address", "Email"),
            NotificationChannel.SMS: lambda: self._check_field("phone_number", "SMS"),
            NotificationChannel.TELEGRAM: self._validate_telegram,
            NotificationChannel.DISCORD: lambda: self._check_field("discord_webhook_url", "Discord"),
            NotificationChannel.WEBHOOK: lambda: self._check_field("webhook_url", "Webhook"),
        }
        
        validator = validators.get(self.channel)
        if validator:
            validator()
    
    def _check_field(self, field_name: str, channel_name: str) -> None:
        """檢查單個字段是否存在"""
        if not getattr(self, field_name, None):
            raise ValueError(f"{channel_name} 通知需要 {field_name}")
    
    def _validate_telegram(self) -> None:
        """Telegram 專用驗證"""
        if not self.telegram_chat_id:
            raise ValueError("Telegram 通知需要 chat_id")
        if not self.telegram_bot_token:
            raise ValueError("Telegram 通知需要 bot_token")


class AlertSummary(BaseModel):
    """警報摘要
    
    統計警報系統的運行狀態。
    """
    
    # 統計時間範圍
    period_start: datetime = Field(..., description="統計開始時間")
    period_end: datetime = Field(..., description="統計結束時間")
    
    # 規則統計
    total_rules: int = Field(default=0, ge=0, description="總規則數")
    enabled_rules: int = Field(default=0, ge=0, description="啟用規則數")
    disabled_rules: int = Field(default=0, ge=0, description="停用規則數")
    
    # 事件統計
    total_events: int = Field(default=0, ge=0, description="總事件數")
    events_by_severity: dict[str, int] = Field(
        default_factory=dict,
        description="按嚴重性分類"
    )
    events_by_type: dict[str, int] = Field(
        default_factory=dict,
        description="按類型分類"
    )
    
    # 確認/解決統計
    acknowledged_events: int = Field(default=0, ge=0, description="已確認事件")
    resolved_events: int = Field(default=0, ge=0, description="已解決事件")
    pending_events: int = Field(default=0, ge=0, description="待處理事件")
    
    # 通知統計
    notifications_sent: dict[str, int] = Field(
        default_factory=dict,
        description="各渠道發送數"
    )
    notification_failures: int = Field(default=0, ge=0, description="通知失敗數")
    
    # 平均響應時間
    avg_acknowledgement_time_seconds: Optional[float] = Field(
        None,
        ge=0,
        description="平均確認時間 (秒)"
    )
    avg_resolution_time_seconds: Optional[float] = Field(
        None,
        ge=0,
        description="平均解決時間 (秒)"
    )
    
    # 活躍警報
    most_triggered_rules: list[dict[str, Any]] = Field(
        default_factory=list,
        description="觸發最多的規則"
    )


# =============================================================================
# 導出
# =============================================================================

__all__ = [
    "AlertCondition",
    "AlertRule",
    "AlertEvent",
    "NotificationConfig",
    "AlertSummary",
]
