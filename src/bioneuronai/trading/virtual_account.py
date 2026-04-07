"""
Trading Virtual Account - 訂單 / 帳戶 / 持倉狀態層
=================================================

此模組現在屬於 ``bioneuronai.trading``，是交易執行事實層的第一個正式實作。

它只負責維護與模擬：
- 餘額與可用資金
- 掛單與成交
- 倉位與盈虧
- 手續費、滑點、保證金

它不負責策略決策。
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid

from schemas.enums import OrderSide, OrderStatus, OrderType

logger = logging.getLogger(__name__)

class PositionSide(Enum):
    """交易模組內部持倉方向。

    目前保留大寫值以維持 Binance-like 帳戶輸出格式。
    """

    LONG = "LONG"
    SHORT = "SHORT"


@dataclass
class VirtualOrder:
    """虛擬訂單"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float]  # 限價單價格 / 止損止盈觸發價
    status: OrderStatus
    filled_quantity: float = 0.0
    filled_price: float = 0.0
    commission: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    stop_price: Optional[float] = None  # 止損/止盈觸發價
    reduce_only: bool = False
    time_in_force: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'orderId': self.order_id,
            'symbol': self.symbol,
            'side': self.side.value,
            'type': self.order_type.value,
            'origQty': str(self.quantity),
            'executedQty': str(self.filled_quantity),
            'price': str(self.price or 0),
            'avgPrice': str(self.filled_price),
            'status': self.status.value,
            'time': int(self.timestamp.timestamp() * 1000),
            'commission': str(self.commission),
            'reduceOnly': self.reduce_only,
            'timeInForce': self.time_in_force or "",
        }


@dataclass
class VirtualPosition:
    """虛擬倉位"""
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    mark_price: float = 0.0
    unrealized_pnl: float = 0.0
    leverage: int = 1
    margin: float = 0.0
    liquidation_price: float = 0.0
    
    def update_mark_price(self, price: float):
        """更新標記價格和未實現盈虧"""
        self.mark_price = price
        
        if self.side == PositionSide.LONG:
            self.unrealized_pnl = (price - self.entry_price) * self.quantity
        else:  # SHORT
            self.unrealized_pnl = (self.entry_price - price) * self.quantity
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'positionSide': self.side.value,
            'positionAmt': str(self.quantity if self.side == PositionSide.LONG else -self.quantity),
            'entryPrice': str(self.entry_price),
            'markPrice': str(self.mark_price),
            'unRealizedProfit': str(self.unrealized_pnl),
            'leverage': str(self.leverage),
            'isolatedMargin': str(self.margin),
            'liquidationPrice': str(self.liquidation_price),
        }


@dataclass
class TradeRecord:
    """交易記錄"""
    trade_id: str
    order_id: str
    symbol: str
    side: str
    price: float
    quantity: float
    commission: float
    realized_pnl: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tradeId': self.trade_id,
            'orderId': self.order_id,
            'symbol': self.symbol,
            'side': self.side,
            'price': str(self.price),
            'qty': str(self.quantity),
            'commission': str(self.commission),
            'realizedPnl': str(self.realized_pnl),
            'time': int(self.timestamp.timestamp() * 1000),
        }


class VirtualAccount:
    """
    虛擬交易帳戶
    
    完整模擬真實帳戶的所有功能：
    - 帳戶餘額管理
    - 倉位追蹤和更新
    - 訂單撮合引擎
    - 手續費計算 (maker/taker)
    - 滑點模擬
    - 資金費率模擬
    - 保證金和清算計算
    
    費率設定 (模擬 Binance Futures):
    - Maker Fee: 0.02%
    - Taker Fee: 0.04%
    - 滑點: 0.01% ~ 0.05% (根據訂單大小)
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        maker_fee: float = 0.0002,      # 0.02%
        taker_fee: float = 0.0004,      # 0.04%
        slippage_rate: float = 0.0001,  # 0.01% 基礎滑點
        leverage: int = 1,
        margin_call_level: float = 0.8,  # 保證金維持率 80%
        liquidation_level: float = 0.5,  # 強平線 50%
    ):
        """
        初始化虛擬帳戶
        
        Args:
            initial_balance: 初始餘額 (USDT)
            maker_fee: Maker 手續費率
            taker_fee: Taker 手續費率
            slippage_rate: 基礎滑點率
            leverage: 默認槓桿倍數
            margin_call_level: 追加保證金水平
            liquidation_level: 強制平倉水平
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.available_balance = initial_balance
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.slippage_rate = slippage_rate
        self.leverage = leverage
        self.margin_call_level = margin_call_level
        self.liquidation_level = liquidation_level
        
        # 倉位管理 {symbol: VirtualPosition}
        self.positions: Dict[str, VirtualPosition] = {}
        
        # 訂單管理
        self.open_orders: Dict[str, VirtualOrder] = {}  # 未成交訂單
        self.order_history: List[VirtualOrder] = []
        
        # 交易記錄
        self.trade_history: List[TradeRecord] = []
        
        # 統計數據
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_commission': 0.0,
            'total_realized_pnl': 0.0,
            'max_drawdown': 0.0,
            'peak_balance': initial_balance,
        }
        
        # 當前市場價格 {symbol: price}
        self._current_prices: Dict[str, float] = {}
        
        logger.info(f"虛擬帳戶初始化: 餘額 {initial_balance} USDT, 槓桿 {leverage}x")
        logger.info(f"費率: Maker {maker_fee*100:.2f}%, Taker {taker_fee*100:.2f}%")
    
    def update_price(
        self,
        symbol: str,
        price: float,
        high: Optional[float] = None,
        low: Optional[float] = None,
    ):
        """
        更新市場價格 (每根 K線結束時調用)
        
        這會觸發：
        1. 倉位未實現盈虧更新
        2. 止損/止盈訂單檢查
        3. 強平檢查
        """
        self._current_prices[symbol] = price
        
        # 更新倉位盈虧
        if symbol in self.positions:
            self.positions[symbol].update_mark_price(price)
        
        # 檢查掛單撮合 / 觸發訂單
        self._check_trigger_orders(symbol, price, high=high, low=low)
        
        # 檢查是否需要強平
        self._check_liquidation(symbol, price)
        
        # 更新可用餘額
        self._update_available_balance()
    
    def get_price(self, symbol: str) -> float:
        """獲取當前價格"""
        return self._current_prices.get(symbol, 0.0)
    
    def _calculate_slippage(self, quantity: float, price: float, side: OrderSide) -> float:
        """
        計算滑點
        
        滑點模型：
        - 基礎滑點 + 數量影響
        - 大單滑點更大
        """
        # 計算名義價值
        notional = quantity * price
        
        # 數量係數 (大單滑點更大)
        size_factor = 1 + (notional / 100000)  # 每 10 萬美元增加 1
        
        # 實際滑點率
        actual_slippage = self.slippage_rate * size_factor
        
        # 滑點方向：買入時價格變高，賣出時價格變低
        if side == OrderSide.BUY:
            return price * (1 + actual_slippage)
        else:
            return price * (1 - actual_slippage)
    
    def _calculate_commission(self, quantity: float, price: float, is_taker: bool = True) -> float:
        """計算手續費"""
        fee_rate = self.taker_fee if is_taker else self.maker_fee
        return quantity * price * fee_rate
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_price: Optional[float] = None,
        reduce_only: bool = False,
        time_in_force: Optional[str] = None,
    ) -> VirtualOrder:
        """
        下單 - 模擬 Binance 下單接口
        
        Args:
            symbol: 交易對
            side: BUY/SELL
            order_type: MARKET/LIMIT/STOP_MARKET/TAKE_PROFIT_MARKET
            quantity: 數量
            price: 限價單價格
            stop_price: 止損/止盈觸發價
            reduce_only: 是否僅減倉
            time_in_force: 訂單有效期
            
        Returns:
            VirtualOrder: 訂單對象
        """
        order_id = str(uuid.uuid4())[:8].upper()
        order_side = OrderSide(side.upper())
        order_type_enum = OrderType(order_type.upper())
        
        order = VirtualOrder(
            order_id=order_id,
            symbol=symbol,
            side=order_side,
            order_type=order_type_enum,
            quantity=quantity,
            price=price,
            status=OrderStatus.NEW,
            stop_price=stop_price,
            reduce_only=reduce_only,
            time_in_force=time_in_force,
        )

        if quantity <= 0:
            order.status = OrderStatus.REJECTED
            logger.warning(f"⚠️ 訂單拒絕: 無效數量 {quantity} {symbol}")
            self.order_history.append(order)
            return order
        
        # 市價單立即撮合
        if order_type_enum == OrderType.MARKET:
            self._execute_market_order(order)
        
        # 限價單加入掛單列表
        elif order_type_enum == OrderType.LIMIT:
            self.open_orders[order_id] = order
            logger.info(f"📝 限價單掛單: {side} {quantity} {symbol} @ {price}")
        
        # 止損/止盈單加入觸發列表
        elif order_type_enum in [OrderType.STOP_MARKET, OrderType.TAKE_PROFIT_MARKET]:
            self.open_orders[order_id] = order
            logger.info(f"🎯 條件單設置: {side} {quantity} {symbol} 觸發價 {stop_price}")
        
        self.order_history.append(order)
        return order
    
    def _execute_market_order(self, order: VirtualOrder):
        """執行市價單"""
        current_price = self._current_prices.get(order.symbol, 0)
        if current_price <= 0:
            order.status = OrderStatus.REJECTED
            logger.error(f"❌ 訂單拒絕: 無法獲取 {order.symbol} 價格")
            return

        fill_price = self._calculate_slippage(order.quantity, current_price, order.side)
        self._finalize_fill(order, fill_price, is_taker=True)

    def _execute_limit_fill(self, order: VirtualOrder):
        """執行限價單成交。"""
        fill_price = order.price or self._current_prices.get(order.symbol, 0)
        if fill_price <= 0:
            order.status = OrderStatus.REJECTED
            logger.error(f"❌ 限價單拒絕: 無法獲取 {order.symbol} 成交價格")
            return

        self._finalize_fill(order, fill_price, is_taker=False)

    def _finalize_fill(self, order: VirtualOrder, fill_price: float, is_taker: bool):
        """統一處理成交後的帳戶更新。"""
        commission = self._calculate_commission(order.quantity, fill_price, is_taker=is_taker)

        required_margin = (order.quantity * fill_price) / self.leverage
        if required_margin + commission > self.available_balance:
            order.status = OrderStatus.REJECTED
            logger.error(
                f"❌ 訂單拒絕: 餘額不足 (需要 {required_margin + commission:.2f}, 可用 {self.available_balance:.2f})"
            )
            return

        order.filled_quantity = order.quantity
        order.filled_price = fill_price
        order.commission = commission
        order.status = OrderStatus.FILLED

        self.balance -= commission
        self.stats['total_commission'] += commission

        realized_pnl = self._update_position(order)

        trade = TradeRecord(
            trade_id=str(uuid.uuid4())[:8].upper(),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side.value,
            price=fill_price,
            quantity=order.quantity,
            commission=commission,
            realized_pnl=realized_pnl,
            timestamp=datetime.now(),
        )
        self.trade_history.append(trade)
        self.stats['total_trades'] += 1

        if realized_pnl > 0:
            self.stats['winning_trades'] += 1
        elif realized_pnl < 0:
            self.stats['losing_trades'] += 1

        self.stats['total_realized_pnl'] += realized_pnl

        total_equity = self.get_total_equity()
        if total_equity > self.stats['peak_balance']:
            self.stats['peak_balance'] = total_equity
        else:
            drawdown = (self.stats['peak_balance'] - total_equity) / self.stats['peak_balance']
            if drawdown > self.stats['max_drawdown']:
                self.stats['max_drawdown'] = drawdown

        logger.info(
            f"✅ 訂單成交: {order.side.value} {order.quantity} {order.symbol} "
            f"@ {fill_price:.2f} (手續費: {commission:.4f})"
        )
    
    def _update_position(self, order: VirtualOrder) -> float:
        """
        更新倉位
        
        Returns:
            實現盈虧
        """
        symbol = order.symbol
        realized_pnl = 0.0
        
        # 獲取現有倉位
        existing_pos = self.positions.get(symbol)
        
        if existing_pos is None:
            # 開新倉
            if order.side == OrderSide.BUY:
                new_pos = VirtualPosition(
                    symbol=symbol,
                    side=PositionSide.LONG,
                    quantity=order.filled_quantity,
                    entry_price=order.filled_price,
                    mark_price=order.filled_price,
                    leverage=self.leverage,
                    margin=(order.filled_quantity * order.filled_price) / self.leverage
                )
            else:
                new_pos = VirtualPosition(
                    symbol=symbol,
                    side=PositionSide.SHORT,
                    quantity=order.filled_quantity,
                    entry_price=order.filled_price,
                    mark_price=order.filled_price,
                    leverage=self.leverage,
                    margin=(order.filled_quantity * order.filled_price) / self.leverage
                )
            
            self.positions[symbol] = new_pos
            logger.info(f"📈 開倉: {new_pos.side.value} {new_pos.quantity} {symbol} @ {new_pos.entry_price:.2f}")
            
        else:
            # 已有倉位
            is_same_direction = (
                (existing_pos.side == PositionSide.LONG and order.side == OrderSide.BUY) or
                (existing_pos.side == PositionSide.SHORT and order.side == OrderSide.SELL)
            )
            
            if is_same_direction:
                # 加倉 - 計算加權平均入場價
                total_value = existing_pos.quantity * existing_pos.entry_price + order.filled_quantity * order.filled_price
                total_quantity = existing_pos.quantity + order.filled_quantity
                if total_quantity <= 0:
                    logger.warning(f"⚠️ 忽略無效加倉: {symbol} total_quantity={total_quantity}")
                    self._update_available_balance()
                    return realized_pnl
                existing_pos.entry_price = total_value / total_quantity
                existing_pos.quantity = total_quantity
                existing_pos.margin = (total_quantity * existing_pos.entry_price) / self.leverage
                
                logger.info(f"📈 加倉: {existing_pos.side.value} 總數量 {existing_pos.quantity} @ 均價 {existing_pos.entry_price:.2f}")
                
            else:
                # 平倉或反向開倉
                if order.filled_quantity >= existing_pos.quantity:
                    # 全部平倉 (可能有剩餘反向開倉)
                    if existing_pos.side == PositionSide.LONG:
                        realized_pnl = (order.filled_price - existing_pos.entry_price) * existing_pos.quantity
                    else:
                        realized_pnl = (existing_pos.entry_price - order.filled_price) * existing_pos.quantity
                    
                    self.balance += realized_pnl
                    remaining = order.filled_quantity - existing_pos.quantity
                    
                    logger.info(f"📉 平倉: 實現盈虧 {realized_pnl:+.2f} USDT")
                    
                    if remaining > 0:
                        # 反向開倉
                        new_side = PositionSide.SHORT if existing_pos.side == PositionSide.LONG else PositionSide.LONG
                        self.positions[symbol] = VirtualPosition(
                            symbol=symbol,
                            side=new_side,
                            quantity=remaining,
                            entry_price=order.filled_price,
                            mark_price=order.filled_price,
                            leverage=self.leverage,
                            margin=(remaining * order.filled_price) / self.leverage
                        )
                        logger.info(f"📈 反向開倉: {new_side.value} {remaining} @ {order.filled_price:.2f}")
                    else:
                        # 完全平倉
                        del self.positions[symbol]
                else:
                    # 部分平倉
                    if existing_pos.side == PositionSide.LONG:
                        realized_pnl = (order.filled_price - existing_pos.entry_price) * order.filled_quantity
                    else:
                        realized_pnl = (existing_pos.entry_price - order.filled_price) * order.filled_quantity
                    
                    self.balance += realized_pnl
                    existing_pos.quantity -= order.filled_quantity
                    existing_pos.margin = (existing_pos.quantity * existing_pos.entry_price) / self.leverage
                    
                    logger.info(f"📉 部分平倉: {order.filled_quantity} 實現盈虧 {realized_pnl:+.2f} USDT")
        
        self._update_available_balance()
        return realized_pnl
    
    def _check_trigger_orders(
        self,
        symbol: str,
        price: float,
        high: Optional[float] = None,
        low: Optional[float] = None,
    ):
        """檢查觸發訂單 (止損/止盈)"""
        orders_to_execute = []
        
        for order_id, order in list(self.open_orders.items()):
            if order.symbol != symbol:
                continue
            
            if order.status != OrderStatus.NEW:
                continue

            if order.order_type == OrderType.LIMIT and order.price is not None:
                bar_high = high if high is not None else price
                bar_low = low if low is not None else price
                if order.side == OrderSide.BUY and bar_low <= order.price:
                    orders_to_execute.append(order)
                elif order.side == OrderSide.SELL and bar_high >= order.price:
                    orders_to_execute.append(order)

            elif order.order_type == OrderType.STOP_MARKET and order.stop_price:
                # 止損單: 賣出方向價格跌破觸發價，買入方向價格漲破觸發價
                if order.side == OrderSide.SELL and price <= order.stop_price:
                    orders_to_execute.append(order)
                elif order.side == OrderSide.BUY and price >= order.stop_price:
                    orders_to_execute.append(order)
            
            elif order.order_type == OrderType.TAKE_PROFIT_MARKET and order.stop_price:
                # 止盈單: 賣出方向價格漲破觸發價，買入方向價格跌破觸發價
                if order.side == OrderSide.SELL and price >= order.stop_price:
                    orders_to_execute.append(order)
                elif order.side == OrderSide.BUY and price <= order.stop_price:
                    orders_to_execute.append(order)
        
        # 執行觸發的訂單
        for order in orders_to_execute:
            if order.order_type == OrderType.LIMIT:
                logger.info(
                    f"📌 限價單成交: {order.side.value} {order.symbol} @ {order.price:.2f}"
                )
                self._execute_limit_fill(order)
            else:
                logger.info(f"🎯 觸發條件單: {order.order_type.value} {order.side.value} @ {price:.2f}")
                self._execute_market_order(order)
            del self.open_orders[order.order_id]
    
    def _check_liquidation(self, symbol: str, price: float):
        """檢查是否需要強平"""
        if symbol not in self.positions:
            return
        
        pos = self.positions[symbol]
        
        # 計算清算價格 (簡化版)
        if pos.side == PositionSide.LONG:
            liq_price = pos.entry_price * (1 - 1 / self.leverage * self.liquidation_level)
            if price <= liq_price:
                logger.warning(f"⚠️ 強制平倉觸發! {symbol} 價格 {price:.2f} <= 清算價 {liq_price:.2f}")
                self._liquidate_position(symbol)
        else:
            liq_price = pos.entry_price * (1 + 1 / self.leverage * self.liquidation_level)
            if price >= liq_price:
                logger.warning(f"⚠️ 強制平倉觸發! {symbol} 價格 {price:.2f} >= 清算價 {liq_price:.2f}")
                self._liquidate_position(symbol)
    
    def _liquidate_position(self, symbol: str):
        """強制平倉"""
        pos = self.positions.get(symbol)
        if not pos:
            return
        
        # 以當前價格強平
        current_price = self._current_prices.get(symbol, pos.mark_price)
        
        # 計算虧損
        if pos.side == PositionSide.LONG:
            loss = (pos.entry_price - current_price) * pos.quantity
        else:
            loss = (current_price - pos.entry_price) * pos.quantity
        
        # 扣除損失 (加上清算手續費)
        liquidation_fee = pos.margin * 0.05  # 5% 清算手續費
        total_loss = loss + liquidation_fee
        
        self.balance -= total_loss
        self.stats['total_commission'] += liquidation_fee
        
        logger.error(f"💀 強制平倉完成: {symbol} 損失 {total_loss:.2f} USDT")
        
        # 刪除倉位
        del self.positions[symbol]
        
        # 取消相關訂單
        self._cancel_symbol_orders(symbol)
        
        self._update_available_balance()
    
    def _cancel_symbol_orders(self, symbol: str):
        """取消某個交易對的所有掛單"""
        orders_to_cancel = [
            order_id for order_id, order in self.open_orders.items()
            if order.symbol == symbol
        ]
        for order_id in orders_to_cancel:
            self.open_orders[order_id].status = OrderStatus.CANCELED
            del self.open_orders[order_id]
    
    def _update_available_balance(self):
        """更新可用餘額"""
        # 計算已用保證金
        used_margin = sum(pos.margin for pos in self.positions.values())
        
        # 計算未實現盈虧
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        # 可用餘額 = 餘額 + 未實現盈虧 - 已用保證金
        self.available_balance = self.balance + unrealized_pnl - used_margin
    
    def get_balance(self) -> float:
        """獲取餘額"""
        return self.balance
    
    def get_available_balance(self) -> float:
        """獲取可用餘額"""
        self._update_available_balance()
        return self.available_balance
    
    def get_total_equity(self) -> float:
        """獲取總權益 (餘額 + 未實現盈虧)"""
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        return self.balance + unrealized_pnl
    
    def get_position(self, symbol: str) -> Optional[VirtualPosition]:
        """獲取指定交易對的倉位"""
        return self.positions.get(symbol)

    def has_open_position(self, symbol: str) -> bool:
        """是否存在非零倉位。"""
        position = self.positions.get(symbol)
        return position is not None and position.quantity > 0

    def get_position_snapshot(self, symbol: str) -> Optional[Dict[str, Any]]:
        """回傳指定交易對的倉位快照。"""
        position = self.get_position(symbol)
        return position.to_dict() if position else None
    
    def get_all_positions(self) -> List[VirtualPosition]:
        """獲取所有倉位"""
        return list(self.positions.values())

    def get_open_orders(
        self,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        reduce_only: Optional[bool] = None,
    ) -> List[VirtualOrder]:
        """查詢未成交掛單。"""
        orders: List[VirtualOrder] = []
        normalized_side = side.upper() if side else None

        for order in self.open_orders.values():
            if symbol and order.symbol != symbol:
                continue
            if normalized_side and order.side.value != normalized_side:
                continue
            if reduce_only is not None and order.reduce_only != reduce_only:
                continue
            orders.append(order)

        return orders

    def has_pending_entry_order(self, symbol: str, side: Optional[str] = None) -> bool:
        """是否存在未成交的開倉掛單。"""
        return bool(
            self.get_open_orders(symbol=symbol, side=side, reduce_only=False)
        )

    def get_open_orders_snapshot(
        self,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        reduce_only: Optional[bool] = None,
    ) -> List[Dict[str, Any]]:
        """回傳掛單快照列表。"""
        return [
            order.to_dict()
            for order in self.get_open_orders(symbol=symbol, side=side, reduce_only=reduce_only)
        ]

    def get_account_snapshot(self) -> Dict[str, Any]:
        """提供 trading 層使用的帳戶狀態快照。"""
        self._update_available_balance()
        unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        used_margin = sum(pos.margin for pos in self.positions.values())
        return {
            "balance": self.balance,
            "available_balance": self.available_balance,
            "total_equity": self.get_total_equity(),
            "unrealized_pnl": unrealized_pnl,
            "used_margin": used_margin,
            "open_orders_count": len(self.open_orders),
            "positions_count": len(self.positions),
        }
    
    def get_account_info(self) -> Dict[str, Any]:
        """
        獲取帳戶信息 - 模擬 Binance API 返回格式
        """
        positions_data = []
        for pos in self.positions.values():
            positions_data.append(pos.to_dict())
        
        assets = [{
            'asset': 'USDT',
            'walletBalance': str(self.balance),
            'availableBalance': str(self.available_balance),
            'unrealizedProfit': str(sum(p.unrealized_pnl for p in self.positions.values())),
            'marginBalance': str(self.get_total_equity()),
        }]
        
        return {
            'totalWalletBalance': str(self.balance),
            'availableBalance': str(self.available_balance),
            'totalUnrealizedProfit': str(sum(p.unrealized_pnl for p in self.positions.values())),
            'totalMarginBalance': str(self.get_total_equity()),
            'assets': assets,
            'positions': positions_data,
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取統計數據"""
        win_rate = (
            self.stats['winning_trades'] / self.stats['total_trades'] * 100
            if self.stats['total_trades'] > 0 else 0
        )
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_equity': self.get_total_equity(),
            'total_return': (self.get_total_equity() - self.initial_balance) / self.initial_balance * 100,
            'total_trades': self.stats['total_trades'],
            'winning_trades': self.stats['winning_trades'],
            'losing_trades': self.stats['losing_trades'],
            'win_rate': win_rate,
            'total_commission': self.stats['total_commission'],
            'total_realized_pnl': self.stats['total_realized_pnl'],
            'max_drawdown': self.stats['max_drawdown'] * 100,
            'peak_balance': self.stats['peak_balance'],
        }
    
    def cancel_order(self, order_id: str) -> bool:
        """取消訂單"""
        if order_id in self.open_orders:
            self.open_orders[order_id].status = OrderStatus.CANCELED
            del self.open_orders[order_id]
            logger.info(f"❌ 訂單已取消: {order_id}")
            return True
        return False
    
    def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """取消所有訂單"""
        count = 0
        orders_to_cancel = []
        
        for order_id, order in self.open_orders.items():
            if symbol is None or order.symbol == symbol:
                orders_to_cancel.append(order_id)
        
        for order_id in orders_to_cancel:
            self.cancel_order(order_id)
            count += 1
        
        return count
    
    def reset(self):
        """重置帳戶"""
        self.balance = self.initial_balance
        self.available_balance = self.initial_balance
        self.positions.clear()
        self.open_orders.clear()
        self.order_history.clear()
        self.trade_history.clear()
        self._current_prices.clear()
        
        self.stats = {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_commission': 0.0,
            'total_realized_pnl': 0.0,
            'max_drawdown': 0.0,
            'peak_balance': self.initial_balance,
        }
        
        logger.info(f"🔄 帳戶已重置: 餘額 {self.initial_balance} USDT")
