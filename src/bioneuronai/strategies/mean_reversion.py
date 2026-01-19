"""
均值回歸策略 (Mean Reversion Strategy)
=======================================

核心理念：
價格傾向於回歸到平均值，當價格偏離過遠時會反轉

適用場景：
- 盤整市場或通道交易
- 價格過度延伸後的反轉
- 波動率收縮後的爆發

主要組件：
1. 布林通道系統
2. Z-Score 偏離測量
3. 反轉確認系統
4. 動態止損系統

技術指標組合：
- Bollinger Bands
- Keltner Channel
- Z-Score
- RSI 極端值
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
class MeanReversionAnalysis:
    """均值回歸分析結果"""
    # 布林通道
    bb_upper: float = 0.0
    bb_middle: float = 0.0
    bb_lower: float = 0.0
    bb_width: float = 0.0
    bb_percent_b: float = 0.5  # 價格在通道中的位置 (0-1)
    bb_squeeze: bool = False   # 是否處於擠壓狀態
    
    # Keltner Channel
    kc_upper: float = 0.0
    kc_middle: float = 0.0
    kc_lower: float = 0.0
    
    # 通道擠壓 (Bollinger in Keltner)
    squeeze_on: bool = False
    squeeze_off: bool = False
    squeeze_momentum: float = 0.0
    
    # Z-Score
    z_score: float = 0.0
    z_score_extreme: bool = False  # |z| > 2
    z_score_very_extreme: bool = False  # |z| > 3
    
    # 均值
    sma_20: float = 0.0
    sma_50: float = 0.0
    price_deviation_from_mean: float = 0.0  # 百分比
    
    # RSI 狀態
    rsi_value: float = 50.0
    rsi_extreme: bool = False
    
    # 反轉訊號
    reversal_candle: bool = False
    reversal_type: str = "none"  # 'hammer', 'shooting_star', 'engulfing', etc.
    
    # 成交量
    volume_spike: bool = False
    relative_volume: float = 1.0


class MeanReversionStrategy(BaseStrategy):
    """
    均值回歸策略
    
    完整的均值回歸交易系統，包含：
    1. 多種偏離測量方法
    2. 反轉確認系統
    3. 擠壓突破識別
    4. 動態風險管理
    """
    
    def __init__(
        self,
        timeframe: str = "1h",
        risk_params: Optional[RiskParameters] = None,
    ):
        super().__init__(
            name="Mean Reversion",
            timeframe=timeframe,
            risk_params=risk_params or RiskParameters(
                max_risk_per_trade_pct=1.0,
                min_risk_reward_ratio=2.0,
                trailing_stop_activation=1.5,
                trailing_stop_distance=0.5,
                max_holding_period_hours=72,  # 3 天
            ),
        )
        
        # 布林通道參數
        self.bb_period = 20
        self.bb_std_dev = 2.0
        
        # Keltner Channel 參數
        self.kc_period = 20
        self.kc_atr_multiplier = 1.5
        
        # Z-Score 參數
        self.z_lookback = 20
        self.z_extreme_threshold = 2.0
        self.z_very_extreme_threshold = 2.5
        
        # RSI 參數
        self.rsi_period = 14
        self.rsi_overbought = 70
        self.rsi_oversold = 30
        self.rsi_extreme_overbought = 80
        self.rsi_extreme_oversold = 20
        
        # 進場確認
        self.required_confirmations = 3
        
        # 出場參數 (均值回歸較保守)
        self.take_profit_r_multiples = [2.0, 3.0, 4.0]
        self.exit_portions = [0.40, 0.35, 0.25]
    
    # ========================
    # 技術指標計算
    # ========================
    
    def _calculate_bollinger_bands(
        self,
        close: np.ndarray,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """計算布林通道"""
        n = len(close)
        middle = np.zeros(n)
        upper = np.zeros(n)
        lower = np.zeros(n)
        
        for i in range(period - 1, n):
            window = close[i - period + 1:i + 1]
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
        """計算 Keltner Channel"""
        n = len(close)
        
        # EMA 作為中線
        ema = np.zeros(n)
        multiplier = 2 / (period + 1)
        ema[period - 1] = np.mean(close[:period])
        for i in range(period, n):
            ema[i] = (close[i] * multiplier) + (ema[i - 1] * (1 - multiplier))
        
        # ATR
        atr = np.zeros(n)
        for i in range(1, n):
            h_l = high[i] - low[i]
            h_pc = abs(high[i] - close[i - 1])
            l_pc = abs(low[i] - close[i - 1])
            atr[i] = max(h_l, h_pc, l_pc)
        
        # 平滑 ATR
        atr_smooth = np.zeros(n)
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
        """計算 Z-Score"""
        n = len(close)
        z_score = np.zeros(n)
        
        for i in range(period - 1, n):
            window = close[i - period + 1:i + 1]
            mean = np.mean(window)
            std = np.std(window)
            if std > 0:
                z_score[i] = (close[i] - mean) / std
        
        return z_score
    
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
        
        avg_gain[period] = np.mean(gains[:period])
        avg_loss[period] = np.mean(losses[:period])
        
        for i in range(period + 1, n):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period
        
        rs = np.where(avg_loss != 0, avg_gain / avg_loss, 100)
        rsi = 100 - (100 / (1 + rs))
        rsi[:period] = 50
        
        return rsi
    
    def _detect_reversal_candle(
        self,
        open_prices: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray
    ) -> Tuple[bool, str]:
        """檢測反轉蠟燭形態"""
        if len(close) < 3:
            return False, "none"
        
        # 當前蠟燭
        o = open_prices[-1]
        h = high[-1]
        l = low[-1]
        c = close[-1]
        
        body = abs(c - o)
        upper_shadow = h - max(o, c)
        lower_shadow = min(o, c) - l
        candle_range = h - l
        
        if candle_range == 0:
            return False, "none"
        
        body_pct = body / candle_range
        
        # 前一根蠟燭
        prev_o = open_prices[-2]
        prev_c = close[-2]
        prev_body = abs(prev_c - prev_o)
        
        # 錘子線 (下影線長，上影線短，小實體，出現在下跌後)
        if (lower_shadow > body * 2 and 
            upper_shadow < body * 0.5 and
            body_pct < 0.3):
            # 確認之前是下跌
            if close[-3] > close[-2]:
                return True, "hammer"
        
        # 射擊之星 (上影線長，下影線短，小實體，出現在上漲後)
        if (upper_shadow > body * 2 and
            lower_shadow < body * 0.5 and
            body_pct < 0.3):
            if close[-3] < close[-2]:
                return True, "shooting_star"
        
        # 吞沒形態 (看漲吞沒)
        if (c > o and  # 當前是陽線
            prev_c < prev_o and  # 前一根是陰線
            o < prev_c and c > prev_o and  # 完全吞沒
            body > prev_body * 1.5):  # 實體更大
            return True, "bullish_engulfing"
        
        # 吞沒形態 (看跌吞沒)
        if (c < o and  # 當前是陰線
            prev_c > prev_o and  # 前一根是陽線
            o > prev_c and c < prev_o and  # 完全吞沒
            body > prev_body * 1.5):
            return True, "bearish_engulfing"
        
        # 十字星
        if body_pct < 0.1:
            return True, "doji"
        
        return False, "none"
    
    def _calculate_squeeze(
        self,
        bb_upper: np.ndarray,
        bb_lower: np.ndarray,
        kc_upper: np.ndarray,
        kc_lower: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """計算擠壓狀態"""
        n = len(bb_upper)
        squeeze_on = np.zeros(n, dtype=bool)
        squeeze_off = np.zeros(n, dtype=bool)
        
        for i in range(n):
            # 擠壓中：布林帶在 Keltner 通道內
            if bb_lower[i] > kc_lower[i] and bb_upper[i] < kc_upper[i]:
                squeeze_on[i] = True
            # 擠壓結束：布林帶突破 Keltner 通道
            elif i > 0 and squeeze_on[i - 1]:
                squeeze_off[i] = True
        
        return squeeze_on, squeeze_off
    
    # ========================
    # 1. 市場分析
    # ========================
    
    def analyze_market(
        self,
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        分析均值回歸機會
        """
        self.state = StrategyState.ANALYZING
        
        # 提取數據
        open_prices = ohlcv_data[:, 1]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        close = ohlcv_data[:, 4]
        volume = ohlcv_data[:, 5]
        
        current_price = close[-1]
        
        # 建立分析結果
        analysis = MeanReversionAnalysis()
        
        # 計算布林通道
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
            close, self.bb_period, self.bb_std_dev
        )
        analysis.bb_upper = bb_upper[-1]
        analysis.bb_middle = bb_middle[-1]
        analysis.bb_lower = bb_lower[-1]
        
        if bb_upper[-1] != 0:
            analysis.bb_width = (bb_upper[-1] - bb_lower[-1]) / bb_middle[-1] * 100
            analysis.bb_percent_b = (current_price - bb_lower[-1]) / (bb_upper[-1] - bb_lower[-1])
        
        # 計算 Keltner Channel
        kc_upper, kc_middle, kc_lower = self._calculate_keltner_channel(
            high, low, close, self.kc_period, self.kc_atr_multiplier
        )
        analysis.kc_upper = kc_upper[-1]
        analysis.kc_middle = kc_middle[-1]
        analysis.kc_lower = kc_lower[-1]
        
        # 擠壓狀態
        squeeze_on, squeeze_off = self._calculate_squeeze(
            bb_upper, bb_lower, kc_upper, kc_lower
        )
        analysis.squeeze_on = squeeze_on[-1]
        analysis.squeeze_off = squeeze_off[-1]
        
        # 擠壓動能
        if len(close) >= 20:
            momentum = close[-1] - np.mean(close[-20:])
            analysis.squeeze_momentum = momentum
        
        # Z-Score
        z_score = self._calculate_z_score(close, self.z_lookback)
        analysis.z_score = z_score[-1]
        analysis.z_score_extreme = abs(z_score[-1]) > self.z_extreme_threshold
        analysis.z_score_very_extreme = abs(z_score[-1]) > self.z_very_extreme_threshold
        
        # 均值偏離
        if len(close) >= 20:
            analysis.sma_20 = float(np.mean(close[-20:]))
        if len(close) >= 50:
            analysis.sma_50 = float(np.mean(close[-50:]))
        
        if analysis.sma_20 > 0:
            analysis.price_deviation_from_mean = (
                (current_price - analysis.sma_20) / analysis.sma_20 * 100
            )
        
        # RSI
        rsi = self._calculate_rsi(close, self.rsi_period)
        analysis.rsi_value = rsi[-1]
        analysis.rsi_extreme = (
            rsi[-1] > self.rsi_extreme_overbought or 
            rsi[-1] < self.rsi_extreme_oversold
        )
        
        # 反轉蠟燭
        has_reversal, reversal_type = self._detect_reversal_candle(
            open_prices, high, low, close
        )
        analysis.reversal_candle = has_reversal
        analysis.reversal_type = reversal_type
        
        # 成交量
        if len(volume) >= 20:
            avg_volume = np.mean(volume[-20:])
            analysis.relative_volume = volume[-1] / avg_volume if avg_volume > 0 else 1.0
            analysis.volume_spike = analysis.relative_volume > 1.5
        
        # 確定市場狀態
        # 均值回歸策略偏好盤整或過度延伸的市場
        if analysis.squeeze_on:
            market_condition = MarketCondition.LOW_VOLATILITY
        elif analysis.z_score_very_extreme:
            market_condition = MarketCondition.HIGH_VOLATILITY
        elif abs(analysis.price_deviation_from_mean) < 2:
            market_condition = MarketCondition.SIDEWAYS
        elif analysis.price_deviation_from_mean > 5:
            market_condition = MarketCondition.STRONG_UPTREND
        elif analysis.price_deviation_from_mean < -5:
            market_condition = MarketCondition.STRONG_DOWNTREND
        else:
            market_condition = MarketCondition.SIDEWAYS
        
        self.state = StrategyState.IDLE
        self._last_analysis_time = datetime.now()
        
        return {
            'market_condition': market_condition,
            'trend_direction': 'up' if current_price > analysis.sma_20 else 'down',
            'trend_strength': abs(analysis.price_deviation_from_mean),
            'volatility': 'low' if analysis.squeeze_on else ('high' if analysis.bb_width > 5 else 'normal'),
            'key_levels': {
                'bb_upper': analysis.bb_upper,
                'bb_middle': analysis.bb_middle,
                'bb_lower': analysis.bb_lower,
                'sma_20': analysis.sma_20,
                'sma_50': analysis.sma_50,
            },
            'mean_reversion_analysis': analysis,
            'indicators': {
                'z_score': analysis.z_score,
                'rsi': analysis.rsi_value,
                'bb_percent_b': analysis.bb_percent_b,
                'squeeze_on': analysis.squeeze_on,
            },
            'current_price': current_price,
            'analysis_summary': self._generate_mr_summary(analysis, market_condition),
        }
    
    def _generate_mr_summary(
        self,
        analysis: MeanReversionAnalysis,
        market_condition: MarketCondition
    ) -> str:
        """生成均值回歸分析摘要"""
        summary = []
        
        summary.append(f"市場狀態: {market_condition.value}")
        summary.append(f"Z-Score: {analysis.z_score:.2f}")
        
        if analysis.z_score_very_extreme:
            summary.append("🔔 極端偏離!")
        elif analysis.z_score_extreme:
            summary.append("⚠️ 顯著偏離")
        
        summary.append(f"BB %B: {analysis.bb_percent_b:.2f}")
        
        if analysis.squeeze_on:
            summary.append("🔒 擠壓中")
        elif analysis.squeeze_off:
            summary.append("💥 擠壓結束")
        
        summary.append(f"RSI: {analysis.rsi_value:.1f}")
        if analysis.rsi_extreme:
            if analysis.rsi_value > 70:
                summary.append("⚠️ 超買極端")
            else:
                summary.append("✅ 超賣極端")
        
        if analysis.reversal_candle:
            summary.append(f"🕯️ {analysis.reversal_type}")
        
        summary.append(f"偏離均值: {analysis.price_deviation_from_mean:.1f}%")
        
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
        評估均值回歸進場條件
        
        進場條件：
        1. 價格觸及布林帶外側或 Z-Score 極端
        2. RSI 極端
        3. 反轉蠟燭確認
        4. 成交量確認
        """
        analysis = market_analysis.get('mean_reversion_analysis')
        current_price = market_analysis.get('current_price')
        
        if not analysis or not current_price:
            return None
        
        # 收集確認訊號
        entry_conditions = []
        confirmations = 0
        direction = None
        
        # ===== 做多條件（價格過度下跌，預期回歸上漲）=====
        long_confirmations = 0
        long_conditions = []
        
        # 1. Z-Score 極端負值
        if analysis.z_score < -self.z_extreme_threshold:
            long_conditions.append(f"Z-Score 極端負值 ({analysis.z_score:.2f})")
            long_confirmations += 1
            if analysis.z_score_very_extreme:
                long_confirmations += 1  # 額外加分
        
        # 2. 價格觸及或跌破布林帶下軌
        if analysis.bb_percent_b < 0.1:
            long_conditions.append(f"觸及 BB 下軌 (%B: {analysis.bb_percent_b:.2f})")
            long_confirmations += 1
        elif analysis.bb_percent_b < 0:
            long_conditions.append(f"跌破 BB 下軌 (%B: {analysis.bb_percent_b:.2f})")
            long_confirmations += 2
        
        # 3. RSI 超賣
        if analysis.rsi_value < self.rsi_extreme_oversold:
            long_conditions.append(f"RSI 極端超賣 ({analysis.rsi_value:.1f})")
            long_confirmations += 1
        elif analysis.rsi_value < self.rsi_oversold:
            long_conditions.append(f"RSI 超賣 ({analysis.rsi_value:.1f})")
            long_confirmations += 1
        
        # 4. 反轉蠟燭
        if analysis.reversal_candle and analysis.reversal_type in ['hammer', 'bullish_engulfing', 'doji']:
            long_conditions.append(f"看漲反轉形態: {analysis.reversal_type}")
            long_confirmations += 1
        
        # 5. 成交量放大
        if analysis.volume_spike:
            long_conditions.append(f"成交量放大 ({analysis.relative_volume:.1f}x)")
            long_confirmations += 1
        
        # 6. 擠壓結束向上
        if analysis.squeeze_off and analysis.squeeze_momentum > 0:
            long_conditions.append("擠壓結束，動能向上")
            long_confirmations += 1
        
        # ===== 做空條件（價格過度上漲，預期回歸下跌）=====
        short_confirmations = 0
        short_conditions = []
        
        # 1. Z-Score 極端正值
        if analysis.z_score > self.z_extreme_threshold:
            short_conditions.append(f"Z-Score 極端正值 ({analysis.z_score:.2f})")
            short_confirmations += 1
            if analysis.z_score_very_extreme:
                short_confirmations += 1
        
        # 2. 價格觸及或突破布林帶上軌
        if analysis.bb_percent_b > 0.9:
            short_conditions.append(f"觸及 BB 上軌 (%B: {analysis.bb_percent_b:.2f})")
            short_confirmations += 1
        elif analysis.bb_percent_b > 1.0:
            short_conditions.append(f"突破 BB 上軌 (%B: {analysis.bb_percent_b:.2f})")
            short_confirmations += 2
        
        # 3. RSI 超買
        if analysis.rsi_value > self.rsi_extreme_overbought:
            short_conditions.append(f"RSI 極端超買 ({analysis.rsi_value:.1f})")
            short_confirmations += 1
        elif analysis.rsi_value > self.rsi_overbought:
            short_conditions.append(f"RSI 超買 ({analysis.rsi_value:.1f})")
            short_confirmations += 1
        
        # 4. 反轉蠟燭
        if analysis.reversal_candle and analysis.reversal_type in ['shooting_star', 'bearish_engulfing', 'doji']:
            short_conditions.append(f"看跌反轉形態: {analysis.reversal_type}")
            short_confirmations += 1
        
        # 5. 成交量放大
        if analysis.volume_spike:
            short_conditions.append(f"成交量放大 ({analysis.relative_volume:.1f}x)")
            short_confirmations += 1
        
        # 6. 擠壓結束向下
        if analysis.squeeze_off and analysis.squeeze_momentum < 0:
            short_conditions.append("擠壓結束，動能向下")
            short_confirmations += 1
        
        # 決定交易方向
        if long_confirmations >= self.required_confirmations:
            direction = 'long'
            entry_conditions = long_conditions
            confirmations = long_confirmations
        elif short_confirmations >= self.required_confirmations:
            direction = 'short'
            entry_conditions = short_conditions
            confirmations = short_confirmations
        else:
            logger.debug(
                f"均值回歸確認不足 - 多: {long_confirmations}, 空: {short_confirmations}"
            )
            return None
        
        # 計算停損
        # 均值回歸使用布林帶作為停損參考
        if direction == 'long':
            # 停損設在布林帶下軌外側
            stop_loss = analysis.bb_lower * 0.99
            # 目標是中軌或更高
            target_base = analysis.bb_middle
        else:
            stop_loss = analysis.bb_upper * 1.01
            target_base = analysis.bb_middle
        
        # 計算風險和目標
        risk_per_unit = abs(current_price - stop_loss)
        
        if direction == 'long':
            tp1 = current_price + (risk_per_unit * self.take_profit_r_multiples[0])
            tp2 = min(analysis.bb_upper, current_price + (risk_per_unit * self.take_profit_r_multiples[1]))
            tp3 = current_price + (risk_per_unit * self.take_profit_r_multiples[2])
        else:
            tp1 = current_price - (risk_per_unit * self.take_profit_r_multiples[0])
            tp2 = max(analysis.bb_lower, current_price - (risk_per_unit * self.take_profit_r_multiples[1]))
            tp3 = current_price - (risk_per_unit * self.take_profit_r_multiples[2])
        
        # 訊號強度
        if confirmations >= 5 and analysis.z_score_very_extreme:
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
            valid_until=datetime.now() + timedelta(minutes=30),
            key_levels={
                'bb_upper': analysis.bb_upper,
                'bb_middle': analysis.bb_middle,
                'bb_lower': analysis.bb_lower,
                'mean': analysis.sma_20,
            },
            invalidation_conditions=[
                f"價格跌破停損 {stop_loss:.2f}",
                "Z-Score 繼續擴大",
                "形成新的趨勢",
            ],
        )
        
        logger.info(
            f"均值回歸策略發現入場機會: "
            f"{direction.upper()} @ {current_price:.2f}, "
            f"Z={analysis.z_score:.2f}, 確認: {confirmations}"
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
        """執行均值回歸進場"""
        try:
            trade_id = f"MR_{setup.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            execution = TradeExecution(
                trade_id=trade_id,
                setup=setup,
            )
            
            # 均值回歸傾向分批進場
            portion_size = setup.total_position_size / setup.entry_portions
            
            if connector is None:
                logger.info(f"模擬均值回歸進場: {trade_id}")
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
                # 使用限價單
                if setup.direction == 'long':
                    limit_price = setup.entry_price * 1.001  # 允許稍高進場
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
            
            execution.highest_price_since_entry = execution.actual_entry_price
            execution.lowest_price_since_entry = execution.actual_entry_price
            
            self.state = StrategyState.POSITION_OPEN
            return execution
            
        except Exception as e:
            logger.error(f"均值回歸進場執行失敗: {e}")
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
        均值回歸部位管理
        
        特點：
        1. 價格回歸到均值時考慮獲利了結
        2. Z-Score 正常化時出場
        3. 較激進的部分獲利
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
        
        # 1. 快速移動停損到損益平衡（均值回歸策略更保守）
        if r_multiple >= 1.0 and not mgmt.stop_loss_moved_to_breakeven:
            new_stop = setup.entry_price
            if setup.direction == 'long':
                new_stop += risk_per_unit * 0.05
            else:
                new_stop -= risk_per_unit * 0.05
            
            mgmt.stop_loss_moved_to_breakeven = True
            mgmt.current_stop_loss = new_stop
            logger.info(f"均值回歸：快速移動到損益平衡 {new_stop:.2f}")
        
        # 2. 追蹤止損
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
        
        # 4. 均值回歸特殊：檢查是否已回歸均值
        close = ohlcv_data[:, 4]
        if len(close) >= self.z_lookback:
            z_score = self._calculate_z_score(close, self.z_lookback)
            current_z = z_score[-1]
            
            # 如果 Z-Score 已經回到正常範圍，考慮出場
            if abs(current_z) < 0.5 and r_multiple >= 1.0:
                logger.info(f"均值回歸完成: Z-Score 回到 {current_z:.2f}")
                # 這個資訊會被 evaluate_exit_conditions 使用
        
        # 5. 加碼機會（價格繼續偏離時加碼）
        if r_multiple < 0 and r_multiple > -0.5 and mgmt.entry_portions_filled < mgmt.entry_portions_total:
            # 如果價格繼續向不利方向移動但還沒觸及停損
            # 且偏離進一步擴大，可以加碼
            z_score = self._calculate_z_score(close, self.z_lookback)
            
            if setup.direction == 'long' and z_score[-1] < z_score[-5]:
                # 做多時，Z-Score 繼續下降
                mgmt.scaling_in_allowed = True
                logger.info("均值回歸加碼機會：偏離擴大")
        
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
        均值回歸出場條件
        
        出場條件：
        1. 停損觸發
        2. 價格回歸到均值
        3. Z-Score 正常化
        4. 反向突破
        5. 時間止損
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
        
        # 3. Z-Score 正常化
        close = ohlcv_data[:, 4]
        if len(close) >= self.z_lookback:
            z_score = self._calculate_z_score(close, self.z_lookback)
            current_z = z_score[-1]
            
            # 如果有足夠獲利且 Z-Score 已回到正常
            if trade.calculate_r_multiple() >= 1.5:
                if setup.direction == 'long' and -0.5 < current_z < 0.5:
                    return True, f"均值回歸完成 (Z: {current_z:.2f})"
                elif setup.direction == 'short' and -0.5 < current_z < 0.5:
                    return True, f"均值回歸完成 (Z: {current_z:.2f})"
        
        # 4. 價格穿越中軌
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
            close, self.bb_period, self.bb_std_dev
        )
        
        if trade.calculate_r_multiple() >= 1.0:
            if setup.direction == 'long' and current_price >= bb_middle[-1]:
                return True, f"價格回歸到布林中軌 ({bb_middle[-1]:.2f})"
            elif setup.direction == 'short' and current_price <= bb_middle[-1]:
                return True, f"價格回歸到布林中軌 ({bb_middle[-1]:.2f})"
        
        # 5. 反向突破（趨勢形成，均值回歸失敗的跡象）
        if len(close) >= 20:
            sma = np.mean(close[-20:])
            
            if setup.direction == 'long':
                # 做多時，如果價格持續在均值下方且持續下跌
                if (current_price < sma * 0.98 and 
                    close[-1] < close[-5] < close[-10]):
                    if trade.calculate_r_multiple() < -0.5:
                        return True, "趨勢形成，均值回歸假設可能失效"
        
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
        """執行均值回歸出場"""
        try:
            exit_size = trade.current_position_size * exit_portion
            
            if connector is None:
                logger.info(f"模擬均值回歸出場: {trade.trade_id}, 原因: {reason}")
                
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
                    f"均值回歸出場完成: {trade.trade_id}, "
                    f"PnL: {trade.realized_pnl:.2f}, "
                    f"R: {trade.calculate_r_multiple():.2f}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"均值回歸出場執行失敗: {e}")
            return False


# 註冊策略
StrategyRegistry.register('mean_reversion', MeanReversionStrategy)
