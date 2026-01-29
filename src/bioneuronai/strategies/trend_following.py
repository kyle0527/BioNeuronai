"""
趨勢跟隨策略 (Trend Following Strategy)
========================================

核心理念：
"趨勢是你的朋友" - 順勢而為，捕捉主要趨勢

適用場景：
- 明確上升或下降趨勢
- 趨勢市場（Trending Market）
- 高動能環境

策略邏輯：
1. 識別趨勢方向（上升/下降/震盪）
2. 確認趨勢強度（ADX）
3. 等待趨勢確認信號
4. 順勢進場，設置追蹤止損

技術指標：
- EMA 均線系統 (21/55/200)
- MACD 動量指標
- ADX 趨勢強度
- ATR 波動率
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
class TrendAnalysis:
    """"""
    # 
    primary_trend: str = "neutral"  # 'bullish', 'bearish', 'neutral'
    primary_trend_strength: float = 0.0  # 0-100
    
    # 
    htf_trend: str = "neutral"  # Higher Timeframe (4h/Daily)
    mtf_trend: str = "neutral"  # Medium Timeframe (1h)
    ltf_trend: str = "neutral"  # Lower Timeframe (15m)
    
    # 
    trend_alignment: float = 0.0  # 0-100, 
    
    # EMA 
    price_above_ema21: bool = False
    price_above_ema55: bool = False
    price_above_ema200: bool = False
    ema21_above_ema55: bool = False
    ema55_above_ema200: bool = False
    
    # MACD 
    macd_bullish: bool = False
    macd_histogram_rising: bool = False
    macd_above_signal: bool = False
    
    # ADX 
    adx_value: float = 0.0
    adx_trending: bool = False  # ADX > 25
    plus_di_above_minus: bool = False
    
    # 
    momentum_score: float = 0.0  # -100  +100


class TrendFollowingStrategy(BaseStrategy):
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
            name="Trend Following",
            timeframe=timeframe,
            risk_params=risk_params or RiskParameters(
                max_risk_per_trade_pct=1.0,
                min_risk_reward_ratio=2.0,
                trailing_stop_activation=1.5,
                trailing_stop_distance=0.5,
                max_holding_period_hours=168,  # 7 
            ),
        )
        
        # 
        self.ema_periods = {'fast': 21, 'medium': 55, 'slow': 200}
        self.macd_params = {'fast': 12, 'slow': 26, 'signal': 9}
        self.adx_period = 14
        self.atr_period = 14
        self.min_adx_for_trend = 25
        self.required_confirmations = 4  # 4
        
        # 
        self.entry_weights = {
            'trend_alignment': 0.25,
            'ema_position': 0.20,
            'macd_confirmation': 0.20,
            'adx_strength': 0.15,
            'momentum': 0.10,
            'volume': 0.10,
        }
        
        # 
        self.take_profit_r_multiples = [2.0, 4.0, 6.0]
        self.exit_portions = [0.35, 0.35, 0.30]
        
    # ========================
    # 
    # ========================
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """ EMA"""
        if len(data) < period:
            return np.full(len(data), np.nan)
        
        ema = np.zeros(len(data))
        multiplier = 2 / (period + 1)
        
        #  SMA 
        ema[period-1] = np.mean(data[:period])
        
        for i in range(period, len(data)):
            ema[i] = (data[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        ema[:period-1] = np.nan
        return ema
    
    def _calculate_macd(
        self, 
        close: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """ MACD"""
        ema_fast = self._calculate_ema(close, self.macd_params['fast'])
        ema_slow = self._calculate_ema(close, self.macd_params['slow'])
        
        macd_line = ema_fast - ema_slow
        signal_line = self._calculate_ema(macd_line, self.macd_params['signal'])
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    def _calculate_adx(
        self, 
        high: np.ndarray, 
        low: np.ndarray, 
        close: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """ ADX, +DI, -DI"""
        period = self.adx_period
        n = len(close)
        
        if n < period + 1:
            return (
                np.full(n, np.nan),
                np.full(n, np.nan),
                np.full(n, np.nan)
            )
        
        # True Range
        tr = np.zeros(n)
        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        
        for i in range(1, n):
            h_l = high[i] - low[i]
            h_pc = abs(high[i] - close[i-1])
            l_pc = abs(low[i] - close[i-1])
            tr[i] = max(h_l, h_pc, l_pc)
            
            up_move = high[i] - high[i-1]
            down_move = low[i-1] - low[i]
            
            if up_move > down_move and up_move > 0:
                plus_dm[i] = up_move
            if down_move > up_move and down_move > 0:
                minus_dm[i] = down_move
        
        # 
        atr = self._calculate_smoothed_ma(tr, period)
        plus_dm_smooth = self._calculate_smoothed_ma(plus_dm, period)
        minus_dm_smooth = self._calculate_smoothed_ma(minus_dm, period)
        
        # +DI, -DI
        plus_di = np.zeros(n)
        minus_di = np.zeros(n)
        dx = np.zeros(n)
        
        for i in range(period, n):
            if atr[i] != 0:
                plus_di[i] = 100 * plus_dm_smooth[i] / atr[i]
                minus_di[i] = 100 * minus_dm_smooth[i] / atr[i]
            
            di_sum = plus_di[i] + minus_di[i]
            if di_sum != 0:
                dx[i] = 100 * abs(plus_di[i] - minus_di[i]) / di_sum
        
        adx = self._calculate_smoothed_ma(dx, period)
        
        return adx, plus_di, minus_di
    
    def _calculate_smoothed_ma(self, data: np.ndarray, period: int) -> np.ndarray:
        """ Smoothed Moving Average (Wilder's)"""
        result = np.zeros(len(data))
        if len(data) < period:
            return result
        
        result[period-1] = np.sum(data[:period])
        for i in range(period, len(data)):
            result[i] = result[i-1] - (result[i-1] / period) + data[i]
        
        return result / period
    
    def _calculate_atr(
        self, 
        high: np.ndarray, 
        low: np.ndarray, 
        close: np.ndarray
    ) -> np.ndarray:
        """ ATR"""
        n = len(close)
        tr = np.zeros(n)
        
        for i in range(1, n):
            h_l = high[i] - low[i]
            h_pc = abs(high[i] - close[i-1])
            l_pc = abs(low[i] - close[i-1])
            tr[i] = max(h_l, h_pc, l_pc)
        
        atr = np.zeros(n)
        if n >= self.atr_period:
            atr[self.atr_period-1] = np.mean(tr[1:self.atr_period])
            multiplier = 2 / (self.atr_period + 1)
            for i in range(self.atr_period, n):
                atr[i] = (tr[i] * multiplier) + (atr[i-1] * (1 - multiplier))
        
        return atr
    
    def _calculate_volume_profile(
        self, 
        volume: np.ndarray, 
        close: np.ndarray,
        period: int = 20
    ) -> Dict[str, float]:
        """"""
        if len(volume) < period:
            return {'relative_volume': 1.0, 'volume_trend': 0.0}
        
        recent_vol = volume[-period:]
        avg_vol = np.mean(volume[-period*3:-period]) if len(volume) >= period*3 else np.mean(recent_vol)
        
        current_vol = volume[-1]
        relative_volume = current_vol / avg_vol if avg_vol > 0 else 1.0
        
        # 
        vol_sma_short = np.mean(volume[-5:])
        vol_sma_long = np.mean(volume[-20:])
        volume_trend = (vol_sma_short - vol_sma_long) / vol_sma_long if vol_sma_long > 0 else 0
        
        return {
            'relative_volume': float(relative_volume),
            'volume_trend': float(volume_trend * 100),
        }
    
    # ========================
    # 1. 
    # ========================
    
    def analyze_market(
        self, 
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """分析市場趨勢 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離分析邏輯模塊
        """
        self.state = StrategyState.ANALYZING
        
        # 準備價格數據
        price_data = self._prepare_price_data(ohlcv_data)
        
        # 計算技術指標
        indicators = self._calculate_trend_indicators(price_data)
        
        # 分析趨勢
        trend = self._analyze_trend_signals(indicators, price_data['current_price'])
        
        # 確定市場狀態
        market_condition = self._determine_market_condition(trend)
        
        # 計算關鍵水準
        key_levels = self._calculate_key_levels(price_data, indicators)
        
        self.state = StrategyState.IDLE
        self._last_analysis_time = datetime.now()
        
        return {
            'market_condition': market_condition,
            'trend_direction': trend.primary_trend,
            'trend_strength': trend.primary_trend_strength,
            'volatility': self._assess_volatility(indicators['atr']),
            'key_levels': key_levels,
            'trend_analysis': trend,
            'indicators': self._format_indicators(indicators),
            'volume_profile': indicators['volume_profile'],
            'current_price': price_data['current_price'],
            'analysis_summary': self._generate_analysis_summary(trend, market_condition),
        }
    
    def _prepare_price_data(self, ohlcv_data: np.ndarray) -> Dict[str, Any]:
        """準備價格數據"""
        return {
            'open': ohlcv_data[:, 1],
            'high': ohlcv_data[:, 2],
            'low': ohlcv_data[:, 3],
            'close': ohlcv_data[:, 4],
            'volume': ohlcv_data[:, 5],
            'current_price': float(ohlcv_data[:, 4][-1])
        }
    
    def _calculate_trend_indicators(self, price_data: Dict) -> Dict[str, Any]:
        """計算趨勢指標"""
        close = price_data['close']
        high = price_data['high']
        low = price_data['low']
        volume = price_data['volume']
        
        # EMA指標
        ema21 = self._calculate_ema(close, self.ema_periods['fast'])
        ema55 = self._calculate_ema(close, self.ema_periods['medium'])
        ema200 = self._calculate_ema(close, self.ema_periods['slow'])
        
        # MACD指標
        macd_line, signal_line, histogram = self._calculate_macd(close)
        
        # ADX指標
        adx, plus_di, minus_di = self._calculate_adx(high, low, close)
        
        # ATR和成交量
        atr = self._calculate_atr(high, low, close)
        volume_profile = self._calculate_volume_profile(volume, close)
        
        return {
            'ema21': ema21, 'ema55': ema55, 'ema200': ema200,
            'macd_line': macd_line, 'signal_line': signal_line, 'histogram': histogram,
            'adx': adx, 'plus_di': plus_di, 'minus_di': minus_di,
            'atr': atr, 'volume_profile': volume_profile
        }
    
    def _analyze_trend_signals(self, indicators: Dict, current_price: float) -> TrendAnalysis:
        """分析趨勢信號"""
        trend = TrendAnalysis()
        
        # EMA趨勢分析
        trend.price_above_ema21 = current_price > indicators['ema21'][-1]
        trend.price_above_ema55 = current_price > indicators['ema55'][-1]
        trend.price_above_ema200 = (current_price > indicators['ema200'][-1] 
                                   if not np.isnan(indicators['ema200'][-1]) else True)
        trend.ema21_above_ema55 = indicators['ema21'][-1] > indicators['ema55'][-1]
        trend.ema55_above_ema200 = (indicators['ema55'][-1] > indicators['ema200'][-1] 
                                   if not np.isnan(indicators['ema200'][-1]) else True)
        
        # MACD趨勢分析
        trend.macd_above_signal = indicators['macd_line'][-1] > indicators['signal_line'][-1]
        trend.macd_histogram_rising = (indicators['histogram'][-1] > indicators['histogram'][-2] 
                                     if len(indicators['histogram']) > 1 else False)
        trend.macd_bullish = (indicators['macd_line'][-1] > 0 and trend.macd_above_signal)
        
        # ADX趨勢分析
        trend.adx_value = indicators['adx'][-1] if not np.isnan(indicators['adx'][-1]) else 0
        trend.adx_trending = trend.adx_value > self.min_adx_for_trend
        trend.plus_di_above_minus = indicators['plus_di'][-1] > indicators['minus_di'][-1]
        
        # 計算趨勢強度和方向
        self._calculate_trend_strength(trend, indicators)
        
        return trend
    
    def _calculate_trend_strength(self, trend: TrendAnalysis, indicators: Dict):
        """計算趨勢強度"""
        bullish_signals = sum([
            trend.price_above_ema21, trend.price_above_ema55, trend.price_above_ema200,
            trend.ema21_above_ema55, trend.ema55_above_ema200,
            trend.macd_bullish, trend.macd_histogram_rising, trend.plus_di_above_minus
        ])
        
        bearish_signals = 8 - bullish_signals
        
        if bullish_signals >= 6:
            trend.primary_trend = "bullish"
            trend.primary_trend_strength = min(100, (bullish_signals / 8) * 100 * (1 + trend.adx_value / 50))
        elif bearish_signals >= 6:
            trend.primary_trend = "bearish" 
            trend.primary_trend_strength = min(100, (bearish_signals / 8) * 100 * (1 + trend.adx_value / 50))
        else:
            trend.primary_trend = "neutral"
            trend.primary_trend_strength = abs(bullish_signals - bearish_signals) / 8 * 100
        
        # 計算動量分數
        self._calculate_momentum_score(trend, indicators)
    
    def _calculate_momentum_score(self, trend: TrendAnalysis, indicators: Dict):
        """計算動量分數"""
        momentum = 0
        if trend.price_above_ema21:
            momentum += 25
        if trend.macd_histogram_rising:
            momentum += 25 if trend.macd_bullish else -25
        if trend.plus_di_above_minus:
            momentum += 25
        if indicators['volume_profile']['relative_volume'] > 1.2:
            momentum += 25 if trend.primary_trend == "bullish" else -25
        
        trend.momentum_score = momentum if trend.primary_trend == "bullish" else -momentum
    
    def _determine_market_condition(self, trend: TrendAnalysis) -> MarketCondition:
        """確定市場狀態"""
        if trend.primary_trend == "bullish" and trend.adx_trending:
            return (MarketCondition.STRONG_UPTREND if trend.primary_trend_strength >= 75 
                   else MarketCondition.UPTREND)
        elif trend.primary_trend == "bearish" and trend.adx_trending:
            return (MarketCondition.STRONG_DOWNTREND if trend.primary_trend_strength >= 75 
                   else MarketCondition.DOWNTREND)
        else:
            return MarketCondition.SIDEWAYS
    
    def _calculate_key_levels(self, price_data: Dict, indicators: Dict) -> Dict[str, Any]:
        """計算關鍵技術水準"""
        recent_high = np.max(price_data['high'][-20:])
        recent_low = np.min(price_data['low'][-20:])
        
        return {
            'resistance': float(recent_high),
            'support': float(recent_low),
            'ema21': float(indicators['ema21'][-1]),
            'ema55': float(indicators['ema55'][-1]),
            'ema200': float(indicators['ema200'][-1]) if not np.isnan(indicators['ema200'][-1]) else None,
        }
    
    def _assess_volatility(self, atr: np.ndarray) -> str:
        """評估市場波動率"""
        return 'high' if atr[-1] > np.mean(atr[-20:]) * 1.5 else 'normal'
    
    def _format_indicators(self, indicators: Dict) -> Dict[str, float]:
        """格式化指標數據"""
        return {
            'ema21': indicators['ema21'][-1],
            'ema55': indicators['ema55'][-1], 
            'ema200': indicators['ema200'][-1],
            'macd': indicators['macd_line'][-1],
            'macd_signal': indicators['signal_line'][-1],
            'macd_histogram': indicators['histogram'][-1],
            'adx': indicators['adx'][-1],
            'plus_di': indicators['plus_di'][-1],
            'minus_di': indicators['minus_di'][-1],
            'atr': indicators['atr'][-1],
        }
    
    def _generate_analysis_summary(
        self, 
        trend: TrendAnalysis, 
        market_condition: MarketCondition
    ) -> str:
        """"""
        summary = []
        
        summary.append(f": {market_condition.value}")
        summary.append(f": {trend.primary_trend} (: {trend.primary_trend_strength:.1f}%)")
        
        if trend.adx_trending:
            summary.append(f"ADX: {trend.adx_value:.1f} - ")
        else:
            summary.append(f"ADX: {trend.adx_value:.1f} - ")
        
        if trend.primary_trend == "bullish":
            confirmations = []
            if trend.price_above_ema21:
                confirmations.append(">EMA21")
            if trend.macd_bullish:
                confirmations.append("MACD")
            if trend.plus_di_above_minus:
                confirmations.append("+DI>-DI")
            summary.append(f": {', '.join(confirmations)}")
        elif trend.primary_trend == "bearish":
            confirmations = []
            if not trend.price_above_ema21:
                confirmations.append("<EMA21")
            if not trend.macd_bullish:
                confirmations.append("MACD")
            if not trend.plus_di_above_minus:
                confirmations.append("-DI>+DI")
            summary.append(f": {', '.join(confirmations)}")
        
        summary.append(f": {trend.momentum_score}")
        
        return " | ".join(summary)
    
    # ========================
    # 2. 
    # ========================
    
    def evaluate_entry_conditions(
        self,
        market_analysis: Dict[str, Any],
        ohlcv_data: np.ndarray,
    ) -> Optional[TradeSetup]:
        """評估進場條件 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離各評估模塊
        
        主要功能：
        1. 趨勢強度檢查 (ADX > 25 且 DI 確認)
        2. 趨勢排列確認 (EMA 順序)
        3. MACD 動量確認
        4. 價格位置確認
        5. 成交量確認
        """
        # 基礎數據驗證
        trend, indicators, volume_profile, current_price = self._extract_analysis_data(market_analysis)
        if not self._validate_trend_prerequisites(trend, current_price):
            return None
        
        # 類型檢查（確保不為 None）
        if trend is None or current_price is None:
            return None
        
        # 確定交易方向
        direction = 'long' if trend.primary_trend == "bullish" else 'short'
        
        # 評估進場條件 (Extract Method)
        entry_conditions, confirmations = self._evaluate_all_entry_criteria(
            trend, direction, volume_profile, indicators, current_price
        )
        
        # 檢查確認數量
        if confirmations < self.required_confirmations:
            logger.debug(f": {confirmations}/{self.required_confirmations}")
            return None
        
        # 計算風險管理參數
        stop_loss, tp1, tp2, tp3 = self._calculate_risk_reward_levels(
            current_price, direction, indicators
        )
        
        # 確定信號強度
        signal_strength = self._determine_signal_strength(confirmations, trend)
        
        # 創建交易設定
        return self._create_trade_setup(
            market_analysis, direction, current_price, entry_conditions,
            confirmations, stop_loss, tp1, tp2, tp3, signal_strength
        )
    
    def _extract_analysis_data(self, market_analysis: Dict[str, Any]):
        """提取分析數據"""
        return (
            market_analysis.get('trend_analysis'),
            market_analysis.get('indicators', {}),
            market_analysis.get('volume_profile', {}),
            market_analysis.get('current_price')
        )
    
    def _validate_trend_prerequisites(self, trend, current_price) -> bool:
        """驗證趨勢前提條件"""
        if not trend or not current_price:
            return False
        
        if trend.primary_trend == "neutral":
            logger.debug("")
            return False
        
        if not trend.adx_trending:
            logger.debug(f"ADX {trend.adx_value:.1f} < {self.min_adx_for_trend}")
            return False
        
        return True
    
    def _evaluate_all_entry_criteria(
        self, trend, direction: str, volume_profile: dict, 
        indicators: dict, current_price: float
    ) -> Tuple[List[str], int]:
        """評估所有進場標準"""
        entry_conditions = []
        confirmations = 0
        
        # EMA 排列確認
        ema_result = self._check_ema_alignment(trend, direction)
        if ema_result:
            entry_conditions.append(ema_result)
            confirmations += 1
        
        # 價格位置確認
        price_result = self._check_price_position(trend, direction)
        if price_result:
            entry_conditions.append(price_result)
            confirmations += 1
        
        # MACD 確認
        macd_result = self._check_macd_confirmation(trend, direction)
        if macd_result:
            entry_conditions.append(macd_result)
            confirmations += 1
        
        # ADX/DI 確認
        adx_result = self._check_adx_di_confirmation(trend, direction)
        if adx_result:
            entry_conditions.append(adx_result)
            confirmations += 1
        
        # 成交量確認
        volume_result = self._check_volume_confirmation(volume_profile)
        if volume_result:
            entry_conditions.append(volume_result)
            confirmations += 1
        
        # 價格回測確認
        pullback_result = self._check_pullback_entry(indicators, direction, current_price)
        if pullback_result:
            entry_conditions.append(pullback_result)
            confirmations += 1
        
        return entry_conditions, confirmations
    
    def _check_ema_alignment(self, trend, direction: str) -> Optional[str]:
        """檢查 EMA 排列"""
        if direction == 'long':
            if trend.ema21_above_ema55 and trend.ema55_above_ema200:
                return "EMA  (21>55>200)"
        else:
            if not trend.ema21_above_ema55 and not trend.ema55_above_ema200:
                return "EMA  (21<55<200)"
        return None
    
    def _check_price_position(self, trend, direction: str) -> Optional[str]:
        """檢查價格位置"""
        if direction == 'long':
            if trend.price_above_ema21 and trend.price_above_ema55:
                return " EMA21/55 "
        else:
            if not trend.price_above_ema21 and not trend.price_above_ema55:
                return " EMA21/55 "
        return None
    
    def _check_macd_confirmation(self, trend, direction: str) -> Optional[str]:
        """檢查 MACD 確認"""
        if direction == 'long':
            if trend.macd_bullish and trend.macd_histogram_rising:
                return "MACD "
        else:
            if not trend.macd_bullish and not trend.macd_histogram_rising:
                return "MACD "
        return None
    
    def _check_adx_di_confirmation(self, trend, direction: str) -> Optional[str]:
        """檢查 ADX/DI 確認"""
        if direction == 'long':
            if trend.plus_di_above_minus:
                return f"+DI > -DI (ADX: {trend.adx_value:.1f})"
        else:
            if not trend.plus_di_above_minus:
                return f"-DI > +DI (ADX: {trend.adx_value:.1f})"
        return None
    
    def _check_volume_confirmation(self, volume_profile: dict) -> Optional[str]:
        """檢查成交量確認"""
        rel_vol = volume_profile.get('relative_volume', 1.0)
        if rel_vol > 1.1:
            return f" ({rel_vol:.1f}x)"
        return None
    
    def _check_pullback_entry(self, indicators: dict, direction: str, current_price: float) -> Optional[str]:
        """檢查回調進場機會"""
        ema21 = indicators.get('ema21')
        if not ema21:
            return None
        
        if direction == 'long':
            if current_price < ema21 * 1.02 and current_price > ema21 * 0.98:
                return " EMA21 "
        else:
            if current_price > ema21 * 0.98 and current_price < ema21 * 1.02:
                return " EMA21 "
        return None
    
    def _calculate_risk_reward_levels(
        self, current_price: float, direction: str, indicators: dict
    ) -> Tuple[float, float, float, float]:
        """計算風險回報水平"""
        atr = indicators.get('atr', 0)
        
        # 止損計算
        if direction == 'long':
            stop_loss = current_price - (atr * 2)
        else:
            stop_loss = current_price + (atr * 2)
        
        # 止盈計算
        risk_per_unit = abs(current_price - stop_loss)
        
        if direction == 'long':
            tp1 = current_price + (risk_per_unit * self.take_profit_r_multiples[0])
            tp2 = current_price + (risk_per_unit * self.take_profit_r_multiples[1])
            tp3 = current_price + (risk_per_unit * self.take_profit_r_multiples[2])
        else:
            tp1 = current_price - (risk_per_unit * self.take_profit_r_multiples[0])
            tp2 = current_price - (risk_per_unit * self.take_profit_r_multiples[1])
            tp3 = current_price - (risk_per_unit * self.take_profit_r_multiples[2])
        
        return stop_loss, tp1, tp2, tp3
    
    def _determine_signal_strength(self, confirmations: int, trend) -> SignalStrength:
        """確定信號強度"""
        if confirmations >= 6 and trend.adx_value > 35:
            return SignalStrength.VERY_STRONG
        elif confirmations >= 5:
            return SignalStrength.STRONG
        elif confirmations >= 4:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _create_trade_setup(
        self, market_analysis: Dict[str, Any], direction: str, current_price: float,
        entry_conditions: List[str], confirmations: int, stop_loss: float,
        tp1: float, tp2: float, tp3: float, signal_strength: SignalStrength
    ) -> TradeSetup:
        """創建交易設定"""
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
            key_levels=market_analysis.get('key_levels', {}),
            invalidation_conditions=[
                f" {stop_loss:.2f}",
                f"ADX  {self.min_adx_for_trend} ",
                "EMA ",
            ],
        )
        
        logger.info(
            f": "
            f"{direction.upper()} @ {current_price:.2f}, "
            f": {confirmations}, : {signal_strength.name}"
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
        """
        
        
        
        1. 
        2. 
        3. 
        """
        try:
            # ID
            trade_id = f"TF_{setup.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 
            execution = TradeExecution(
                trade_id=trade_id,
                setup=setup,
            )
            
            # 
            portion_size = setup.total_position_size / setup.entry_portions
            
            # 
            if connector is None:
                # 
                logger.info(f": {trade_id}")
                execution.actual_entry_price = setup.entry_price
                execution.current_position_size = portion_size
                execution.average_entry_price = setup.entry_price
                execution.entry_fills.append({
                    'price': setup.entry_price,
                    'size': portion_size,
                    'time': datetime.now().isoformat(),
                    'type': 'market',
                })
            else:
                # 
                #  ()
                order_result = connector.place_order(
                    symbol=setup.symbol,
                    side='BUY' if setup.direction == 'long' else 'SELL',
                    order_type='LIMIT',
                    quantity=portion_size,
                    price=setup.entry_price,
                )
                
                if order_result.get('status') == 'FILLED':
                    fill_price = float(order_result.get('avgPrice', setup.entry_price))
                    execution.actual_entry_price = fill_price
                    execution.entry_slippage = abs(fill_price - setup.entry_price)
                    execution.current_position_size = portion_size
                    execution.average_entry_price = fill_price
                    execution.entry_fills.append({
                        'order_id': order_result.get('orderId'),
                        'price': fill_price,
                        'size': portion_size,
                        'time': datetime.now().isoformat(),
                        'type': 'limit',
                    })
                    
                    # 
                    stop_order = connector.place_order(
                        symbol=setup.symbol,
                        side='SELL' if setup.direction == 'long' else 'BUY',
                        order_type='STOP_MARKET',
                        quantity=portion_size,
                        stop_price=setup.stop_loss,
                        reduce_only=True,
                    )
                    
                    logger.info(f": {stop_order.get('orderId')}")
            
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
        """管理趨勢跟隨倉位 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離倉位管理邏輯
        """
        mgmt = PositionManagement()
        setup = trade.setup
        
        # 更新價格記錄
        self._update_price_records(trade, current_price, setup)
        
        # 各種倉位管理操作
        self._handle_breakeven_protection(mgmt, trade, setup)
        self._handle_trailing_stop_tf(mgmt, trade, current_price)
        self._handle_profit_taking(mgmt, setup, current_price)
        self._consider_position_scaling(mgmt, trade, ohlcv_data)
        
        return mgmt
    
    def _update_price_records(self, trade: TradeExecution, current_price: float, setup):
        """更新價格記錄和最大有利偏移"""
        risk_per_unit = abs(setup.entry_price - setup.stop_loss)
        
        if setup.direction == 'long':
            trade.highest_price_since_entry = max(
                trade.highest_price_since_entry, 
                current_price
            )
            trade.max_favorable_excursion = max(
                trade.max_favorable_excursion,
                (trade.highest_price_since_entry - setup.entry_price) / risk_per_unit
            )
        else:
            trade.lowest_price_since_entry = min(
                trade.lowest_price_since_entry,
                current_price
            )
            trade.max_favorable_excursion = max(
                trade.max_favorable_excursion,
                (setup.entry_price - trade.lowest_price_since_entry) / risk_per_unit
            )
    
    def _handle_breakeven_protection(self, mgmt: PositionManagement, trade: TradeExecution, setup):
        """處理保本保護（達到1R後）"""
        r_multiple = trade.calculate_r_multiple()
        if r_multiple >= 1.0 and not mgmt.stop_loss_moved_to_breakeven:
            risk_per_unit = abs(setup.entry_price - setup.stop_loss)
            new_stop = setup.entry_price
            
            if setup.direction == 'long':
                new_stop += risk_per_unit * 0.1  # 略微保本上方
            else:
                new_stop -= risk_per_unit * 0.1
            
            mgmt.stop_loss_moved_to_breakeven = True
            mgmt.current_stop_loss = new_stop
            logger.info(f"移至保本停損: {new_stop:.2f}")
    
    def _handle_trailing_stop_tf(self, mgmt: PositionManagement, trade: TradeExecution, current_price: float):
        """處理追蹤停損"""
        new_trailing = self.update_trailing_stop(trade, current_price)
        if new_trailing:
            mgmt.stop_loss_trailing = True
            mgmt.current_stop_loss = new_trailing
            logger.info(f"更新追蹤停損: {new_trailing:.2f}")
    
    def _handle_profit_taking(self, mgmt: PositionManagement, setup, current_price: float):
        """處理分批止盈"""
        if setup.direction == 'long':
            self._handle_long_profit_taking(mgmt, setup, current_price)
        else:
            self._handle_short_profit_taking(mgmt, setup, current_price)
    
    def _handle_long_profit_taking(self, mgmt: PositionManagement, setup, current_price: float):
        """處理多頭分批止盈"""
        if current_price >= setup.take_profit_1 and not mgmt.tp1_filled:
            mgmt.tp1_filled = True
            mgmt.exit_portions_filled += 1
            logger.info(f"觸發 TP1 {setup.take_profit_1:.2f}")
        
        if current_price >= setup.take_profit_2 and not mgmt.tp2_filled:
            mgmt.tp2_filled = True
            mgmt.exit_portions_filled += 1
            logger.info(f"觸發 TP2 {setup.take_profit_2:.2f}")
        
        if current_price >= setup.take_profit_3 and not mgmt.tp3_filled:
            mgmt.tp3_filled = True
            mgmt.exit_portions_filled += 1
            logger.info(f"觸發 TP3 {setup.take_profit_3:.2f}")
    
    def _handle_short_profit_taking(self, mgmt: PositionManagement, setup, current_price: float):
        """處理空頭分批止盈"""
        if current_price <= setup.take_profit_1 and not mgmt.tp1_filled:
            mgmt.tp1_filled = True
            mgmt.exit_portions_filled += 1
        
        if current_price <= setup.take_profit_2 and not mgmt.tp2_filled:
            mgmt.tp2_filled = True
            mgmt.exit_portions_filled += 1
        
        if current_price <= setup.take_profit_3 and not mgmt.tp3_filled:
            mgmt.tp3_filled = True
            mgmt.exit_portions_filled += 1
    
    def _consider_position_scaling(self, mgmt: PositionManagement, trade: TradeExecution, ohlcv_data: np.ndarray):
        """考慮倉位加碼"""
        r_multiple = trade.calculate_r_multiple()
        if r_multiple < 1.0 or mgmt.entry_portions_filled >= mgmt.entry_portions_total:
            return
        
        # 檢查EMA21回調機會
        close = ohlcv_data[:, 4]
        if len(close) >= 21:
            ema21 = self._calculate_ema(close, 21)[-1]
            setup = trade.setup
            current_price = close[-1]
            
            if setup.direction == 'long':
                if current_price <= ema21 * 1.01:  # 回調至EMA21附近
                    mgmt.scaling_in_allowed = True
                    logger.info("加倉機會: 價格回調至EMA21")
            else:
                if current_price >= ema21 * 0.99:
                    mgmt.scaling_in_allowed = True
    
    # ========================
    # 5. 
    # ========================
    
    def evaluate_exit_conditions(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> Tuple[bool, str]:
        """
        
        
        
        1. 
        2. 
        3. 
        4. 
        5. 
        """
        setup = trade.setup
        
        # 1. 
        if setup.direction == 'long':
            active_stop = trade.trailing_stop_price or setup.stop_loss
            if current_price <= active_stop:
                return True, f" @ {current_price:.2f} (: {active_stop:.2f})"
        else:
            active_stop = trade.trailing_stop_price or setup.stop_loss
            if current_price >= active_stop:
                return True, f" @ {current_price:.2f} (: {active_stop:.2f})"
        
        # 2. 
        should_time_exit, time_reason = self.check_time_based_exit(trade)
        if should_time_exit:
            return True, time_reason
        
        # 3. 
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        
        if len(close) >= 26:
            # MACD 
            macd_line, signal_line, _ = self._calculate_macd(close)
            
            if setup.direction == 'long':
                # MACD 
                if macd_line[-1] < signal_line[-1] and macd_line[-2] > signal_line[-2]:
                    # 
                    if trade.calculate_r_multiple() >= 1.0:
                        return True, "MACD "
            else:
                # MACD 
                if macd_line[-1] > signal_line[-1] and macd_line[-2] < signal_line[-2]:
                    if trade.calculate_r_multiple() >= 1.0:
                        return True, "MACD "
        
        # 4. ADX 
        if len(close) >= self.adx_period * 2:
            adx, plus_di, minus_di = self._calculate_adx(high, low, close)
            current_adx = adx[-1]
            prev_adx = adx[-5] if len(adx) >= 5 else current_adx
            
            # ADX  30% 
            if current_adx < prev_adx * 0.7 and current_adx < self.min_adx_for_trend:
                if trade.calculate_r_multiple() >= 1.5:
                    return True, f" (ADX: {current_adx:.1f})"
        
        # 5. 
        # 
        
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
        """
        
        """
        try:
            exit_size = trade.current_position_size * exit_portion
            
            if connector is None:
                # 
                logger.info(f": {trade.trade_id}, : {reason}")
                
                # 
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
                # 
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
            
            # 
            if trade.current_position_size <= 0:
                trade.exit_time = datetime.now()
                trade.exit_reason = reason
                trade.holding_duration = trade.exit_time - trade.entry_time
                
                # 
                self.performance.update(trade)
                self.trade_history.append(trade)
                
                # 
                if trade.realized_pnl < 0:
                    self._cooldown_until = datetime.now() + timedelta(
                        hours=self.risk_params.cooldown_after_loss
                    )
                
                self.state = StrategyState.IDLE
                
                logger.info(
                    f": {trade.trade_id}, "
                    f"PnL: {trade.realized_pnl:.2f}, "
                    f"R: {trade.calculate_r_multiple():.2f}, "
                    f": {reason}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f": {e}")
            return False


# 
StrategyRegistry.register('trend_following', TrendFollowingStrategy)
