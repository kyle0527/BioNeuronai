"""Live-market paper execution connector.

This connector intentionally keeps the BinanceFuturesConnector market-data
surface while replacing signed order/account operations with VirtualAccount.
Strategies and TradingEngine can use it as if it were the normal connector;
the final execution step never sends an order to Binance.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from bioneuronai.trading.virtual_account import VirtualAccount, VirtualOrder

from .binance_futures import BinanceFuturesConnector, OrderResult

logger = logging.getLogger(__name__)


class PaperBinanceFuturesConnector(BinanceFuturesConnector):
    """Binance market data + local virtual execution."""

    def __init__(
        self,
        api_key: str = "",
        api_secret: str = "",
        testnet: bool = False,
        initial_balance: float = 10000.0,
        leverage: int = 1,
        maker_fee: float = 0.0002,
        taker_fee: float = 0.00055,
        slippage_rate: float = 0.0001,
        log_dir: Optional[str | Path] = None,
    ) -> None:
        super().__init__(api_key=api_key, api_secret=api_secret, testnet=testnet)
        self.paper_trading = True
        self.virtual_account = VirtualAccount(
            initial_balance=initial_balance,
            leverage=leverage,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            slippage_rate=slippage_rate,
        )
        project_root = Path(__file__).resolve().parents[3]
        self.log_dir = Path(log_dir) if log_dir else project_root / "data" / "bioneuronai" / "trading" / "paper_live"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.orders_log = self.log_dir / "orders.jsonl"
        self.account_log = self.log_dir / "account_snapshots.jsonl"
        self.state_file = self.log_dir / "paper_state.json"
        self._restored_from_state = self._restore_virtual_account()
        self.virtual_account.set_state_change_callback(self._persist_virtual_account)
        if not self._restored_from_state:
            self._persist_virtual_account(self.virtual_account.export_state())
        logger.info(
            "Paper live connector enabled: market_data=%s, initial_balance=%.2f, restored=%s",
            "testnet" if testnet else "mainnet",
            self.virtual_account.initial_balance,
            self._restored_from_state,
        )

    def _persist_virtual_account(self, state: Dict[str, Any]) -> None:
        """原子保存可恢復的帳戶事實；失敗由 VirtualAccount 記錄但不阻斷成交。"""
        payload = {
            "saved_at": datetime.now().isoformat(),
            "mode": "paper_live",
            "virtual_account": state,
        }
        temporary = self.state_file.with_suffix(".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.state_file)

    def _restore_virtual_account(self) -> bool:
        """只接受完整可驗證 state；損壞檔案不會覆蓋新帳戶。"""
        if not self.state_file.exists():
            return False
        try:
            payload = json.loads(self.state_file.read_text(encoding="utf-8"))
            state = payload.get("virtual_account") if isinstance(payload, dict) else None
            self.virtual_account.restore_state(state)
            logger.info("Paper virtual account restored | positions=%d open_orders=%d",
                        len(self.virtual_account.positions), len(self.virtual_account.open_orders))
            return True
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
            logger.warning("Paper state restore skipped: %s", exc)
            return False

    def _refresh_virtual_price(self, symbol: str, fallback_price: Optional[float] = None) -> float:
        price = fallback_price or 0.0
        market_data = self.get_ticker_price(symbol)
        if market_data is not None and market_data.close > 0:
            price = float(market_data.close)
        if price > 0:
            self.virtual_account.update_price(symbol, price)
        return price

    def _write_jsonl(self, path: Path, payload: Dict[str, Any]) -> None:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, default=str))
            handle.write("\n")

    def _to_order_result(
        self,
        order: VirtualOrder,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        requested_price: Optional[float] = None,
    ) -> OrderResult:
        price = float(order.filled_price or order.price or requested_price or 0.0)
        return OrderResult(
            order_id=order.order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            status=order.status.value,
            timestamp=order.timestamp,
            error="" if order.status.value != "REJECTED" else "paper order rejected",
        )

    def get_account_info(self) -> Dict[str, Any]:
        """Return Binance-like account state from the virtual account."""
        snapshot = self.virtual_account.get_account_info()
        self._write_jsonl(
            self.account_log,
            {
                "timestamp": datetime.now().isoformat(),
                "mode": "paper_live",
                "snapshot": snapshot,
            },
        )
        return snapshot

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        **kwargs: Any,
    ) -> Optional[OrderResult]:
        """Execute locally and persist an order record; never call Binance POST."""
        client_order_id = str(kwargs.get("client_order_id") or "").strip() or None
        existing = self.virtual_account.get_order_by_client_id(client_order_id)
        if existing is not None:
            logger.info("PAPER intent deduplicated: %s", client_order_id)
            return self._to_order_result(
                existing,
                symbol,
                side,
                order_type,
                quantity,
                price,
            )

        current_price = self._refresh_virtual_price(symbol, fallback_price=price)
        execution_price = price if order_type.upper() == "LIMIT" else current_price

        order = self.virtual_account.place_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=execution_price,
            stop_price=kwargs.get("stop_price"),
            reduce_only=bool(kwargs.get("reduce_only", False)),
            time_in_force=kwargs.get("time_in_force"),
            client_order_id=client_order_id,
        )

        opposite_side = "SELL" if side.upper() == "BUY" else "BUY"
        child_orders: list[Dict[str, Any]] = []
        if stop_loss:
            stop_order = self.virtual_account.place_order(
                symbol=symbol,
                side=opposite_side,
                order_type="STOP_MARKET",
                quantity=quantity,
                stop_price=float(stop_loss),
                reduce_only=True,
                client_order_id=f"{client_order_id}:stop" if client_order_id else None,
            )
            child_orders.append(stop_order.to_dict())
        if take_profit:
            tp_order = self.virtual_account.place_order(
                symbol=symbol,
                side=opposite_side,
                order_type="TAKE_PROFIT_MARKET",
                quantity=quantity,
                stop_price=float(take_profit),
                reduce_only=True,
                client_order_id=(
                    f"{client_order_id}:take_profit" if client_order_id else None
                ),
            )
            child_orders.append(tp_order.to_dict())

        result = self._to_order_result(order, symbol, side, order_type, quantity, execution_price)
        self._write_jsonl(
            self.orders_log,
            {
                "timestamp": datetime.now().isoformat(),
                "mode": "paper_live",
                "primary_order": order.to_dict(),
                "child_orders": child_orders,
                "result": result.to_dict(),
                "account": self.virtual_account.get_account_snapshot(),
            },
        )
        logger.info(
            "PAPER order executed locally: %s %s %s qty=%.8f status=%s",
            side,
            order_type,
            symbol,
            quantity,
            result.status,
        )
        return result

    def get_paper_state(self) -> Dict[str, Any]:
        return {
            "mode": "paper_live",
            "log_dir": str(self.log_dir),
            "state_file": str(self.state_file),
            "restored_from_state": self._restored_from_state,
            "account": self.virtual_account.get_account_snapshot(),
            "stats": self.virtual_account.get_stats(),
            "positions": [position.to_dict() for position in self.virtual_account.get_all_positions()],
            "open_orders": self.virtual_account.get_open_orders_snapshot(),
        }
