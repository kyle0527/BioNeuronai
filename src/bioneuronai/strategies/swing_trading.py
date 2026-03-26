"""
波段交易策略 (Swing Trading Strategy)
======================================

核心理念：
在支撐阻力位之間交易，捕捉價格波動的機會。

適用場景：
- 震盪市場
- 支撐/阻力位明確
- 中等波動環境

策略邏輯：
1. 識別支撐和阻力位
2. 等待價格測試這些關鍵位
3. 確認反轉信號（K線形態、RSI）
4. 在支撐位買入/阻力位賣出

技術指標：
- 支撐/阻力位 (Pivot Points)
- RSI 超買超賣
- Stochastic 動量振盪
- 價格行為分析
"""

from __future__ import annotations

import numpy as np
import logging
from typing import Optional, Dict, Any, Tuple, List, cast
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

logger: logging.Logger = logging.getLogger(__name__)


@dataclass
class SwingPoint:
    """"""
    price: float
    index: int
    type: str  # 'high' or 'low'
    strength: int  # K
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SwingAnalysis:
    """"""
    # 
    swing_highs: List[SwingPoint] = field(default_factory=list)
    swing_lows: List[SwingPoint] = field(default_factory=list)
    
    # 
    higher_highs: bool = False
    higher_lows: bool = False
    lower_highs: bool = False
    lower_lows: bool = False
    
    # 
    nearest_resistance: float = 0.0
    nearest_support: float = 0.0
    key_levels: List[float] = field(default_factory=list)
    
    # 
    fib_retracement_levels: Dict[str, float] = field(default_factory=dict)
    current_retracement_pct: float = 0.0
    
    # RSI 
    rsi_value: float = 50.0
    rsi_divergence: str = "none"  # 'bullish', 'bearish', 'none'
    rsi_overbought: bool = False
    rsi_oversold: bool = False
    
    # Stochastic 
    stoch_k: float = 50.0
    stoch_d: float = 50.0
    stoch_oversold: bool = False
    stoch_overbought: bool = False
    stoch_bullish_cross: bool = False
    stoch_bearish_cross: bool = False
    
    # 
    current_swing_size: float = 0.0
    average_swing_size: float = 0.0
    swing_volatility: float = 0.0


class SwingTradingStrategy(BaseStrategy):
    """
    
    
    
    1. 
    2. 
    3. RSI 
    4. 
    """
    
    def __init__(
        self,
        timeframe: str = "4h",
        risk_params: Optional[RiskParameters] = None,
    ) -> None:
        super().__init__(
            name="Swing Trading",
            timeframe=timeframe,
            risk_params=risk_params or RiskParameters(
                max_risk_per_trade_pct=1.5,
                min_risk_reward_ratio=2.5,
                trailing_stop_activation=2.0,
                trailing_stop_distance=0.75,
                max_holding_period_hours=336,  # 14 
            ),
        )
        
        # 
        self.swing_lookback = 5  #  5  K 
        self.rsi_period = 14
        self.stoch_period = 14
        self.stoch_smooth = 3
        
        # 
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.stoch_overbought = 80
        self.stoch_oversold = 20
        
        # 
        self.fib_levels: List[float] = [0.236, 0.382, 0.5, 0.618, 0.786]
        self.ideal_retracement_range = (0.382, 0.618)  # 
        
        # 
        self.required_confirmations = 3
        
        # 
        self.take_profit_r_multiples: List[float] = [2.5, 4.0, 6.0]
        self.exit_portions: List[float] = [0.40, 0.35, 0.25]
    
    # ========================
    # 
    # ========================
    
    def _find_swing_points(
        self,
        high: np.ndarray,
        low: np.ndarray,
        lookback: int = 5
    ) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """"""
        swing_highs = []
        swing_lows = []
        n: int = len(high)
        
        for i in range(lookback, n - lookback):
            # 檢查swing high
            if self._is_swing_high(high, i, lookback):
                swing_highs.append(SwingPoint(
                    price=float(high[i]),
                    index=i,
                    type='high',
                    strength=lookback,
                ))
            
            # 檢查swing low
            if self._is_swing_low(low, i, lookback):
                swing_lows.append(SwingPoint(
                    price=float(low[i]),
                    index=i,
                    type='low',
                    strength=lookback,
                ))
        
        return swing_highs, swing_lows
    
    def _is_swing_high(self, high: np.ndarray, index: int, lookback: int) -> bool:
        """檢查指定索引是否為swing high"""
        for j in range(1, lookback + 1):
            if high[index] < high[index - j] or high[index] < high[index + j]:
                return False
        return True
    
    def _is_swing_low(self, low: np.ndarray, index: int, lookback: int) -> bool:
        """檢查指定索引是否為swing low"""
        for j in range(1, lookback + 1):
            if low[index] > low[index - j] or low[index] > low[index + j]:
                return False
        return True

    def _calculate_rsi(self, close: np.ndarray, period: int = 14) -> np.ndarray:
        """ RSI"""
        n: int = len(close)
        if n < period + 1:
            return cast(np.ndarray, np.full(n, 50.0))
        
        deltas: np.ndarray[Tuple[Any], np.dtype[Any]] = np.diff(close)
        gains: np.ndarray[Tuple[Any], np.dtype[Any]] = np.where(deltas > 0, deltas, 0)
        losses: np.ndarray[Tuple[Any], np.dtype[Any]] = np.where(deltas < 0, -deltas, 0)
        
        avg_gain: np.ndarray[Tuple[int], np.dtype[np.float64]] = np.zeros(n)
        avg_loss: np.ndarray[Tuple[int], np.dtype[np.float64]] = np.zeros(n)
        
        # 
        avg_gain[period] = np.mean(gains[:period])
        avg_loss[period] = np.mean(losses[:period])
        
        # 
        for i in range(period + 1, n):
            avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i-1]) / period
            avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i-1]) / period
        
        rs: np.ndarray[Tuple[Any], np.dtype[Any]] = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
        rsi: np.ndarray[Tuple[Any], np.dtype[np.float64]] = 100 - (100 / (1 + rs))
        rsi[:period] = 50
        
        return cast(np.ndarray, rsi)
    
    def _calculate_stochastic(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """ Stochastic Oscillator"""
        n: int = len(close)
        if n < period:
            return np.full(n, 50.0), np.full(n, 50.0)
        
        raw_k: np.ndarray[Tuple[int], np.dtype[np.float64]] = np.zeros(n)
        
        for i in range(period - 1, n):
            highest: float = float(np.max(high[i - period + 1:i + 1]))
            lowest: float = float(np.min(low[i - period + 1:i + 1]))
            
            if highest != lowest:
                raw_k[i] = 100 * (close[i] - lowest) / (highest - lowest)
            else:
                raw_k[i] = 50
        
        #  K 
        k: np.ndarray[Tuple[Any], np.dtype[np.floating[Any]]] = np.convolve(raw_k, np.ones(smooth_k) / smooth_k, mode='same')
        
        # D  (K )
        d: np.ndarray[Tuple[Any], np.dtype[np.floating[Any]]] = np.convolve(k, np.ones(smooth_d) / smooth_d, mode='same')
        
        return cast(np.ndarray, k), cast(np.ndarray, d)
    
    def _calculate_fibonacci_levels(
        self,
        swing_high: float,
        swing_low: float,
        direction: str = 'bullish'
    ) -> Dict[str, float]:
        """"""
        diff: float = swing_high - swing_low
        levels = {}
        
        if direction == 'bullish':
            # 
            for level in self.fib_levels:
                levels[f'{level:.3f}'] = swing_high - (diff * level)
        else:
            # 
            for level in self.fib_levels:
                levels[f'{level:.3f}'] = swing_low + (diff * level)
        
        levels['high'] = swing_high
        levels['low'] = swing_low
        
        return levels
    
    def _detect_rsi_divergence(
        self,
        _close: np.ndarray,
        rsi: np.ndarray,
        swing_lows: List[SwingPoint],
        swing_highs: List[SwingPoint]
    ) -> str:
        """檢測 RSI 背離
        
        Args:
            _close: 保留參數以保持接口一致性，實際使用 swing points 中的價格
            rsi: RSI 指標值
            swing_lows: 低點列表
            swing_highs: 高點列表
        """
        # 
        if len(swing_lows) < 2 and len(swing_highs) < 2:
            return "none"
        
        #  RSI 
        if len(swing_lows) >= 2:
            recent_lows: List[SwingPoint] = sorted(swing_lows, key=lambda x: x.index)[-2:]
            if (recent_lows[1].price < recent_lows[0].price and 
                rsi[recent_lows[1].index] > rsi[recent_lows[0].index]):
                return "bullish"
        
        #  RSI 
        if len(swing_highs) >= 2:
            recent_highs: List[SwingPoint] = sorted(swing_highs, key=lambda x: x.index)[-2:]
            if (recent_highs[1].price > recent_highs[0].price and
                rsi[recent_highs[1].index] < rsi[recent_highs[0].index]):
                return "bearish"
        
        return "none"
    
    def _find_support_resistance(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint]
    ) -> Tuple[float, float, List[float]]:
        """"""
        current_price = close[-1]
        key_levels = []
        
        # 加入擺動點位
        for sh in swing_highs:
            key_levels.append(sh.price)
        for sl in swing_lows:
            key_levels.append(sl.price)
        
        # 
        if len(high) >= 20:
            key_levels.append(np.max(high[-20:]))
            key_levels.append(np.min(low[-20:]))
        
        # 
        resistances = [level for level in key_levels if level > current_price]
        supports = [level for level in key_levels if level < current_price]
        
        nearest_resistance = min(resistances) if resistances else current_price * 1.05
        nearest_support = max(supports) if supports else current_price * 0.95
        
        # 去重並排序
        key_levels = sorted(set(key_levels))
        
        return nearest_resistance, nearest_support, key_levels
    
    # ========================
    # 1. 
    # ========================
    
    def analyze_market(
        self,
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """市場分析 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離各分析模塊
        """
        self.state: StrategyState = StrategyState.ANALYZING
        
        # 提取基礎數據
        high: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 2]
        low: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 3]
        close: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 4]
        current_price = close[-1]
        
        # 計算擺動點和指標
        swing_highs, swing_lows = self._find_swing_points(high, low, self.swing_lookback)
        rsi: np.ndarray[Tuple[Any], np.dtype[Any]] = self._calculate_rsi(close, self.rsi_period)
        stoch_k, stoch_d = self._calculate_stochastic(
            high, low, close, self.stoch_period, self.stoch_smooth, self.stoch_smooth
        )
        
        # 構建分析對象
        analysis = SwingAnalysis()
        analysis.swing_highs = swing_highs
        analysis.swing_lows = swing_lows
        
        # 各模塊分析 (Extract Method 降低複雜度)
        self._analyze_trend_pattern(analysis, swing_highs, swing_lows)
        self._analyze_support_resistance(analysis, high, low, close, swing_highs, swing_lows)
        self._analyze_fibonacci_levels(analysis, swing_highs, swing_lows, float(current_price))
        self._analyze_rsi_indicators(analysis, close, rsi, swing_lows, swing_highs)
        self._analyze_stochastic_indicators(analysis, stoch_k, stoch_d)
        self._analyze_swing_statistics(analysis, swing_highs, swing_lows)
        
        # 判斷市場狀態
        market_condition, trend_direction = self._determine_market_condition(analysis)
        
        self.state = StrategyState.IDLE
        self._last_analysis_time = datetime.now()
        
        return {
            'market_condition': market_condition,
            'trend_direction': trend_direction,
            'trend_strength': 50,
            'volatility': 'high' if analysis.swing_volatility > analysis.average_swing_size else 'normal',
            'key_levels': {
                'resistance': analysis.nearest_resistance,
                'support': analysis.nearest_support,
                'fib_levels': analysis.fib_retracement_levels,
            },
            'swing_analysis': analysis,
            'indicators': {
                'rsi': analysis.rsi_value,
                'stoch_k': analysis.stoch_k,
                'stoch_d': analysis.stoch_d,
            },
            'current_price': current_price,
            'analysis_summary': self._generate_swing_summary(analysis, market_condition),
        }
    
    def _analyze_trend_pattern(
        self, 
        analysis: SwingAnalysis, 
        swing_highs: List[SwingPoint], 
        swing_lows: List[SwingPoint]
    ) -> None:
        """分析趨勢模式"""
        if len(swing_highs) >= 2:
            recent_highs: List[SwingPoint] = sorted(swing_highs, key=lambda x: x.index)[-2:]
            analysis.higher_highs = recent_highs[1].price > recent_highs[0].price
            analysis.lower_highs = recent_highs[1].price < recent_highs[0].price
        
        if len(swing_lows) >= 2:
            recent_lows: List[SwingPoint] = sorted(swing_lows, key=lambda x: x.index)[-2:]
            analysis.higher_lows = recent_lows[1].price > recent_lows[0].price
            analysis.lower_lows = recent_lows[1].price < recent_lows[0].price
    
    def _analyze_support_resistance(
        self,
        analysis: SwingAnalysis,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint]
    ) -> None:
        """分析支撐阻力位"""
        resistance, support, key_levels = self._find_support_resistance(
            high, low, close, swing_highs, swing_lows
        )
        analysis.nearest_resistance = resistance
        analysis.nearest_support = support
        analysis.key_levels = key_levels
    
    def _analyze_fibonacci_levels(
        self,
        analysis: SwingAnalysis,
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint],
        current_price: float
    ) -> None:
        """分析斐波那契回撤水平"""
        if not (swing_highs and swing_lows):
            return
        
        latest_high: SwingPoint = max(swing_highs, key=lambda x: x.index)
        latest_low: SwingPoint = max(swing_lows, key=lambda x: x.index)
        swing_range: float = latest_high.price - latest_low.price
        
        if swing_range <= 0:
            return
        
        if latest_high.index > latest_low.index:
            # 看漲回撤
            fib_levels: Dict[str, float] = self._calculate_fibonacci_levels(
                latest_high.price, latest_low.price, 'bullish'
            )
            analysis.current_retracement_pct = (
                (latest_high.price - current_price) / swing_range
            )
        else:
            # 看跌回撤
            fib_levels = self._calculate_fibonacci_levels(
                latest_high.price, latest_low.price, 'bearish'
            )
            analysis.current_retracement_pct = (
                (current_price - latest_low.price) / swing_range
            )
        
        analysis.fib_retracement_levels = fib_levels
    
    def _analyze_rsi_indicators(
        self,
        analysis: SwingAnalysis,
        close: np.ndarray,
        rsi: np.ndarray,
        swing_lows: List[SwingPoint],
        swing_highs: List[SwingPoint]
    ) -> None:
        """分析 RSI 指標"""
        analysis.rsi_value = float(rsi[-1])
        analysis.rsi_overbought = bool(rsi[-1] > self.rsi_overbought)
        analysis.rsi_oversold = bool(rsi[-1] < self.rsi_oversold)
        analysis.rsi_divergence = self._detect_rsi_divergence(
            close, rsi, swing_lows, swing_highs
        )
    
    def _analyze_stochastic_indicators(
        self,
        analysis: SwingAnalysis,
        stoch_k: np.ndarray,
        stoch_d: np.ndarray
    ) -> None:
        """分析 Stochastic 指標"""
        analysis.stoch_k = float(stoch_k[-1])
        analysis.stoch_d = float(stoch_d[-1])
        analysis.stoch_overbought = bool(stoch_k[-1] > self.stoch_overbought)
        analysis.stoch_oversold = bool(stoch_k[-1] < self.stoch_oversold)
        
        if len(stoch_k) >= 2 and len(stoch_d) >= 2:
            analysis.stoch_bullish_cross = bool(
                stoch_k[-1] > stoch_d[-1] and stoch_k[-2] <= stoch_d[-2]
            )
            analysis.stoch_bearish_cross = bool(
                stoch_k[-1] < stoch_d[-1] and stoch_k[-2] >= stoch_d[-2]
            )
    
    def _analyze_swing_statistics(
        self,
        analysis: SwingAnalysis,
        swing_highs: List[SwingPoint],
        swing_lows: List[SwingPoint]
    ) -> None:
        """分析擺動統計數據"""
        if not (swing_highs and swing_lows):
            return
        
        swings: List[SwingPoint] = sorted(swing_highs + swing_lows, key=lambda x: x.index)
        swing_sizes: List[float] = [
            abs(swings[i].price - swings[i-1].price)
            for i in range(1, len(swings))
        ]
        
        if swing_sizes:
            analysis.average_swing_size = float(np.mean(swing_sizes))
            analysis.swing_volatility = float(np.std(swing_sizes))
            analysis.current_swing_size = swing_sizes[-1]
    
    def _determine_market_condition(
        self, 
        analysis: SwingAnalysis
    ) -> Tuple[MarketCondition, str]:
        """判斷市場狀態"""
        if analysis.higher_highs and analysis.higher_lows:
            return MarketCondition.UPTREND, 'bullish'
        elif analysis.lower_highs and analysis.lower_lows:
            return MarketCondition.DOWNTREND, 'bearish'
        else:
            return MarketCondition.SIDEWAYS, 'neutral'
    
    def _generate_swing_summary(
        self,
        analysis: SwingAnalysis,
        market_condition: MarketCondition
    ) -> str:
        """"""
        summary = []
        
        summary.append(f": {market_condition.value}")
        
        if analysis.higher_highs and analysis.higher_lows:
            summary.append(": HH + HL ()")
        elif analysis.lower_highs and analysis.lower_lows:
            summary.append(": LH + LL ()")
        else:
            summary.append(": ")
        
        summary.append(f"RSI: {analysis.rsi_value:.1f}")
        if analysis.rsi_overbought:
            summary.append("⚠️ RSI 超買")
        elif analysis.rsi_oversold:
            summary.append("⚠️ RSI 超賣")
        
        if analysis.rsi_divergence != "none":
            summary.append(f" RSI {analysis.rsi_divergence} ")
        
        summary.append(f"Stoch: K={analysis.stoch_k:.1f}, D={analysis.stoch_d:.1f}")
        if analysis.stoch_bullish_cross:
            summary.append("📈 Stoch 黃金交叉")
        elif analysis.stoch_bearish_cross:
            summary.append("📉 Stoch 死亡交叉")
        
        if analysis.fib_retracement_levels:
            summary.append(f": {analysis.current_retracement_pct*100:.1f}%")
        
        return " | ".join(summary)
    
    # ========================
    # 2. 
    # ========================
    
    def _evaluate_bullish_conditions(
        self, 
        analysis: Any, 
        current_price: float
    ) -> Tuple[int, List[str]]:
        """評估多頭條件 - Extract Method 降低複雜度"""
        confirmations = 0
        conditions = []
        
        # 1. 趨勢確認: HH + HL
        if analysis.higher_highs and analysis.higher_lows:
            conditions.append(" (HH+HL)")
            confirmations += 1
        
        # 2. 支撐位確認
        support_distance = abs(current_price - analysis.nearest_support) / current_price
        if support_distance < 0.02:
            conditions.append(f" ({analysis.nearest_support:.2f})")
            confirmations += 1
        
        # 3. 回撤水平
        retracement = analysis.current_retracement_pct
        if self.ideal_retracement_range[0] <= retracement <= self.ideal_retracement_range[1]:
            conditions.append(f" ({retracement*100:.1f}%)")
            confirmations += 1
        
        # 4. RSI 超賣
        if analysis.rsi_oversold:
            conditions.append(f"RSI  ({analysis.rsi_value:.1f})")
            confirmations += 1
        
        # 5. RSI 背離
        if analysis.rsi_divergence == "bullish":
            conditions.append("RSI ")
            confirmations += 1
        
        # 6. Stochastic 交叉
        if analysis.stoch_bullish_cross and analysis.stoch_k < 30:
            conditions.append("Stoch ")
            confirmations += 1
        
        return confirmations, conditions
    
    def _evaluate_bearish_conditions(
        self, 
        analysis: Any, 
        current_price: float
    ) -> Tuple[int, List[str]]:
        """評估空頭條件 - Extract Method 降低複雜度"""
        confirmations = 0
        conditions = []
        
        # 1. 趨勢確認: LH + LL
        if analysis.lower_highs and analysis.lower_lows:
            conditions.append(" (LH+LL)")
            confirmations += 1
        
        # 2. 阻力位確認
        resistance_distance = abs(analysis.nearest_resistance - current_price) / current_price
        if resistance_distance < 0.02:
            conditions.append(f" ({analysis.nearest_resistance:.2f})")
            confirmations += 1
        
        # 3. 回撤水平
        retracement = analysis.current_retracement_pct
        if (self.ideal_retracement_range[0] <= retracement <= self.ideal_retracement_range[1]
            and analysis.lower_highs):
            conditions.append(f" ({retracement*100:.1f}%)")
            confirmations += 1
        
        # 4. RSI 超買
        if analysis.rsi_overbought:
            conditions.append(f"RSI  ({analysis.rsi_value:.1f})")
            confirmations += 1
        
        # 5. RSI 背離
        if analysis.rsi_divergence == "bearish":
            conditions.append("RSI ")
            confirmations += 1
        
        # 6. Stochastic 交叉
        if analysis.stoch_bearish_cross and analysis.stoch_k > 70:
            conditions.append("Stoch ")
            confirmations += 1
        
        return confirmations, conditions
    
    def evaluate_entry_conditions(
        self,
        market_analysis: Dict[str, Any],
        ohlcv_data: np.ndarray,
    ) -> Optional[TradeSetup]:
        """評估進場條件 - 重構後降低複雜度
        
        複雜度降低策略：Extract Method
        - 將多頭/空頭條件評估提取為獨立方法
        - 簡化主流程邏輯
        """
        analysis: Any | None = market_analysis.get('swing_analysis')
        current_price: Any | None = market_analysis.get('current_price')
        
        if not analysis or not current_price:
            return None
        
        # 評估多頭和空頭條件
        bullish_confirmations, bullish_conditions = self._evaluate_bullish_conditions(
            analysis, current_price
        )
        bearish_confirmations, bearish_conditions = self._evaluate_bearish_conditions(
            analysis, current_price
        )
        
        # 決定方向
        if bullish_confirmations >= self.required_confirmations:
            direction = 'long'
            entry_conditions: List[str] = bullish_conditions
            confirmations: int = bullish_confirmations
        elif bearish_confirmations >= self.required_confirmations:
            direction = 'short'
            entry_conditions = bearish_conditions
            confirmations = bearish_confirmations
        else:
            logger.debug(
                f" - : {bullish_confirmations}, : {bearish_confirmations}"
            )
            return None
        
        # 進入条件評估
        if direction == 'long':
            # 
            recent_lows: List[Any] = sorted(analysis.swing_lows, key=lambda x: x.index)
            if recent_lows:
                stop_loss = recent_lows[-1].price * 0.995  #  0.5%
            else:
                stop_loss = analysis.nearest_support * 0.99
        else:
            # 
            recent_highs: List[Any] = sorted(analysis.swing_highs, key=lambda x: x.index)
            if recent_highs:
                stop_loss = recent_highs[-1].price * 1.005
            else:
                stop_loss = analysis.nearest_resistance * 1.01
        
        # 
        risk_per_unit = abs(current_price - stop_loss)
        
        if direction == 'long':
            tp1 = current_price + (risk_per_unit * self.take_profit_r_multiples[0])
            tp2 = current_price + (risk_per_unit * self.take_profit_r_multiples[1])
            tp3 = min(
                analysis.nearest_resistance,
                current_price + (risk_per_unit * self.take_profit_r_multiples[2])
            )
        else:
            tp1 = current_price - (risk_per_unit * self.take_profit_r_multiples[0])
            tp2 = current_price - (risk_per_unit * self.take_profit_r_multiples[1])
            tp3 = max(
                analysis.nearest_support,
                current_price - (risk_per_unit * self.take_profit_r_multiples[2])
            )
        
        # 
        if confirmations >= 5:
            signal_strength: SignalStrength = SignalStrength.VERY_STRONG
        elif confirmations >= 4:
            signal_strength = SignalStrength.STRONG
        elif confirmations >= 3:
            signal_strength = SignalStrength.MODERATE
        else:
            signal_strength = SignalStrength.WEAK
        
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
            valid_until=datetime.now() + timedelta(hours=4),  # 4
            key_levels={
                'resistance': analysis.nearest_resistance,
                'support': analysis.nearest_support,
                'fib_382': analysis.fib_retracement_levels.get('0.382'),
                'fib_618': analysis.fib_retracement_levels.get('0.618'),
            },
            invalidation_conditions=[
                f" {stop_loss:.2f}",
                "",
                "RSI  (40-60)",
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
        
        
        
        """
        try:
            trade_id: str = f"SW_{setup.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            execution = TradeExecution(
                trade_id=trade_id,
                setup=setup,
            )
            
            # 
            portion_size: float = setup.total_position_size / setup.entry_portions
            
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
                    'type': 'limit',
                })
            else:
                # 
                if setup.direction == 'long':
                    limit_price: float = setup.entry_price * 0.999  #  0.1%
                else:
                    limit_price = setup.entry_price * 1.001  #  0.1%
                
                order_result = connector.place_order(
                    symbol=setup.symbol,
                    side='BUY' if setup.direction == 'long' else 'SELL',
                    order_type='LIMIT',
                    quantity=portion_size,
                    price=limit_price,
                    time_in_force='GTC',
                )
                
                #  OCO  + 
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
            
            execution.highest_price_since_entry = execution.actual_entry_price
            execution.lowest_price_since_entry = execution.actual_entry_price
            
            self.state = StrategyState.POSITION_OPEN
            return execution
            
        except Exception as e:
            logger.error(f"執行交易時發生錯誤: {e}")
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
        """持倉管理 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離各管理模塊
        
        主要功能：
        1. 更新最佳/最差價格
        2. 移動止損到盈虧平衡點
        3. 追蹤止損更新
        4. 檢測止盈水平
        5. 評估加倉機會
        """
        mgmt = PositionManagement()
        setup: TradeSetup = trade.setup
        r_multiple: float = trade.calculate_r_multiple()
        risk_per_unit: float = abs(setup.entry_price - setup.stop_loss)
        
        # 模塊1: 更新最佳/最差價格追蹤
        self._update_price_extremes(trade, current_price, setup, risk_per_unit)
        
        # 模塊2: 移動止損到盈虧平衡點
        self._handle_breakeven_stop(mgmt, r_multiple, setup, risk_per_unit)
        
        # 模塊3: 追蹤止損
        self._handle_trailing_stop(mgmt, trade, current_price)
        
        # 模塊4: 止盈水平檢測
        self._check_take_profit_levels(mgmt, setup, current_price)
        
        # 模塊5: 加倉機會評估
        self._evaluate_scaling_opportunity(mgmt, r_multiple, setup, current_price, ohlcv_data)
        
        return mgmt
    
    def _update_price_extremes(
        self,
        trade: TradeExecution,
        current_price: float,
        setup: TradeSetup,
        risk_per_unit: float
    ) -> None:
        """更新最高/最低價格追蹤"""
        if setup.direction == 'long':
            trade.highest_price_since_entry = max(
                trade.highest_price_since_entry, current_price
            )
            trade.max_favorable_excursion = max(
                trade.max_favorable_excursion,
                (trade.highest_price_since_entry - setup.entry_price) / risk_per_unit
            )
        else:
            trade.lowest_price_since_entry = min(
                trade.lowest_price_since_entry, current_price
            )
            trade.max_favorable_excursion = max(
                trade.max_favorable_excursion,
                (setup.entry_price - trade.lowest_price_since_entry) / risk_per_unit
            )
    
    def _handle_breakeven_stop(
        self,
        mgmt: PositionManagement,
        r_multiple: float,
        setup: TradeSetup,
        risk_per_unit: float
    ) -> None:
        """處理盈虧平衡點止損 (達到 1.5R)"""
        if r_multiple < 1.5 or mgmt.stop_loss_moved_to_breakeven:
            return
        
        # 計算新止損 (入場價 + 0.1R 緩衝)
        new_stop: float = setup.entry_price
        if setup.direction == 'long':
            new_stop += risk_per_unit * 0.1
        else:
            new_stop -= risk_per_unit * 0.1
        
        mgmt.stop_loss_moved_to_breakeven = True
        mgmt.current_stop_loss = new_stop
        logger.info(f" {new_stop:.2f}")
    
    def _handle_trailing_stop(
        self,
        mgmt: PositionManagement,
        trade: TradeExecution,
        current_price: float
    ) -> None:
        """處理追蹤止損更新"""
        new_trailing: float | None = self.update_trailing_stop(trade, current_price)
        if new_trailing:
            mgmt.stop_loss_trailing = True
            mgmt.current_stop_loss = new_trailing
    
    def _check_take_profit_levels(
        self,
        mgmt: PositionManagement,
        setup: TradeSetup,
        current_price: float
    ) -> None:
        """檢測止盈水平"""
        if setup.direction == 'long':
            self._check_long_take_profits(mgmt, setup, current_price)
        else:
            self._check_short_take_profits(mgmt, setup, current_price)
    
    def _check_long_take_profits(
        self,
        mgmt: PositionManagement,
        setup: TradeSetup,
        current_price: float
    ) -> None:
        """檢查多頭止盈"""
        if current_price >= setup.take_profit_1 and not mgmt.tp1_filled:
            mgmt.tp1_filled = True
            mgmt.exit_portions_filled += 1
            logger.info(f" TP1 : {setup.take_profit_1:.2f}")
        
        if current_price >= setup.take_profit_2 and not mgmt.tp2_filled:
            mgmt.tp2_filled = True
            mgmt.exit_portions_filled += 1
            logger.info(f" TP2 : {setup.take_profit_2:.2f}")
    
    def _check_short_take_profits(
        self,
        mgmt: PositionManagement,
        setup: TradeSetup,
        current_price: float
    ) -> None:
        """檢查空頭止盈"""
        if current_price <= setup.take_profit_1 and not mgmt.tp1_filled:
            mgmt.tp1_filled = True
            mgmt.exit_portions_filled += 1
        
        if current_price <= setup.take_profit_2 and not mgmt.tp2_filled:
            mgmt.tp2_filled = True
            mgmt.exit_portions_filled += 1
    
    def _evaluate_scaling_opportunity(
        self,
        mgmt: PositionManagement,
        r_multiple: float,
        setup: TradeSetup,
        current_price: float,
        ohlcv_data: np.ndarray
    ) -> None:
        """評估加倉機會 (回調到擺動低點)"""
        if r_multiple < 0.5 or mgmt.entry_portions_filled >= mgmt.entry_portions_total:
            return
        
        if setup.direction != 'long':
            return
        
        high: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 2]
        low: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 3]
        _swing_highs, swing_lows = self._find_swing_points(high, low, self.swing_lookback)
        
        if not swing_lows:
            return
        
        latest_low: SwingPoint = max(swing_lows, key=lambda x: x.index)
        if abs(current_price - latest_low.price) / current_price < 0.01:
            mgmt.scaling_in_allowed = True
            logger.info("")
    
    # ========================
    # 5. 
    # ========================
    
    def evaluate_exit_conditions(
        self,
        trade: TradeExecution,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> Tuple[bool, str]:
        """評估出場條件 - 重構後降低複雜度
        
        複雜度降低策略：Extract Method + Early Return
        """
        # 1. 止損檢查 (Early Return)
        should_stop, stop_reason = self._check_stop_loss(trade, current_price)
        if should_stop:
            return True, stop_reason
        
        # 2. 時間退出檢查 (Early Return)
        should_time_exit, time_reason = self.check_time_based_exit(trade)
        if should_time_exit:
            return True, time_reason
        
        # 3. 趨勢反轉檢查
        should_trend_exit, trend_reason = self._check_trend_reversal(trade, ohlcv_data)
        if should_trend_exit:
            return True, trend_reason
        
        # 4. RSI 背離檢查
        should_rsi_exit, rsi_reason = self._check_rsi_divergence_exit(
            trade, ohlcv_data[:, 4]
        )
        if should_rsi_exit:
            return True, rsi_reason
        
        return False, ""
    
    def _check_stop_loss(
        self, 
        trade: TradeExecution, 
        current_price: float
    ) -> Tuple[bool, str]:
        """檢查止損條件"""
        setup: TradeSetup = trade.setup
        active_stop: float = trade.trailing_stop_price or setup.stop_loss
        
        if setup.direction == 'long' and current_price <= active_stop:
            return True, f"多單止損觸發 @ {current_price:.2f}"
        elif setup.direction == 'short' and current_price >= active_stop:
            return True, f"空單止損觸發 @ {current_price:.2f}"
        
        return False, ""
    
    def _check_trend_reversal(
        self, 
        trade: TradeExecution, 
        ohlcv_data: np.ndarray
    ) -> Tuple[bool, str]:
        """檢查趨勢反轉"""
        high: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 2]
        low: np.ndarray[Tuple[Any], np.dtype[Any]] = ohlcv_data[:, 3]
        setup: TradeSetup = trade.setup
        
        swing_highs, swing_lows = self._find_swing_points(high, low, self.swing_lookback)
        
        if len(swing_lows) < 2 or len(swing_highs) < 2:
            return False, ""
        
        recent_lows: List[SwingPoint] = sorted(swing_lows, key=lambda x: x.index)[-2:]
        recent_highs: List[SwingPoint] = sorted(swing_highs, key=lambda x: x.index)[-2:]
        
        # 檢查趨勢反轉
        if setup.direction == 'long':
            return self._check_downtrend_reversal(recent_highs, recent_lows, trade)
        elif setup.direction == 'short':
            return self._check_uptrend_reversal(recent_highs, recent_lows, trade)
        
        return False, ""
    
    def _check_downtrend_reversal(
        self, 
        recent_highs: List[SwingPoint], 
        recent_lows: List[SwingPoint], 
        trade: TradeExecution
    ) -> Tuple[bool, str]:
        """檢查下跌趨勢反轉（多頭持倉）"""
        if (recent_highs[1].price < recent_highs[0].price and
            recent_lows[1].price < recent_lows[0].price):
            if trade.calculate_r_multiple() >= 1.0:
                return True, " (LH+LL)"
        return False, ""
    
    def _check_uptrend_reversal(
        self, 
        recent_highs: List[SwingPoint], 
        recent_lows: List[SwingPoint], 
        trade: TradeExecution
    ) -> Tuple[bool, str]:
        """檢查上漲趨勢反轉（空頭持倉）"""
        if (recent_highs[1].price > recent_highs[0].price and
            recent_lows[1].price > recent_lows[0].price):
            if trade.calculate_r_multiple() >= 1.0:
                return True, " (HH+HL)"
        return False, ""

    def _check_rsi_divergence_exit(
        self, 
        trade: TradeExecution, 
        close: np.ndarray
    ) -> Tuple[bool, str]:
        """檢查 RSI 背離出場信號"""
        rsi: np.ndarray[Tuple[Any], np.dtype[Any]] = self._calculate_rsi(close, self.rsi_period)
        
        if len(rsi) < 3:
            return False, ""
        
        setup: TradeSetup = trade.setup
        
        # 多頭持倉：頂部背離
        if setup.direction == 'long':
            if rsi[-3] > 70 and rsi[-1] < rsi[-2] < rsi[-3]:
                if trade.calculate_r_multiple() >= 2.0:
                    return True, f"RSI  ({rsi[-1]:.1f})"
        
        # 空頭持倉：底部背離
        elif setup.direction == 'short':
            if rsi[-3] < 30 and rsi[-1] > rsi[-2] > rsi[-3]:
                if trade.calculate_r_multiple() >= 2.0:
                    return True, f"RSI  ({rsi[-1]:.1f})"
        
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
            
            # 執行出場訂單
            if not self._process_exit_order(trade, reason, connector, exit_size):
                return False
            
            # 處理完全出場後的清理工作
            if trade.current_position_size <= 0:
                self._handle_complete_exit(trade, reason)
            
            return True
            
        except Exception as e:
            logger.error(f" execute_exit: {e}")
            return False
    
    def _process_exit_order(
        self, 
        trade: TradeExecution, 
        reason: str, 
        connector: Any, 
        exit_size: float
    ) -> bool:
        """處理出場訂單執行"""
        if connector is None:
            return self._simulate_exit_order(trade, reason, exit_size)
        else:
            return self._execute_real_exit_order(trade, reason, connector, exit_size)
    
    def _simulate_exit_order(
        self, 
        trade: TradeExecution, 
        reason: str, 
        exit_size: float
    ) -> bool:
        """模擬模式下的出場處理"""
        logger.info(f": {trade.trade_id}, : {reason}")
        
        pnl = self._calculate_exit_pnl(trade, trade.average_exit_price or trade.setup.entry_price, exit_size)
        trade.realized_pnl += pnl
        trade.current_position_size -= exit_size
        trade.exit_fills.append({
            'price': trade.average_exit_price or trade.setup.entry_price,
            'size': exit_size,
            'time': datetime.now().isoformat(),
            'reason': reason,
        })
        return True
    
    def _execute_real_exit_order(
        self, 
        trade: TradeExecution, 
        reason: str, 
        connector: Any, 
        exit_size: float
    ) -> bool:
        """實盤模式下的出場處理"""
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
            
            pnl = self._calculate_exit_pnl(trade, fill_price, exit_size)
            trade.realized_pnl += pnl
            trade.current_position_size -= exit_size
            trade.exit_fills.append({
                'order_id': order_result.get('orderId'),
                'price': fill_price,
                'size': exit_size,
                'time': datetime.now().isoformat(),
                'reason': reason,
            })
            return True
        return False
    
    def _calculate_exit_pnl(
        self, 
        trade: TradeExecution, 
        exit_price: float, 
        exit_size: float
    ) -> float:
        """計算出場PnL"""
        if trade.setup.direction == 'long':
            return (exit_price - trade.average_entry_price) * exit_size
        else:
            return (trade.average_entry_price - exit_price) * exit_size
    
    def _handle_complete_exit(self, trade: TradeExecution, reason: str) -> None:
        """處理完全出場後的清理工作"""
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
            f"R: {trade.calculate_r_multiple():.2f}, "
            f": {trade.holding_duration}"
        )


# 
StrategyRegistry.register('swing_trading', SwingTradingStrategy)
