"""
方向變化策略 (Direction Change Strategy)
=========================================

核心理念：
使用事件驅動的 DC (Direction Change) 算法，以價格方向變化事件作為市場分析基礎，
而非傳統固定時間序列方法。

DC 算法原理：
- 定義閾值 θ（如 0.5%）
- 當價格從前低點上漲 θ 時，觸發「上升DC事件」(Upward DC Event)
- 當價格從前高點下跌 θ 時，觸發「下降DC事件」(Downward DC Event)
- DC 事件之間的區域稱為「超越區域」(Overshoot, OS)

交易邏輯：
1. 確認連續 DC 事件方向形成趨勢
2. 在 OS 回調/反彈合適位置進場（逆 OS、順 DC）
3. 止損設在前 DC 極值（底部/頂部）
4. 獲利目標：2R / 4R / 6R

優勢：
- 過濾短期噪音，聚焦真實趨勢轉折
- 自適應市場波動（θ 可動態調整）
- 比固定時間框架更早發現趨勢反轉

創建日期：2026-03-09
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .base_strategy import (
    BaseStrategy,
    MarketCondition,
    PositionManagement,
    RiskParameters,
    SignalStrength,
    StrategyRegistry,
    StrategyState,
    TradeExecution,
    TradeSetup,
)

logger = logging.getLogger(__name__)


class DCEventType(Enum):
    """DC 事件類型"""
    UPWARD = "upward"
    DOWNWARD = "downward"


@dataclass
class DCEvent:
    """單個 DC 事件"""
    event_type: DCEventType
    trigger_price: float      # 觸發 DC 的價格
    extreme_price: float      # 前一個極值（高點或低點）
    index: int                # 在數據中的位置（相對索引）
    os_length: int = 0        # 本次 OS 持續 K 線數
    os_return: float = 0.0    # 本次 OS 回報率


@dataclass
class DCStrategyAnalysis:
    """DC 策略分析結果"""
    current_dc_direction: str = "neutral"   # 'up', 'down', 'neutral'
    last_dc_extreme: float = 0.0
    last_dc_trigger: float = 0.0
    bars_since_dc: int = 0

    in_overshoot: bool = False
    os_retracement_pct: float = 0.0         # OS 回撤百分比（0-1）
    current_os_return: float = 0.0          # 當前 OS 延伸幅度

    consecutive_up_dc: int = 0
    consecutive_down_dc: int = 0
    dc_trend_strength: float = 0.0          # DC 趨勢強度（0-100）

    recent_dc_events: List[DCEvent] = field(default_factory=list)
    avg_os_length: float = 0.0
    avg_dc_amplitude: float = 0.0           # 平均 DC 振幅（%）
    dc_volatility: float = 0.0              # DC 波動率


class DirectionChangeStrategy(BaseStrategy):
    """
    方向變化策略 (Direction Change Strategy)

    基於事件驅動的 DC 算法：
    - 識別價格方向轉換事件（而非時間序列信號）
    - 在 OS 區域的回調/反彈中進場
    - 以 DC 極值作為止損參考
    """

    def __init__(
        self,
        timeframe: str = "1h",
        dc_threshold: float = 0.003,     # 0.3%
        risk_params: Optional[RiskParameters] = None,
    ):
        super().__init__(
            name="Direction Change",
            timeframe=timeframe,
            risk_params=risk_params or RiskParameters(
                max_risk_per_trade_pct=1.0,
                min_risk_reward_ratio=2.0,
                trailing_stop_activation=1.5,
                trailing_stop_distance=0.6,
                max_holding_period_hours=72,
            ),
        )
        self.dc_threshold = dc_threshold
        self.min_consecutive_dc = 1
        self.os_entry_min_retracement = 0.15   # OS 最少回撤 15%
        self.os_entry_max_retracement = 0.85   # OS 超過 85% 視為趨勢可能反轉
        self.lookback_bars = 200
        self.required_confirmations = 3
        self.atr_period = 14
        self.take_profit_r_multiples = [2.0, 4.0, 6.0]
        self.exit_portions = [0.35, 0.35, 0.30]

    # ========================
    # DC 核心算法
    # ========================

    def _detect_dc_events(self, close: np.ndarray) -> List[DCEvent]:
        """
        偵測 DC 事件序列

        從頭到尾掃描價格，當偏離當前極值達到閾值時觸發 DC 事件。
        """
        if len(close) < 10:
            return []

        events: List[DCEvent] = []
        direction = 'up' if close[1] >= close[0] else 'down'
        extreme = float(close[0])
        last_dc_index = 0

        for i in range(1, len(close)):
            price = float(close[i])

            if direction == 'up':
                if price > extreme:
                    extreme = price
                elif extreme > 0 and (extreme - price) / extreme >= self.dc_threshold:
                    events.append(DCEvent(
                        event_type=DCEventType.DOWNWARD,
                        trigger_price=price,
                        extreme_price=extreme,
                        index=i,
                        os_length=i - last_dc_index,
                        os_return=(price - extreme) / extreme,
                    ))
                    direction = 'down'
                    extreme = price
                    last_dc_index = i
            else:
                if price < extreme:
                    extreme = price
                elif extreme > 0 and (price - extreme) / extreme >= self.dc_threshold:
                    events.append(DCEvent(
                        event_type=DCEventType.UPWARD,
                        trigger_price=price,
                        extreme_price=extreme,
                        index=i,
                        os_length=i - last_dc_index,
                        os_return=(price - extreme) / extreme,
                    ))
                    direction = 'up'
                    extreme = price
                    last_dc_index = i

        return events

    def _count_consecutive_dc(
        self, events: List[DCEvent], event_type: DCEventType
    ) -> int:
        """從最近一個事件起算，連續相同類型的 DC 事件數"""
        count = 0
        for event in reversed(events):
            if event.event_type == event_type:
                count += 1
            else:
                break
        return count

    def _calculate_atr(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
    ) -> float:
        """計算 ATR（平均真實波幅）"""
        n = len(close)
        if n < self.atr_period + 1:
            return float(np.mean(high[-5:] - low[-5:]))
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1]),
            ),
        )
        return float(np.mean(tr[-self.atr_period:]))

    def _analyze_os_state(
        self,
        close: np.ndarray,
        last_dc_event: DCEvent,
    ) -> Dict[str, float]:
        """分析當前 OS（超越區域）狀態"""
        current_price = float(close[-1])
        trigger_price = last_dc_event.trigger_price
        extreme_price = last_dc_event.extreme_price
        event_close = close[last_dc_event.index:]

        if last_dc_event.event_type == DCEventType.UPWARD:
            os_high = float(np.max(event_close))
            os_extension = (os_high - trigger_price) / trigger_price if trigger_price > 0 else 0.0
            denom = os_high - extreme_price
            os_retracement = (os_high - current_price) / denom if denom > 0 else 0.0
        else:
            os_low = float(np.min(event_close))
            os_extension = (trigger_price - os_low) / trigger_price if trigger_price > 0 else 0.0
            denom = extreme_price - os_low
            os_retracement = (current_price - os_low) / denom if denom > 0 else 0.0

        return {
            'os_extension': float(os_extension),
            'os_retracement': float(max(0.0, min(1.0, os_retracement))),
        }

    # ========================
    # 1. 市場分析
    # ========================

    def analyze_market(
        self,
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """分析市場 — 基於 DC 事件"""
        self.state = StrategyState.ANALYZING

        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        close = ohlcv_data[:, 4]
        current_price = float(close[-1])

        use_close = close[-self.lookback_bars:]
        dc_events = self._detect_dc_events(use_close)

        analysis = DCStrategyAnalysis(recent_dc_events=dc_events)
        atr = self._calculate_atr(high, low, close)

        if dc_events:
            last_event = dc_events[-1]
            analysis.last_dc_extreme = last_event.extreme_price
            analysis.last_dc_trigger = last_event.trigger_price
            analysis.bars_since_dc = len(use_close) - last_event.index - 1

            if last_event.event_type == DCEventType.UPWARD:
                analysis.current_dc_direction = 'up'
                analysis.consecutive_up_dc = self._count_consecutive_dc(
                    dc_events, DCEventType.UPWARD
                )
            else:
                analysis.current_dc_direction = 'down'
                analysis.consecutive_down_dc = self._count_consecutive_dc(
                    dc_events, DCEventType.DOWNWARD
                )

            consecutive = max(analysis.consecutive_up_dc, analysis.consecutive_down_dc)
            analysis.dc_trend_strength = min(100.0, consecutive * 25.0)

            if analysis.bars_since_dc > 0:
                os_metrics = self._analyze_os_state(use_close, last_event)
                analysis.in_overshoot = True
                analysis.os_retracement_pct = os_metrics['os_retracement']
                analysis.current_os_return = os_metrics['os_extension']

            if len(dc_events) >= 2:
                os_lengths = [e.os_length for e in dc_events[-5:]]
                analysis.avg_os_length = float(np.mean(os_lengths))
                amplitudes = [abs(e.os_return) for e in dc_events[-5:]]
                analysis.avg_dc_amplitude = float(np.mean(amplitudes)) * 100.0

        analysis.dc_volatility = atr / current_price * 100.0 if current_price > 0 else 0.0

        self._finalize_analysis_state()
        self._last_analysis_time = datetime.now()

        symbol = (additional_data or {}).get("symbol")
        return self._build_analysis_result(analysis, current_price, atr, symbol)

    def _build_analysis_result(
        self,
        analysis: DCStrategyAnalysis,
        current_price: float,
        atr: float,
        symbol: Optional[str] = None,
    ) -> Dict[str, Any]:
        """組裝分析結果字典"""
        if analysis.current_dc_direction == 'up':
            if analysis.dc_trend_strength >= 75:
                market_condition = MarketCondition.STRONG_UPTREND
            else:
                market_condition = MarketCondition.UPTREND
        elif analysis.current_dc_direction == 'down':
            if analysis.dc_trend_strength >= 75:
                market_condition = MarketCondition.STRONG_DOWNTREND
            else:
                market_condition = MarketCondition.DOWNTREND
        else:
            market_condition = MarketCondition.SIDEWAYS

        consecutive = max(analysis.consecutive_up_dc, analysis.consecutive_down_dc)
        return {
            'symbol': symbol,
            'market_condition': market_condition,
            'trend_direction': analysis.current_dc_direction,
            'trend_strength': analysis.dc_trend_strength,
            'volatility': 'high' if analysis.dc_volatility > 2.0 else 'normal',
            'key_levels': {
                'dc_extreme': analysis.last_dc_extreme,
                'dc_trigger': analysis.last_dc_trigger,
                'current_price': current_price,
            },
            'dc_analysis': analysis,
            'atr': atr,
            'current_price': current_price,
            'analysis_summary': (
                f"DC方向: {analysis.current_dc_direction.upper()}, "
                f"連續DC數: {consecutive}, "
                f"趨勢強度: {analysis.dc_trend_strength:.0f}%, "
                f"OS回撤: {analysis.os_retracement_pct:.1%}"
            ),
        }

    # ========================
    # 2. 入場條件評估
    # ========================

    def evaluate_entry_conditions(
        self,
        market_analysis: Dict[str, Any],
        ohlcv_data: np.ndarray,
    ) -> Optional[TradeSetup]:
        """
        DC 策略入場條件：
        1. 有連續同向 DC 事件（趨勢確認）
        2. 當前在 OS 回調/反彈的合適位置（30-80%）
        3. DC 趨勢強度 >= 25
        4. 風險回報比 >= min_risk_reward_ratio
        """
        dc_analysis: Optional[DCStrategyAnalysis] = market_analysis.get('dc_analysis')
        if dc_analysis is None:
            return None

        current_price = market_analysis['current_price']
        atr = market_analysis.get('atr', 0.0)
        if atr == 0.0 or current_price == 0.0:
            return None

        direction = dc_analysis.current_dc_direction
        consecutive = max(dc_analysis.consecutive_up_dc, dc_analysis.consecutive_down_dc)

        if consecutive < self.min_consecutive_dc:
            return None
        if not dc_analysis.in_overshoot:
            return None
        os_ret = dc_analysis.os_retracement_pct
        if not (self.os_entry_min_retracement <= os_ret <= self.os_entry_max_retracement):
            return None
        if dc_analysis.dc_trend_strength < 25.0:
            return None

        if direction == 'up':
            trade_direction = 'long'
            stop_loss = dc_analysis.last_dc_extreme * 0.998
            risk_amount = abs(current_price - stop_loss)
            if risk_amount == 0.0:
                return None
            tp1 = current_price + risk_amount * self.take_profit_r_multiples[0]
            tp2 = current_price + risk_amount * self.take_profit_r_multiples[1]
            tp3 = current_price + risk_amount * self.take_profit_r_multiples[2]
        elif direction == 'down':
            trade_direction = 'short'
            stop_loss = dc_analysis.last_dc_extreme * 1.002
            risk_amount = abs(current_price - stop_loss)
            if risk_amount == 0.0:
                return None
            tp1 = current_price - risk_amount * self.take_profit_r_multiples[0]
            tp2 = current_price - risk_amount * self.take_profit_r_multiples[1]
            tp3 = current_price - risk_amount * self.take_profit_r_multiples[2]
        else:
            return None

        risk_reward = abs(tp1 - current_price) / risk_amount
        if risk_reward < self.risk_params.min_risk_reward_ratio:
            return None

        if consecutive >= 4 and dc_analysis.dc_trend_strength >= 75:
            signal_strength = SignalStrength.VERY_STRONG
        elif consecutive >= 3 and dc_analysis.dc_trend_strength >= 50:
            signal_strength = SignalStrength.STRONG
        elif consecutive >= 2:
            signal_strength = SignalStrength.MODERATE
        else:
            signal_strength = SignalStrength.WEAK

        confirmations = 0
        if consecutive >= self.min_consecutive_dc:
            confirmations += 1
        if dc_analysis.in_overshoot:
            confirmations += 1
        if self.os_entry_min_retracement <= os_ret <= self.os_entry_max_retracement:
            confirmations += 1
        if dc_analysis.dc_trend_strength >= 50.0:
            confirmations += 1

        symbol = market_analysis.get('symbol')
        if not symbol:
            raise ValueError("市場分析必須包含 'symbol' 字段，不再支持預設幣種")

        return TradeSetup(
            symbol=symbol,
            direction=trade_direction,
            entry_price=current_price,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            risk_amount=risk_amount,
            risk_reward_ratio=risk_reward,
            signal_strength=signal_strength,
            market_condition=market_analysis['market_condition'],
            entry_conditions=[
                f"連續 {consecutive} 次 {direction.upper()} DC 事件",
                f"OS 回撤: {os_ret:.1%}",
                f"DC 趨勢強度: {dc_analysis.dc_trend_strength:.0f}%",
            ],
            entry_confirmations=confirmations,
            required_confirmations=self.required_confirmations,
            valid_until=datetime.now() + timedelta(hours=4),
            key_levels={
                'dc_extreme': dc_analysis.last_dc_extreme,
                'dc_trigger': dc_analysis.last_dc_trigger,
            },
        )

    # ========================
    # 3. 執行入場
    # ========================

    def execute_entry(
        self,
        setup: TradeSetup,
        connector: Any,
    ) -> Optional[TradeExecution]:
        """執行入場"""
        try:
            portion_size = setup.total_position_size
            if portion_size <= 0:
                logger.warning(f"[DC策略] 忽略無效進場數量: {portion_size}")
                return None

            execution = TradeExecution(
                trade_id=f"DC_{uuid.uuid4().hex[:8]}",
                setup=setup,
                actual_entry_price=setup.entry_price,
                entry_time=datetime.now(),
                current_position_size=portion_size,
                average_entry_price=setup.entry_price,
                highest_price_since_entry=setup.entry_price,
                lowest_price_since_entry=setup.entry_price,
            )

            if connector is None:
                execution.entry_fills.append(
                    {
                        'price': setup.entry_price,
                        'size': portion_size,
                        'time': datetime.now().isoformat(),
                        'type': 'market',
                    }
                )
            else:
                order_result = connector.place_order(
                    symbol=setup.symbol,
                    side='BUY' if setup.direction == 'long' else 'SELL',
                    order_type='MARKET',
                    quantity=portion_size,
                )
                if order_result.get('status') not in ['FILLED', 'PARTIALLY_FILLED']:
                    return None

                fill_price = float(order_result.get('avgPrice', setup.entry_price))
                execution.actual_entry_price = fill_price
                execution.entry_slippage = abs(fill_price - setup.entry_price)
                execution.current_position_size = portion_size
                execution.average_entry_price = fill_price
                execution.highest_price_since_entry = fill_price
                execution.lowest_price_since_entry = fill_price
                execution.entry_fills.append(
                    {
                        'order_id': order_result.get('orderId'),
                        'price': fill_price,
                        'size': portion_size,
                        'time': datetime.now().isoformat(),
                        'type': 'market',
                    }
                )

            self.state = StrategyState.POSITION_OPEN
            logger.info(
                f"[DC策略] 入場: {setup.direction.upper()} @ {execution.actual_entry_price:.2f}, "
                f"SL: {setup.stop_loss:.2f}, TP1: {setup.take_profit_1:.2f}"
            )
            return execution
        except Exception as e:
            logger.error(f"[DC策略] 入場失敗: {e}")
            return None

    # ========================
    # 4. 倉位管理
    # ========================

    def manage_position(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> PositionManagement:
        """管理倉位 — 移至保本、分批出場、追蹤止損"""
        mgmt = PositionManagement(current_stop_loss=trade.setup.stop_loss)

        if trade.setup.direction == 'long':
            trade.highest_price_since_entry = max(
                trade.highest_price_since_entry, current_price
            )
        else:
            trade.lowest_price_since_entry = min(
                trade.lowest_price_since_entry, current_price
            )

        r_multiple = trade.calculate_r_multiple()
        if r_multiple >= 1.0 and not mgmt.stop_loss_moved_to_breakeven:
            mgmt.stop_loss_moved_to_breakeven = True
            mgmt.current_stop_loss = trade.setup.entry_price
            logger.info(f"[DC策略] 止損移至保本 @ {trade.setup.entry_price:.2f}")

        if not mgmt.tp1_filled:
            if (trade.setup.direction == 'long' and current_price >= trade.setup.take_profit_1) or \
               (trade.setup.direction == 'short' and current_price <= trade.setup.take_profit_1):
                mgmt.tp1_filled = True
                mgmt.scaling_out_in_progress = True

        new_stop = self.update_trailing_stop(trade, current_price)
        if new_stop is not None:
            mgmt.stop_loss_trailing = True
            mgmt.current_stop_loss = new_stop

        return mgmt

    # ========================
    # 5. 出場條件評估
    # ========================

    def evaluate_exit_conditions(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> Tuple[bool, str]:
        """
        出場條件：
        1. 觸及止損
        2. 觸及 TP3
        3. 偵測到反向 DC 事件
        4. 超過持倉時限
        """
        setup = trade.setup
        effective_stop = trade.trailing_stop_price or setup.stop_loss

        if setup.direction == 'long' and current_price <= effective_stop:
            return True, f"觸及止損 {effective_stop:.2f}"
        if setup.direction == 'short' and current_price >= effective_stop:
            return True, f"觸及止損 {effective_stop:.2f}"

        if setup.direction == 'long' and current_price >= setup.take_profit_3:
            return True, f"觸及 TP3 {setup.take_profit_3:.2f}"
        if setup.direction == 'short' and current_price <= setup.take_profit_3:
            return True, f"觸及 TP3 {setup.take_profit_3:.2f}"

        # 反向 DC 偵測（掃描最近 20 根）
        recent_close = ohlcv_data[-20:, 4]
        recent_events = self._detect_dc_events(recent_close)
        if recent_events:
            last_event = recent_events[-1]
            if setup.direction == 'long' and last_event.event_type == DCEventType.DOWNWARD:
                return True, f"反向 DC 下降事件 @ {last_event.trigger_price:.2f}"
            if setup.direction == 'short' and last_event.event_type == DCEventType.UPWARD:
                return True, f"反向 DC 上升事件 @ {last_event.trigger_price:.2f}"

        time_exit, time_reason = self.check_time_based_exit(trade)
        if time_exit:
            return True, time_reason

        return False, ""

    # ========================
    # 6. 執行出場
    # ========================

    def execute_exit(
        self,
        trade: TradeExecution,
        reason: str,
        connector: Any,
        partial_exit: bool = False,
        exit_portion: float = 1.0,
    ) -> bool:
        """執行出場"""
        try:
            exit_size = trade.current_position_size * exit_portion
            if exit_size <= 0:
                logger.warning(f"[DC策略] 忽略無效出場數量: {exit_size}")
                return False

            if connector is None:
                fill_price = trade.average_exit_price or trade.setup.entry_price
                if trade.setup.direction == 'long':
                    pnl = (fill_price - trade.average_entry_price) * exit_size
                else:
                    pnl = (trade.average_entry_price - fill_price) * exit_size
                trade.average_exit_price = fill_price
                trade.realized_pnl += pnl
                trade.current_position_size -= exit_size
                trade.exit_fills.append(
                    {
                        'price': fill_price,
                        'size': exit_size,
                        'time': datetime.now().isoformat(),
                        'reason': reason,
                    }
                )
            else:
                order_result = connector.place_order(
                    symbol=trade.setup.symbol,
                    side='SELL' if trade.setup.direction == 'long' else 'BUY',
                    order_type='MARKET',
                    quantity=exit_size,
                    reduce_only=True,
                )
                if order_result.get('status') not in ['FILLED', 'PARTIALLY_FILLED']:
                    return False

                fill_price = float(order_result.get('avgPrice', 0))
                trade.average_exit_price = fill_price
                if trade.setup.direction == 'long':
                    pnl = (fill_price - trade.average_entry_price) * exit_size
                else:
                    pnl = (trade.average_entry_price - fill_price) * exit_size

                trade.realized_pnl += pnl
                trade.current_position_size -= exit_size
                trade.exit_fills.append(
                    {
                        'order_id': order_result.get('orderId'),
                        'price': fill_price,
                        'size': exit_size,
                        'time': datetime.now().isoformat(),
                        'reason': reason,
                    }
                )

            if trade.current_position_size <= 0:
                trade.exit_reason = reason
                trade.exit_time = datetime.now()
                trade.holding_duration = trade.exit_time - trade.entry_time
                self.state = StrategyState.IDLE
                self.performance.update(trade)
                self.trade_history.append(trade)
                logger.info(
                    f"[DC策略] 出場: {reason}, "
                    f"PnL: {trade.realized_pnl:.2f}, "
                    f"R倍數: {trade.calculate_r_multiple():.2f}"
                )
                if "止損" in reason:
                    self._cooldown_until = datetime.now() + timedelta(
                        hours=self.risk_params.cooldown_after_loss
                    )
            return True
        except Exception as e:
            logger.error(f"[DC策略] 出場失敗: {e}")
            return False


StrategyRegistry.register("direction_change", DirectionChangeStrategy)
