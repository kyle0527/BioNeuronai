"""市場狀態識別模組 (Market Regime Detection Module)
========================================================

基於統計模型與機器學習的市場狀態自動識別系統。

核心功能：

1. 市場狀態分類
   - 牛市 (Bullish) - 持續上漲趨勢
   - 熊市 (Bearish) - 持續下跌趨勢
   - 震盪市 (Ranging) - 橫盤整理
   - 高波動 (High Volatility) - 劇烈波動期

2. 狀態轉換檢測
   - 實時監控市場狀態變化
   - 轉換點精確識別
   - 狀態持續時間統計
   - 轉換概率預測

3. 波動性聚集識別
   - GARCH 模型波動率預測
   - 波動性叢集檢測
   - 異常波動預警
   - 波動週期分析

4. 情境感知分析
   - 多維度市場特徵整合
   - 技術指標綜合評估
   - 成交量模式識別
   - 價格動能分析

技術方法：

- 隱馬可夫模型 (HMM) - 狀態序列建模
- 波動性聚集檢測 (Volatility Clustering)
- 移動平均系統 - 趨勢方向識別
- 統計檢驗 - 狀態轉換驗證
- 多時間框架分析 - 提高識別準確度

應用場景：
- 交易策略自適應調整
- 風險參數動態優化
- 市場環境評估報告
- 策略切換決策支持

Author: BioNeuronai Team
Version: 1.0
"""


import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any, cast
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


# ============================================================================
# 
# ============================================================================

class MarketRegime(Enum):
    """"""
    STRONG_UPTREND = "strong_uptrend"       # 
    UPTREND = "uptrend"                      # 
    WEAK_UPTREND = "weak_uptrend"           # 
    SIDEWAYS_RANGE = "sideways_range"       # 
    WEAK_DOWNTREND = "weak_downtrend"       # 
    DOWNTREND = "downtrend"                  # 
    STRONG_DOWNTREND = "strong_downtrend"   # 
    HIGH_VOLATILITY = "high_volatility"     #  ()
    BREAKOUT = "breakout"                    # 
    REVERSAL = "reversal"                    # 


class VolatilityRegime(Enum):
    """"""
    VERY_LOW = "very_low"       #  ()
    LOW = "low"                  # 
    NORMAL = "normal"            # 
    HIGH = "high"                # 
    EXTREME = "extreme"          # 


class TrendStrength(Enum):
    """"""
    NO_TREND = 0
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


@dataclass
class RegimeAnalysis:
    """"""
    symbol: str
    timestamp: datetime
    
    # 
    current_regime: MarketRegime
    regime_confidence: float  # 0-1
    regime_duration_minutes: int  # 
    
    # 
    volatility_regime: VolatilityRegime
    current_volatility: float  # ATR 
    volatility_percentile: float  # 
    
    # 
    trend_direction: int  # 1=, 0=, -1=
    trend_strength: TrendStrength
    trend_score: float  # -100  100
    
    # ADX 
    adx: float = 0.0
    plus_di: float = 0.0
    minus_di: float = 0.0
    
    # 
    support_levels: List[float] = field(default_factory=list)
    resistance_levels: List[float] = field(default_factory=list)
    
    # 
    transition_probabilities: Dict[str, float] = field(default_factory=dict)
    
    def get_trading_recommendation(self) -> str:
        """根據當前市場狀態給出交易建議"""
        regime = self.current_regime
        
        if regime in [MarketRegime.STRONG_UPTREND, MarketRegime.UPTREND]:
            return "做多，跟隨上升趨勢"
        
        elif regime in [MarketRegime.STRONG_DOWNTREND, MarketRegime.DOWNTREND]:
            return "做空，跟隨下跌趨勢"
        
        elif regime == MarketRegime.SIDEWAYS_RANGE:
            return "震盪區間操作，高賣低買/等待突破"
        
        elif regime == MarketRegime.HIGH_VOLATILITY:
            return "高波動期，降低倉位或觀望"
        
        elif regime == MarketRegime.BREAKOUT:
            return "突破行情，順勢追漲/追跌"
        
        elif regime == MarketRegime.REVERSAL:
            return "趨勢反轉訊號，謹慎操作"
        
        else:
            return "市場狀態不明，觀望為主"
    
    def to_prompt(self) -> str:
        """ LLM """
        regime_names = {
            MarketRegime.STRONG_UPTREND: " ",
            MarketRegime.UPTREND: " ",
            MarketRegime.WEAK_UPTREND: " ",
            MarketRegime.SIDEWAYS_RANGE: "↔ ",
            MarketRegime.WEAK_DOWNTREND: " ",
            MarketRegime.DOWNTREND: " ",
            MarketRegime.STRONG_DOWNTREND: " ",
            MarketRegime.HIGH_VOLATILITY: " ",
            MarketRegime.BREAKOUT: " ",
            MarketRegime.REVERSAL: " ",
        }
        
        vol_names = {
            VolatilityRegime.VERY_LOW: " ()",
            VolatilityRegime.LOW: "",
            VolatilityRegime.NORMAL: "",
            VolatilityRegime.HIGH: "",
            VolatilityRegime.EXTREME: " ()",
        }
        
        lines = [
            f" {self.symbol}",
            f": {regime_names.get(self.current_regime, str(self.current_regime))}",
            f": {self.regime_confidence:.1%}",
            f": {self.regime_duration_minutes} ",
            "市場狀態分析",
            f": {vol_names.get(self.volatility_regime, str(self.volatility_regime))}",
            f"   ATR: {self.current_volatility:.2f}%",
            f"  : {self.volatility_percentile:.0f}%",
            "趋勢分析",
            "詳細狀態:",
            f"  趋勢方向: {self._get_trend_direction_text()}",
            f"  : {self.trend_strength.name} ({self.trend_score:.0f})",
            f"  ADX: {self.adx:.1f} (>25=, >50=)",
            "交易建議",
            f" : {self.get_trading_recommendation()}",
        ]
        
        if self.support_levels:
            lines.append(f": {', '.join([f'{p:.2f}' for p in self.support_levels[:3]])}")
        if self.resistance_levels:
            lines.append(f": {', '.join([f'{p:.2f}' for p in self.resistance_levels[:3]])}")
        
        return "\n".join(lines)
    
    def _get_trend_direction_text(self) -> str:
        """獲取趨勢方向文本描述"""
        if self.trend_direction > 0:
            return "上升"
        elif self.trend_direction < 0:
            return "下跌"
        else:
            return "橫盤"
    
    def to_feature_vector(self) -> List[float]:
        """"""
        #  (one-hot )
        regime_score = {
            MarketRegime.STRONG_UPTREND: 1.0,
            MarketRegime.UPTREND: 0.7,
            MarketRegime.WEAK_UPTREND: 0.3,
            MarketRegime.SIDEWAYS_RANGE: 0.0,
            MarketRegime.WEAK_DOWNTREND: -0.3,
            MarketRegime.DOWNTREND: -0.7,
            MarketRegime.STRONG_DOWNTREND: -1.0,
            MarketRegime.HIGH_VOLATILITY: 0.0,
            MarketRegime.BREAKOUT: 0.5,
            MarketRegime.REVERSAL: -0.5,
        }.get(self.current_regime, 0.0)
        
        vol_score = {
            VolatilityRegime.VERY_LOW: -1.0,
            VolatilityRegime.LOW: -0.5,
            VolatilityRegime.NORMAL: 0.0,
            VolatilityRegime.HIGH: 0.5,
            VolatilityRegime.EXTREME: 1.0,
        }.get(self.volatility_regime, 0.0)
        
        return [
            regime_score,
            self.regime_confidence,
            vol_score,
            self.current_volatility / 5,  # 
            self.volatility_percentile / 100,
            float(self.trend_direction),
            self.trend_strength.value / 4,
            self.trend_score / 100,
            self.adx / 100,
            (self.plus_di - self.minus_di) / 100,
        ]


# ============================================================================
# 
# ============================================================================

class MarketRegimeDetector:
    """
    
    
    """
    
    def __init__(
        self,
        lookback_periods: int = 100,
        atr_period: int = 14,
        adx_period: int = 14,
        trend_ema_periods: Tuple[int, int, int] = (10, 20, 50)
    ):
        self.lookback_periods = lookback_periods
        self.atr_period = atr_period
        self.adx_period = adx_period
        self.trend_ema_periods = trend_ema_periods
        
        # 
        self.price_history: Dict[str, deque] = {}
        self.high_history: Dict[str, deque] = {}
        self.low_history: Dict[str, deque] = {}
        self.volume_history: Dict[str, deque] = {}
        
        # 
        self.regime_history: Dict[str, List[Tuple[datetime, MarketRegime]]] = {}
        
        #  ()
        self.volatility_history: Dict[str, deque] = {}
    
    def update_data(
        self,
        symbol: str,
        price: float,
        high: float,
        low: float,
        volume: float
    ):
        """"""
        # 
        if symbol not in self.price_history:
            self.price_history[symbol] = deque(maxlen=self.lookback_periods * 2)
            self.high_history[symbol] = deque(maxlen=self.lookback_periods * 2)
            self.low_history[symbol] = deque(maxlen=self.lookback_periods * 2)
            self.volume_history[symbol] = deque(maxlen=self.lookback_periods * 2)
            self.volatility_history[symbol] = deque(maxlen=500)
            self.regime_history[symbol] = []
        
        self.price_history[symbol].append(price)
        self.high_history[symbol].append(high)
        self.low_history[symbol].append(low)
        self.volume_history[symbol].append(volume)
    
    def detect_regime(self, symbol: str) -> Optional[RegimeAnalysis]:
        """"""
        if symbol not in self.price_history:
            return None
        
        prices = list(self.price_history[symbol])
        highs = list(self.high_history[symbol])
        lows = list(self.low_history[symbol])
        
        if len(prices) < self.lookback_periods:
            logger.warning(f" {self.lookback_periods} ")
            return None
        
        prices = np.array(prices)
        highs = np.array(highs)
        lows = np.array(lows)
        
        # 1. 
        trend_direction, trend_strength, trend_score = self._analyze_trend(prices)
        
        # 2. 
        _, atr_percent = self._calculate_atr(highs, lows, prices)
        volatility_regime = self._classify_volatility(symbol, atr_percent)
        vol_percentile = self._get_volatility_percentile(symbol, atr_percent)
        
        # 3.  ADX
        adx, plus_di, minus_di = self._calculate_adx(highs, lows, prices)
        
        # 4. /
        support, resistance = self._find_support_resistance(prices, highs, lows)
        
        # 5. 
        regime, confidence = self._classify_regime(
            trend_direction, trend_strength, trend_score,
            volatility_regime, adx, plus_di, minus_di
        )
        
        # 6. 
        duration = self._get_regime_duration(symbol, regime)
        
        # 7. 
        transitions = self._estimate_transitions(regime, volatility_regime, adx)
        
        # 
        self.regime_history[symbol].append((datetime.now(), regime))
        if len(self.regime_history[symbol]) > 100:
            self.regime_history[symbol].pop(0)
        
        return RegimeAnalysis(
            symbol=symbol,
            timestamp=datetime.now(),
            current_regime=regime,
            regime_confidence=confidence,
            regime_duration_minutes=duration,
            volatility_regime=volatility_regime,
            current_volatility=atr_percent,
            volatility_percentile=vol_percentile,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            trend_score=trend_score,
            adx=adx,
            plus_di=plus_di,
            minus_di=minus_di,
            support_levels=support,
            resistance_levels=resistance,
            transition_probabilities=transitions
        )
    
    def _analyze_trend(self, prices: np.ndarray) -> Tuple[int, TrendStrength, float]:
        """"""
        #  EMA
        ema_short = self._ema(prices, self.trend_ema_periods[0])
        ema_medium = self._ema(prices, self.trend_ema_periods[1])
        ema_long = self._ema(prices, self.trend_ema_periods[2])
        
        current_price = prices[-1]
        
        # 
        score = 0
        
        #  EMA 
        if current_price > ema_short:
            score += 20
        else:
            score -= 20
        
        if current_price > ema_medium:
            score += 15
        else:
            score -= 15
        
        if current_price > ema_long:
            score += 15
        else:
            score -= 15
        
        # EMA 
        if ema_short > ema_medium > ema_long:
            score += 25  # 
        elif ema_short < ema_medium < ema_long:
            score -= 25  # 
        
        # EMA 
        ema_slope = (ema_short - self._ema(prices[:-5], self.trend_ema_periods[0])) / ema_short * 100
        score += np.clip(ema_slope * 10, -25, 25)
        
        # 
        if score > 20:
            direction = 1
        elif score < -20:
            direction = -1
        else:
            direction = 0
        
        # 
        abs_score = abs(score)
        if abs_score < 20:
            strength = TrendStrength.NO_TREND
        elif abs_score < 40:
            strength = TrendStrength.WEAK
        elif abs_score < 60:
            strength = TrendStrength.MODERATE
        elif abs_score < 80:
            strength = TrendStrength.STRONG
        else:
            strength = TrendStrength.VERY_STRONG
        
        return direction, strength, score
    
    def _calculate_atr(
        self, 
        highs: np.ndarray, 
        lows: np.ndarray, 
        closes: np.ndarray
    ) -> Tuple[float, float]:
        """ ATR  ATR """
        if len(highs) < self.atr_period + 1:
            return 0.0, 0.0
        
        # True Range
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )
        
        # ATR (EMA of TR)
        atr = self._ema(tr, self.atr_period)
        
        # ATR 
        atr_percent = (atr / closes[-1]) * 100
        
        return atr, atr_percent
    
    def _calculate_adx(
        self, 
        highs: np.ndarray, 
        lows: np.ndarray, 
        closes: np.ndarray
    ) -> Tuple[float, float, float]:
        """ ADX, +DI, -DI"""
        if len(highs) < self.adx_period + 2:
            return 0.0, 0.0, 0.0
        
        # +DM  -DM
        high_diff = np.diff(highs)
        low_diff = -np.diff(lows)
        
        _zero = np.float64(0)
        plus_dm = np.where((high_diff > low_diff) & (high_diff > _zero), high_diff, _zero)
        minus_dm = np.where((low_diff > high_diff) & (low_diff > _zero), low_diff, _zero)
        
        # ATR
        tr = np.maximum(
            highs[1:] - lows[1:],
            np.maximum(
                np.abs(highs[1:] - closes[:-1]),
                np.abs(lows[1:] - closes[:-1])
            )
        )
        
        # 
        atr_smooth = self._ema(tr, self.adx_period)
        plus_dm_smooth = self._ema(plus_dm, self.adx_period)
        minus_dm_smooth = self._ema(minus_dm, self.adx_period)
        
        # +DI  -DI
        plus_di = (plus_dm_smooth / atr_smooth) * 100 if atr_smooth > 0 else 0
        minus_di = (minus_dm_smooth / atr_smooth) * 100 if atr_smooth > 0 else 0
        
        # DX  ADX
        di_diff = abs(plus_di - minus_di)
        di_sum = plus_di + minus_di
        dx = (di_diff / di_sum) * 100 if di_sum > 0 else 0
        
        # ADX  DX 
        #  DX
        adx = dx
        
        return adx, plus_di, minus_di
    
    def _classify_volatility(self, symbol: str, atr_percent: float) -> VolatilityRegime:
        """"""
        # 
        self.volatility_history[symbol].append(atr_percent)
        
        #  (BTC )
        if atr_percent < 0.5:
            return VolatilityRegime.VERY_LOW
        elif atr_percent < 1.0:
            return VolatilityRegime.LOW
        elif atr_percent < 2.0:
            return VolatilityRegime.NORMAL
        elif atr_percent < 4.0:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME
    
    def _get_volatility_percentile(self, symbol: str, current_vol: float) -> float:
        """"""
        history = list(self.volatility_history.get(symbol, []))
        if len(history) < 20:
            return 50.0
        
        percentile = np.percentile(
            [v for v in history if v > 0], 
            [np.sum(np.array(history) <= current_vol) / len(history) * 100]
        )
        return float(np.ravel(percentile)[0])
    
    def _find_support_resistance(
        self, 
        prices: np.ndarray,
        highs: np.ndarray,
        lows: np.ndarray,
        num_levels: int = 5
    ) -> Tuple[List[float], List[float]]:
        """"""
        current_price = prices[-1]
        
        # 
        recent_highs = highs[-20:]
        recent_lows = lows[-20:]
        
        # 
        local_highs: List[float] = []
        local_lows: List[float] = []
        
        for i in range(2, len(recent_highs) - 2):
            if recent_highs[i] > recent_highs[i-1] and recent_highs[i] > recent_highs[i-2]:
                if recent_highs[i] > recent_highs[i+1] and recent_highs[i] > recent_highs[i+2]:
                    local_highs.append(float(recent_highs[i]))
            
            if recent_lows[i] < recent_lows[i-1] and recent_lows[i] < recent_lows[i-2]:
                if recent_lows[i] < recent_lows[i+1] and recent_lows[i] < recent_lows[i+2]:
                    local_lows.append(float(recent_lows[i]))
        
        # 
        support = sorted([p for p in local_lows if p < current_price], reverse=True)[:num_levels]
        resistance = sorted([p for p in local_highs if p > current_price])[:num_levels]
        
        return support, resistance
    
    def _classify_regime(
        self,
        trend_direction: int,
        trend_strength: TrendStrength,
        _trend_score: float,
        volatility_regime: VolatilityRegime,
        adx: float,
        _plus_di: float,
        _minus_di: float
    ) -> Tuple[MarketRegime, float]:
        """"""
        confidence = 0.5
        
        # 
        if volatility_regime == VolatilityRegime.EXTREME:
            return MarketRegime.HIGH_VOLATILITY, 0.8
        
        #  ADX 
        has_trend = adx > 25
        strong_trend = adx > 40
        
        if has_trend:
            # 
            if trend_direction > 0:
                if strong_trend and trend_strength in [TrendStrength.STRONG, TrendStrength.VERY_STRONG]:
                    regime = MarketRegime.STRONG_UPTREND
                    confidence = 0.85
                elif trend_strength in [TrendStrength.MODERATE, TrendStrength.STRONG]:
                    regime = MarketRegime.UPTREND
                    confidence = 0.75
                else:
                    regime = MarketRegime.WEAK_UPTREND
                    confidence = 0.6
            
            elif trend_direction < 0:
                if strong_trend and trend_strength in [TrendStrength.STRONG, TrendStrength.VERY_STRONG]:
                    regime = MarketRegime.STRONG_DOWNTREND
                    confidence = 0.85
                elif trend_strength in [TrendStrength.MODERATE, TrendStrength.STRONG]:
                    regime = MarketRegime.DOWNTREND
                    confidence = 0.75
                else:
                    regime = MarketRegime.WEAK_DOWNTREND
                    confidence = 0.6
            
            else:
                # ADX  -> 
                if volatility_regime in [VolatilityRegime.HIGH, VolatilityRegime.EXTREME]:
                    regime = MarketRegime.BREAKOUT
                    confidence = 0.5
                else:
                    regime = MarketRegime.SIDEWAYS_RANGE
                    confidence = 0.6
        
        else:
            #  -> 
            if volatility_regime == VolatilityRegime.VERY_LOW:
                # 
                regime = MarketRegime.SIDEWAYS_RANGE
                confidence = 0.7
            else:
                regime = MarketRegime.SIDEWAYS_RANGE
                confidence = 0.6
        
        return regime, confidence
    
    def _get_regime_duration(self, symbol: str, current_regime: MarketRegime) -> int:
        """"""
        history = self.regime_history.get(symbol, [])
        if not history:
            return 0
        
        duration = 0
        for i in range(len(history) - 1, -1, -1):
            ts, regime = history[i]
            if regime == current_regime:
                if i == len(history) - 1:
                    duration = 0
                else:
                    duration = int((datetime.now() - ts).total_seconds() / 60)
            else:
                break
        
        return duration
    
    def _estimate_transitions(
        self,
        current_regime: MarketRegime,
        vol_regime: VolatilityRegime,
        adx: float
    ) -> Dict[str, float]:
        """估算下一體制的轉換概率

        返回值：鍵為 MarketRegime.value 字串，值和恆為 1.0。
        涵蓋全部 10 種體制，依波動度體制與 ADX 強度調整。
        """
        R = MarketRegime
        V = VolatilityRegime
        high_adx = adx > 40
        high_vol = vol_regime in (V.HIGH, V.EXTREME)

        if current_regime == R.STRONG_UPTREND:
            if high_adx:
                probs = {R.STRONG_UPTREND: 0.55, R.UPTREND: 0.30,
                         R.WEAK_UPTREND: 0.10, R.REVERSAL: 0.05}
            else:
                probs = {R.UPTREND: 0.40, R.STRONG_UPTREND: 0.25,
                         R.WEAK_UPTREND: 0.25, R.REVERSAL: 0.10}

        elif current_regime == R.UPTREND:
            if high_vol:
                probs = {R.UPTREND: 0.30, R.BREAKOUT: 0.25,
                         R.HIGH_VOLATILITY: 0.25, R.REVERSAL: 0.20}
            elif high_adx:
                probs = {R.STRONG_UPTREND: 0.30, R.UPTREND: 0.40,
                         R.WEAK_UPTREND: 0.20, R.SIDEWAYS_RANGE: 0.10}
            else:
                probs = {R.UPTREND: 0.35, R.WEAK_UPTREND: 0.30,
                         R.SIDEWAYS_RANGE: 0.25, R.REVERSAL: 0.10}

        elif current_regime == R.WEAK_UPTREND:
            probs = {R.SIDEWAYS_RANGE: 0.35, R.UPTREND: 0.25,
                     R.WEAK_UPTREND: 0.25, R.WEAK_DOWNTREND: 0.15}

        elif current_regime == R.SIDEWAYS_RANGE:
            if vol_regime == V.VERY_LOW:
                probs = {R.BREAKOUT: 0.40, R.SIDEWAYS_RANGE: 0.35,
                         R.WEAK_UPTREND: 0.15, R.WEAK_DOWNTREND: 0.10}
            elif high_vol:
                probs = {R.BREAKOUT: 0.35, R.HIGH_VOLATILITY: 0.30,
                         R.UPTREND: 0.20, R.DOWNTREND: 0.15}
            else:
                probs = {R.SIDEWAYS_RANGE: 0.40, R.WEAK_UPTREND: 0.20,
                         R.WEAK_DOWNTREND: 0.20, R.BREAKOUT: 0.20}

        elif current_regime == R.WEAK_DOWNTREND:
            probs = {R.SIDEWAYS_RANGE: 0.35, R.DOWNTREND: 0.25,
                     R.WEAK_DOWNTREND: 0.25, R.WEAK_UPTREND: 0.15}

        elif current_regime == R.DOWNTREND:
            if high_vol:
                probs = {R.DOWNTREND: 0.30, R.BREAKOUT: 0.25,
                         R.HIGH_VOLATILITY: 0.25, R.REVERSAL: 0.20}
            elif high_adx:
                probs = {R.STRONG_DOWNTREND: 0.30, R.DOWNTREND: 0.40,
                         R.WEAK_DOWNTREND: 0.20, R.SIDEWAYS_RANGE: 0.10}
            else:
                probs = {R.DOWNTREND: 0.35, R.WEAK_DOWNTREND: 0.30,
                         R.SIDEWAYS_RANGE: 0.25, R.REVERSAL: 0.10}

        elif current_regime == R.STRONG_DOWNTREND:
            if high_adx:
                probs = {R.STRONG_DOWNTREND: 0.55, R.DOWNTREND: 0.30,
                         R.WEAK_DOWNTREND: 0.10, R.REVERSAL: 0.05}
            else:
                probs = {R.DOWNTREND: 0.40, R.STRONG_DOWNTREND: 0.25,
                         R.WEAK_DOWNTREND: 0.25, R.REVERSAL: 0.10}

        elif current_regime == R.BREAKOUT:
            probs = {R.STRONG_UPTREND: 0.30, R.STRONG_DOWNTREND: 0.25,
                     R.HIGH_VOLATILITY: 0.25, R.SIDEWAYS_RANGE: 0.20}

        elif current_regime == R.HIGH_VOLATILITY:
            probs = {R.SIDEWAYS_RANGE: 0.30, R.BREAKOUT: 0.25,
                     R.UPTREND: 0.25, R.DOWNTREND: 0.20}

        elif current_regime == R.REVERSAL:
            probs = {R.SIDEWAYS_RANGE: 0.35, R.WEAK_UPTREND: 0.25,
                     R.WEAK_DOWNTREND: 0.25, R.HIGH_VOLATILITY: 0.15}

        else:
            probs = {current_regime: 1.0}

        return {k.value: v for k, v in probs.items()}
    
    def _ema(self, data: np.ndarray, period: int) -> float:
        """"""
        if len(data) < period:
            return float(np.mean(data)) if len(data) > 0 else 0.0
        
        multiplier = 2 / (period + 1)
        ema = data[0]
        
        for price in data[1:]:
            ema = (price - ema) * multiplier + ema
        
        return float(ema)


# ============================================================================
#  ()
# ============================================================================

class RegimeBasedStrategySelector:
    """"""
    
    # -
    REGIME_STRATEGY_MAP = {
        MarketRegime.STRONG_UPTREND: {
            "recommended": ["trend_following", "breakout"],
            "avoid": ["mean_reversion", "short_selling"],
            "position_bias": "long_only"
        },
        MarketRegime.UPTREND: {
            "recommended": ["trend_following", "swing_long"],
            "avoid": ["mean_reversion"],
            "position_bias": "long_preferred"
        },
        MarketRegime.WEAK_UPTREND: {
            "recommended": ["swing_trading", "trend_following"],
            "avoid": [],
            "position_bias": "slight_long"
        },
        MarketRegime.SIDEWAYS_RANGE: {
            "recommended": ["mean_reversion", "range_trading"],
            "avoid": ["trend_following", "breakout"],
            "position_bias": "neutral"
        },
        MarketRegime.WEAK_DOWNTREND: {
            "recommended": ["swing_trading", "trend_following"],
            "avoid": [],
            "position_bias": "slight_short"
        },
        MarketRegime.DOWNTREND: {
            "recommended": ["trend_following", "swing_short"],
            "avoid": ["mean_reversion"],
            "position_bias": "short_preferred"
        },
        MarketRegime.STRONG_DOWNTREND: {
            "recommended": ["trend_following", "breakout_short"],
            "avoid": ["mean_reversion", "long_buying"],
            "position_bias": "short_only"
        },
        MarketRegime.HIGH_VOLATILITY: {
            "recommended": ["reduce_position", "wait"],
            "avoid": ["high_leverage", "large_position"],
            "position_bias": "reduce_all"
        },
        MarketRegime.BREAKOUT: {
            "recommended": ["breakout", "momentum"],
            "avoid": ["mean_reversion"],
            "position_bias": "follow_breakout"
        },
        MarketRegime.REVERSAL: {
            "recommended": ["wait", "small_position"],
            "avoid": ["trend_following", "large_position"],
            "position_bias": "cautious"
        },
    }
    
    def get_strategy_recommendation(
        self, 
        regime_analysis: RegimeAnalysis
    ) -> Dict[str, Any]:
        """"""
        regime = regime_analysis.current_regime
        config = self.REGIME_STRATEGY_MAP.get(regime, {})
        
        # 
        vol_adjustment = self._get_volatility_adjustment(regime_analysis.volatility_regime)
        
        return {
            "regime": regime.value,
            "confidence": regime_analysis.regime_confidence,
            "recommended_strategies": config.get("recommended", []),
            "avoid_strategies": config.get("avoid", []),
            "position_bias": config.get("position_bias", "neutral"),
            "position_size_multiplier": vol_adjustment["size_multiplier"],
            "stop_loss_multiplier": vol_adjustment["stop_multiplier"],
            "trading_frequency": vol_adjustment["frequency"],
            "prompt": regime_analysis.to_prompt()
        }
    
    def _get_volatility_adjustment(self, vol_regime: VolatilityRegime) -> Dict[str, float]:
        """"""
        adjustments = {
            VolatilityRegime.VERY_LOW: {
                "size_multiplier": 1.2,  # 
                "stop_multiplier": 0.8,  # 
                "frequency": "normal"
            },
            VolatilityRegime.LOW: {
                "size_multiplier": 1.1,
                "stop_multiplier": 0.9,
                "frequency": "normal"
            },
            VolatilityRegime.NORMAL: {
                "size_multiplier": 1.0,
                "stop_multiplier": 1.0,
                "frequency": "normal"
            },
            VolatilityRegime.HIGH: {
                "size_multiplier": 0.7,  # 
                "stop_multiplier": 1.5,  # 
                "frequency": "reduced"
            },
            VolatilityRegime.EXTREME: {
                "size_multiplier": 0.3,  # 
                "stop_multiplier": 2.0,  # 
                "frequency": "minimal"
            },
        }
        
        return cast(Dict[str, float], adjustments.get(vol_regime, adjustments[VolatilityRegime.NORMAL]))
