"""
突破交易策略 (Breakout Trading Strategy)
========================================

核心理念：
在價格突破重要技術關卡時進場，捕捉新趨勢的起始階段

適用場景：
- 價格區間盤整後的突破
- 重要支撐/阻力位突破
- 波動率收縮後的擴張

主要組件：
1. 價格區間識別系統
2. 突破有效性驗證
3. 假突破過濾
4. 動量確認系統

技術指標組合：
- 價格高低點區間
- ATR 波動率
- 成交量確認
- 擠壓指標
"""

import numpy as np
import logging
from typing import Optional, Dict, Any, Tuple, List
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
    """價格區間分析"""
    range_high: float = 0.0
    range_low: float = 0.0
    range_size: float = 0.0
    range_percent: float = 0.0
    range_duration_bars: int = 0
    
    # 突破狀態
    breakout_detected: bool = False
    breakout_direction: str = "none"  # 'up', 'down', 'none'
    breakout_strength: float = 0.0  # 突破幅度佔 ATR 的比例
    
    # 通道
    channel_upper: float = 0.0
    channel_lower: float = 0.0
    
    # 關鍵價位
    pivot_point: float = 0.0
    resistance_1: float = 0.0
    resistance_2: float = 0.0
    support_1: float = 0.0
    support_2: float = 0.0


@dataclass
class BreakoutAnalysis:
    """突破分析結果"""
    # 區間資訊
    range_analysis: RangeAnalysis = field(default_factory=RangeAnalysis)
    
    # ATR
    atr: float = 0.0
    atr_ma: float = 0.0  # ATR 移動平均
    volatility_expanding: bool = False
    
    # 擠壓狀態
    squeeze_on: bool = False
    squeeze_releasing: bool = False
    squeeze_duration: int = 0
    
    # 成交量
    volume_breakout: bool = False
    volume_ratio: float = 1.0
    
    # 動量
    momentum: float = 0.0
    momentum_confirming: bool = False
    
    # 蠟燭特徵
    strong_close: bool = False  # 收盤在實體上/下 1/3
    wide_range_bar: bool = False  # 區間大於平均
    
    # 重測
    retest_completed: bool = False
    retest_held: bool = False


class BreakoutTradingStrategy(BaseStrategy):
    """
    突破交易策略
    
    完整的突破交易系統，包含：
    1. 區間識別和突破檢測
    2. 假突破過濾
    3. 成交量和動量確認
    4. 突破後追蹤管理
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
                max_holding_period_hours=120,  # 5 天
            ),
        )
        
        # 區間識別參數
        self.range_lookback = 20  # 識別區間的回看期
        self.range_threshold = 0.05  # 區間佔價格的最大百分比
        self.min_range_bars = 10  # 最少區間持續 K 線數
        
        # 突破確認參數
        self.breakout_threshold = 0.5  # 突破需超過區間邊界 0.5 ATR
        self.close_threshold = 0.8  # 收盤需在突破方向的 80%
        self.volume_threshold = 1.5  # 成交量需達到平均的 1.5 倍
        
        # 擠壓參數
        self.bb_period = 20
        self.bb_std = 2.0
        self.kc_period = 20
        self.kc_atr_mult = 1.5
        
        # 動量參數
        self.momentum_period = 10
        
        # 進場確認
        self.required_confirmations = 3
        
        # 出場參數
        self.take_profit_r_multiples = [2.5, 4.0, 6.0]
        self.exit_portions = [0.35, 0.35, 0.30]
    
    # ========================
    # 技術指標計算
    # ========================
    
    def _calculate_atr(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> np.ndarray:
        """計算 ATR"""
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
        
        return atr
    
    def _identify_range(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        lookback: int = 20
    ) -> RangeAnalysis:
        """識別價格區間"""
        analysis = RangeAnalysis()
        
        if len(close) < lookback:
            return analysis
        
        # 最近 lookback 根 K 線的高低點
        recent_high = high[-lookback:]
        recent_low = low[-lookback:]
        
        range_high = np.max(recent_high)
        range_low = np.min(recent_low)
        range_size = range_high - range_low
        mid_price = (range_high + range_low) / 2
        
        analysis.range_high = range_high
        analysis.range_low = range_low
        analysis.range_size = range_size
        analysis.range_percent = range_size / mid_price * 100
        
        # 計算區間持續時間
        # 從最近往回看，找到價格首次進入區間的位置
        tolerance = range_size * 0.1
        range_start = 0
        for i in range(len(close) - 1, -1, -1):
            if close[i] > range_high + tolerance or close[i] < range_low - tolerance:
                range_start = i + 1
                break
        analysis.range_duration_bars = len(close) - range_start
        
        # 計算通道
        analysis.channel_upper = range_high
        analysis.channel_lower = range_low
        
        # 計算樞紐點和支撐/阻力
        analysis.pivot_point = (range_high + range_low + close[-1]) / 3
        analysis.resistance_1 = 2 * analysis.pivot_point - range_low
        analysis.resistance_2 = analysis.pivot_point + range_size
        analysis.support_1 = 2 * analysis.pivot_point - range_high
        analysis.support_2 = analysis.pivot_point - range_size
        
        return analysis
    
    def _detect_breakout(
        self,
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        range_analysis: RangeAnalysis,
        atr: float
    ) -> Tuple[bool, str, float]:
        """檢測突破"""
        current_close = close[-1]
        current_high = high[-1]
        current_low = low[-1]
        
        # 向上突破
        if current_close > range_analysis.range_high:
            breakout_distance = current_close - range_analysis.range_high
            breakout_strength = breakout_distance / atr if atr > 0 else 0
            
            if breakout_strength >= self.breakout_threshold:
                return True, 'up', breakout_strength
        
        # 向下突破
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
        """計算擠壓狀態"""
        n = len(close)
        if n < self.bb_period:
            return False, False, 0
        
        # 布林帶
        sma = np.mean(close[-self.bb_period:])
        std = np.std(close[-self.bb_period:])
        bb_upper = sma + (std * self.bb_std)
        bb_lower = sma - (std * self.bb_std)
        
        # Keltner Channel (使用 EMA)
        ema = sma  # 簡化
        atr = np.mean([high[i] - low[i] for i in range(-self.kc_period, 0)])
        kc_upper = ema + (atr * self.kc_atr_mult)
        kc_lower = ema - (atr * self.kc_atr_mult)
        
        # 擠壓中：BB 在 KC 內
        squeeze_on = bb_lower > kc_lower and bb_upper < kc_upper
        
        # 計算擠壓持續時間
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
        
        # 擠壓釋放
        squeeze_releasing = False
        if not squeeze_on and squeeze_duration == 0:
            # 檢查前一根是否還在擠壓中
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
        """檢查成交量突破"""
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
        """檢查蠟燭強度"""
        candle_range = high - low
        body = abs(close - open_price)
        
        # 寬幅 K 線
        wide_range_bar = candle_range > avg_range * 1.2
        
        # 強勢收盤
        if direction == 'up':
            # 向上突破時，收盤應該在實體上部
            body_position = (close - low) / candle_range if candle_range > 0 else 0.5
            strong_close = body_position >= self.close_threshold and close > open_price
        else:
            # 向下突破時，收盤應該在實體下部
            body_position = (high - close) / candle_range if candle_range > 0 else 0.5
            strong_close = body_position >= self.close_threshold and close < open_price
        
        return strong_close, wide_range_bar
    
    def _calculate_momentum(
        self,
        close: np.ndarray,
        period: int = 10
    ) -> float:
        """計算動量"""
        if len(close) < period:
            return 0.0
        
        return close[-1] - close[-period]
    
    def _check_false_breakout_filter(
        self,
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        direction: str,
        range_level: float
    ) -> bool:
        """假突破過濾"""
        # 檢查是否有多次突破失敗的歷史
        false_breakout_count = 0
        
        for i in range(-10, -1):
            if direction == 'up':
                # 檢查是否曾經突破後又回到區間內
                if high[i] > range_level and close[i + 1] < range_level:
                    false_breakout_count += 1
            else:
                if low[i] < range_level and close[i + 1] > range_level:
                    false_breakout_count += 1
        
        # 如果最近有多次假突破，發出警告
        return false_breakout_count >= 2
    
    # ========================
    # 1. 市場分析
    # ========================
    
    def analyze_market(
        self,
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """分析突破機會"""
        self.state = StrategyState.ANALYZING
        
        # 提取數據
        open_prices = ohlcv_data[:, 1]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        close = ohlcv_data[:, 4]
        volume = ohlcv_data[:, 5]
        
        current_price = close[-1]
        
        # 建立分析結果
        analysis = BreakoutAnalysis()
        
        # 1. 識別價格區間
        range_analysis = self._identify_range(
            high, low, close, self.range_lookback
        )
        analysis.range_analysis = range_analysis
        
        # 2. 計算 ATR
        atr = self._calculate_atr(high, low, close, 14)
        analysis.atr = atr[-1]
        if len(atr) >= 20:
            analysis.atr_ma = float(np.mean(atr[-20:]))
            analysis.volatility_expanding = atr[-1] > analysis.atr_ma * 1.2
        
        # 3. 檢測突破
        breakout_detected, direction, strength = self._detect_breakout(
            close, high, low, range_analysis, analysis.atr
        )
        range_analysis.breakout_detected = breakout_detected
        range_analysis.breakout_direction = direction
        range_analysis.breakout_strength = strength
        
        # 4. 擠壓狀態
        squeeze_on, squeeze_releasing, squeeze_duration = self._calculate_squeeze(
            high, low, close
        )
        analysis.squeeze_on = squeeze_on
        analysis.squeeze_releasing = squeeze_releasing
        analysis.squeeze_duration = squeeze_duration
        
        # 5. 成交量確認
        vol_breakout, vol_ratio = self._check_volume_breakout(volume)
        analysis.volume_breakout = vol_breakout
        analysis.volume_ratio = vol_ratio
        
        # 6. 動量
        analysis.momentum = self._calculate_momentum(close, self.momentum_period)
        if direction == 'up':
            analysis.momentum_confirming = analysis.momentum > 0
        elif direction == 'down':
            analysis.momentum_confirming = analysis.momentum < 0
        else:
            analysis.momentum_confirming = False
        
        # 7. 蠟燭強度
        avg_range = np.mean([high[i] - low[i] for i in range(-20, 0)])
        strong_close, wide_range = self._check_candle_strength(
            open_prices[-1], high[-1], low[-1], close[-1],
            direction if breakout_detected else 'none',
            float(avg_range)
        )
        analysis.strong_close = strong_close
        analysis.wide_range_bar = wide_range
        
        # 確定市場狀態
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
            market_condition = "NORMAL"  # 暫時使用字串
        
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
        market_condition: MarketCondition
    ) -> str:
        """生成突破分析摘要"""
        summary = []
        ra = analysis.range_analysis
        
        summary.append(f"市場狀態: {market_condition.value}")
        summary.append(f"區間: {ra.range_low:.2f} - {ra.range_high:.2f}")
        summary.append(f"區間寬度: {ra.range_percent:.1f}%")
        summary.append(f"區間持續: {ra.range_duration_bars} 根")
        
        if ra.breakout_detected:
            summary.append(f"🚀 突破方向: {ra.breakout_direction.upper()}")
            summary.append(f"突破強度: {ra.breakout_strength:.2f} ATR")
        
        if analysis.squeeze_on:
            summary.append(f"🔒 擠壓中 ({analysis.squeeze_duration} 根)")
        elif analysis.squeeze_releasing:
            summary.append("💥 擠壓釋放")
        
        if analysis.volume_breakout:
            summary.append(f"📊 放量 ({analysis.volume_ratio:.1f}x)")
        
        if analysis.strong_close:
            summary.append("💪 強勢收盤")
        
        if analysis.momentum_confirming:
            summary.append("✅ 動量確認")
        
        return " | ".join(summary)
    
    # ========================
    # 2. 進場條件評估
    # ========================
    
    def evaluate_entry_conditions(
        self,
        market_analysis: Dict[str, Any],
        ohlcv_data: np.ndarray,
    ) -> Optional[TradeSetup]:
        """
        評估突破進場條件
        
        進場條件：
        1. 有效突破（收盤價確認）
        2. 成交量放大
        3. 動量確認
        4. 蠟燭形態確認
        5. 擠壓釋放（可選但加分）
        """
        analysis = market_analysis.get('breakout_analysis')
        current_price = market_analysis.get('current_price')
        
        if not analysis or not current_price:
            return None
        
        ra = analysis.range_analysis
        
        # 必須有突破
        if not ra.breakout_detected:
            return None
        
        direction = 'long' if ra.breakout_direction == 'up' else 'short'
        
        # 假突破過濾
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        
        breakout_level = ra.range_high if direction == 'long' else ra.range_low
        
        has_false_breakout_history = self._check_false_breakout_filter(
            close, high, low, ra.breakout_direction, breakout_level
        )
        
        if has_false_breakout_history:
            logger.debug("檢測到假突破歷史，需要更多確認")
            self.required_confirmations = 4  # 臨時提高要求
        
        # 收集確認訊號
        confirmations = 0
        entry_conditions = []
        
        # 1. 突破強度（必要）
        if ra.breakout_strength >= self.breakout_threshold:
            confirmations += 1
            entry_conditions.append(f"突破強度: {ra.breakout_strength:.2f} ATR")
            if ra.breakout_strength >= 1.0:
                confirmations += 1  # 強勢突破加分
                entry_conditions.append("強勢突破 (> 1 ATR)")
        
        # 2. 成交量確認
        if analysis.volume_breakout:
            confirmations += 1
            entry_conditions.append(f"成交量放大: {analysis.volume_ratio:.1f}x")
        
        # 3. 動量確認
        if analysis.momentum_confirming:
            confirmations += 1
            entry_conditions.append("動量方向一致")
        
        # 4. 強勢收盤
        if analysis.strong_close:
            confirmations += 1
            entry_conditions.append("強勢收盤")
        
        # 5. 寬幅 K 線
        if analysis.wide_range_bar:
            confirmations += 1
            entry_conditions.append("寬幅 K 線")
        
        # 6. 擠壓釋放
        if analysis.squeeze_releasing:
            confirmations += 1
            entry_conditions.append("擠壓釋放")
        elif analysis.squeeze_on and analysis.squeeze_duration >= 5:
            # 擠壓中但即將釋放
            entry_conditions.append(f"擠壓中 ({analysis.squeeze_duration} 根)")
        
        # 7. 波動率擴張
        if analysis.volatility_expanding:
            confirmations += 1
            entry_conditions.append("波動率擴張")
        
        # 8. 區間時間足夠
        if ra.range_duration_bars >= self.min_range_bars:
            confirmations += 1
            entry_conditions.append(f"區間持續 {ra.range_duration_bars} 根")
        
        # 檢查確認數量
        if confirmations < self.required_confirmations:
            logger.debug(f"突破確認不足: {confirmations}/{self.required_confirmations}")
            return None
        
        # 計算停損和目標
        if direction == 'long':
            # 停損設在區間下方
            stop_loss = ra.range_low - (analysis.atr * 0.5)
            
            # 目標基於區間大小 + R 倍數
            risk = current_price - stop_loss
            tp1 = current_price + (risk * self.take_profit_r_multiples[0])
            tp2 = current_price + (risk * self.take_profit_r_multiples[1])
            tp3 = current_price + (risk * self.take_profit_r_multiples[2])
            
            # 也可以用技術位作為參考
            # tp1 = max(tp1, ra.resistance_1)
        else:
            stop_loss = ra.range_high + (analysis.atr * 0.5)
            
            risk = stop_loss - current_price
            tp1 = current_price - (risk * self.take_profit_r_multiples[0])
            tp2 = current_price - (risk * self.take_profit_r_multiples[1])
            tp3 = current_price - (risk * self.take_profit_r_multiples[2])
        
        # 訊號強度
        if confirmations >= 6 and ra.breakout_strength >= 1.5:
            signal_strength = SignalStrength.VERY_STRONG
        elif confirmations >= 5:
            signal_strength = SignalStrength.STRONG
        elif confirmations >= 4:
            signal_strength = SignalStrength.MODERATE
        else:
            signal_strength = SignalStrength.WEAK
        
        # 如果有假突破歷史，降級訊號
        if has_false_breakout_history:
            if signal_strength == SignalStrength.VERY_STRONG:
                signal_strength = SignalStrength.STRONG
            elif signal_strength == SignalStrength.STRONG:
                signal_strength = SignalStrength.MODERATE
            entry_conditions.append("⚠️ 注意：有假突破歷史")
        
        setup = TradeSetup(
            symbol=market_analysis.get('symbol', 'BTCUSDT'),
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
                f"價格回到區間內 (< {ra.range_high if direction == 'long' else ra.range_low})",
                f"停損觸發 {stop_loss:.2f}",
                "成交量快速萎縮",
            ],
        )
        
        logger.info(
            f"突破策略發現入場機會: "
            f"{direction.upper()} @ {current_price:.2f}, "
            f"突破 {breakout_level:.2f}, 強度: {ra.breakout_strength:.2f}, "
            f"確認: {confirmations}"
        )
        
        return setup
    
    # ========================
    # 3. 進場執行
    # ========================
    
    def execute_entry(
        self,
        setup: TradeSetup,
        connector: Any,
    ) -> Optional[TradeExecution]:
        """執行突破進場"""
        try:
            trade_id = f"BO_{setup.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            execution = TradeExecution(
                trade_id=trade_id,
                setup=setup,
            )
            
            if connector is None:
                logger.info(f"模擬突破進場: {trade_id}")
                execution.actual_entry_price = setup.entry_price
                execution.current_position_size = setup.total_position_size
                execution.average_entry_price = setup.entry_price
                execution.entry_fills.append({
                    'price': setup.entry_price,
                    'size': setup.total_position_size,
                    'time': datetime.now().isoformat(),
                    'type': 'market',  # 突破用市價單
                })
            else:
                # 突破策略通常用市價單快速進場
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
            logger.error(f"突破進場執行失敗: {e}")
            return None
    
    # ========================
    # 4. 部位管理
    # ========================
    
    def manage_position(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> PositionManagement:
        """
        突破策略部位管理
        
        特點：
        1. 突破確認後快速移動停損
        2. 追蹤止損保護利潤
        3. 關注假突破風險
        """
        mgmt = PositionManagement()
        setup = trade.setup
        r_multiple = trade.calculate_r_multiple()
        risk_per_unit = abs(setup.entry_price - setup.stop_loss)
        
        # 更新極值
        if setup.direction == 'long':
            trade.highest_price_since_entry = max(
                trade.highest_price_since_entry,
                current_price
            )
        else:
            trade.lowest_price_since_entry = min(
                trade.lowest_price_since_entry,
                current_price
            )
        
        # 1. 快速移動停損（突破確認後）
        if r_multiple >= 1.0 and not mgmt.stop_loss_moved_to_breakeven:
            # 移動到損益平衡加一點緩衝
            buffer = risk_per_unit * 0.1
            if setup.direction == 'long':
                new_stop = setup.entry_price + buffer
            else:
                new_stop = setup.entry_price - buffer
            
            mgmt.stop_loss_moved_to_breakeven = True
            mgmt.current_stop_loss = new_stop
            logger.info(f"突破確認：移動停損到 {new_stop:.2f}")
        
        # 2. 突破後的激進追蹤
        # 突破策略在確認後應該積極保護利潤
        if r_multiple >= 1.5:
            new_trailing = self.update_trailing_stop(trade, current_price)
            if new_trailing:
                mgmt.stop_loss_trailing = True
                mgmt.current_stop_loss = new_trailing
        
        # 3. 檢查目標達成
        if setup.direction == 'long':
            if current_price >= setup.take_profit_1 and not mgmt.tp1_filled:
                mgmt.tp1_filled = True
                mgmt.exit_portions_filled += 1
            if current_price >= setup.take_profit_2 and not mgmt.tp2_filled:
                mgmt.tp2_filled = True
                mgmt.exit_portions_filled += 1
        else:
            if current_price <= setup.take_profit_1 and not mgmt.tp1_filled:
                mgmt.tp1_filled = True
                mgmt.exit_portions_filled += 1
            if current_price <= setup.take_profit_2 and not mgmt.tp2_filled:
                mgmt.tp2_filled = True
                mgmt.exit_portions_filled += 1
        
        # 4. 假突破警告
        # 檢查價格是否回到突破位附近
        breakout_level = setup.key_levels.get('breakout_level', setup.entry_price)
        
        if setup.direction == 'long':
            if current_price < breakout_level and r_multiple > 0:
                logger.warning("警告：價格回到突破位下方，可能是假突破")
        else:
            if current_price > breakout_level and r_multiple > 0:
                logger.warning("警告：價格回到突破位上方，可能是假突破")
        
        # 5. 加碼機會
        # 突破確認且回測後可以加碼
        if r_multiple >= 1.5 and r_multiple <= 2.0:
            close = ohlcv_data[:, 4]
            
            # 檢查是否有回測並守住
            if setup.direction == 'long':
                # 價格回測後反彈
                if (close[-2] < close[-3] and 
                    close[-1] > close[-2] and 
                    close[-1] > breakout_level):
                    mgmt.scaling_in_allowed = True
                    logger.info("回測成功，可以加碼")
        
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
        突破策略出場條件
        
        出場條件：
        1. 停損觸發
        2. 假突破確認
        3. 動量衰減
        4. 時間止損
        5. 目標達成
        """
        setup = trade.setup
        
        # 1. 停損檢查
        active_stop = trade.trailing_stop_price or setup.stop_loss
        if setup.direction == 'long':
            if current_price <= active_stop:
                return True, f"停損觸發 @ {current_price:.2f}"
        else:
            if current_price >= active_stop:
                return True, f"停損觸發 @ {current_price:.2f}"
        
        # 2. 時間止損
        should_time_exit, time_reason = self.check_time_based_exit(trade)
        if should_time_exit:
            return True, time_reason
        
        # 3. 假突破確認
        breakout_level = setup.key_levels.get('breakout_level')
        if breakout_level:
            close = ohlcv_data[:, 4]
            
            if setup.direction == 'long':
                # 如果收盤價連續兩根在突破位下方
                if close[-1] < breakout_level and close[-2] < breakout_level:
                    return True, f"假突破確認：價格回到區間內"
            else:
                if close[-1] > breakout_level and close[-2] > breakout_level:
                    return True, f"假突破確認：價格回到區間內"
        
        # 4. 動量衰減
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        
        if trade.calculate_r_multiple() >= 2.0:
            # 計算最近的動量
            recent_momentum = self._calculate_momentum(close, 5)
            
            if setup.direction == 'long':
                # 動量轉負
                if recent_momentum < 0:
                    # 檢查是否形成更低的高點
                    if high[-1] < high[-3] < high[-5]:
                        return True, "動量衰減，形成更低高點"
            else:
                if recent_momentum > 0:
                    if low[-1] > low[-3] > low[-5]:
                        return True, "動量衰減，形成更高低點"
        
        # 5. 成交量急劇萎縮（突破後動能不足）
        volume = ohlcv_data[:, 5]
        if len(volume) >= 5:
            recent_vol = np.mean(volume[-3:])
            prev_vol = np.mean(volume[-10:-3])
            
            if prev_vol > 0 and recent_vol / prev_vol < 0.4:
                if trade.calculate_r_multiple() >= 1.0:
                    return True, "成交量急劇萎縮，動能不足"
        
        return False, ""
    
    # ========================
    # 6. 出場執行
    # ========================
    
    def execute_exit(
        self,
        trade: TradeExecution,
        reason: str,
        connector: Any,
        partial_exit: bool = False,
        exit_portion: float = 1.0,
    ) -> bool:
        """執行突破策略出場"""
        try:
            exit_size = trade.current_position_size * exit_portion
            
            if connector is None:
                logger.info(f"模擬突破出場: {trade.trade_id}, 原因: {reason}")
                
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
                    f"突破策略出場完成: {trade.trade_id}, "
                    f"PnL: {trade.realized_pnl:.2f}, "
                    f"R: {trade.calculate_r_multiple():.2f}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"突破策略出場執行失敗: {e}")
            return False


# 註冊策略
StrategyRegistry.register('breakout', BreakoutTradingStrategy)
