"""
配對交易策略 (Pair Trading / Statistical Arbitrage Strategy)
============================================================

核心理念：
利用兩個具有長期協整關係的加密貨幣（如 BTC/ETH），交易它們之間
對數價格比率（spread）的均值回歸特性。

交易邏輯：
1. 計算兩資產的對數價格比率（log spread）
2. 計算 spread 的滾動 Z 分數
3. 當 Z > +閾值 → 做空 spread（做空主要資產）
4. 當 Z < -閾值 → 做多 spread（做多主要資產）
5. 當 |Z| 回歸到出場閾值 → 平倉

資料輸入：
- ohlcv_data: 主要資產（如 BTC）的 OHLCV 數組
- additional_data['secondary_ohlcv']: 次要資產（如 ETH）的 OHLCV 數組

優勢：
- 市場中性（降低方向性風險）
- 基於統計套利的理論基礎
- 適合震盪或低趨勢市場環境

創建日期：2026-03-09
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
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


@dataclass
class PairAnalysis:
    """配對分析結果"""
    correlation: float = 0.0
    cointegration_score: float = 0.0

    spread: float = 0.0
    spread_mean: float = 0.0
    spread_std: float = 0.0
    z_score: float = 0.0
    halflife: float = float('inf')

    signal_direction: Optional[str] = None
    spread_history: np.ndarray = field(default_factory=lambda: np.array([]))
    z_history: np.ndarray = field(default_factory=lambda: np.array([]))


class PairTradingStrategy(BaseStrategy):
    """
    配對交易策略（統計套利）

    以主要資產（如 BTC）為交易標的。
    次要資產數據通過 additional_data['secondary_ohlcv'] 傳入。
    """

    def __init__(
        self,
        timeframe: str = "1h",
        lookback_period: int = 60,
        entry_z_threshold: float = 2.0,
        exit_z_threshold: float = 0.5,
        min_correlation: float = 0.65,
        min_halflife: float = 5.0,
        max_halflife: float = 120.0,
        risk_params: Optional[RiskParameters] = None,
    ):
        super().__init__(
            name="Pair Trading",
            timeframe=timeframe,
            risk_params=risk_params or RiskParameters(
                max_risk_per_trade_pct=1.5,
                min_risk_reward_ratio=1.5,
                max_holding_period_hours=96,
                cooldown_after_loss=1,
            ),
        )
        self.lookback_period = lookback_period
        self.entry_z_threshold = entry_z_threshold
        self.exit_z_threshold = exit_z_threshold
        self.min_correlation = min_correlation
        self.min_halflife = min_halflife
        self.max_halflife = max_halflife
        self.required_confirmations = 2
        self.atr_period = 14
        self.take_profit_r_multiples = [2.0, 3.5, 5.0]
        self.exit_portions = [0.40, 0.35, 0.25]

    # ========================
    # Spread 核心計算
    # ========================

    def _calculate_spread(
        self,
        primary_close: np.ndarray,
        secondary_close: np.ndarray,
    ) -> np.ndarray:
        """計算對數價格比率作為 spread"""
        min_len = min(len(primary_close), len(secondary_close))
        primary = primary_close[-min_len:]
        secondary = secondary_close[-min_len:]
        primary = np.where(primary <= 0, 1e-8, primary)
        secondary = np.where(secondary <= 0, 1e-8, secondary)
        return np.log(primary) - np.log(secondary)

    def _calculate_z_score(
        self,
        spread: np.ndarray,
        lookback: int,
    ) -> Tuple[np.ndarray, float, float]:
        """計算滾動 Z 分數序列，返回 (z_scores, final_mean, final_std)"""
        n = len(spread)
        lookback = min(lookback, n)
        z_scores = np.full(n, np.nan)

        for i in range(lookback - 1, n):
            window = spread[i - lookback + 1:i + 1]
            mean = np.mean(window)
            std = np.std(window)
            if std > 1e-10:
                z_scores[i] = (spread[i] - mean) / std

        final_window = spread[-lookback:]
        return z_scores, float(np.mean(final_window)), float(np.std(final_window))

    def _calculate_correlation(
        self,
        primary_close: np.ndarray,
        secondary_close: np.ndarray,
        period: int,
    ) -> float:
        """計算皮爾遜相關係數"""
        min_len = min(len(primary_close), len(secondary_close), period)
        p = primary_close[-min_len:]
        s = secondary_close[-min_len:]
        if len(p) < 10 or np.std(p) == 0 or np.std(s) == 0:
            return 0.0
        corr = float(np.corrcoef(p, s)[0, 1])
        return 0.0 if np.isnan(corr) else corr

    def _estimate_halflife(self, spread: np.ndarray) -> float:
        """
        估計 spread 均值回歸半衰期（AR(1) OLS 估計）

        Δspread_t = φ * spread_(t-1) + ε
        halflife = -ln(2) / ln(1 + φ)
        """
        if len(spread) < 20:
            return float('inf')

        spread_lag = spread[:-1]
        spread_diff = np.diff(spread)
        var_lag = np.var(spread_lag)
        if var_lag < 1e-10:
            return float('inf')

        phi = float(np.cov(spread_diff, spread_lag)[0, 1] / var_lag)
        if phi >= 0:
            return float('inf')

        return max(1.0, float(-np.log(2) / np.log(1 + phi)))

    def _calculate_atr(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
    ) -> float:
        """計算 ATR"""
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

    # ========================
    # 1. 市場分析
    # ========================

    def analyze_market(
        self,
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """分析配對市場狀態"""
        self.state = StrategyState.ANALYZING

        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        primary_close = ohlcv_data[:, 4]
        current_price = float(primary_close[-1])
        atr = self._calculate_atr(high, low, primary_close)

        secondary_ohlcv = (additional_data or {}).get('secondary_ohlcv')
        if secondary_ohlcv is None or len(secondary_ohlcv) < self.lookback_period:
            self.state = StrategyState.IDLE
            return self._no_pair_data_result(current_price, atr)

        secondary_close = secondary_ohlcv[:, 4]
        analysis = PairAnalysis()

        analysis.correlation = self._calculate_correlation(
            primary_close, secondary_close, self.lookback_period
        )
        spread = self._calculate_spread(primary_close, secondary_close)
        analysis.spread_history = spread

        z_scores, spread_mean, spread_std = self._calculate_z_score(
            spread, self.lookback_period
        )
        analysis.z_history = z_scores
        analysis.spread = float(spread[-1]) if len(spread) > 0 else 0.0
        analysis.spread_mean = spread_mean
        analysis.spread_std = spread_std
        analysis.z_score = float(z_scores[-1]) if not np.isnan(z_scores[-1]) else 0.0

        analysis.halflife = self._estimate_halflife(spread[-self.lookback_period:])

        recent_z = z_scores[~np.isnan(z_scores)][-20:]
        if len(recent_z) > 0:
            analysis.cointegration_score = float(np.mean(np.abs(recent_z) < 3.0))

        self.state = StrategyState.IDLE
        self._last_analysis_time = datetime.now()

        abs_z = abs(analysis.z_score)
        if abs_z > self.entry_z_threshold:
            market_condition = MarketCondition.HIGH_VOLATILITY
        else:
            market_condition = MarketCondition.SIDEWAYS

        return {
            'market_condition': market_condition,
            'trend_direction': 'long' if analysis.z_score < 0 else 'short',
            'trend_strength': min(100.0, abs_z / max(self.entry_z_threshold, 0.01) * 50.0),
            'volatility': 'high' if abs_z > self.entry_z_threshold else 'normal',
            'key_levels': {
                'spread': analysis.spread,
                'spread_mean': spread_mean,
                'z_score': analysis.z_score,
            },
            'pair_analysis': analysis,
            'atr': atr,
            'current_price': current_price,
            'analysis_summary': (
                f"配對Z分數: {analysis.z_score:.2f}, "
                f"相關性: {analysis.correlation:.2f}, "
                f"半衰期: {analysis.halflife:.1f}K線"
            ),
        }

    def _no_pair_data_result(self, current_price: float, atr: float) -> Dict[str, Any]:
        """缺少次要資產數據時的默認返回"""
        return {
            'market_condition': MarketCondition.SIDEWAYS,
            'trend_direction': 'neutral',
            'trend_strength': 0.0,
            'volatility': 'normal',
            'key_levels': {},
            'pair_analysis': None,
            'atr': atr,
            'current_price': current_price,
            'analysis_summary': "配對交易：缺少次要資產 OHLCV 數據",
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
        配對交易入場條件：
        1. 相關性 >= min_correlation
        2. 半衰期在合理範圍（具有均值回歸性）
        3. |Z 分數| >= entry_z_threshold
        4. 風險回報比 >= min_risk_reward_ratio
        """
        pair_analysis: Optional[PairAnalysis] = market_analysis.get('pair_analysis')
        if pair_analysis is None:
            return None

        current_price = market_analysis['current_price']
        atr = market_analysis.get('atr', 0.0)
        if atr == 0.0 or current_price == 0.0:
            return None

        if pair_analysis.correlation < self.min_correlation:
            return None
        if not (self.min_halflife <= pair_analysis.halflife <= self.max_halflife):
            return None

        z = pair_analysis.z_score
        if abs(z) < self.entry_z_threshold:
            return None

        if z > self.entry_z_threshold:
            direction = 'short'
            entry_note = f"Spread 高估 Z={z:.2f}，做空主要資產"
        else:
            direction = 'long'
            entry_note = f"Spread 低估 Z={z:.2f}，做多主要資產"

        stop_atr_mult = 2.0
        risk_amount = atr * stop_atr_mult
        if direction == 'long':
            stop_loss = current_price - risk_amount
            tp1 = current_price + risk_amount * self.take_profit_r_multiples[0]
            tp2 = current_price + risk_amount * self.take_profit_r_multiples[1]
            tp3 = current_price + risk_amount * self.take_profit_r_multiples[2]
        else:
            stop_loss = current_price + risk_amount
            tp1 = current_price - risk_amount * self.take_profit_r_multiples[0]
            tp2 = current_price - risk_amount * self.take_profit_r_multiples[1]
            tp3 = current_price - risk_amount * self.take_profit_r_multiples[2]
        if risk_amount == 0.0:
            return None

        risk_reward = abs(tp1 - current_price) / risk_amount
        if risk_reward < self.risk_params.min_risk_reward_ratio:
            return None

        abs_z = abs(z)
        if abs_z >= 3.0:
            signal_strength = SignalStrength.VERY_STRONG
        elif abs_z >= 2.5:
            signal_strength = SignalStrength.STRONG
        elif abs_z >= 2.0:
            signal_strength = SignalStrength.MODERATE
        else:
            signal_strength = SignalStrength.WEAK

        return TradeSetup(
            symbol="BTCUSDT",
            direction=direction,
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
                entry_note,
                f"相關性: {pair_analysis.correlation:.2f}",
                f"半衰期: {pair_analysis.halflife:.1f} K線",
                f"協整強度: {pair_analysis.cointegration_score:.1%}",
            ],
            entry_confirmations=2,
            required_confirmations=self.required_confirmations,
            valid_until=datetime.now() + timedelta(hours=8),
            key_levels={
                'spread_mean': pair_analysis.spread_mean,
                'z_score': z,
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
        """執行配對交易入場"""
        try:
            execution = TradeExecution(
                trade_id=f"PT_{uuid.uuid4().hex[:8]}",
                setup=setup,
                actual_entry_price=setup.entry_price,
                entry_time=datetime.now(),
                current_position_size=setup.total_position_size,
                average_entry_price=setup.entry_price,
                highest_price_since_entry=setup.entry_price,
                lowest_price_since_entry=setup.entry_price,
            )
            self.state = StrategyState.POSITION_OPEN
            logger.info(
                f"[配對交易] 入場: {setup.direction.upper()} @ {setup.entry_price:.2f}, "
                f"Z={setup.key_levels.get('z_score', 0):.2f}, "
                f"SL: {setup.stop_loss:.2f}"
            )
            return execution
        except Exception as e:
            logger.error(f"[配對交易] 入場失敗: {e}")
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
        """管理配對交易倉位"""
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
            logger.info(f"[配對交易] 止損移至保本 @ {trade.setup.entry_price:.2f}")

        if not mgmt.tp1_filled:
            tp1 = trade.setup.take_profit_1
            if (trade.setup.direction == 'long' and current_price >= tp1) or \
               (trade.setup.direction == 'short' and current_price <= tp1):
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
        3. 超過持倉時限
        （Z 分數回歸出場建議透過 evaluate_exit_by_z_score 處理）
        """
        setup = trade.setup
        effective_stop = trade.trailing_stop_price or setup.stop_loss

        if setup.direction == 'long' and current_price <= effective_stop:
            return True, f"觸及止損 {effective_stop:.2f}"
        if setup.direction == 'short' and current_price >= effective_stop:
            return True, f"觸及止損 {effective_stop:.2f}"

        if setup.direction == 'long' and current_price >= setup.take_profit_3:
            return True, "觸及 TP3"
        if setup.direction == 'short' and current_price <= setup.take_profit_3:
            return True, "觸及 TP3"

        time_exit, time_reason = self.check_time_based_exit(trade)
        if time_exit:
            return True, time_reason

        return False, ""

    def evaluate_exit_by_z_score(
        self,
        current_z: float,
        trade: TradeExecution,
    ) -> Tuple[bool, str]:
        """
        基於 Z 分數的出場（由交易管理層在持倉期間持續調用）

        - |Z| <= exit_z_threshold → Z 回歸均值，平倉
        - Z 持續朝不利方向擴大（> 1.5x entry_threshold）→ 停損
        """
        if abs(current_z) <= self.exit_z_threshold:
            return True, f"Z 分數回歸均值 Z={current_z:.2f}"

        unfavorable_threshold = self.entry_z_threshold * 1.5
        if trade.setup.direction == 'long' and current_z > unfavorable_threshold:
            return True, f"Z 分數反向擴大 Z={current_z:.2f}"
        if trade.setup.direction == 'short' and current_z < -unfavorable_threshold:
            return True, f"Z 分數反向擴大 Z={current_z:.2f}"

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
        """執行配對交易出場"""
        try:
            trade.exit_reason = reason
            trade.exit_time = datetime.now()
            self.state = StrategyState.IDLE
            self.performance.update(trade)
            self.trade_history.append(trade)
            logger.info(
                f"[配對交易] 出場: {reason}, "
                f"R倍數: {trade.calculate_r_multiple():.2f}"
            )
            if "止損" in reason:
                self._cooldown_until = datetime.now() + timedelta(
                    hours=self.risk_params.cooldown_after_loss
                )
            return True
        except Exception as e:
            logger.error(f"[配對交易] 出場失敗: {e}")
            return False


StrategyRegistry.register("pair_trading", PairTradingStrategy)
