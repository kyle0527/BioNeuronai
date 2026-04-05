"""Core replay contracts.

These contracts keep the replay layer narrow:
- historical market data is read-only input
- the project decides orders
- replay only receives intents and returns simulated results
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Protocol


@dataclass(slots=True)
class OrderIntent:
    """Standardized order request sent from the project to an execution sink."""

    symbol: str
    side: str
    order_type: str
    quantity: float
    price: Optional[float] = None
    reduce_only: bool = False
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionReceipt:
    """Execution result returned by live or replay execution."""

    accepted: bool
    order_id: str
    status: str
    filled_qty: float = 0.0
    avg_price: float = 0.0
    message: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ReplayRuntimeState:
    """Mutable replay state, isolated from immutable historical data."""

    mode: str = "replay"
    current_bar_index: int = 0
    current_open_time: Optional[int] = None
    current_price: Optional[float] = None
    orders_received: int = 0
    fills_emitted: int = 0
    last_updated_at: Optional[datetime] = None


class ReplayDataFeed(Protocol):
    """Read-only market data interface for replay."""

    def load_data(self) -> Any:
        ...

    def stream_bars(self) -> Any:
        ...

    def get_klines_until_now(self, limit: int = 500) -> Any:
        ...


class ExecutionSink(Protocol):
    """Execution target used by the project after a strategy decides to trade."""

    def submit_order(self, intent: OrderIntent) -> ExecutionReceipt:
        ...
