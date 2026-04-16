"""
均值回歸策略 (Mean Reversion Strategy)
=======================================

核心理念：
價格偏離平均值後，會回歸到平均值附近。

適用場景：
- 震盪市場（Range-bound Market）
- 低波動環境
- 橫盤整理階段

策略邏輯：
1. 計算移動平均線作為"平均值"
2. Z-Score 檢測價格偏離程度
3. 布林帶識別超買超賣區域
4. 均值回歸信號觸發交易

技術指標：
- Bollinger Bands
- Keltner Channel
- Z-Score
- RSI 輔助確認
"""

from __future__ import annotations

import numpy as np
import logging
from typing import Optional, Dict, Any, Tuple, List, Callable, cast
from datetime import datetime, timedelta
from dataclasses import dataclass
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

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class MeanReversionAnalysis:
    """"""
    # 
    bb_upper: float = 0.0
    bb_middle: float = 0.0
    bb_lower: float = 0.0
    bb_width: float = 0.0
    bb_percent_b: float = 0.5  #  (0-1)
    bb_squeeze: bool = False   # 
    
    # Keltner Channel
    kc_upper: float = 0.0
    kc_middle: float = 0.0
    kc_lower: float = 0.0
    
    #  (Bollinger in Keltner)
    squeeze_on: bool = False
    squeeze_off: bool = False
    squeeze_momentum: float = 0.0
    
    # Z-Score
    z_score: float = 0.0
    z_score_extreme: bool = False  # |z| > 2
    z_score_very_extreme: bool = False  # |z| > 3
    
    # 
    sma_20: float = 0.0
    sma_50: float = 0.0
    price_deviation_from_mean: float = 0.0  # 
    
    # RSI 
    rsi_value: float = 50.0
    rsi_extreme: bool = False
    
    # 
    reversal_candle: bool = False
    reversal_type: str = "none"  # 'hammer', 'shooting_star', 'engulfing', etc.
    
    # 
    volume_spike: bool = False
    relative_volume: float = 1.0


class MeanReversionStrategy(BaseStrategy):
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
    ) -> None:
        super().__init__(
            name="Mean Reversion",
            timeframe=timeframe,
            risk_params=risk_params or RiskParameters(
                max_risk_per_trade_pct=1.0,
                min_risk_reward_ratio=2.0,
                trailing_stop_activation=1.5,
                trailing_stop_distance=0.5,
                max_holding_period_hours=72,  # 3 
            ),
        )
        
        # 
        self.bb_period = 20
        self.bb_std_dev = 2.0
        
        # Keltner Channel 
        self.kc_period = 20
        self.kc_atr_multiplier = 1.5
        
        # Z-Score 
        self.z_lookback = 20
        self.z_extreme_threshold = 2.0
        self.z_very_extreme_threshold = 2.5
        
        # RSI 
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.rsi_extreme_overbought = 80
        self.rsi_extreme_oversold = 20
        
        # 
        self.required_confirmations = 3
        
        #  ()
        self.take_profit_r_multiples: List[float] = [2.0, 3.0, 4.0]
        self.exit_portions: List[float] = [0.40, 0.35, 0.25]
    
    # ========================
    # 
    # ========================
    
    def _calculate_bollinger_bands(
        self,
        close: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """"""
        n: int = len(close)
        middle: np.ndarray = np.zeros(n)
        upper: np.ndarray = np.zeros(n)
        lower: np.ndarray = np.zeros(n)
        
        for i in range(period - 1, n):
            window: np.ndarray = close[i - period + 1:i + 1]
            middle[i] = np.mean(window)
            std = np.std(window)
            upper[i] = middle[i] + (std * std_dev)
            lower[i] = middle[i] - (std * std_dev)
        
        return upper, middle, lower
    
    def _calculate_keltner_channel(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 20,
        atr_mult: float = 1.5
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """ Keltner Channel"""
        n: int = len(close)
        
        # EMA 
        ema: np.ndarray = np.zeros(n)
        multiplier: float = 2 / (period + 1)
        ema[period - 1] = np.mean(close[:period])
        for i in range(period, n):
            ema[i] = (close[i] * multiplier) + (ema[i - 1] * (1 - multiplier))
        
        # ATR
        atr: np.ndarray = np.zeros(n)
        for i in range(1, n):
            h_l = high[i] - low[i]
            h_pc = abs(high[i] - close[i - 1])
            l_pc = abs(low[i] - close[i - 1])
            atr[i] = max(h_l, h_pc, l_pc)
        
        #  ATR
        atr_smooth: np.ndarray = np.zeros(n)
        if n >= period:
            atr_smooth[period - 1] = np.mean(atr[1:period])
            for i in range(period, n):
                atr_smooth[i] = (atr_smooth[i - 1] * (period - 1) + atr[i]) / period
        
        upper = ema + (atr_smooth * atr_mult)
        lower = ema - (atr_smooth * atr_mult)
        
        return upper, ema, lower
    
    def _calculate_z_score(
        self,
        close: np.ndarray,
        period: int = 20
    ) -> np.ndarray:
        """ Z-Score"""
        n: int = len(close)
        z_score: np.ndarray = np.zeros(n)
        
        for i in range(period - 1, n):
            window: np.ndarray = close[i - period + 1:i + 1]
            mean = np.mean(window)
            std = np.std(window)
            if std > 0:
                z_score[i] = (close[i] - mean) / std
        
        return z_score
    
    def _calculate_rsi(self, close: np.ndarray, period: int = 14) -> np.ndarray:
        """ RSI"""
        n: int = len(close)
        if n < period + 1:
            return cast(np.ndarray, np.full(n, 50.0))

        deltas: np.ndarray = np.diff(close)
        gains: np.ndarray = np.where(deltas > 0, deltas, 0)
        losses: np.ndarray = np.where(deltas < 0, -deltas, 0)
        
        avg_gain: np.ndarray = np.zeros(n)
        avg_loss: np.ndarray = np.zeros(n)
        
        avg_gain[period] = np.mean(gains[:period])
        avg_loss[period] = np.mean(losses[:period])
        
        for i in range(period + 1, n):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period
        
        with np.errstate(divide='ignore', invalid='ignore'):
            rs: np.ndarray = np.divide(
                avg_gain,
                avg_loss,
                out=np.full(n, 100.0, dtype=np.float64),
                where=avg_loss != 0,
            )
        rsi: np.ndarray = 100 - (100 / (1 + rs))
        rsi[:period] = 50
        
        return cast(np.ndarray, rsi)
    
    def _detect_reversal_candle(
        self,
        open_prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> Tuple[bool, str]:
        """檢測反轉K線模式 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離各種K線模式檢測
        """
        if len(close) < 3:
            return False, "none"
        
        # 準備K線數據
        candle_data = self._prepare_candle_data(open_prices, high, low, close)
        if not candle_data:
            return False, "none"
        
        # 檢測各種反轉模式
        reversal_patterns = [
            self._check_hammer_pattern,
            self._check_shooting_star_pattern,
            self._check_bullish_engulfing_pattern,
            self._check_bearish_engulfing_pattern,
            self._check_doji_pattern
        ]
        
        for check_pattern in reversal_patterns:
            is_reversal, pattern_name = check_pattern(candle_data)
            if is_reversal:
                return True, pattern_name
        
        return False, "none"
    
    def _prepare_candle_data(self, open_prices: np.ndarray, high: np.ndarray, 
                            low: np.ndarray, close: np.ndarray) -> Optional[Dict]:
        """準備K線分析數據"""
        o, h, lo, c = open_prices[-1], high[-1], low[-1], close[-1]
        candle_range = h - lo
        
        if candle_range == 0:
            return None
        
        body = abs(c - o)
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - lo
        body_pct = body / candle_range
        
        # 前一根K線數據
        prev_o, prev_c = open_prices[-2], close[-2]
        prev_body = abs(prev_c - prev_o)
        
        return {
            'o': o, 'h': h, 'l': lo, 'c': c,
            'body': body, 'upper_shadow': upper_shadow, 
            'lower_shadow': lower_shadow, 'body_pct': body_pct,
            'prev_o': prev_o, 'prev_c': prev_c, 'prev_body': prev_body,
            'close_3': close[-3] if len(close) >= 3 else c
        }
    
    def _check_hammer_pattern(self, data: Dict) -> Tuple[bool, str]:
        """檢測錘子線（看漲反轉）"""
        if (data['lower_shadow'] > data['body'] * 2 and 
            data['upper_shadow'] < data['body'] * 0.5 and
            data['body_pct'] < 0.3):
            # 需要在下降趨勢中出現
            if data['close_3'] > data['prev_c']:
                return True, "hammer"
        return False, ""
    
    def _check_shooting_star_pattern(self, data: Dict) -> Tuple[bool, str]:
        """檢測流星線（看跌反轉）"""
        if (data['upper_shadow'] > data['body'] * 2 and
            data['lower_shadow'] < data['body'] * 0.5 and
            data['body_pct'] < 0.3):
            # 需要在上升趨勢中出現
            if data['close_3'] < data['prev_c']:
                return True, "shooting_star"
        return False, ""
    
    def _check_bullish_engulfing_pattern(self, data: Dict) -> Tuple[bool, str]:
        """檢測看漲吞噬形態"""
        conditions = [
            data['c'] > data['o'],  # 當前為陽線
            data['prev_c'] < data['prev_o'],  # 前一根為陰線
            data['o'] < data['prev_c'],  # 低開
            data['c'] > data['prev_o'],  # 高收
            data['body'] > data['prev_body'] * 1.5  # 實體放大
        ]
        
        if all(conditions):
            return True, "bullish_engulfing"
        return False, ""
    
    def _check_bearish_engulfing_pattern(self, data: Dict) -> Tuple[bool, str]:
        """檢測看跌吞噬形態"""
        conditions = [
            data['c'] < data['o'],  # 當前為陰線
            data['prev_c'] > data['prev_o'],  # 前一根為陽線
            data['o'] > data['prev_c'],  # 高開
            data['c'] < data['prev_o'],  # 低收
            data['body'] > data['prev_body'] * 1.5  # 實體放大
        ]
        
        if all(conditions):
            return True, "bearish_engulfing"
        return False, ""
    
    def _check_doji_pattern(self, data: Dict) -> Tuple[bool, str]:
        """檢測十字星形態"""
        if data['body_pct'] < 0.1:
            return True, "doji"
        return False, ""
    
    def _calculate_squeeze(
        self,
        bb_upper: np.ndarray,
        bb_lower: np.ndarray,
        kc_upper: np.ndarray,
        kc_lower: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """"""
        n: int = len(bb_upper)
        squeeze_on: np.ndarray = np.zeros(n, dtype=bool)
        squeeze_off: np.ndarray = np.zeros(n, dtype=bool)
        
        for i in range(n):
            #  Keltner 
            if bb_lower[i] > kc_lower[i] and bb_upper[i] < kc_upper[i]:
                squeeze_on[i] = True
            #  Keltner 
            elif i > 0 and squeeze_on[i - 1]:
                squeeze_off[i] = True
        
        return squeeze_on, squeeze_off
    
    # ========================
    # 1. 
    # ========================
    
    def analyze_market(
        self,
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        市場分析主函數 - 重構後降低複雜度
        """
        self.state: StrategyState = StrategyState.ANALYZING
        
        # 提取價格數據
        open_prices, high, low, close, volume = self._extract_price_data(ohlcv_data)
        current_price = close[-1]
        
        # 初始化分析結果
        analysis = MeanReversionAnalysis()
        
        # 各項指標計算
        self._calculate_bollinger_analysis(close, current_price, analysis)
        self._calculate_keltner_analysis(high, low, close, analysis)
        self._calculate_squeeze_analysis(analysis)
        self._calculate_momentum_analysis(close, analysis)
        self._calculate_zscore_analysis(close, analysis)
        self._calculate_moving_average_analysis(close, current_price, analysis)
        self._calculate_rsi_analysis(close, analysis)
        self._calculate_reversal_analysis(open_prices, high, low, close, analysis)
        self._calculate_volume_analysis(volume, analysis)
        
        # 確定市場狀態
        market_condition = self._determine_market_condition(analysis)
        volatility_level = self._determine_volatility_level(analysis)
        
        self._finalize_analysis_state()
        self._last_analysis_time = datetime.now()
        
        return {
            'symbol': additional_data.get('symbol') if additional_data else None,
            'current_price': current_price,
            'mean_reversion_analysis': analysis,
            'market_condition': market_condition,
            'volatility': volatility_level,
            'analysis_time': self._last_analysis_time.isoformat(),
        }
    
    def _extract_price_data(self, ohlcv_data: np.ndarray) -> tuple:
        """提取價格和成交量數據"""
        open_prices = ohlcv_data[:, 1]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        close: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 4]
        volume: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 5]
        return open_prices, high, low, close, volume
    
    def _calculate_bollinger_analysis(
        self, 
        close: np.ndarray, 
        current_price: float, 
        analysis: MeanReversionAnalysis
    ) -> None:
        """計算布林帶相關指標"""
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
            close, self.bb_period, self.bb_std_dev
        )
        analysis.bb_upper = float(bb_upper[-1])
        analysis.bb_middle = float(bb_middle[-1])
        analysis.bb_lower = float(bb_lower[-1])
        
        if bb_upper[-1] != 0:
            analysis.bb_width = float((bb_upper[-1] - bb_lower[-1]) / bb_middle[-1] * 100)
            analysis.bb_percent_b = float((current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1]))
    
    def _calculate_keltner_analysis(
        self, 
        high: np.ndarray, 
        low: np.ndarray, 
        close: np.ndarray, 
        analysis: MeanReversionAnalysis
    ) -> None:
        """計算Keltner Channel相關指標"""
        kc_upper, kc_middle, kc_lower = self._calculate_keltner_channel(
            high, low, close, self.kc_period, self.kc_atr_multiplier
        )
        analysis.kc_upper = float(kc_upper[-1])
        analysis.kc_middle = float(kc_middle[-1])
        analysis.kc_lower = float(kc_lower[-1])
    
    def _calculate_squeeze_analysis(self, analysis: MeanReversionAnalysis) -> None:
        """計算壓縮指標"""
        bb_upper = np.array([analysis.bb_upper])
        bb_lower = np.array([analysis.bb_lower])
        kc_upper = np.array([analysis.kc_upper])
        kc_lower = np.array([analysis.kc_lower])
        
        squeeze_on, squeeze_off = self._calculate_squeeze(
            bb_upper, bb_lower, kc_upper, kc_lower
        )
        analysis.squeeze_on = bool(squeeze_on[-1])
        analysis.squeeze_off = bool(squeeze_off[-1])
    
    def _calculate_momentum_analysis(
        self, 
        close: np.ndarray, 
        analysis: MeanReversionAnalysis
    ) -> None:
        """計算動量分析"""
        if len(close) >= 20:
            momentum = close[-1] - np.mean(close[-20:])
            analysis.squeeze_momentum = float(momentum)
    
    def _calculate_zscore_analysis(
        self, 
        close: np.ndarray, 
        analysis: MeanReversionAnalysis
    ) -> None:
        """計算Z-Score分析"""
        z_score: np.ndarray[Tuple[Any], np.dtype[Any]] = self._calculate_z_score(close, self.z_lookback)
        analysis.z_score = float(z_score[-1])
        analysis.z_score_extreme = bool(abs(z_score[-1]) > self.z_extreme_threshold)
        analysis.z_score_very_extreme = bool(abs(z_score[-1]) > self.z_very_extreme_threshold)
    
    def _calculate_moving_average_analysis(
        self, 
        close: np.ndarray, 
        current_price: float, 
        analysis: MeanReversionAnalysis
    ) -> None:
        """計算移動平均分析"""
        if len(close) >= 20:
            analysis.sma_20 = float(np.mean(close[-20:]))
        if len(close) >= 50:
            analysis.sma_50 = float(np.mean(close[-50:]))
        
        if analysis.sma_20 > 0:
            analysis.price_deviation_from_mean = (
                (current_price - analysis.sma_20) / analysis.sma_20 * 100
            )
    
    def _calculate_rsi_analysis(
        self, 
        close: np.ndarray, 
        analysis: MeanReversionAnalysis
    ) -> None:
        """計算RSI分析"""
        rsi: np.ndarray[Tuple[Any], np.dtype[Any]] = self._calculate_rsi(close, self.rsi_period)
        analysis.rsi_value = float(rsi[-1])
        analysis.rsi_extreme = bool(
            rsi[-1] > self.rsi_extreme_overbought or 
            rsi[-1] < self.rsi_extreme_oversold
        )
    
    def _calculate_reversal_analysis(
        self, 
        open_prices: np.ndarray, 
        high: np.ndarray, 
        low: np.ndarray, 
        close: np.ndarray, 
        analysis: MeanReversionAnalysis
    ) -> None:
        """計算反轉K線分析"""
        has_reversal, reversal_type = self._detect_reversal_candle(
            open_prices, high, low, close
        )
        analysis.reversal_candle = has_reversal
        analysis.reversal_type = reversal_type
    
    def _calculate_volume_analysis(
        self, 
        volume: np.ndarray, 
        analysis: MeanReversionAnalysis
    ) -> None:
        """計算成交量分析"""
        if len(volume) >= 20:
            avg_volume = np.mean(volume[-20:])
            analysis.relative_volume = volume[-1] / avg_volume if avg_volume > 0 else 1.0
            analysis.volume_spike = analysis.relative_volume > 1.5
    
    def _determine_market_condition(self, analysis: MeanReversionAnalysis) -> MarketCondition:
        """確定市場狀態"""
        if analysis.squeeze_on:
            return MarketCondition.LOW_VOLATILITY
        elif analysis.z_score_very_extreme:
            return MarketCondition.HIGH_VOLATILITY
        elif abs(analysis.price_deviation_from_mean) < 2:
            return MarketCondition.SIDEWAYS
        elif analysis.price_deviation_from_mean > 5:
            return MarketCondition.STRONG_UPTREND
        elif analysis.price_deviation_from_mean < -5:
            return MarketCondition.STRONG_DOWNTREND
        else:
            return MarketCondition.SIDEWAYS
    
    def _determine_volatility_level(self, analysis: MeanReversionAnalysis) -> str:
        """確定波動性級別"""
        if analysis.squeeze_on:
            return 'low'
        elif analysis.bb_width > 5:
            return 'high'
        else:
            return 'medium'

    def evaluate_entry_conditions(
        self,
        market_analysis: Dict[str, Any],
        ohlcv_data: np.ndarray,
    ) -> Optional[TradeSetup]:
        """評估均值回歸進場條件

        使用 analyze_market() 產出的 MeanReversionAnalysis 執行多頭/空頭評估，
        需達到 self.required_confirmations 才建立 TradeSetup。
        """
        analysis, current_price = self._extract_mean_reversion_data(market_analysis)
        if analysis is None or current_price is None:
            return None

        # 排除趨勢市場：強趨勢下均值回歸容易被追殺
        market_condition = market_analysis.get('market_condition')
        if market_condition in (MarketCondition.STRONG_UPTREND, MarketCondition.STRONG_DOWNTREND):
            logger.debug("均值回歸：強趨勢市場，跳過進場評估")
            return None

        long_conditions, long_confirmations = self._evaluate_long_opportunities(analysis)
        short_conditions, short_confirmations = self._evaluate_short_opportunities(analysis)

        direction, entry_conditions, confirmations = self._determine_trading_direction(
            long_conditions, long_confirmations,
            short_conditions, short_confirmations,
        )

        if direction is None:
            return None

        stop_loss, tp1, tp2, tp3 = self._calculate_mean_reversion_levels(
            direction, current_price, analysis
        )

        # 確保 R:R 達到最低要求
        risk = abs(current_price - stop_loss)
        reward = abs(tp1 - current_price)
        if risk <= 0 or reward / risk < self.risk_params.min_risk_reward_ratio:
            logger.debug(
                f"均值回歸：R:R 不足 ({reward/risk:.2f} < {self.risk_params.min_risk_reward_ratio})"
            )
            return None

        signal_strength = self._determine_mr_signal_strength(confirmations, analysis)

        return self._create_mean_reversion_setup(
            market_analysis, direction, current_price,
            entry_conditions, confirmations,
            stop_loss, tp1, tp2, tp3, signal_strength, analysis,
        )

    def _generate_mr_summary(
        self,
        analysis: MeanReversionAnalysis,
        market_condition: MarketCondition
    ) -> str:
        """"""
        summary = []
        
        summary.append(f": {market_condition.value}")
        summary.append(f"Z-Score: {analysis.z_score:.2f}")
        
        if analysis.z_score_very_extreme:
            summary.append(" !")
        elif analysis.z_score_extreme:
            summary.append(" ")
        
        summary.append(f"BB %B: {analysis.bb_percent_b:.2f}")
        
        if analysis.squeeze_on or analysis.squeeze_off:
            summary.append(" ")
        
        summary.append(f"RSI: {analysis.rsi_value:.1f}")
        if analysis.rsi_extreme:
            summary.append(" ")
        
        if analysis.reversal_candle:
            summary.append(f" {analysis.reversal_type}")
        
        summary.append(f": {analysis.price_deviation_from_mean:.1f}%")
        
        return " | ".join(summary)
    
    # ========================
    # 2. 進場條件評估
    # ========================
    
    def _extract_mean_reversion_data(self, market_analysis: Dict[str, Any]) -> Tuple[Any | None, Any | None]:
        """提取均值回歸數據"""
        return (
            market_analysis.get('mean_reversion_analysis'),
            market_analysis.get('current_price')
        )
    
    def _evaluate_long_opportunities(self, analysis) -> Tuple[List[str], int]:
        """評估多頭機會"""
        long_conditions = []
        long_confirmations = 0
        
        # Z-Score 極值檢查
        z_score_result: str | None = self._check_long_z_score(analysis)
        if z_score_result:
            long_conditions.append(z_score_result)
            long_confirmations += 1
            if analysis.z_score_very_extreme:
                long_confirmations += 1
        
        # 布林帶位置檢查
        bb_result, bb_bonus = self._check_long_bollinger_bands(analysis)
        if bb_result:
            long_conditions.append(bb_result)
            long_confirmations += bb_bonus
        
        # RSI 檢查
        rsi_result: str | None = self._check_long_rsi(analysis)
        if rsi_result:
            long_conditions.append(rsi_result)
            long_confirmations += 1
        
        # 反轉燭形檢查
        candle_result: str | None = self._check_long_reversal_candle(analysis)
        if candle_result:
            long_conditions.append(candle_result)
            long_confirmations += 1
        
        # 成交量和擠壓確認
        volume_result: str | None = self._check_volume_confirmation(analysis)
        if volume_result:
            long_conditions.append(volume_result)
            long_confirmations += 1
        
        squeeze_result: str | None = self._check_long_squeeze_momentum(analysis)
        if squeeze_result:
            long_conditions.append(squeeze_result)
            long_confirmations += 1
        
        return long_conditions, long_confirmations
    
    def _evaluate_short_opportunities(self, analysis) -> Tuple[List[str], int]:
        """評估空頭機會"""
        short_conditions = []
        short_confirmations = 0
        
        # Z-Score 極值檢查
        z_score_result: str | None = self._check_short_z_score(analysis)
        if z_score_result:
            short_conditions.append(z_score_result)
            short_confirmations += 1
            if analysis.z_score_very_extreme:
                short_confirmations += 1
        
        # 布林帶位置檢查
        bb_result, bb_bonus = self._check_short_bollinger_bands(analysis)
        if bb_result:
            short_conditions.append(bb_result)
            short_confirmations += bb_bonus
        
        # RSI 檢查
        rsi_result: str | None = self._check_short_rsi(analysis)
        if rsi_result:
            short_conditions.append(rsi_result)
            short_confirmations += 1
        
        # 反轉燭形檢查
        candle_result: str | None = self._check_short_reversal_candle(analysis)
        if candle_result:
            short_conditions.append(candle_result)
            short_confirmations += 1
        
        # 成交量和擠壓確認
        volume_result: str | None = self._check_volume_confirmation(analysis)
        if volume_result:
            short_conditions.append(volume_result)
            short_confirmations += 1
        
        squeeze_result: str | None = self._check_short_squeeze_momentum(analysis)
        if squeeze_result:
            short_conditions.append(squeeze_result)
            short_confirmations += 1
        
        return short_conditions, short_confirmations
    
    def _check_long_z_score(self, analysis) -> Optional[str]:
        """檢查多頭 Z-Score 極值"""
        if analysis.z_score < -self.z_extreme_threshold:
            return f"Z-Score  ({analysis.z_score:.2f})"
        return None
    
    def _check_short_z_score(self, analysis) -> Optional[str]:
        """檢查空頭 Z-Score 極值"""
        if analysis.z_score > self.z_extreme_threshold:
            return f"Z-Score  ({analysis.z_score:.2f})"
        return None
    
    def _check_long_bollinger_bands(self, analysis) -> Tuple[Optional[str], int]:
        """檢查多頭布林帶位置"""
        if analysis.bb_percent_b < 0:
            return f" BB  (%B: {analysis.bb_percent_b:.2f})", 2
        elif analysis.bb_percent_b < 0.1:
            return f" BB  (%B: {analysis.bb_percent_b:.2f})", 1
        return None, 0
    
    def _check_short_bollinger_bands(self, analysis) -> Tuple[Optional[str], int]:
        """檢查空頭布林帶位置"""
        if analysis.bb_percent_b > 1.0:
            return f" BB  (%B: {analysis.bb_percent_b:.2f})", 2
        elif analysis.bb_percent_b > 0.9:
            return f" BB  (%B: {analysis.bb_percent_b:.2f})", 1
        return None, 0
    
    def _check_long_rsi(self, analysis) -> Optional[str]:
        """檢查多頭 RSI 極值"""
        if analysis.rsi_value < self.rsi_oversold:
            return f"RSI  ({analysis.rsi_value:.1f})"
        return None
    
    def _check_short_rsi(self, analysis) -> Optional[str]:
        """檢查空頭 RSI 極值"""
        if analysis.rsi_value > self.rsi_overbought:
            return f"RSI  ({analysis.rsi_value:.1f})"
        return None
    
    def _check_long_reversal_candle(self, analysis) -> Optional[str]:
        """檢查多頭反轉燭形"""
        if analysis.reversal_candle and analysis.reversal_type in ['hammer', 'bullish_engulfing', 'doji']:
            return f": {analysis.reversal_type}"
        return None
    
    def _check_short_reversal_candle(self, analysis) -> Optional[str]:
        """檢查空頭反轉燭形"""
        if analysis.reversal_candle and analysis.reversal_type in ['shooting_star', 'bearish_engulfing', 'doji']:
            return f": {analysis.reversal_type}"
        return None
    
    def _check_volume_confirmation(self, analysis) -> Optional[str]:
        """檢查成交量確認"""
        if analysis.volume_spike:
            return f" ({analysis.relative_volume:.1f}x)"
        return None
    
    def _check_long_squeeze_momentum(self, analysis) -> Optional[str]:
        """檢查多頭擠壓動量"""
        if analysis.squeeze_off and analysis.squeeze_momentum > 0:
            return ""
        return None
    
    def _check_short_squeeze_momentum(self, analysis) -> Optional[str]:
        """檢查空頭擠壓動量"""
        if analysis.squeeze_off and analysis.squeeze_momentum < 0:
            return ""
        return None
    
    def _determine_trading_direction(
        self, long_conditions: List[str], long_confirmations: int,
        short_conditions: List[str], short_confirmations: int
    ) -> Tuple[Optional[str], List[str], int]:
        """確定交易方向"""
        if long_confirmations >= self.required_confirmations:
            return 'long', long_conditions, long_confirmations
        elif short_confirmations >= self.required_confirmations:
            return 'short', short_conditions, short_confirmations
        else:
            logger.debug(
                f" - : {long_confirmations}, : {short_confirmations}"
            )
            return None, [], 0
    
    def _calculate_mean_reversion_levels(
        self, direction: str, current_price: float, analysis
    ) -> Tuple[float, float, float, float]:
        """計算均值回歸水平"""
        # 止損設定
        if direction == 'long':
            stop_loss = analysis.bb_lower * 0.99
        else:
            stop_loss = analysis.bb_upper * 1.01
        
        # 止盈計算
        risk_per_unit = abs(current_price - stop_loss)
        
        if direction == 'long':
            tp1 = current_price + (risk_per_unit * self.take_profit_r_multiples[0])
            tp2 = min(analysis.bb_upper, current_price + (risk_per_unit * self.take_profit_r_multiples[1]))
            tp3 = current_price + (risk_per_unit * self.take_profit_r_multiples[2])
        else:
            tp1 = current_price - (risk_per_unit * self.take_profit_r_multiples[0])
            tp2 = max(analysis.bb_lower, current_price - (risk_per_unit * self.take_profit_r_multiples[1]))
            tp3 = current_price - (risk_per_unit * self.take_profit_r_multiples[2])
        
        return stop_loss, tp1, tp2, tp3
    
    def _determine_mr_signal_strength(self, confirmations: int, analysis) -> SignalStrength:
        """確定均值回歸信號強度"""
        if confirmations >= 5 and analysis.z_score_very_extreme:
            return SignalStrength.VERY_STRONG
        elif confirmations >= 4:
            return SignalStrength.STRONG
        elif confirmations >= 3:
            return SignalStrength.MODERATE
        else:
            return SignalStrength.WEAK
    
    def _create_mean_reversion_setup(
        self, market_analysis: Dict[str, Any], direction: str, current_price: float,
        entry_conditions: List[str], confirmations: int, stop_loss: float,
        tp1: float, tp2: float, tp3: float, signal_strength: SignalStrength, analysis
    ) -> TradeSetup:
        """創建均值回歸交易設定"""
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
                'bb_upper': analysis.bb_upper,
                'bb_middle': analysis.bb_middle,
                'bb_lower': analysis.bb_lower,
                'mean': analysis.sma_20,
            },
            invalidation_conditions=[
                f" {stop_loss:.2f}",
                "Z-Score ",
                "",
            ],
        )
        
        logger.debug(
            f": "
            f"{direction.upper()} @ {current_price:.2f}, "
            f"Z={analysis.z_score:.2f}, : {confirmations}"
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
            trade_id: str = f"MR_{setup.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            execution = TradeExecution(
                trade_id=trade_id,
                setup=setup,
            )
            
            # 
            portion_size: float = setup.total_position_size / setup.entry_portions
            if portion_size <= 0:
                logger.warning(f"⚠️ 均值回歸策略忽略無效進場數量: {portion_size}")
                return None

            passed, reason = self._passes_pre_entry_guards(setup, connector)
            if not passed:
                logger.warning(f"⚠️ 均值回歸策略取消進場: {reason}")
                return None
            
            if connector is None:
                logger.info(f": {trade_id}")
                execution.actual_entry_price = setup.entry_price
                execution.current_position_size = portion_size
                execution.average_entry_price = setup.entry_price
                execution.entry_fills.append({
                    'price': setup.entry_price,
                    'size': portion_size,
                    'time': datetime.now().isoformat(),
                    'type': 'limit',
                })
            else:
                # 
                if setup.direction == 'long':
                    limit_price: float = setup.entry_price * 1.001  # 
                else:
                    limit_price = setup.entry_price * 0.999
                
                order_result = connector.place_order(
                    symbol=setup.symbol,
                    side='BUY' if setup.direction == 'long' else 'SELL',
                    order_type='LIMIT',
                    quantity=portion_size,
                    price=limit_price,
                    time_in_force='GTC',
                )
                
                if order_result.get('status') in ['FILLED', 'PARTIALLY_FILLED']:
                    fill_price = float(order_result.get('avgPrice', limit_price))
                    execution.actual_entry_price = fill_price
                    execution.current_position_size = portion_size
                    execution.average_entry_price = fill_price
                    execution.entry_fills.append({
                        'order_id': order_result.get('orderId'),
                        'price': fill_price,
                        'size': portion_size,
                        'time': datetime.now().isoformat(),
                        'type': 'limit',
                    })
                else:
                    return None
            
            execution.highest_price_since_entry = execution.actual_entry_price
            execution.lowest_price_since_entry = execution.actual_entry_price
            
            self.state = StrategyState.POSITION_OPEN
            return execution
            
        except Exception as e:
            logger.error(f"執行交易失敗: {e}")
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
        """管理均值回歸倉位 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離倉位管理邏輯
        """
        mgmt = PositionManagement()
        setup: TradeSetup = trade.setup
        
        # 更新價格追蹤
        self._update_price_tracking_mr(trade, current_price, setup)
        
        # 各種倉位管理操作
        self._handle_breakeven_stop_mr(mgmt, setup, trade)
        self._handle_trailing_stop_mr(mgmt, trade, current_price)
        self._handle_take_profits_mr(mgmt, setup, current_price)
        self._check_z_score_signals(trade, ohlcv_data)
        self._consider_scaling_in_mr(mgmt, trade, ohlcv_data)
        
        return mgmt
    
    def _update_price_tracking_mr(self, trade: TradeExecution, current_price: float, setup) -> None:
        """更新均值回歸策略的價格追蹤"""
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
    
    def _handle_breakeven_stop_mr(self, mgmt: PositionManagement, setup, trade: TradeExecution) -> None:
        """處理均值回歸保本停損"""
        r_multiple: float = trade.calculate_r_multiple()
        if r_multiple >= 1.0 and not mgmt.stop_loss_moved_to_breakeven:
            risk_per_unit = abs(setup.entry_price - setup.stop_loss)
            new_stop = setup.entry_price
            
            if setup.direction == 'long':
                new_stop += risk_per_unit * 0.05
            else:
                new_stop -= risk_per_unit * 0.05
            
            mgmt.stop_loss_moved_to_breakeven = True
            mgmt.current_stop_loss = new_stop
            logger.info(f"移至保本停損 {new_stop:.2f}")
    
    def _handle_trailing_stop_mr(self, mgmt: PositionManagement, trade: TradeExecution, current_price: float) -> None:
        """處理均值回歸追蹤停損"""
        new_trailing: float | None = self.update_trailing_stop(trade, current_price)
        if new_trailing:
            mgmt.stop_loss_trailing = True
            mgmt.current_stop_loss = new_trailing
    
    def _handle_take_profits_mr(self, mgmt: PositionManagement, setup, current_price: float) -> None:
        """處理均值回歸止盈"""
        if setup.direction == 'long':
            self._check_long_take_profits_mr(mgmt, setup, current_price)
        else:
            self._check_short_take_profits_mr(mgmt, setup, current_price)
    
    def _check_long_take_profits_mr(self, mgmt: PositionManagement, setup, current_price: float) -> None:
        """檢查多頭止盈觸發"""
        if current_price >= setup.take_profit_1 and not mgmt.tp1_filled:
            mgmt.tp1_filled = True
            mgmt.exit_portions_filled += 1
        if current_price >= setup.take_profit_2 and not mgmt.tp2_filled:
            mgmt.tp2_filled = True
            mgmt.exit_portions_filled += 1
    
    def _check_short_take_profits_mr(self, mgmt: PositionManagement, setup, current_price: float) -> None:
        """檢查空頭止盈觸發"""
        if current_price <= setup.take_profit_1 and not mgmt.tp1_filled:
            mgmt.tp1_filled = True
            mgmt.exit_portions_filled += 1
        if current_price <= setup.take_profit_2 and not mgmt.tp2_filled:
            mgmt.tp2_filled = True
            mgmt.exit_portions_filled += 1
    
    def _check_z_score_signals(self, trade: TradeExecution, ohlcv_data: np.ndarray) -> None:
        """檢查Z-Score信號"""
        close: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 4]
        if len(close) < self.z_lookback:
            return
        
        z_score: np.ndarray[Tuple[Any], np.dtype[Any]] = self._calculate_z_score(close, self.z_lookback)
        current_z = z_score[-1]
        r_multiple: float = trade.calculate_r_multiple()
        
        # 價格回歸中性，準備出場
        if abs(current_z) < 0.5 and r_multiple >= 1.0:
            logger.info(f"均值回歸信號: Z-Score 回歸中性 {current_z:.2f}")
            # 實際出場由 evaluate_exit_conditions 處理
    
    def _consider_scaling_in_mr(self, mgmt: PositionManagement, trade: TradeExecution, ohlcv_data: np.ndarray) -> None:
        """考慮均值回歸加倉"""
        r_multiple: float = trade.calculate_r_multiple()
        if (r_multiple < 0 and r_multiple > -0.5 and 
            mgmt.entry_portions_filled < mgmt.entry_portions_total):
            
            close: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 4]
            if len(close) >= self.z_lookback:
                z_score: np.ndarray[Tuple[Any], np.dtype[Any]] = self._calculate_z_score(close, self.z_lookback)
                setup: TradeSetup = trade.setup
                
                if setup.direction == 'long' and z_score[-1] < z_score[-5]:
                    # Z-Score 進一步惡化，可以加倉
                    mgmt.scaling_in_allowed = True
                    logger.info("均值回歸加倉信號：極端值進一步擴大")
    
    # ========================
    # 5. 
    # ========================
    
    def evaluate_exit_conditions(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> Tuple[bool, str]:
        """評估均值回歸出場條件 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離各出場檢查邏輯
        """
        
        # 依次檢查各種出場條件
        exit_checks: List[Callable[[], Tuple[bool, str]]] = [
            lambda: self._check_stop_loss_hit_mr(trade, current_price),
            lambda: self._check_time_exit_mr(trade),
            lambda: self._check_z_score_exit(trade, ohlcv_data),
            lambda: self._check_bollinger_mean_revert(trade, current_price, ohlcv_data),
            lambda: self._check_trend_continuation_risk(trade, current_price, ohlcv_data)
        ]
        
        for check_exit in exit_checks:
            should_exit, reason = check_exit()
            if should_exit:
                return True, reason
        
        return False, ""
    
    def _check_stop_loss_hit_mr(self, trade: TradeExecution, current_price: float) -> Tuple[bool, str]:
        """檢查停損觸發"""
        setup: TradeSetup = trade.setup
        active_stop: float = trade.trailing_stop_price or setup.stop_loss
        
        if setup.direction == 'long':
            if current_price <= active_stop:
                return True, f"停損觸發 @ {current_price:.2f}"
        else:
            if current_price >= active_stop:
                return True, f"停損觸發 @ {current_price:.2f}"
        
        return False, ""
    
    def _check_time_exit_mr(self, trade: TradeExecution) -> Tuple[bool, str]:
        """檢查時間基準出場"""
        should_time_exit, time_reason = self.check_time_based_exit(trade)
        return should_time_exit, time_reason
    
    def _check_z_score_exit(self, trade: TradeExecution, ohlcv_data: np.ndarray) -> Tuple[bool, str]:
        """檢查Z-Score回歸中位"""
        close: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 4]
        if len(close) < self.z_lookback or trade.calculate_r_multiple() < 1.5:
            return False, ""
        
        z_score: np.ndarray[Tuple[Any], np.dtype[Any]] = self._calculate_z_score(close, self.z_lookback)
        current_z = z_score[-1]
        setup: TradeSetup = trade.setup
        
        # 價格回歸到中性區間
        if -0.5 < current_z < 0.5:
            if setup.direction == 'long':
                return True, f"多頭回歸中性 (Z: {current_z:.2f})"
            elif setup.direction == 'short':
                return True, f"空頭回歸中性 (Z: {current_z:.2f})"
        
        return False, ""
    
    def _check_bollinger_mean_revert(self, trade: TradeExecution, current_price: float, 
                                    ohlcv_data: np.ndarray) -> Tuple[bool, str]:
        """檢查布林通道中軸回歸"""
        if trade.calculate_r_multiple() < 1.0:
            return False, ""
        
        close: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 4]
        _, bb_middle, _ = self._calculate_bollinger_bands(
            close, self.bb_period, self.bb_std_dev
        )
        
        setup: TradeSetup = trade.setup
        middle_price = bb_middle[-1]
        
        if setup.direction == 'long' and current_price >= middle_price:
            return True, f"多頭回歸中軸 ({middle_price:.2f})"
        elif setup.direction == 'short' and current_price <= middle_price:
            return True, f"空頭回歸中軸 ({middle_price:.2f})"
        
        return False, ""
    
    def _check_trend_continuation_risk(self, trade: TradeExecution, current_price: float,
                                      ohlcv_data: np.ndarray) -> Tuple[bool, str]:
        """檢查趨勢延續風險"""
        close: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 4]
        if len(close) < 20 or trade.calculate_r_multiple() >= -0.5:
            return False, ""
        
        sma = np.mean(close[-20:])
        setup: TradeSetup = trade.setup
        
        if setup.direction == 'long':
            # 價格持續下跌，可能成為趨勢而非回歸
            if (current_price < sma * 0.98 and 
                close[-1] < close[-5] < close[-10]):
                return True, "趨勢延續風險，停止逆勢操作"
        
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
            exit_size: float = trade.current_position_size * exit_portion
            
            if connector is None:
                logger.info(f": {trade.trade_id}, : {reason}")
                
                if trade.setup.direction == 'long':
                    pnl: float = (trade.average_exit_price - trade.average_entry_price) * exit_size
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
            logger.error(f"平倉失敗: {e}")
            return False


# 
StrategyRegistry.register('mean_reversion', MeanReversionStrategy)
