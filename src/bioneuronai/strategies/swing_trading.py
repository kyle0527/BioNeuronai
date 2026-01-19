"""
波段交易策略 (Swing Trading Strategy)
======================================

核心理念：
捕捉市場中期價格波動，持倉數天到數週，
利用市場的擺動特性進行交易

適用場景：
- 有明確支撐/阻力區域的市場
- 波動性適中的市場環境
- 需要較少盯盤時間的交易者

主要組件：
1. 支撐阻力識別系統
2. 多時間框架分析
3. 擺動高低點識別
4. 斐波那契回調/擴展

技術指標組合：
- 支撐/阻力 (Pivot Points)
- RSI 超買超賣
- Stochastic 動能
- 斐波那契回調
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
class SwingPoint:
    """擺動點"""
    price: float
    index: int
    type: str  # 'high' or 'low'
    strength: int  # 左右各有幾根K線確認
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SwingAnalysis:
    """波段分析結果"""
    # 擺動結構
    swing_highs: List[SwingPoint] = field(default_factory=list)
    swing_lows: List[SwingPoint] = field(default_factory=list)
    
    # 趨勢結構
    higher_highs: bool = False
    higher_lows: bool = False
    lower_highs: bool = False
    lower_lows: bool = False
    
    # 支撐阻力
    nearest_resistance: float = 0.0
    nearest_support: float = 0.0
    key_levels: List[float] = field(default_factory=list)
    
    # 斐波那契
    fib_retracement_levels: Dict[str, float] = field(default_factory=dict)
    current_retracement_pct: float = 0.0
    
    # RSI 狀態
    rsi_value: float = 50.0
    rsi_divergence: str = "none"  # 'bullish', 'bearish', 'none'
    rsi_overbought: bool = False
    rsi_oversold: bool = False
    
    # Stochastic 狀態
    stoch_k: float = 50.0
    stoch_d: float = 50.0
    stoch_oversold: bool = False
    stoch_overbought: bool = False
    stoch_bullish_cross: bool = False
    stoch_bearish_cross: bool = False
    
    # 波段特徵
    current_swing_size: float = 0.0
    average_swing_size: float = 0.0
    swing_volatility: float = 0.0


class SwingTradingStrategy(BaseStrategy):
    """
    波段交易策略
    
    完整的波段交易系統，包含：
    1. 支撐阻力識別
    2. 擺動高低點分析
    3. RSI 背離檢測
    4. 斐波那契回調入場
    """
    
    def __init__(
        self,
        timeframe: str = "4h",
        risk_params: Optional[RiskParameters] = None,
    ):
        super().__init__(
            name="Swing Trading",
            timeframe=timeframe,
            risk_params=risk_params or RiskParameters(
                max_risk_per_trade_pct=1.5,
                min_risk_reward_ratio=2.5,
                trailing_stop_activation=2.0,
                trailing_stop_distance=0.75,
                max_holding_period_hours=336,  # 14 天
            ),
        )
        
        # 策略特定參數
        self.swing_lookback = 5  # 擺動點需要左右各 5 根 K 線確認
        self.rsi_period = 14
        self.stoch_period = 14
        self.stoch_smooth = 3
        
        # 超買超賣閾值
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.stoch_overbought = 80
        self.stoch_oversold = 20
        
        # 斐波那契回調關鍵位
        self.fib_levels = [0.236, 0.382, 0.5, 0.618, 0.786]
        self.ideal_retracement_range = (0.382, 0.618)  # 黃金回調區間
        
        # 進場確認
        self.required_confirmations = 3
        
        # 出場參數
        self.take_profit_r_multiples = [2.5, 4.0, 6.0]
        self.exit_portions = [0.40, 0.35, 0.25]
    
    # ========================
    # 技術指標計算
    # ========================
    
    def _find_swing_points(
        self,
        high: np.ndarray,
        low: np.ndarray,
        lookback: int = 5
    ) -> Tuple[List[SwingPoint], List[SwingPoint]]:
        """找出擺動高點和低點"""
        swing_highs = []
        swing_lows = []
        n = len(high)
        
        for i in range(lookback, n - lookback):
            # 檢查擺動高點
            is_swing_high = True
            for j in range(1, lookback + 1):
                if high[i] < high[i - j] or high[i] < high[i + j]:
                    is_swing_high = False
                    break
            
            if is_swing_high:
                swing_highs.append(SwingPoint(
                    price=high[i],
                    index=i,
                    type='high',
                    strength=lookback,
                ))
            
            # 檢查擺動低點
            is_swing_low = True
            for j in range(1, lookback + 1):
                if low[i] > low[i - j] or low[i] > low[i + j]:
                    is_swing_low = False
                    break
            
            if is_swing_low:
                swing_lows.append(SwingPoint(
                    price=low[i],
                    index=i,
                    type='low',
                    strength=lookback,
                ))
        
        return swing_highs, swing_lows
    
    def _calculate_rsi(self, close: np.ndarray, period: int = 14) -> np.ndarray:
        """計算 RSI"""
        n = len(close)
        if n < period + 1:
            return np.full(n, 50.0)
        
        deltas = np.diff(close)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.zeros(n)
        avg_loss = np.zeros(n)
        
        # 初始平均
        avg_gain[period] = np.mean(gains[:period])
        avg_loss[period] = np.mean(losses[:period])
        
        # 平滑平均
        for i in range(period + 1, n):
            avg_gain[i] = (avg_gain[i-1] * (period - 1) + gains[i-1]) / period
            avg_loss[i] = (avg_loss[i-1] * (period - 1) + losses[i-1]) / period
        
        rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
        rsi = 100 - (100 / (1 + rs))
        rsi[:period] = 50
        
        return rsi
    
    def _calculate_stochastic(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """計算 Stochastic Oscillator"""
        n = len(close)
        if n < period:
            return np.full(n, 50.0), np.full(n, 50.0)
        
        raw_k = np.zeros(n)
        
        for i in range(period - 1, n):
            highest = np.max(high[i - period + 1:i + 1])
            lowest = np.min(low[i - period + 1:i + 1])
            
            if highest != lowest:
                raw_k[i] = 100 * (close[i] - lowest) / (highest - lowest)
            else:
                raw_k[i] = 50
        
        # 平滑 K 線
        k = np.convolve(raw_k, np.ones(smooth_k) / smooth_k, mode='same')
        
        # D 線 (K 的移動平均)
        d = np.convolve(k, np.ones(smooth_d) / smooth_d, mode='same')
        
        return k, d
    
    def _calculate_fibonacci_levels(
        self,
        swing_high: float,
        swing_low: float,
        direction: str = 'bullish'
    ) -> Dict[str, float]:
        """計算斐波那契回調位"""
        diff = swing_high - swing_low
        levels = {}
        
        if direction == 'bullish':
            # 上漲後回調
            for level in self.fib_levels:
                levels[f'{level:.3f}'] = swing_high - (diff * level)
        else:
            # 下跌後反彈
            for level in self.fib_levels:
                levels[f'{level:.3f}'] = swing_low + (diff * level)
        
        levels['high'] = swing_high
        levels['low'] = swing_low
        
        return levels
    
    def _detect_rsi_divergence(
        self,
        close: np.ndarray,
        rsi: np.ndarray,
        swing_lows: List[SwingPoint],
        swing_highs: List[SwingPoint]
    ) -> str:
        """檢測 RSI 背離"""
        # 至少需要兩個擺動點來檢測背離
        if len(swing_lows) < 2 and len(swing_highs) < 2:
            return "none"
        
        # 看漲背離：價格創新低但 RSI 沒有
        if len(swing_lows) >= 2:
            recent_lows = sorted(swing_lows, key=lambda x: x.index)[-2:]
            if (recent_lows[1].price < recent_lows[0].price and 
                rsi[recent_lows[1].index] > rsi[recent_lows[0].index]):
                return "bullish"
        
        # 看跌背離：價格創新高但 RSI 沒有
        if len(swing_highs) >= 2:
            recent_highs = sorted(swing_highs, key=lambda x: x.index)[-2:]
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
        """找出支撐和阻力位"""
        current_price = close[-1]
        key_levels = []
        
        # 收集所有擺動點價格
        for sh in swing_highs:
            key_levels.append(sh.price)
        for sl in swing_lows:
            key_levels.append(sl.price)
        
        # 加入最近高低點
        if len(high) >= 20:
            key_levels.append(np.max(high[-20:]))
            key_levels.append(np.min(low[-20:]))
        
        # 找最近的支撐和阻力
        resistances = [l for l in key_levels if l > current_price]
        supports = [l for l in key_levels if l < current_price]
        
        nearest_resistance = min(resistances) if resistances else current_price * 1.05
        nearest_support = max(supports) if supports else current_price * 0.95
        
        # 去重並排序
        key_levels = sorted(list(set(key_levels)))
        
        return nearest_resistance, nearest_support, key_levels
    
    # ========================
    # 1. 市場分析
    # ========================
    
    def analyze_market(
        self,
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        分析市場波段結構
        """
        self.state = StrategyState.ANALYZING
        
        # 提取數據
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        close = ohlcv_data[:, 4]
        volume = ohlcv_data[:, 5]
        
        current_price = close[-1]
        
        # 找出擺動點
        swing_highs, swing_lows = self._find_swing_points(
            high, low, self.swing_lookback
        )
        
        # 計算技術指標
        rsi = self._calculate_rsi(close, self.rsi_period)
        stoch_k, stoch_d = self._calculate_stochastic(
            high, low, close, 
            self.stoch_period, self.stoch_smooth, self.stoch_smooth
        )
        
        # 建立波段分析
        analysis = SwingAnalysis()
        analysis.swing_highs = swing_highs
        analysis.swing_lows = swing_lows
        
        # 分析趨勢結構
        if len(swing_highs) >= 2:
            recent_highs = sorted(swing_highs, key=lambda x: x.index)[-2:]
            analysis.higher_highs = recent_highs[1].price > recent_highs[0].price
            analysis.lower_highs = recent_highs[1].price < recent_highs[0].price
        
        if len(swing_lows) >= 2:
            recent_lows = sorted(swing_lows, key=lambda x: x.index)[-2:]
            analysis.higher_lows = recent_lows[1].price > recent_lows[0].price
            analysis.lower_lows = recent_lows[1].price < recent_lows[0].price
        
        # 支撐阻力
        resistance, support, key_levels = self._find_support_resistance(
            high, low, close, swing_highs, swing_lows
        )
        analysis.nearest_resistance = resistance
        analysis.nearest_support = support
        analysis.key_levels = key_levels
        
        # 斐波那契回調
        if swing_highs and swing_lows:
            latest_high = max(swing_highs, key=lambda x: x.index)
            latest_low = max(swing_lows, key=lambda x: x.index)
            
            if latest_high.index > latest_low.index:
                # 上漲後的回調
                fib_levels = self._calculate_fibonacci_levels(
                    latest_high.price, latest_low.price, 'bullish'
                )
                swing_range = latest_high.price - latest_low.price
                if swing_range > 0:
                    analysis.current_retracement_pct = (
                        (latest_high.price - current_price) / swing_range
                    )
            else:
                # 下跌後的反彈
                fib_levels = self._calculate_fibonacci_levels(
                    latest_high.price, latest_low.price, 'bearish'
                )
                swing_range = latest_high.price - latest_low.price
                if swing_range > 0:
                    analysis.current_retracement_pct = (
                        (current_price - latest_low.price) / swing_range
                    )
            
            analysis.fib_retracement_levels = fib_levels
        
        # RSI 分析
        analysis.rsi_value = rsi[-1]
        analysis.rsi_overbought = rsi[-1] > self.rsi_overbought
        analysis.rsi_oversold = rsi[-1] < self.rsi_oversold
        analysis.rsi_divergence = self._detect_rsi_divergence(
            close, rsi, swing_lows, swing_highs
        )
        
        # Stochastic 分析
        analysis.stoch_k = stoch_k[-1]
        analysis.stoch_d = stoch_d[-1]
        analysis.stoch_overbought = stoch_k[-1] > self.stoch_overbought
        analysis.stoch_oversold = stoch_k[-1] < self.stoch_oversold
        
        if len(stoch_k) >= 2 and len(stoch_d) >= 2:
            analysis.stoch_bullish_cross = (
                stoch_k[-1] > stoch_d[-1] and stoch_k[-2] <= stoch_d[-2]
            )
            analysis.stoch_bearish_cross = (
                stoch_k[-1] < stoch_d[-1] and stoch_k[-2] >= stoch_d[-2]
            )
        
        # 波段統計
        if swing_highs and swing_lows:
            swings = sorted(swing_highs + swing_lows, key=lambda x: x.index)
            swing_sizes = []
            for i in range(1, len(swings)):
                swing_sizes.append(abs(swings[i].price - swings[i-1].price))
            
            if swing_sizes:
                analysis.average_swing_size = float(np.mean(swing_sizes))
                analysis.swing_volatility = float(np.std(swing_sizes))
                analysis.current_swing_size = swing_sizes[-1] if swing_sizes else 0
        
        # 確定市場狀態
        if analysis.higher_highs and analysis.higher_lows:
            market_condition = MarketCondition.UPTREND
            trend_direction = 'bullish'
        elif analysis.lower_highs and analysis.lower_lows:
            market_condition = MarketCondition.DOWNTREND
            trend_direction = 'bearish'
        else:
            market_condition = MarketCondition.SIDEWAYS
            trend_direction = 'neutral'
        
        self.state = StrategyState.IDLE
        self._last_analysis_time = datetime.now()
        
        return {
            'market_condition': market_condition,
            'trend_direction': trend_direction,
            'trend_strength': 50,  # 波段策略較少關注趨勢強度
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
    
    def _generate_swing_summary(
        self,
        analysis: SwingAnalysis,
        market_condition: MarketCondition
    ) -> str:
        """生成波段分析摘要"""
        summary = []
        
        summary.append(f"市場結構: {market_condition.value}")
        
        if analysis.higher_highs and analysis.higher_lows:
            summary.append("趨勢: HH + HL (上升趨勢)")
        elif analysis.lower_highs and analysis.lower_lows:
            summary.append("趨勢: LH + LL (下降趨勢)")
        else:
            summary.append("趨勢: 盤整中")
        
        summary.append(f"RSI: {analysis.rsi_value:.1f}")
        if analysis.rsi_overbought:
            summary.append("⚠️ RSI 超買")
        elif analysis.rsi_oversold:
            summary.append("✅ RSI 超賣")
        
        if analysis.rsi_divergence != "none":
            summary.append(f"🔔 RSI {analysis.rsi_divergence} 背離")
        
        summary.append(f"Stoch: K={analysis.stoch_k:.1f}, D={analysis.stoch_d:.1f}")
        if analysis.stoch_bullish_cross:
            summary.append("✅ Stoch 金叉")
        elif analysis.stoch_bearish_cross:
            summary.append("⚠️ Stoch 死叉")
        
        if analysis.fib_retracement_levels:
            summary.append(f"回調: {analysis.current_retracement_pct*100:.1f}%")
        
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
        評估波段進場條件
        
        進場條件：
        1. 價格回調到支撐/斐波那契位
        2. RSI/Stochastic 超賣/超買確認
        3. 價格行為確認 (蠟燭形態)
        4. 擺動結構支持
        """
        analysis = market_analysis.get('swing_analysis')
        current_price = market_analysis.get('current_price')
        
        if not analysis or not current_price:
            return None
        
        # 收集確認訊號
        entry_conditions = []
        confirmations = 0
        direction = None
        
        # ===== 看多條件 =====
        bullish_confirmations = 0
        bullish_conditions = []
        
        # 1. 結構確認：HH + HL
        if analysis.higher_highs and analysis.higher_lows:
            bullish_conditions.append("上升趨勢結構 (HH+HL)")
            bullish_confirmations += 1
        
        # 2. 回調到支撐位
        support_distance = abs(current_price - analysis.nearest_support) / current_price
        if support_distance < 0.02:  # 價格接近支撐 2% 以內
            bullish_conditions.append(f"價格接近支撐 ({analysis.nearest_support:.2f})")
            bullish_confirmations += 1
        
        # 3. 斐波那契回調入場
        retracement = analysis.current_retracement_pct
        if self.ideal_retracement_range[0] <= retracement <= self.ideal_retracement_range[1]:
            bullish_conditions.append(f"黃金回調區 ({retracement*100:.1f}%)")
            bullish_confirmations += 1
        
        # 4. RSI 超賣
        if analysis.rsi_oversold:
            bullish_conditions.append(f"RSI 超賣 ({analysis.rsi_value:.1f})")
            bullish_confirmations += 1
        
        # 5. RSI 看漲背離
        if analysis.rsi_divergence == "bullish":
            bullish_conditions.append("RSI 看漲背離")
            bullish_confirmations += 1
        
        # 6. Stochastic 金叉且在超賣區
        if analysis.stoch_bullish_cross and analysis.stoch_k < 30:
            bullish_conditions.append("Stoch 超賣金叉")
            bullish_confirmations += 1
        
        # ===== 看空條件 =====
        bearish_confirmations = 0
        bearish_conditions = []
        
        # 1. 結構確認：LH + LL
        if analysis.lower_highs and analysis.lower_lows:
            bearish_conditions.append("下降趨勢結構 (LH+LL)")
            bearish_confirmations += 1
        
        # 2. 反彈到阻力位
        resistance_distance = abs(analysis.nearest_resistance - current_price) / current_price
        if resistance_distance < 0.02:
            bearish_conditions.append(f"價格接近阻力 ({analysis.nearest_resistance:.2f})")
            bearish_confirmations += 1
        
        # 3. 斐波那契反彈入場
        if self.ideal_retracement_range[0] <= retracement <= self.ideal_retracement_range[1]:
            # 如果是下跌趨勢中的反彈
            if analysis.lower_highs:
                bearish_conditions.append(f"反彈至黃金區 ({retracement*100:.1f}%)")
                bearish_confirmations += 1
        
        # 4. RSI 超買
        if analysis.rsi_overbought:
            bearish_conditions.append(f"RSI 超買 ({analysis.rsi_value:.1f})")
            bearish_confirmations += 1
        
        # 5. RSI 看跌背離
        if analysis.rsi_divergence == "bearish":
            bearish_conditions.append("RSI 看跌背離")
            bearish_confirmations += 1
        
        # 6. Stochastic 死叉且在超買區
        if analysis.stoch_bearish_cross and analysis.stoch_k > 70:
            bearish_conditions.append("Stoch 超買死叉")
            bearish_confirmations += 1
        
        # 決定交易方向
        if bullish_confirmations >= self.required_confirmations:
            direction = 'long'
            entry_conditions = bullish_conditions
            confirmations = bullish_confirmations
        elif bearish_confirmations >= self.required_confirmations:
            direction = 'short'
            entry_conditions = bearish_conditions
            confirmations = bearish_confirmations
        else:
            logger.debug(
                f"確認不足 - 多: {bullish_confirmations}, 空: {bearish_confirmations}"
            )
            return None
        
        # 計算停損
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        
        # 使用最近擺動點作為停損參考
        if direction == 'long':
            # 停損設在最近擺動低點下方
            recent_lows = sorted(analysis.swing_lows, key=lambda x: x.index)
            if recent_lows:
                stop_loss = recent_lows[-1].price * 0.995  # 低點下 0.5%
            else:
                stop_loss = analysis.nearest_support * 0.99
        else:
            # 停損設在最近擺動高點上方
            recent_highs = sorted(analysis.swing_highs, key=lambda x: x.index)
            if recent_highs:
                stop_loss = recent_highs[-1].price * 1.005
            else:
                stop_loss = analysis.nearest_resistance * 1.01
        
        # 計算目標價
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
        
        # 訊號強度
        if confirmations >= 5:
            signal_strength = SignalStrength.VERY_STRONG
        elif confirmations >= 4:
            signal_strength = SignalStrength.STRONG
        elif confirmations >= 3:
            signal_strength = SignalStrength.MODERATE
        else:
            signal_strength = SignalStrength.WEAK
        
        # 建立交易設置
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
            valid_until=datetime.now() + timedelta(hours=4),  # 4小時有效
            key_levels={
                'resistance': analysis.nearest_resistance,
                'support': analysis.nearest_support,
                'fib_382': analysis.fib_retracement_levels.get('0.382'),
                'fib_618': analysis.fib_retracement_levels.get('0.618'),
            },
            invalidation_conditions=[
                f"價格跌破停損 {stop_loss:.2f}",
                "擺動結構被破壞",
                "RSI 中性化 (40-60)",
            ],
        )
        
        logger.info(
            f"波段策略發現入場機會: "
            f"{direction.upper()} @ {current_price:.2f}, "
            f"確認: {confirmations}, 強度: {signal_strength.name}"
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
        """
        執行波段進場
        
        波段策略傾向使用限價單，等待更好的價格
        """
        try:
            trade_id = f"SW_{setup.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            execution = TradeExecution(
                trade_id=trade_id,
                setup=setup,
            )
            
            # 波段策略使用分批進場
            portion_size = setup.total_position_size / setup.entry_portions
            
            if connector is None:
                # 模擬執行
                logger.info(f"模擬波段進場: {trade_id}")
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
                # 使用限價單進場，設置在當前價格略優的位置
                if setup.direction == 'long':
                    limit_price = setup.entry_price * 0.999  # 低 0.1%
                else:
                    limit_price = setup.entry_price * 1.001  # 高 0.1%
                
                order_result = connector.place_order(
                    symbol=setup.symbol,
                    side='BUY' if setup.direction == 'long' else 'SELL',
                    order_type='LIMIT',
                    quantity=portion_size,
                    price=limit_price,
                    time_in_force='GTC',
                )
                
                # 設置 OCO 訂單（停損 + 止盈）
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
            logger.error(f"波段進場執行失敗: {e}")
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
        波段部位管理
        
        特點：
        1. 較寬的追蹤止損
        2. 分批獲利了結
        3. 關注擺動點變化
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
        
        # 1. 移動停損到損益平衡 (當達到 1.5R)
        if r_multiple >= 1.5 and not mgmt.stop_loss_moved_to_breakeven:
            new_stop = setup.entry_price
            # 加一點緩衝
            if setup.direction == 'long':
                new_stop += risk_per_unit * 0.1
            else:
                new_stop -= risk_per_unit * 0.1
            
            mgmt.stop_loss_moved_to_breakeven = True
            mgmt.current_stop_loss = new_stop
            logger.info(f"波段策略：停損移到損益平衡 {new_stop:.2f}")
        
        # 2. 追蹤止損（使用較寬的距離）
        new_trailing = self.update_trailing_stop(trade, current_price)
        if new_trailing:
            mgmt.stop_loss_trailing = True
            mgmt.current_stop_loss = new_trailing
        
        # 3. 檢查目標達成
        if setup.direction == 'long':
            if current_price >= setup.take_profit_1 and not mgmt.tp1_filled:
                mgmt.tp1_filled = True
                mgmt.exit_portions_filled += 1
                logger.info(f"波段 TP1 達成: {setup.take_profit_1:.2f}")
            
            if current_price >= setup.take_profit_2 and not mgmt.tp2_filled:
                mgmt.tp2_filled = True
                mgmt.exit_portions_filled += 1
                logger.info(f"波段 TP2 達成: {setup.take_profit_2:.2f}")
        else:
            if current_price <= setup.take_profit_1 and not mgmt.tp1_filled:
                mgmt.tp1_filled = True
                mgmt.exit_portions_filled += 1
            
            if current_price <= setup.take_profit_2 and not mgmt.tp2_filled:
                mgmt.tp2_filled = True
                mgmt.exit_portions_filled += 1
        
        # 4. 評估加碼機會（波段策略在回調時加碼）
        if r_multiple >= 0.5 and mgmt.entry_portions_filled < mgmt.entry_portions_total:
            high = ohlcv_data[:, 2]
            low = ohlcv_data[:, 3]
            
            swing_highs, swing_lows = self._find_swing_points(
                high, low, self.swing_lookback
            )
            
            if setup.direction == 'long' and swing_lows:
                latest_low = max(swing_lows, key=lambda x: x.index)
                if abs(current_price - latest_low.price) / current_price < 0.01:
                    mgmt.scaling_in_allowed = True
                    logger.info("波段加碼機會：回調到擺動低點")
        
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
        波段出場條件評估
        
        出場條件：
        1. 停損/追蹤止損觸發
        2. 擺動結構改變
        3. RSI 極端反轉
        4. 時間止損
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
        
        # 3. 擺動結構檢查
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        close = ohlcv_data[:, 4]
        
        swing_highs, swing_lows = self._find_swing_points(
            high, low, self.swing_lookback
        )
        
        if len(swing_lows) >= 2 and len(swing_highs) >= 2:
            recent_lows = sorted(swing_lows, key=lambda x: x.index)[-2:]
            recent_highs = sorted(swing_highs, key=lambda x: x.index)[-2:]
            
            if setup.direction == 'long':
                # 多單：如果開始出現 LH + LL
                if (recent_highs[1].price < recent_highs[0].price and
                    recent_lows[1].price < recent_lows[0].price):
                    if trade.calculate_r_multiple() >= 1.0:
                        return True, "擺動結構轉為下降趨勢 (LH+LL)"
            else:
                # 空單：如果開始出現 HH + HL
                if (recent_highs[1].price > recent_highs[0].price and
                    recent_lows[1].price > recent_lows[0].price):
                    if trade.calculate_r_multiple() >= 1.0:
                        return True, "擺動結構轉為上升趨勢 (HH+HL)"
        
        # 4. RSI 極端反轉
        rsi = self._calculate_rsi(close, self.rsi_period)
        
        if setup.direction == 'long':
            # 多單：RSI 超買後開始下降
            if len(rsi) >= 3:
                if rsi[-3] > 70 and rsi[-1] < rsi[-2] < rsi[-3]:
                    if trade.calculate_r_multiple() >= 2.0:
                        return True, f"RSI 從超買回落 ({rsi[-1]:.1f})"
        else:
            # 空單：RSI 超賣後開始上升
            if len(rsi) >= 3:
                if rsi[-3] < 30 and rsi[-1] > rsi[-2] > rsi[-3]:
                    if trade.calculate_r_multiple() >= 2.0:
                        return True, f"RSI 從超賣回升 ({rsi[-1]:.1f})"
        
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
        """執行波段出場"""
        try:
            exit_size = trade.current_position_size * exit_portion
            
            if connector is None:
                logger.info(f"模擬波段出場: {trade.trade_id}, 原因: {reason}")
                
                # 計算盈虧
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
                # 波段策略優先使用限價單出場
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
            
            # 完全出場時
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
                    f"波段出場完成: {trade.trade_id}, "
                    f"PnL: {trade.realized_pnl:.2f}, "
                    f"R: {trade.calculate_r_multiple():.2f}, "
                    f"持倉: {trade.holding_duration}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"波段出場執行失敗: {e}")
            return False


# 註冊策略
StrategyRegistry.register('swing_trading', SwingTradingStrategy)
