"""
突破交易策略 (Breakout Trading Strategy)
========================================

核心理念：
捕捉價格突破關鍵位後的強勁動能。

適用場景：
- 盤整後的突破
- 關鍵支撐/阻力位突破
- 高波動環境

策略邏輯：
1. 識別關鍵價格區間（盤整區）
2. 監測突破信號（放量突破）
3. 確認突破有效性（回踩測試）
4. 順勢進場，設置止損

技術指標：
- 布林帶突破
- ATR 波動率確認
- 成交量驗證
- 價格行為分析
"""

import numpy as np
import logging
from typing import Optional, Dict, Any, Tuple, Union, List, cast
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import uuid

from .base_strategy import (
    BaseStrategy,
    TradeSetup,
    TradeExecution,
    PositionManagement,
    RiskParameters,
    StrategyState,
    SignalStrength,
    MarketCondition,
    StrategyRegistry,
)

logger = logging.getLogger(__name__)


@dataclass
class RangeAnalysis:
    """"""
    range_high: float = 0.0
    range_low: float = 0.0
    range_size: float = 0.0
    range_percent: float = 0.0
    range_duration_bars: int = 0
    
    # 
    breakout_detected: bool = False
    breakout_direction: str = "none"  # 'up', 'down', 'none'
    breakout_strength: float = 0.0  #  ATR 
    
    # 
    channel_upper: float = 0.0
    channel_lower: float = 0.0
    
    # 
    pivot_point: float = 0.0
    resistance_1: float = 0.0
    resistance_2: float = 0.0
    support_1: float = 0.0
    support_2: float = 0.0


@dataclass
class BreakoutAnalysis:
    """突破分析數據結構"""
    # 價格區間分析
    range_analysis: RangeAnalysis = field(default_factory=RangeAnalysis)
    
    # 支撐阻力位
    support_level: float = 0.0
    resistance_level: float = 0.0
    
    # ATR波動率
    atr: float = 0.0
    atr_ma: float = 0.0  # ATR移動平均
    volatility_expanding: bool = False
    
    # 壓縮狀態
    squeeze_on: bool = False
    squeeze_releasing: bool = False
    squeeze_duration: int = 0
    
    # 成交量分析
    volume_breakout: bool = False
    volume_ratio: float = 1.0
    volume_spike: bool = False
    
    # 動量分析
    momentum: float = 0.0
    momentum_confirming: bool = False
    momentum_strength: float = 0.0
    
    # 突破強度
    breakout_strength: float = 0.0
    volatility_spike: bool = False
    
    # 燭形分析
    strong_close: bool = False  # 強勢收盤：收在區間上/下1/3
    wide_range_bar: bool = False  # 寬幅震盪
    
    # 回踩測試
    retest_completed: bool = False
    retest_held: bool = False


class BreakoutTradingStrategy(BaseStrategy):
    """
    
    
    
    1. 
    2. 
    3. 
    4. 
    """
    
    def __init__(
        self,
        timeframe: str = "1h",
        risk_params: Optional[RiskParameters] = None,
    ):
        super().__init__(
            name="Breakout Trading",
            timeframe=timeframe,
            risk_params=risk_params or RiskParameters(
                max_risk_per_trade_pct=1.0,
                min_risk_reward_ratio=2.5,
                trailing_stop_activation=2.0,
                trailing_stop_distance=0.8,
                max_holding_period_hours=120,  # 5 
            ),
        )
        
        # 
        self.range_lookback = 20  # 
        self.range_threshold = 0.05  # 
        self.min_range_bars = 10  #  K 
        
        # 
        self.breakout_threshold = 0.5  #  0.5 ATR
        self.close_threshold = 0.8  #  80%
        self.volume_threshold = 1.5  #  1.5 
        
        # 
        self.bb_period = 20
        self.bb_std = 2.0
        self.kc_period = 20
        self.kc_atr_mult = 1.5
        
        # 動量週期
        self.momentum_period = 10
        
        # 確認閾值設置
        self.required_confirmations = 3
        self.min_confirmations = 2
        self.breakeven_r_multiple = 1.0
        self.trailing_start_r_multiple = 2.0
        self.trailing_stop_percentage = 0.02
        
        # 
        self.take_profit_r_multiples = [2.5, 4.0, 6.0]
        self.exit_portions = [0.35, 0.35, 0.30]
    
    # ========================
    # 
    # ========================
    
    def _calculate_atr(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """ ATR"""
        n = len(close)
        tr = np.zeros(n)
        atr = np.zeros(n)
        
        for i in range(1, n):
            h_l = high[i] - low[i]
            h_pc = abs(high[i] - close[i - 1])
            l_pc = abs(low[i] - close[i - 1])
            tr[i] = max(h_l, h_pc, l_pc)
        
        if n >= period:
            atr[period - 1] = np.mean(tr[1:period])
            for i in range(period, n):
                atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        
        return cast(np.ndarray, atr)
    
    def _identify_range(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        lookback: int = 20
    ) -> RangeAnalysis:
        """"""
        analysis = RangeAnalysis()
        
        if len(close) < lookback:
            return analysis
        
        #  lookback  K 
        recent_high = high[-lookback:]
        recent_low = low[-lookback:]
        
        range_high: float = float(np.max(recent_high))
        range_low: float = float(np.min(recent_low))
        range_size = range_high - range_low
        mid_price = (range_high + range_low) / 2
        
        analysis.range_high = range_high
        analysis.range_low = range_low
        analysis.range_size = range_size
        analysis.range_percent = range_size / mid_price * 100
        
        # 
        # 
        tolerance = range_size * 0.1
        range_start = 0
        for i in range(len(close) - 1, -1, -1):
            if close[i] > range_high + tolerance or close[i] < range_low - tolerance:
                range_start = i + 1
                break
        analysis.range_duration_bars = len(close) - range_start
        
        # 
        analysis.channel_upper = range_high
        analysis.channel_lower = range_low
        
        # /
        analysis.pivot_point = (range_high + range_low + close[-1]) / 3
        analysis.resistance_1 = 2 * analysis.pivot_point - range_low
        analysis.resistance_2 = analysis.pivot_point + range_size
        analysis.support_1 = 2 * analysis.pivot_point - range_high
        analysis.support_2 = analysis.pivot_point - range_size
        
        return analysis
    
    def _detect_breakout(
        self,
        close: np.ndarray,
        _high: np.ndarray,
        _low: np.ndarray,
        range_analysis: RangeAnalysis,
        atr: float
    ) -> Tuple[bool, str, float]:
        """檢測突破信號"""
        current_close = close[-1]

        # 檢查向上突破
        if current_close > range_analysis.range_high:
            breakout_distance = current_close - range_analysis.range_high
            breakout_strength = breakout_distance / atr if atr > 0 else 0
            
            if breakout_strength >= self.breakout_threshold:
                return True, 'up', breakout_strength
        
        # 
        if current_close < range_analysis.range_low:
            breakout_distance = range_analysis.range_low - current_close
            breakout_strength = breakout_distance / atr if atr > 0 else 0
            
            if breakout_strength >= self.breakout_threshold:
                return True, 'down', breakout_strength
        
        return False, 'none', 0.0
    
    def _calculate_squeeze(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> Tuple[bool, bool, int]:
        """"""
        n = len(close)
        if n < self.bb_period:
            return False, False, 0
        
        # 
        sma = np.mean(close[-self.bb_period:])
        std = np.std(close[-self.bb_period:])
        bb_upper = sma + (std * self.bb_std)
        bb_lower = sma - (std * self.bb_std)
        
        # Keltner Channel ( EMA)
        ema = sma  # 
        atr = np.mean([high[i] - low[i] for i in range(-self.kc_period, 0)])
        kc_upper = ema + (atr * self.kc_atr_mult)
        kc_lower = ema - (atr * self.kc_atr_mult)
        
        # BB  KC 
        squeeze_on = bb_lower > kc_lower and bb_upper < kc_upper
        
        # 
        squeeze_duration = 0
        if squeeze_on:
            for i in range(min(50, n - self.bb_period)):
                idx = -1 - i
                if len(close) + idx < self.bb_period:
                    break
                
                window = close[idx - self.bb_period + 1:idx + 1]
                if len(window) < self.bb_period:
                    break
                    
                _sma = np.mean(window)
                _std = np.std(window)
                _bb_u = _sma + (_std * self.bb_std)
                _bb_l = _sma - (_std * self.bb_std)
                
                atr_w = np.mean([high[idx - self.kc_period + 1 + j] - low[idx - self.kc_period + 1 + j] 
                                for j in range(self.kc_period) if idx - self.kc_period + 1 + j >= 0])
                _kc_u = _sma + (atr_w * self.kc_atr_mult)
                _kc_l = _sma - (atr_w * self.kc_atr_mult)
                
                if _bb_l > _kc_l and _bb_u < _kc_u:
                    squeeze_duration += 1
                else:
                    break
        
        # 
        squeeze_releasing = False
        if not squeeze_on and squeeze_duration == 0:
            # 
            if n > self.bb_period + 1:
                prev_window = close[-self.bb_period - 1:-1]
                prev_sma = np.mean(prev_window)
                prev_std = np.std(prev_window)
                prev_bb_u = prev_sma + (prev_std * self.bb_std)
                prev_bb_l = prev_sma - (prev_std * self.bb_std)
                
                prev_atr = np.mean([high[i] - low[i] for i in range(-self.kc_period - 1, -1)])
                prev_kc_u = prev_sma + (prev_atr * self.kc_atr_mult)
                prev_kc_l = prev_sma - (prev_atr * self.kc_atr_mult)
                
                if prev_bb_l > prev_kc_l and prev_bb_u < prev_kc_u:
                    squeeze_releasing = True
        
        return bool(squeeze_on), squeeze_releasing, squeeze_duration
    
    def _check_volume_breakout(
        self,
        volume: np.ndarray,
        lookback: int = 20
    ) -> Tuple[bool, float]:
        """"""
        if len(volume) < lookback + 1:
            return False, 1.0
        
        avg_volume = np.mean(volume[-lookback - 1:-1])
        current_volume = volume[-1]
        
        if avg_volume <= 0:
            return False, 1.0
        
        volume_ratio = current_volume / avg_volume
        is_breakout = volume_ratio >= self.volume_threshold
        
        return is_breakout, volume_ratio
    
    def _check_candle_strength(
        self,
        open_price: float,
        high: float,
        low: float,
        close: float,
        direction: str,
        avg_range: float
    ) -> Tuple[bool, bool]:
        """"""
        candle_range = high - low

        
        #  K 
        wide_range_bar = candle_range > avg_range * 1.2
        
        # 
        if direction == 'up':
            # 
            body_position = (close - low) / candle_range if candle_range > 0 else 0.5
            strong_close = body_position >= self.close_threshold and close > open_price
        else:
            # 
            body_position = (high - close) / candle_range if candle_range > 0 else 0.5
            strong_close = body_position >= self.close_threshold and close < open_price
        
        return strong_close, wide_range_bar
    
    def _calculate_momentum(
        self,
        close: np.ndarray,
        period: int = 10
    ) -> float:
        """"""
        if len(close) < period:
            return 0.0
        
        return float(close[-1] - close[-period])
    
    def _check_false_breakout_filter(
        self,
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        direction: str,
        range_level: float
    ) -> bool:
        """"""
        # 
        false_breakout_count = 0
        
        for i in range(-10, -1):
            if direction == 'up':
                # 
                if high[i] > range_level and close[i + 1] < range_level:
                    false_breakout_count += 1
            else:
                if low[i] < range_level and close[i + 1] > range_level:
                    false_breakout_count += 1
        
        # 
        return false_breakout_count >= 2
    
    # ========================
    # 1. 
    # ========================
    
    def analyze_market(
        self,
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """"""
        self.state = StrategyState.ANALYZING
        
        # 
        open_prices = ohlcv_data[:, 1]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        close = ohlcv_data[:, 4]
        volume = ohlcv_data[:, 5]
        
        current_price = float(close[-1])
        
        # 
        analysis = BreakoutAnalysis()
        
        # 1. 
        range_analysis = self._identify_range(
            high, low, close, self.range_lookback
        )
        analysis.range_analysis = range_analysis
        
        # 2.  ATR
        atr = self._calculate_atr(high, low, close, 14)
        analysis.atr = float(atr[-1])
        if len(atr) >= 20:
            analysis.atr_ma = float(np.mean(atr[-20:]))
            analysis.volatility_expanding = bool(atr[-1] > analysis.atr_ma * 1.2)
        
        # 3. 
        breakout_detected, direction, strength = self._detect_breakout(
            close, high, low, range_analysis, analysis.atr
        )
        range_analysis.breakout_detected = breakout_detected
        range_analysis.breakout_direction = direction
        range_analysis.breakout_strength = strength
        
        # 4. 
        squeeze_on, squeeze_releasing, squeeze_duration = self._calculate_squeeze(
            high, low, close
        )
        analysis.squeeze_on = squeeze_on
        analysis.squeeze_releasing = squeeze_releasing
        analysis.squeeze_duration = squeeze_duration
        
        # 5. 
        vol_breakout, vol_ratio = self._check_volume_breakout(volume)
        analysis.volume_breakout = vol_breakout
        analysis.volume_ratio = vol_ratio
        
        # 6. 
        analysis.momentum = self._calculate_momentum(close, self.momentum_period)
        if direction == 'up':
            analysis.momentum_confirming = analysis.momentum > 0
        elif direction == 'down':
            analysis.momentum_confirming = analysis.momentum < 0
        else:
            analysis.momentum_confirming = False
        
        # 7. 
        avg_range = np.mean([high[i] - low[i] for i in range(-20, 0)])
        strong_close, wide_range = self._check_candle_strength(
            float(open_prices[-1]), float(high[-1]), float(low[-1]), float(close[-1]),
            direction if breakout_detected else 'none',
            float(avg_range)
        )
        analysis.strong_close = strong_close
        analysis.wide_range_bar = wide_range
        
        # 
        if squeeze_on:
            market_condition = MarketCondition.LOW_VOLATILITY
        elif breakout_detected and strength > 1.0:
            if direction == 'up':
                market_condition = MarketCondition.STRONG_UPTREND
            else:
                market_condition = MarketCondition.STRONG_DOWNTREND
        elif range_analysis.range_percent < 5:
            market_condition = MarketCondition.SIDEWAYS
        else:
            market_condition = MarketCondition.SIDEWAYS  # 
        
        self.state = StrategyState.IDLE
        self._last_analysis_time = datetime.now()
        
        return {
            'market_condition': market_condition,
            'trend_direction': direction if breakout_detected else 'neutral',
            'trend_strength': strength,
            'volatility': 'expanding' if analysis.volatility_expanding else (
                'contracting' if squeeze_on else 'normal'
            ),
            'key_levels': {
                'range_high': range_analysis.range_high,
                'range_low': range_analysis.range_low,
                'pivot': range_analysis.pivot_point,
                'resistance_1': range_analysis.resistance_1,
                'support_1': range_analysis.support_1,
            },
            'breakout_analysis': analysis,
            'indicators': {
                'atr': analysis.atr,
                'squeeze_on': squeeze_on,
                'volume_ratio': vol_ratio,
                'momentum': analysis.momentum,
            },
            'current_price': current_price,
            'analysis_summary': self._generate_breakout_summary(analysis, market_condition),
        }
    
    def _generate_breakout_summary(
        self,
        analysis: BreakoutAnalysis,
        market_condition: Union[MarketCondition, str]
    ) -> str:
        """"""
        summary = []
        ra = analysis.range_analysis
        
        #  market_condition 
        if isinstance(market_condition, str):
            condition_str = market_condition
        else:
            condition_str = market_condition.value
        
        summary.append(f": {condition_str}")
        summary.append(f": {ra.range_low:.2f} - {ra.range_high:.2f}")
        summary.append(f": {ra.range_percent:.1f}%")
        summary.append(f": {ra.range_duration_bars} ")
        
        if ra.breakout_detected:
            summary.append(f" : {ra.breakout_direction.upper()}")
            summary.append(f": {ra.breakout_strength:.2f} ATR")
        
        if analysis.squeeze_on:
            summary.append(f"  ({analysis.squeeze_duration} )")
        elif analysis.squeeze_releasing:
            summary.append(" ")
        
        if analysis.volume_breakout:
            summary.append(f"  ({analysis.volume_ratio:.1f}x)")
        
        if analysis.strong_close:
            summary.append(" ")
        
        if analysis.momentum_confirming:
            summary.append(" ")
        
        return " | ".join(summary)
    
    # ========================
    # 2. 
    # ========================
    
    def evaluate_entry_conditions(
        self,
        market_analysis: Dict[str, Any],
        ohlcv_data: np.ndarray,
    ) -> Optional[TradeSetup]:
        """評估突破策略進場條件 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離各評估模塊
        """
        # 基本驗證
        analysis = market_analysis.get('breakout_analysis')
        current_price = market_analysis.get('current_price')
        
        if not analysis or not current_price:
            return None
        
        ra = analysis.range_analysis
        if not ra.breakout_detected:
            return None
        
        direction = 'long' if ra.breakout_direction == 'up' else 'short'
        
        # 檢查假突破歷史並調整確認數量
        has_false_breakout_history = self._check_false_breakout_history(
            ohlcv_data, ra, direction
        )
        
        # 收集所有確認條件
        confirmations, entry_conditions = self._collect_entry_confirmations(
            analysis, ra, direction
        )
        
        # 檢查最低確認要求
        if not self._meets_confirmation_threshold(confirmations):
            return None
        
        # 計算價格水準
        price_levels = self._calculate_price_levels(
            current_price, ra, direction
        )
        stop_loss = price_levels['stop_loss']
        tp1 = price_levels['tp1']
        tp2 = price_levels['tp2']
        tp3 = price_levels['tp3']
        breakout_level = price_levels['breakout_level']
        
        # 確定信號強度
        signal_strength = self._determine_signal_strength(
            confirmations, ra.breakout_strength
        )
        
        # 調整假突破風險
        if has_false_breakout_history:
            if signal_strength == SignalStrength.VERY_STRONG:
                signal_strength = SignalStrength.STRONG
            elif signal_strength == SignalStrength.STRONG:
                signal_strength = SignalStrength.MODERATE
            entry_conditions.append(" ")
        
        # 建立交易設定 - 從 market_analysis 獲取 symbol，必須提供
        if 'symbol' not in market_analysis:
            raise ValueError("市場分析必須包含 'symbol' 字段，不再支持預設幣種")
        
        setup = TradeSetup(
            symbol=market_analysis['symbol'],
            direction=direction,
            entry_price=current_price,
            entry_conditions=entry_conditions,
            entry_confirmations=confirmations,
            required_confirmations=self.required_confirmations,
            stop_loss=stop_loss,
            take_profit_1=tp1,
            take_profit_2=tp2,
            take_profit_3=tp3,
            exit_portions={
                'tp1': self.exit_portions[0],
                'tp2': self.exit_portions[1],
                'tp3': self.exit_portions[2],
            },
            risk_reward_ratio=self.take_profit_r_multiples[0],
            signal_strength=signal_strength,
            market_condition=market_analysis.get('market_condition', "NORMAL"),
            setup_time=datetime.now(),
            valid_until=datetime.now() + timedelta(minutes=30),
            key_levels={
                'range_high': ra.range_high,
                'range_low': ra.range_low,
                'breakout_level': breakout_level,
                'pivot': ra.pivot_point,
            },
            invalidation_conditions=[
                f" (< {ra.range_high if direction == 'long' else ra.range_low})",
                f" {stop_loss:.2f}",
                "",
            ],
        )
        
        logger.info(
            f": "
            f"{direction.upper()} @ {current_price:.2f}, "
            f" {breakout_level:.2f}, : {ra.breakout_strength:.2f}, "
            f": {confirmations}"
        )
        
        return setup
    
    # ========================
    # 3. 
    # ========================
    
    def execute_entry(
        self,
        setup: TradeSetup,
        connector: Any,
    ) -> Optional[TradeExecution]:
        """"""
        try:
            trade_id = f"BO_{setup.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            execution = TradeExecution(
                trade_id=trade_id,
                setup=setup,
            )
            
            if connector is None:
                logger.info(f": {trade_id}")
                execution.actual_entry_price = setup.entry_price
                execution.current_position_size = setup.total_position_size
                execution.average_entry_price = setup.entry_price
                execution.entry_fills.append({
                    'price': setup.entry_price,
                    'size': setup.total_position_size,
                    'time': datetime.now().isoformat(),
                    'type': 'market',  # 
                })
            else:
                # 
                order_result = connector.place_order(
                    symbol=setup.symbol,
                    side='BUY' if setup.direction == 'long' else 'SELL',
                    order_type='MARKET',
                    quantity=setup.total_position_size,
                )
                
                if order_result.get('status') == 'FILLED':
                    fill_price = float(order_result.get('avgPrice', setup.entry_price))
                    execution.actual_entry_price = fill_price
                    execution.current_position_size = setup.total_position_size
                    execution.average_entry_price = fill_price
                    execution.entry_fills.append({
                        'order_id': order_result.get('orderId'),
                        'price': fill_price,
                        'size': setup.total_position_size,
                        'time': datetime.now().isoformat(),
                        'type': 'market',
                    })
            
            execution.highest_price_since_entry = execution.actual_entry_price
            execution.lowest_price_since_entry = execution.actual_entry_price
            
            self.state = StrategyState.POSITION_OPEN
            return execution
            
        except Exception as e:
            logger.error(f": {e}")
            return None
    
    # ========================
    # 4. 
    # ========================
    
    def manage_position(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> PositionManagement:
        """管理突破交易倉位 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離管理模塊
        """
        mgmt = PositionManagement()
        setup = trade.setup
        r_multiple = trade.calculate_r_multiple()
        
        # 更新價格追蹤
        self._update_price_tracking(trade, current_price, setup)
        
        # 建立管理字典以替代PositionManagement
        mgmt_dict: Dict[str, Any] = {}
        
        # 1. 保本停損
        self._handle_breakeven_stop(mgmt_dict, r_multiple)
        
        # 2. 追蹤停損
        self._handle_trailing_stop(trade, current_price, r_multiple)
        
        # 3. 止盈管理
        self._handle_take_profits(mgmt, setup, current_price)
        
        # 4. 突破回歸監控
        self._monitor_breakout_failure(setup, current_price, r_multiple)
        
        # 5. 部分獲利了結
        if r_multiple >= 1.5 and r_multiple <= 2.0:
            close = ohlcv_data[:, 4]
            breakout_level = setup.key_levels.get('breakout_level', setup.entry_price)
            
            # 確認突破有效性
            if setup.direction == 'long':
                # 
                if (close[-2] < close[-3] and 
                    close[-1] > close[-2] and 
                    close[-1] > breakout_level):
                    mgmt.scaling_in_allowed = True
                    logger.info("")
        
        return mgmt
    
    # ========================
    # 5. 
    # ========================
    
    def evaluate_exit_conditions(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> Tuple[bool, str]:
        """評估突破策略出場條件 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離各出場檢查模塊
        """
        
        # 檢查各種出場條件
        exit_checks = [
            lambda: self._check_stop_loss_hit(trade, current_price),
            lambda: self._check_time_based_exit(trade),
            lambda: self._check_breakout_failure(trade, ohlcv_data),
            lambda: self._check_momentum_exhaustion(trade, ohlcv_data),
            lambda: self._check_volume_drying_up(trade, ohlcv_data)
        ]
        
        for check_exit in exit_checks:
            should_exit, reason = check_exit()
            if should_exit:
                return True, reason
        
        return False, ""
    
    def _check_stop_loss_hit(self, trade: TradeExecution, current_price: float) -> Tuple[bool, str]:
        """檢查停損觸發"""
        setup = trade.setup
        active_stop = trade.trailing_stop_price or setup.stop_loss
        
        if setup.direction == 'long':
            if current_price <= active_stop:
                return True, f"停損觸發 @ {current_price:.2f}"
        else:
            if current_price >= active_stop:
                return True, f"停損觸發 @ {current_price:.2f}"
        
        return False, ""
    
    def _check_time_based_exit(self, trade: TradeExecution) -> Tuple[bool, str]:
        """檢查時間基準出場"""
        should_time_exit, time_reason = self.check_time_based_exit(trade)
        return should_time_exit, time_reason
    
    def _check_breakout_failure(self, trade: TradeExecution, ohlcv_data: np.ndarray) -> Tuple[bool, str]:
        """檢查突破失效"""
        setup = trade.setup
        breakout_level = setup.key_levels.get('breakout_level')
        
        if not breakout_level:
            return False, ""
        
        close = ohlcv_data[:, 4]
        if len(close) < 2:
            return False, ""
        
        if setup.direction == 'long':
            # 連續兩根K線收盤低於突破水準
            if close[-1] < breakout_level and close[-2] < breakout_level:
                return True, f"突破失效，價格回落至 {breakout_level:.2f} 以下"
        else:
            if close[-1] > breakout_level and close[-2] > breakout_level:
                return True, f"突破失效，價格回升至 {breakout_level:.2f} 以上"
        
        return False, ""
    
    def _check_momentum_exhaustion(self, trade: TradeExecution, ohlcv_data: np.ndarray) -> Tuple[bool, str]:
        """檢查動量衰竭"""
        if trade.calculate_r_multiple() < 2.0:
            return False, ""
        
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        
        if len(close) < 5:
            return False, ""
        
        setup = trade.setup
        recent_momentum = self._calculate_momentum(close, 5)
        
        if setup.direction == 'long':
            # 動量轉負且高點遞減
            if recent_momentum < 0 and high[-1] < high[-3] < high[-5]:
                return True, "多頭動量衰竭，高點遞減"
        else:
            # 動量轉正且低點遞增
            if recent_momentum > 0 and low[-1] > low[-3] > low[-5]:
                return True, "空頭動量衰竭，低點遞增"
        
        return False, ""
    
    def _check_volume_drying_up(self, trade: TradeExecution, ohlcv_data: np.ndarray) -> Tuple[bool, str]:
        """檢查成交量萎縮"""
        volume = ohlcv_data[:, 5]
        if len(volume) < 10 or trade.calculate_r_multiple() < 1.0:
            return False, ""
        
        recent_vol = np.mean(volume[-3:])
        prev_vol = np.mean(volume[-10:-3])
        
        if prev_vol > 0 and recent_vol / prev_vol < 0.4:
            return True, "成交量萎縮，動能不足"
        
        return False, ""
    
    # ========================
    # 6. 
    # ========================
    
    def execute_exit(
        self,
        trade: TradeExecution,
        reason: str,
        connector: Any,
        partial_exit: bool = False,
        exit_portion: float = 1.0,
    ) -> bool:
        """"""
        try:
            exit_size = trade.current_position_size * exit_portion
            
            if connector is None:
                logger.info(f": {trade.trade_id}, : {reason}")
                
                if trade.setup.direction == 'long':
                    pnl = (trade.average_exit_price - trade.average_entry_price) * exit_size
                else:
                    pnl = (trade.average_entry_price - trade.average_exit_price) * exit_size
                
                trade.realized_pnl += pnl
                trade.current_position_size -= exit_size
                trade.exit_fills.append({
                    'price': trade.average_exit_price or trade.setup.entry_price,
                    'size': exit_size,
                    'time': datetime.now().isoformat(),
                    'reason': reason,
                })
            else:
                order_result = connector.place_order(
                    symbol=trade.setup.symbol,
                    side='SELL' if trade.setup.direction == 'long' else 'BUY',
                    order_type='MARKET',
                    quantity=exit_size,
                    reduce_only=True,
                )
                
                if order_result.get('status') == 'FILLED':
                    fill_price = float(order_result.get('avgPrice', 0))
                    trade.average_exit_price = fill_price
                    
                    if trade.setup.direction == 'long':
                        pnl = (fill_price - trade.average_entry_price) * exit_size
                    else:
                        pnl = (trade.average_entry_price - fill_price) * exit_size
                    
                    trade.realized_pnl += pnl
                    trade.current_position_size -= exit_size
                    trade.exit_fills.append({
                        'order_id': order_result.get('orderId'),
                        'price': fill_price,
                        'size': exit_size,
                        'time': datetime.now().isoformat(),
                        'reason': reason,
                    })
            
            if trade.current_position_size <= 0:
                trade.exit_time = datetime.now()
                trade.exit_reason = reason
                trade.holding_duration = trade.exit_time - trade.entry_time
                
                self.performance.update(trade)
                self.trade_history.append(trade)
                
                if trade.realized_pnl < 0:
                    self._cooldown_until = datetime.now() + timedelta(
                        hours=self.risk_params.cooldown_after_loss
                    )
                
                self.state = StrategyState.IDLE
                
                logger.info(
                    f": {trade.trade_id}, "
                    f"PnL: {trade.realized_pnl:.2f}, "
                    f"R: {trade.calculate_r_multiple():.2f}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"執行出場時發生錯誤: {e}")
            return False
    
    def _check_false_breakout_history(
        self, 
        ohlcv_data: np.ndarray, 
        ra: BreakoutAnalysis, 
        direction: str
    ) -> bool:
        """檢查假突破歷史"""
        # 簡化實現 - 檢查最近是否有假突破
        close = ohlcv_data[:, 4]
        if len(close) < 20:
            return False
        
        # 檢查最近20根K線是否有突破後回撤的情況
        recent_high: float = float(np.max(close[-20:]))
        recent_low: float = float(np.min(close[-20:]))
        current_price = float(close[-1])
        
        if direction == 'long':
            # 檢查是否曾經突破後回落
            return bool(recent_high > ra.resistance_level and current_price < ra.resistance_level * 0.99)
        else:
            # 檢查是否曾經跌破後反彈
            return bool(recent_low < ra.support_level and current_price > ra.support_level * 1.01)
    
    def _collect_entry_confirmations(
        self, 
        analysis: Dict[str, Any], 
        ra: BreakoutAnalysis, 
        direction: str
    ) -> Tuple[int, List[str]]:
        """收集進場確認條件"""
        confirmations = 0
        conditions = []
        
        # 成交量確認
        if ra.volume_spike:
            confirmations += 2
            conditions.append("成交量放大確認")
        
        # 動量確認
        if ra.momentum_strength > 0.5:
            confirmations += 1
            conditions.append("動量強勁")
        
        # 波動性突破
        if ra.volatility_spike:
            confirmations += 1
            conditions.append("波動性突破")
        
        # 趨勢一致性
        trend_direction = analysis.get('trend_direction', 'neutral')
        if (direction == 'long' and trend_direction == 'up') or \
           (direction == 'short' and trend_direction == 'down'):
            confirmations += 1
            conditions.append("趨勢一致")
        
        return confirmations, conditions
    
    def _meets_confirmation_threshold(self, confirmations: int) -> bool:
        """檢查是否達到最低確認要求"""
        return confirmations >= self.min_confirmations
    
    def _calculate_price_levels(
        self, 
        current_price: float, 
        ra: BreakoutAnalysis, 
        direction: str
    ) -> Dict[str, float]:
        """計算價格水準"""
        if direction == 'long':
            stop_loss = ra.support_level * 0.99
            tp1 = current_price * 1.02
            tp2 = current_price * 1.04
            tp3 = current_price * 1.06
            breakout_level = ra.resistance_level
        else:
            stop_loss = ra.resistance_level * 1.01
            tp1 = current_price * 0.98
            tp2 = current_price * 0.96
            tp3 = current_price * 0.94
            breakout_level = ra.support_level
        
        return {
            'stop_loss': stop_loss,
            'tp1': tp1,
            'tp2': tp2,
            'tp3': tp3,
            'breakout_level': breakout_level
        }
    
    def _determine_signal_strength(
        self, 
        confirmations: int, 
        ra: BreakoutAnalysis
    ) -> SignalStrength:
        """確定信號強度"""
        if confirmations >= 4 and ra.breakout_strength > 0.8:
            return SignalStrength.VERY_STRONG
        elif confirmations >= 3 and ra.breakout_strength > 0.6:
            return SignalStrength.STRONG
        elif confirmations >= 2:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _update_price_tracking(
        self, 
        trade: TradeExecution, 
        current_price: float, 
        setup: TradeSetup
    ) -> None:
        """更新價格追蹤 - 簡化實現"""
        # 暫時跳過具體實現
        pass
    
    def _handle_breakeven_stop(
        self, 
        mgmt: Dict[str, Any], 
        r_multiple: float
    ) -> None:
        """處理保本停損"""
        if r_multiple >= self.breakeven_r_multiple and not mgmt.get('breakeven_set', False):
            mgmt['breakeven_set'] = True
            mgmt['stop_moved_to_breakeven'] = True
    
    def _handle_trailing_stop(
        self, 
        trade: TradeExecution, 
        current_price: float, 
        r_multiple: float
    ) -> None:
        """處理移動停損"""
        if r_multiple >= self.trailing_start_r_multiple:
            if trade.setup.direction == 'long':
                new_stop = current_price * (1 - self.trailing_stop_percentage)
                if trade.trailing_stop_price is None or new_stop > trade.trailing_stop_price:
                    trade.trailing_stop_price = new_stop
            else:
                new_stop = current_price * (1 + self.trailing_stop_percentage)
                if trade.trailing_stop_price is None or new_stop < trade.trailing_stop_price:
                    trade.trailing_stop_price = new_stop
    
    def _handle_take_profits(
        self, 
        mgmt: PositionManagement, 
        setup: TradeSetup, 
        current_price: float
    ) -> None:
        """處理獲利了結 - 簡化實現"""
        # 可以在這裡實現部分獲利邏輯
        pass
    
    def _monitor_breakout_failure(
        self, 
        setup: TradeSetup, 
        current_price: float, 
        r_multiple: float
    ) -> None:
        """監控突破失效"""
        # 如果突破失效，標記為高風險
        if setup.direction == 'long':
            breakout_level = setup.key_levels.get('breakout_level', setup.entry_price)
            if current_price < breakout_level * 0.995:  # 突破失效
                # 突破失效的處理邏輯
                pass
        else:
            breakout_level = setup.key_levels.get('breakout_level', setup.entry_price)
            if current_price > breakout_level * 1.005:  # 突破失效
                # 突破失效的處理邏輯
                pass


# 註冊策略
StrategyRegistry.register('breakout', BreakoutTradingStrategy)
