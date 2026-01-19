"""
趨勢跟隨策略 (Trend Following Strategy)
========================================

核心理念：
"趨勢是你的朋友" - 順勢而為，在趨勢確認後進場，持有直到趨勢反轉

適用場景：
- 明確的上升或下降趨勢
- 中長期持倉 (數小時到數天)
- 市場有足夠的波動性

主要組件：
1. 趨勢識別系統（多時間框架分析）
2. 進場確認系統（多指標確認）
3. 動態追蹤止損系統
4. 分批獲利了結系統

技術指標組合：
- EMA 系統 (21/55/200)
- MACD 趨勢確認
- ADX 趨勢強度
- ATR 波動性調整
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
    """趨勢分析結果"""
    # 主趨勢判斷
    primary_trend: str = "neutral"  # 'bullish', 'bearish', 'neutral'
    primary_trend_strength: float = 0.0  # 0-100
    
    # 多時間框架趨勢
    htf_trend: str = "neutral"  # Higher Timeframe (4h/Daily)
    mtf_trend: str = "neutral"  # Medium Timeframe (1h)
    ltf_trend: str = "neutral"  # Lower Timeframe (15m)
    
    # 趨勢一致性
    trend_alignment: float = 0.0  # 0-100, 越高表示多時間框架越一致
    
    # EMA 位置
    price_above_ema21: bool = False
    price_above_ema55: bool = False
    price_above_ema200: bool = False
    ema21_above_ema55: bool = False
    ema55_above_ema200: bool = False
    
    # MACD 狀態
    macd_bullish: bool = False
    macd_histogram_rising: bool = False
    macd_above_signal: bool = False
    
    # ADX 趨勢強度
    adx_value: float = 0.0
    adx_trending: bool = False  # ADX > 25
    plus_di_above_minus: bool = False
    
    # 動能
    momentum_score: float = 0.0  # -100 到 +100


class TrendFollowingStrategy(BaseStrategy):
    """
    趨勢跟隨策略
    
    完整的趨勢交易系統，包含：
    1. 多時間框架趨勢分析
    2. 多指標進場確認
    3. 動態風險管理
    4. 分批進出場管理
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
                max_holding_period_hours=168,  # 7 天
            ),
        )
        
        # 策略特定參數
        self.ema_periods = {'fast': 21, 'medium': 55, 'slow': 200}
        self.macd_params = {'fast': 12, 'slow': 26, 'signal': 9}
        self.adx_period = 14
        self.atr_period = 14
        self.min_adx_for_trend = 25
        self.required_confirmations = 4  # 需要至少4個確認訊號
        
        # 進場規則權重
        self.entry_weights = {
            'trend_alignment': 0.25,
            'ema_position': 0.20,
            'macd_confirmation': 0.20,
            'adx_strength': 0.15,
            'momentum': 0.10,
            'volume': 0.10,
        }
        
        # 出場參數
        self.take_profit_r_multiples = [2.0, 4.0, 6.0]
        self.exit_portions = [0.35, 0.35, 0.30]
        
    # ========================
    # 技術指標計算
    # ========================
    
    def _calculate_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """計算 EMA"""
        if len(data) < period:
            return np.full(len(data), np.nan)
        
        ema = np.zeros(len(data))
        multiplier = 2 / (period + 1)
        
        # 使用 SMA 初始化
        ema[period-1] = np.mean(data[:period])
        
        for i in range(period, len(data)):
            ema[i] = (data[i] * multiplier) + (ema[i-1] * (1 - multiplier))
        
        ema[:period-1] = np.nan
        return ema
    
    def _calculate_macd(
        self, 
        close: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """計算 MACD"""
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
        """計算 ADX, +DI, -DI"""
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
        
        # 平滑
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
        """計算 Smoothed Moving Average (Wilder's)"""
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
        """計算 ATR"""
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
        """計算成交量特徵"""
        if len(volume) < period:
            return {'relative_volume': 1.0, 'volume_trend': 0.0}
        
        recent_vol = volume[-period:]
        avg_vol = np.mean(volume[-period*3:-period]) if len(volume) >= period*3 else np.mean(recent_vol)
        
        current_vol = volume[-1]
        relative_volume = current_vol / avg_vol if avg_vol > 0 else 1.0
        
        # 成交量趨勢
        vol_sma_short = np.mean(volume[-5:])
        vol_sma_long = np.mean(volume[-20:])
        volume_trend = (vol_sma_short - vol_sma_long) / vol_sma_long if vol_sma_long > 0 else 0
        
        return {
            'relative_volume': float(relative_volume),
            'volume_trend': float(volume_trend * 100),
        }
    
    # ========================
    # 1. 市場分析
    # ========================
    
    def analyze_market(
        self, 
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        分析市場趨勢狀態
        
        OHLCV 格式: [timestamp, open, high, low, close, volume]
        """
        self.state = StrategyState.ANALYZING
        
        # 提取數據
        open_prices = ohlcv_data[:, 1]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        close = ohlcv_data[:, 4]
        volume = ohlcv_data[:, 5]
        
        current_price = close[-1]
        
        # 計算技術指標
        ema21 = self._calculate_ema(close, self.ema_periods['fast'])
        ema55 = self._calculate_ema(close, self.ema_periods['medium'])
        ema200 = self._calculate_ema(close, self.ema_periods['slow'])
        
        macd_line, signal_line, histogram = self._calculate_macd(close)
        adx, plus_di, minus_di = self._calculate_adx(high, low, close)
        atr = self._calculate_atr(high, low, close)
        
        volume_profile = self._calculate_volume_profile(volume, close)
        
        # 建立趨勢分析
        trend = TrendAnalysis()
        
        # EMA 位置分析
        trend.price_above_ema21 = current_price > ema21[-1]
        trend.price_above_ema55 = current_price > ema55[-1]
        trend.price_above_ema200 = current_price > ema200[-1] if not np.isnan(ema200[-1]) else True
        trend.ema21_above_ema55 = ema21[-1] > ema55[-1]
        trend.ema55_above_ema200 = ema55[-1] > ema200[-1] if not np.isnan(ema200[-1]) else True
        
        # MACD 分析
        trend.macd_above_signal = macd_line[-1] > signal_line[-1]
        trend.macd_histogram_rising = histogram[-1] > histogram[-2] if len(histogram) > 1 else False
        trend.macd_bullish = macd_line[-1] > 0 and trend.macd_above_signal
        
        # ADX 分析
        trend.adx_value = adx[-1] if not np.isnan(adx[-1]) else 0
        trend.adx_trending = trend.adx_value > self.min_adx_for_trend
        trend.plus_di_above_minus = plus_di[-1] > minus_di[-1]
        
        # 計算主趨勢
        bullish_signals = sum([
            trend.price_above_ema21,
            trend.price_above_ema55,
            trend.price_above_ema200,
            trend.ema21_above_ema55,
            trend.ema55_above_ema200,
            trend.macd_bullish,
            trend.macd_histogram_rising,
            trend.plus_di_above_minus,
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
        
        # 動能計算
        momentum = 0
        if trend.price_above_ema21:
            momentum += 25
        if trend.macd_histogram_rising:
            momentum += 25 if trend.macd_bullish else -25
        if trend.plus_di_above_minus:
            momentum += 25
        if volume_profile['relative_volume'] > 1.2:
            momentum += 25 if trend.primary_trend == "bullish" else -25
        
        trend.momentum_score = momentum if trend.primary_trend == "bullish" else -momentum
        
        # 計算支撐阻力
        recent_high = np.max(high[-20:])
        recent_low = np.min(low[-20:])
        
        # 確定市場狀態
        if trend.primary_trend == "bullish" and trend.adx_trending:
            market_condition = MarketCondition.UPTREND if trend.primary_trend_strength < 75 else MarketCondition.STRONG_UPTREND
        elif trend.primary_trend == "bearish" and trend.adx_trending:
            market_condition = MarketCondition.DOWNTREND if trend.primary_trend_strength < 75 else MarketCondition.STRONG_DOWNTREND
        else:
            market_condition = MarketCondition.SIDEWAYS
        
        self.state = StrategyState.IDLE
        self._last_analysis_time = datetime.now()
        
        return {
            'market_condition': market_condition,
            'trend_direction': trend.primary_trend,
            'trend_strength': trend.primary_trend_strength,
            'volatility': 'high' if atr[-1] > np.mean(atr[-20:]) * 1.5 else 'normal',
            'key_levels': {
                'resistance': recent_high,
                'support': recent_low,
                'ema21': ema21[-1],
                'ema55': ema55[-1],
                'ema200': ema200[-1] if not np.isnan(ema200[-1]) else None,
            },
            'trend_analysis': trend,
            'indicators': {
                'ema21': ema21[-1],
                'ema55': ema55[-1],
                'ema200': ema200[-1],
                'macd': macd_line[-1],
                'macd_signal': signal_line[-1],
                'macd_histogram': histogram[-1],
                'adx': adx[-1],
                'plus_di': plus_di[-1],
                'minus_di': minus_di[-1],
                'atr': atr[-1],
            },
            'volume_profile': volume_profile,
            'current_price': current_price,
            'analysis_summary': self._generate_analysis_summary(trend, market_condition),
        }
    
    def _generate_analysis_summary(
        self, 
        trend: TrendAnalysis, 
        market_condition: MarketCondition
    ) -> str:
        """生成分析摘要"""
        summary = []
        
        summary.append(f"市場狀態: {market_condition.value}")
        summary.append(f"主趨勢: {trend.primary_trend} (強度: {trend.primary_trend_strength:.1f}%)")
        
        if trend.adx_trending:
            summary.append(f"ADX: {trend.adx_value:.1f} - 趨勢明確")
        else:
            summary.append(f"ADX: {trend.adx_value:.1f} - 趨勢不明")
        
        if trend.primary_trend == "bullish":
            confirmations = []
            if trend.price_above_ema21:
                confirmations.append("價格>EMA21")
            if trend.macd_bullish:
                confirmations.append("MACD看多")
            if trend.plus_di_above_minus:
                confirmations.append("+DI>-DI")
            summary.append(f"多頭確認: {', '.join(confirmations)}")
        elif trend.primary_trend == "bearish":
            confirmations = []
            if not trend.price_above_ema21:
                confirmations.append("價格<EMA21")
            if not trend.macd_bullish:
                confirmations.append("MACD看空")
            if not trend.plus_di_above_minus:
                confirmations.append("-DI>+DI")
            summary.append(f"空頭確認: {', '.join(confirmations)}")
        
        summary.append(f"動能分數: {trend.momentum_score}")
        
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
        評估進場條件
        
        趨勢跟隨策略進場條件：
        1. 趨勢方向確認 (ADX > 25 且 DI 確認方向)
        2. 價格位置確認 (EMA 排列正確)
        3. MACD 確認
        4. 成交量確認
        5. 回調入場時機
        """
        trend = market_analysis.get('trend_analysis')
        indicators = market_analysis.get('indicators', {})
        volume_profile = market_analysis.get('volume_profile', {})
        current_price = market_analysis.get('current_price')
        
        if not trend or not current_price:
            return None
        
        # 基本趨勢檢查
        if trend.primary_trend == "neutral":
            logger.debug("趨勢不明確，跳過")
            return None
        
        if not trend.adx_trending:
            logger.debug(f"ADX {trend.adx_value:.1f} < {self.min_adx_for_trend}，趨勢不夠強")
            return None
        
        # 確定交易方向
        direction = 'long' if trend.primary_trend == "bullish" else 'short'
        
        # 收集確認訊號
        entry_conditions = []
        confirmations = 0
        
        # 確認 1: EMA 排列
        if direction == 'long':
            if trend.ema21_above_ema55 and trend.ema55_above_ema200:
                entry_conditions.append("EMA 多頭排列 (21>55>200)")
                confirmations += 1
        else:
            if not trend.ema21_above_ema55 and not trend.ema55_above_ema200:
                entry_conditions.append("EMA 空頭排列 (21<55<200)")
                confirmations += 1
        
        # 確認 2: 價格位置
        if direction == 'long':
            if trend.price_above_ema21 and trend.price_above_ema55:
                entry_conditions.append("價格在 EMA21/55 上方")
                confirmations += 1
        else:
            if not trend.price_above_ema21 and not trend.price_above_ema55:
                entry_conditions.append("價格在 EMA21/55 下方")
                confirmations += 1
        
        # 確認 3: MACD 方向
        if direction == 'long':
            if trend.macd_bullish and trend.macd_histogram_rising:
                entry_conditions.append("MACD 多頭且動能增強")
                confirmations += 1
        else:
            if not trend.macd_bullish and not trend.macd_histogram_rising:
                entry_conditions.append("MACD 空頭且動能增強")
                confirmations += 1
        
        # 確認 4: ADX/DI 方向
        if direction == 'long':
            if trend.plus_di_above_minus:
                entry_conditions.append(f"+DI > -DI (ADX: {trend.adx_value:.1f})")
                confirmations += 1
        else:
            if not trend.plus_di_above_minus:
                entry_conditions.append(f"-DI > +DI (ADX: {trend.adx_value:.1f})")
                confirmations += 1
        
        # 確認 5: 成交量
        rel_vol = volume_profile.get('relative_volume', 1.0)
        if rel_vol > 1.1:
            entry_conditions.append(f"成交量放大 ({rel_vol:.1f}x)")
            confirmations += 1
        
        # 確認 6: 回調入場（可選加分）
        close = ohlcv_data[:, 4]
        ema21 = indicators.get('ema21')
        
        if direction == 'long':
            # 價格回調到 EMA21 附近是好的入場點
            if ema21 and current_price < ema21 * 1.02 and current_price > ema21 * 0.98:
                entry_conditions.append("價格回調至 EMA21 附近")
                confirmations += 1
        else:
            if ema21 and current_price > ema21 * 0.98 and current_price < ema21 * 1.02:
                entry_conditions.append("價格反彈至 EMA21 附近")
                confirmations += 1
        
        # 檢查是否有足夠確認
        if confirmations < self.required_confirmations:
            logger.debug(
                f"確認訊號不足: {confirmations}/{self.required_confirmations}"
            )
            return None
        
        # 計算停損
        atr = indicators.get('atr', 0)
        if direction == 'long':
            stop_loss = current_price - (atr * 2)  # 2 ATR 停損
        else:
            stop_loss = current_price + (atr * 2)
        
        # 計算風險報酬
        risk_per_unit = abs(current_price - stop_loss)
        
        # 計算目標價
        if direction == 'long':
            tp1 = current_price + (risk_per_unit * self.take_profit_r_multiples[0])
            tp2 = current_price + (risk_per_unit * self.take_profit_r_multiples[1])
            tp3 = current_price + (risk_per_unit * self.take_profit_r_multiples[2])
        else:
            tp1 = current_price - (risk_per_unit * self.take_profit_r_multiples[0])
            tp2 = current_price - (risk_per_unit * self.take_profit_r_multiples[1])
            tp3 = current_price - (risk_per_unit * self.take_profit_r_multiples[2])
        
        # 確定訊號強度
        if confirmations >= 6 and trend.adx_value > 35:
            signal_strength = SignalStrength.VERY_STRONG
        elif confirmations >= 5:
            signal_strength = SignalStrength.STRONG
        elif confirmations >= 4:
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
            risk_reward_ratio=self.take_profit_r_multiples[0],  # 最小 R:R
            signal_strength=signal_strength,
            market_condition=market_analysis.get('market_condition', "NORMAL"),
            setup_time=datetime.now(),
            valid_until=datetime.now() + timedelta(minutes=30),
            key_levels=market_analysis.get('key_levels', {}),
            invalidation_conditions=[
                f"價格跌破停損 {stop_loss:.2f}",
                f"ADX 下降到 {self.min_adx_for_trend} 以下",
                "EMA 排列反轉",
            ],
        )
        
        logger.info(
            f"趨勢跟隨策略發現入場機會: "
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
        執行進場
        
        趨勢跟隨策略的進場執行：
        1. 使用限價單在有利價格進場
        2. 同時設置停損單
        3. 記錄所有執行細節
        """
        try:
            # 生成交易ID
            trade_id = f"TF_{setup.symbol}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
            
            # 建立交易執行記錄
            execution = TradeExecution(
                trade_id=trade_id,
                setup=setup,
            )
            
            # 分批進場參數
            portion_size = setup.total_position_size / setup.entry_portions
            
            # 模擬或實際執行（這裡提供介面，實際需要連接交易所）
            if connector is None:
                # 模擬執行
                logger.info(f"模擬進場: {trade_id}")
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
                # 實際執行
                # 第一批進場 (使用限價單)
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
                    
                    # 設置停損單
                    stop_order = connector.place_order(
                        symbol=setup.symbol,
                        side='SELL' if setup.direction == 'long' else 'BUY',
                        order_type='STOP_MARKET',
                        quantity=portion_size,
                        stop_price=setup.stop_loss,
                        reduce_only=True,
                    )
                    
                    logger.info(f"停損單已設置: {stop_order.get('orderId')}")
            
            execution.highest_price_since_entry = execution.actual_entry_price
            execution.lowest_price_since_entry = execution.actual_entry_price
            
            self.state = StrategyState.POSITION_OPEN
            return execution
            
        except Exception as e:
            logger.error(f"進場執行失敗: {e}")
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
        管理持倉部位
        
        趨勢跟隨的部位管理：
        1. 追蹤止損更新
        2. 達到 1R 獲利時移動停損到損益平衡
        3. 達到目標價時分批獲利了結
        4. 趨勢持續時考慮加碼
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
        
        # 1. 移動停損到損益平衡 (當達到 1R)
        if r_multiple >= 1.0 and not mgmt.stop_loss_moved_to_breakeven:
            new_stop = setup.entry_price
            if setup.direction == 'long':
                new_stop += risk_per_unit * 0.1  # 小幅盈利保護
            else:
                new_stop -= risk_per_unit * 0.1
            
            mgmt.stop_loss_moved_to_breakeven = True
            mgmt.current_stop_loss = new_stop
            logger.info(f"停損移動到損益平衡: {new_stop:.2f}")
        
        # 2. 追蹤止損
        new_trailing = self.update_trailing_stop(trade, current_price)
        if new_trailing:
            mgmt.stop_loss_trailing = True
            mgmt.current_stop_loss = new_trailing
            logger.info(f"追蹤止損更新: {new_trailing:.2f}")
        
        # 3. 檢查目標價達成
        if setup.direction == 'long':
            if current_price >= setup.take_profit_1 and not mgmt.tp1_filled:
                mgmt.tp1_filled = True
                mgmt.exit_portions_filled += 1
                logger.info(f"達到 TP1 {setup.take_profit_1:.2f}")
            
            if current_price >= setup.take_profit_2 and not mgmt.tp2_filled:
                mgmt.tp2_filled = True
                mgmt.exit_portions_filled += 1
                logger.info(f"達到 TP2 {setup.take_profit_2:.2f}")
            
            if current_price >= setup.take_profit_3 and not mgmt.tp3_filled:
                mgmt.tp3_filled = True
                mgmt.exit_portions_filled += 1
                logger.info(f"達到 TP3 {setup.take_profit_3:.2f}")
        else:
            if current_price <= setup.take_profit_1 and not mgmt.tp1_filled:
                mgmt.tp1_filled = True
                mgmt.exit_portions_filled += 1
            
            if current_price <= setup.take_profit_2 and not mgmt.tp2_filled:
                mgmt.tp2_filled = True
                mgmt.exit_portions_filled += 1
            
            if current_price <= setup.take_profit_3 and not mgmt.tp3_filled:
                mgmt.tp3_filled = True
                mgmt.exit_portions_filled += 1
        
        # 4. 評估加碼機會（趨勢持續且回調時）
        if r_multiple >= 1.0 and mgmt.entry_portions_filled < mgmt.entry_portions_total:
            # 檢查是否出現回調入場機會
            close = ohlcv_data[:, 4]
            if len(close) >= 21:
                ema21 = self._calculate_ema(close, 21)[-1]
                
                if setup.direction == 'long':
                    if current_price <= ema21 * 1.01:  # 回調到 EMA21
                        mgmt.scaling_in_allowed = True
                        logger.info("加碼機會: 價格回調到 EMA21")
                else:
                    if current_price >= ema21 * 0.99:
                        mgmt.scaling_in_allowed = True
        
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
        評估出場條件
        
        趨勢跟隨的出場條件：
        1. 停損觸發
        2. 追蹤止損觸發
        3. 趨勢反轉訊號
        4. 時間止損
        5. 所有目標達成
        """
        setup = trade.setup
        
        # 1. 停損檢查
        if setup.direction == 'long':
            active_stop = trade.trailing_stop_price or setup.stop_loss
            if current_price <= active_stop:
                return True, f"停損觸發 @ {current_price:.2f} (止損: {active_stop:.2f})"
        else:
            active_stop = trade.trailing_stop_price or setup.stop_loss
            if current_price >= active_stop:
                return True, f"停損觸發 @ {current_price:.2f} (止損: {active_stop:.2f})"
        
        # 2. 時間止損
        should_time_exit, time_reason = self.check_time_based_exit(trade)
        if should_time_exit:
            return True, time_reason
        
        # 3. 趨勢反轉檢查
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        
        if len(close) >= 26:
            # MACD 反轉
            macd_line, signal_line, _ = self._calculate_macd(close)
            
            if setup.direction == 'long':
                # 多單：MACD 由上穿下
                if macd_line[-1] < signal_line[-1] and macd_line[-2] > signal_line[-2]:
                    # 確認是否有足夠獲利才因反轉出場
                    if trade.calculate_r_multiple() >= 1.0:
                        return True, "MACD 死叉，趨勢可能反轉"
            else:
                # 空單：MACD 由下穿上
                if macd_line[-1] > signal_line[-1] and macd_line[-2] < signal_line[-2]:
                    if trade.calculate_r_multiple() >= 1.0:
                        return True, "MACD 金叉，趨勢可能反轉"
        
        # 4. ADX 大幅下降（趨勢減弱）
        if len(close) >= self.adx_period * 2:
            adx, plus_di, minus_di = self._calculate_adx(high, low, close)
            current_adx = adx[-1]
            prev_adx = adx[-5] if len(adx) >= 5 else current_adx
            
            # ADX 下降超過 30% 且低於趨勢閾值
            if current_adx < prev_adx * 0.7 and current_adx < self.min_adx_for_trend:
                if trade.calculate_r_multiple() >= 1.5:
                    return True, f"趨勢減弱 (ADX: {current_adx:.1f})"
        
        # 5. 所有目標達成
        # （由部位管理處理分批出場，這裡只處理完全出場）
        
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
        """
        執行出場
        """
        try:
            exit_size = trade.current_position_size * exit_portion
            
            if connector is None:
                # 模擬執行
                logger.info(f"模擬出場: {trade.trade_id}, 原因: {reason}")
                
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
                # 實際執行
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
                
                # 更新績效
                self.performance.update(trade)
                self.trade_history.append(trade)
                
                # 虧損後設置冷卻期
                if trade.realized_pnl < 0:
                    self._cooldown_until = datetime.now() + timedelta(
                        hours=self.risk_params.cooldown_after_loss
                    )
                
                self.state = StrategyState.IDLE
                
                logger.info(
                    f"出場完成: {trade.trade_id}, "
                    f"PnL: {trade.realized_pnl:.2f}, "
                    f"R: {trade.calculate_r_multiple():.2f}, "
                    f"原因: {reason}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"出場執行失敗: {e}")
            return False


# 註冊策略
StrategyRegistry.register('trend_following', TrendFollowingStrategy)
