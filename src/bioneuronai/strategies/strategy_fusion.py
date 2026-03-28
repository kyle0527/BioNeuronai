"""
AI 策略融合系統 (AI Strategy Fusion System)
==========================================

核心理念：
結合 AI 預測與多個傳統策略，動態調整權重。

整合模塊：
AI 推理引擎 + 趨勢跟隨 + 均值回歸 + 波段交易 + 突破交易

工作流程：
1. 收集各策略信號
2. AI 評估市場狀態
3. 動態調整策略權重
4. 融合生成最終信號
5. 根據結果調整權重

優勢特點：
- 適應不同市場環境
- 降低單一策略風險
- 提高整體穩定性
- 持續自我優化
"""

import numpy as np
import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid

from .base_strategy import (
    BaseStrategy,
    TradeSetup,
    TradeExecution,
    PositionManagement,
    SignalStrength,
    MarketCondition,
)
from .breakout_trading import BreakoutTradingStrategy
from .direction_change_strategy import DirectionChangeStrategy
from .mean_reversion import MeanReversionStrategy
from .pair_trading_strategy import PairTradingStrategy
from .swing_trading import SwingTradingStrategy
from .trend_following import TrendFollowingStrategy

# 從 schemas 導入 EventContext (Single Source of Truth - 2026-01-25)
from schemas.rag import EventContext

logger = logging.getLogger(__name__)


class FusionMethod(Enum):
    """"""
    WEIGHTED_VOTE = "weighted_vote"          # 
    BEST_PERFORMER = "best_performer"        # 
    MARKET_ADAPTIVE = "market_adaptive"      # 
    CONFIDENCE_BASED = "confidence_based"    # 
    ENSEMBLE = "ensemble"                     # 


@dataclass
class StrategyWeight:
    """"""
    strategy_name: str
    base_weight: float = 0.25  # 
    performance_weight: float = 0.0  # 
    market_condition_weight: float = 0.0  # 
    recent_performance_weight: float = 0.0  # 
    final_weight: float = 0.25  # 
    
    # 
    win_rate: float = 0.5
    profit_factor: float = 1.0
    avg_r_multiple: float = 0.0
    total_trades: int = 0
    recent_trades: int = 0
    recent_wins: int = 0
    
    # 
    best_conditions: List[MarketCondition] = field(default_factory=list)
    worst_conditions: List[MarketCondition] = field(default_factory=list)


@dataclass
class FusionSignal:
    """"""
    signal_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 
    contributing_strategies: List[str] = field(default_factory=list)
    strategy_signals: Dict[str, Optional[TradeSetup]] = field(default_factory=dict)
    
    # 
    consensus_direction: Optional[str] = None  # 'long', 'short', None
    consensus_strength: float = 0.0  # 0-1
    confidence_score: float = 0.0  # 0-1
    
    # 
    should_trade: bool = False
    selected_setup: Optional[TradeSetup] = None
    fusion_method_used: FusionMethod = FusionMethod.WEIGHTED_VOTE
    
    # 
    has_conflict: bool = False
    conflict_description: str = ""
    conflict_resolution: str = ""


@dataclass
class MarketRegime:
    """"""
    regime_type: str = "normal"  # 'trending', 'ranging', 'volatile', 'quiet', 'transitioning'
    confidence: float = 0.5
    duration_bars: int = 0
    
    # 
    recommended_strategies: List[str] = field(default_factory=list)
    avoid_strategies: List[str] = field(default_factory=list)


class AIStrategyFusion:
    """
    AI 
    
    
    """
    
    def __init__(
        self,
        timeframe: str = "1h",
        fusion_method: FusionMethod = FusionMethod.MARKET_ADAPTIVE,
        enable_learning: bool = True,
    ):
        self.timeframe = timeframe
        self.fusion_method = fusion_method
        self.enable_learning = enable_learning
        
        # 策略實例
        self.strategies: Dict[str, BaseStrategy] = {
            'trend_following': TrendFollowingStrategy(timeframe),
            'swing_trading': SwingTradingStrategy(timeframe),
            'mean_reversion': MeanReversionStrategy(timeframe),
            'breakout': BreakoutTradingStrategy(timeframe),
            'direction_change': DirectionChangeStrategy(timeframe),
            'pair_trading': PairTradingStrategy(timeframe),
        }

        # 各策略的市場環境適配性（必須在 _initialize_weights 之前設置）
        self._market_preference = {
            'trend_following': {
                'best': [MarketCondition.STRONG_UPTREND, MarketCondition.STRONG_DOWNTREND,
                         MarketCondition.UPTREND, MarketCondition.DOWNTREND],
                'worst': [MarketCondition.SIDEWAYS, MarketCondition.HIGH_VOLATILITY],
            },
            'swing_trading': {
                'best': [MarketCondition.UPTREND, MarketCondition.DOWNTREND,
                         MarketCondition.SIDEWAYS],
                'worst': [MarketCondition.STRONG_UPTREND, MarketCondition.STRONG_DOWNTREND],
            },
            'mean_reversion': {
                'best': [MarketCondition.SIDEWAYS, MarketCondition.LOW_VOLATILITY],
                'worst': [MarketCondition.STRONG_UPTREND, MarketCondition.STRONG_DOWNTREND],
            },
            'breakout': {
                'best': [MarketCondition.LOW_VOLATILITY],
                'worst': [MarketCondition.SIDEWAYS, MarketCondition.HIGH_VOLATILITY],
            },
            'direction_change': {
                'best': [MarketCondition.UPTREND, MarketCondition.DOWNTREND,
                         MarketCondition.STRONG_UPTREND, MarketCondition.STRONG_DOWNTREND],
                'worst': [MarketCondition.HIGH_VOLATILITY],
            },
            'pair_trading': {
                'best': [MarketCondition.SIDEWAYS, MarketCondition.LOW_VOLATILITY],
                'worst': [MarketCondition.STRONG_UPTREND, MarketCondition.STRONG_DOWNTREND],
            },
        }
        
        # 初始化權重 (必須在 _market_preference 之後)
        self.strategy_weights: Dict[str, StrategyWeight] = {}
        self._initialize_weights()
        
        # 
        self.fusion_history: List[FusionSignal] = []
        self.trade_outcomes: List[Dict[str, Any]] = []
        
        # 
        self.current_regime: Optional[MarketRegime] = None
        self._active_trade: Optional[TradeExecution] = None
        self._active_strategy: Optional[str] = None
        
        # 
        self.learning_rate = 0.1
        self.performance_decay = 0.95  # 
        self.min_weight = 0.05
        self.max_weight = 0.60
        
        # 
        self.min_consensus_strength = 0.4
        self.min_confidence_score = 0.5
        self.conflict_threshold = 0.3
    
    def _initialize_weights(self):
        """"""
        n_strategies = len(self.strategies)
        base_weight = 1.0 / n_strategies
        
        for name in self.strategies:
            self.strategy_weights[name] = StrategyWeight(
                strategy_name=name,
                base_weight=base_weight,
                final_weight=base_weight,
                best_conditions=self._market_preference.get(name, {}).get('best', []),
                worst_conditions=self._market_preference.get(name, {}).get('worst', []),
            )
    
    # ========================
    # 
    # ========================
    
    def identify_market_regime(
        self,
        ohlcv_data: np.ndarray,
    ) -> MarketRegime:
        """"""
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        
        regime = MarketRegime()
        
        if len(close) < 50:
            return regime
        
        # 
        sma_20 = np.mean(close[-20:])
        sma_50 = np.mean(close[-50:])
        
        # 
        returns = np.diff(close[-21:]) / close[-21:-1]
        volatility = np.std(returns) * np.sqrt(252)  # 

        # 使用對齊的一階報酬率視窗，避免 np.diff 後長度與分母不一致
        baseline_window = close[-50:-20]
        baseline_returns = (
            np.diff(baseline_window) / baseline_window[:-1]
            if len(baseline_window) >= 2 else np.array([0.0])
        )
        avg_volatility = np.std(baseline_returns) * np.sqrt(252)
        
        # 
        range_20 = (max(high[-20:]) - min(low[-20:])) / np.mean(close[-20:])
        
        # 
        trend_strength = abs(sma_20 - sma_50) / sma_50 * 100
        
        # ADX  ()
        adx = self._calculate_adx_simple(high, low, close)
        
        # 
        if adx > 30 and trend_strength > 3:
            if close[-1] > sma_20 > sma_50:
                regime.regime_type = "uptrending"
                regime.recommended_strategies = ['trend_following', 'breakout']
                regime.avoid_strategies = ['mean_reversion']
            elif close[-1] < sma_20 < sma_50:
                regime.regime_type = "downtrending"
                regime.recommended_strategies = ['trend_following', 'breakout']
                regime.avoid_strategies = ['mean_reversion']
            regime.confidence = 0.7 + (adx - 30) / 100
        
        elif range_20 < 0.05 and volatility < avg_volatility * 0.8:
            regime.regime_type = "quiet"
            regime.recommended_strategies = ['breakout']  # 
            regime.avoid_strategies = ['trend_following', 'swing_trading']
            regime.confidence = 0.6
        
        elif volatility > avg_volatility * 1.5:
            regime.regime_type = "volatile"
            regime.recommended_strategies = ['swing_trading']  # 
            regime.avoid_strategies = ['breakout']
            regime.confidence = 0.65
        
        elif adx < 20 and range_20 < 0.08:
            regime.regime_type = "ranging"
            regime.recommended_strategies = ['mean_reversion', 'swing_trading']
            regime.avoid_strategies = ['trend_following']
            regime.confidence = 0.6
        
        else:
            regime.regime_type = "normal"
            regime.recommended_strategies = ['swing_trading', 'trend_following']
            regime.avoid_strategies = []
            regime.confidence = 0.5
        
        # 
        regime.duration_bars = self._estimate_regime_duration(
            close, high, low, regime.regime_type
        )
        
        self.current_regime = regime
        return regime
    
    def _calculate_adx_simple(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> float:
        """ ADX """
        n = len(close)
        if n < period * 2:
            return 20.0  # 
        
        # +DM, -DM
        plus_dm = np.zeros(n)
        minus_dm = np.zeros(n)
        tr = np.zeros(n)
        
        for i in range(1, n):
            h_diff = high[i] - high[i-1]
            l_diff = low[i-1] - low[i]
            
            if h_diff > l_diff and h_diff > 0:
                plus_dm[i] = h_diff
            if l_diff > h_diff and l_diff > 0:
                minus_dm[i] = l_diff
            
            tr[i] = max(
                high[i] - low[i],
                abs(high[i] - close[i-1]),
                abs(low[i] - close[i-1])
            )
        
        # 
        atr = np.mean(tr[-period:]) if len(tr) >= period else 0
        plus_di = 100 * np.mean(plus_dm[-period:]) / atr if atr > 0 else 0
        minus_di = 100 * np.mean(minus_dm[-period:]) / atr if atr > 0 else 0
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0
        
        return float(dx)
    
    def _estimate_regime_duration(
        self,
        close: np.ndarray,
        _high: np.ndarray,
        _low: np.ndarray,
        regime_type: str
    ) -> int:
        """"""
        duration = 0
        n = len(close)
        
        for i in range(1, min(100, n)):
            idx = -1 - i
            if abs(idx) >= n:
                break
            
            # 
            window_close = close[idx:idx+20] if idx+20 < 0 else close[idx:]
            
            if len(window_close) < 5:
                break
            
            local_trend = window_close[-1] - window_close[0]
            
            if regime_type == "trending" and abs(local_trend) > np.std(window_close) * 0.5:
                duration += 1
            elif regime_type == "ranging" and abs(local_trend) < np.std(window_close) * 0.3:
                duration += 1
            elif regime_type in ["quiet", "volatile", "normal"]:
                duration += 1
            else:
                break
        
        return duration
    
    # ========================
    # 
    # ========================
    
    def update_weights_for_market(
        self,
        market_condition: Union[MarketCondition, str],
        regime: MarketRegime
    ):
        """"""
        for name, weight in self.strategy_weights.items():
            # 1. 
            condition_weight = 0.0
            
            # 2. 
            if market_condition in weight.best_conditions:
                condition_weight += 0.3
            elif market_condition in weight.worst_conditions:
                condition_weight -= 0.3
            
            # 3. 
            if name in regime.recommended_strategies:
                condition_weight += 0.2
            if name in regime.avoid_strategies:
                condition_weight -= 0.2
            
            weight.market_condition_weight = condition_weight
            
            # 4. 
            total = (
                weight.base_weight +
                weight.performance_weight +
                weight.market_condition_weight +
                weight.recent_performance_weight
            )
            
            # 
            weight.final_weight = max(self.min_weight, min(self.max_weight, total))
        
        # 
        self._normalize_weights()
    
    def update_weights_from_performance(self, strategy_name: str, trade_result: Dict):
        """"""
        if not self.enable_learning:
            return
        
        weight = self.strategy_weights.get(strategy_name)
        if not weight:
            return
        
        # 
        weight.total_trades += 1
        
        r_multiple = trade_result.get('r_multiple', 0)
        is_win = r_multiple > 0
        
        if is_win:
            weight.win_rate = (
                (weight.win_rate * (weight.total_trades - 1) + 1) / 
                weight.total_trades
            )
        else:
            weight.win_rate = (
                (weight.win_rate * (weight.total_trades - 1)) / 
                weight.total_trades
            )
        
        #
        weight.recent_trades = min(weight.recent_trades + 1, 20)  #  20
        if is_win:
            weight.recent_wins += 1
        # recent_wins 不可超過 recent_trades（避免勝率 > 1.0）
        weight.recent_wins = min(weight.recent_wins, weight.recent_trades)
        
        # 
        recent_win_rate = weight.recent_wins / weight.recent_trades if weight.recent_trades > 0 else 0.5
        
        # 
        performance_score = (weight.win_rate - 0.5) * 2  # -1  1
        recent_score = (recent_win_rate - 0.5) * 2
        
        weight.performance_weight = performance_score * 0.15
        weight.recent_performance_weight = recent_score * 0.1
        
        # 
        if weight.recent_trades >= 20:
            # 
            weight.recent_wins = int(weight.recent_wins * self.performance_decay)
            weight.recent_trades = int(weight.recent_trades * self.performance_decay)
        
        logger.info(
            f" {strategy_name} : "
            f"={weight.win_rate:.1%}, "
            f"={recent_win_rate:.1%}, "
            f"={weight.final_weight:.2f}"
        )
    
    def _normalize_weights(self):
        """權重正規化，確保總和為 1"""
        total = sum(w.final_weight for w in self.strategy_weights.values())
        
        if total > 0:
            for weight in self.strategy_weights.values():
                weight.final_weight /= total
    
    def _apply_asymmetric_filter(
        self,
        strategy_name: str,
        setup: Optional[TradeSetup],
        event_score: float
    ) -> Optional[TradeSetup]:
        """非對稱過濾器 - 根據新聞大腦評分過濾信號
        
        這是「司令部(News)對前線(Strategy)下達的交戰規則(ROE)」。
        在極端環境下，對逆勢信號實施嚴格過濾，對順勢信號快速放行。
        
        Args:
            strategy_name: 策略名稱
            setup: 原始交易設置
            event_score: 環境評分 (-10 到 +10)
            
        Returns:
            過濾後的交易設置，被攔截則返回 None
        """
        if not setup:
            return None
        
        # 環境閾值定義 (可由 AI 優化)
        EXTREME_BEARISH = -5.0  # 極度看空
        EXTREME_BULLISH = 5.0   # 極度看多
        
        # --- 情境 A: 環境極度看空 (如：戰爭+監管) ---
        if event_score < EXTREME_BEARISH:
            if setup.direction == 'long':
                # 對「做多」信號實施「禁飛令」：只有最強信號才放行
                if setup.signal_strength != SignalStrength.VERY_STRONG:
                    logger.info(
                        f"[非對稱過濾] 環境極空({event_score:.1f})，"
                        f"攔截 {strategy_name} 的普通做多信號"
                    )
                    return None
            # 對「做空」信號：順風，直接放行
        
        # --- 情境 B: 環境極度看多 ---
        elif event_score > EXTREME_BULLISH:
            if setup.direction == 'short' and setup.signal_strength != SignalStrength.VERY_STRONG:
                    logger.info(
                        f"[非對稱過濾] 環境極多({event_score:.1f})，"
                        f"攔截 {strategy_name} 的普通做空信號"
                    )
                    return None
        
        return setup
    
    def _adjust_weights_by_event(self, event_context: EventContext):
        """根據事件類型動態調整策略權重
        
        不同類型的事件適合不同的策略：
        - 突發事件 (WAR/HACK): 趨勢策略權重提高
        - 政策事件 (REGULATION): 觀望為主，降低所有權重
        - 宏觀事件 (MACRO): 趨勢和突破策略權重提高
        
        Args:
            event_context: 事件上下文
        """
        if not event_context or not event_context.event_type:
            return
        
        event_type = event_context.event_type.upper()
        intensity = event_context.intensity.upper()
        
        # 強度乘數
        intensity_multiplier = {
            'LOW': 0.5,
            'MEDIUM': 1.0,
            'HIGH': 1.5,
            'EXTREME': 2.0,
        }.get(intensity, 1.0)

        def _scale(name: str, factor: float) -> None:
            """安全地縮放單一策略權重"""
            w = self.strategy_weights.get(name)
            if w:
                w.final_weight *= factor

        # --- 突發事件 (戰爭、駭客攻擊): 強方向性趨勢，均值回歸失效 ---
        if event_type in ['WAR', 'HACK', 'BLACK_SWAN']:
            adj = 0.2 * intensity_multiplier
            _scale('trend_following', 1 + adj)
            _scale('breakout', 1 + adj)
            _scale('direction_change', 1 + adj * 0.5)   # DC 能捕捉事件驅動趨勢
            _scale('mean_reversion', 1 - adj)
            _scale('pair_trading', 1 - adj * 0.5)       # 配對關係在衝擊下不穩定
            logger.info(f"[事件權重調整] {event_type}: 提升趨勢/突破/DC，降低均值回歸/配對")

        # --- 監管事件: 謹慎觀望，將權重拉向均等分佈以降低集中度 ---
        elif event_type in ['REGULATION', 'POLICY']:
            adj = min(0.15 * intensity_multiplier, 1.0)
            n_strategies = len(self.strategy_weights)
            equal_weight = 1.0 / n_strategies if n_strategies > 0 else 1.0
            for weight in self.strategy_weights.values():
                # 向均等權重靠攏 adj 比例，實際改變分佈而不被 normalize 抵消
                weight.final_weight = weight.final_weight * (1 - adj) + equal_weight * adj
            logger.info(f"[事件權重調整] {event_type}: 權重向均等分佈靠攏 {adj:.0%}，降低策略集中度")

        # --- 宏觀經濟事件: 趨勢與波段主導 ---
        elif event_type in ['MACRO', 'FED', 'CPI', 'EARNINGS']:
            adj = 0.15 * intensity_multiplier
            _scale('trend_following', 1 + adj)
            _scale('swing_trading', 1 + adj * 0.5)
            _scale('direction_change', 1 + adj * 0.5)   # DC 同樣能捕捉宏觀驅動趨勢
            _scale('pair_trading', 1 - adj * 0.3)        # 宏觀事件可能破壞配對相關性
            logger.info(f"[事件權重調整] {event_type}: 提升趨勢/波段/DC")
        
        # 重新正規化權重
        self._normalize_weights()
    
    # ========================
    # 信號融合方法
    # ========================
    
    def generate_fusion_signal(
        self,
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None,
        event_score: float = 0.0,  # 來自新聞大腦的環境評分 (-10 到 +10)
        event_context: Optional[EventContext] = None  # 詳細事件上下文
    ) -> FusionSignal:
        """生成融合信號
        
        Args:
            ohlcv_data: OHLCV K線數據
            additional_data: 額外市場數據
            event_score: 環境評分，來自新聞分析大腦 (-10 看空, +10 看多, 0 中性)
            event_context: 詳細事件上下文，包含事件類型、強度等資訊
        
        Returns:
            FusionSignal: 融合後的交易信號
        """
        signal = FusionSignal(
            signal_id=f"FS_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(),
        )
        
        # 0. 處理事件上下文，計算有效的 event_score
        effective_event_score = event_score
        if event_context:
            effective_event_score = event_context.get_effective_score()
            # 根據事件類型調整策略權重
            self._adjust_weights_by_event(event_context)
        
        # 1. 識別市場狀態
        regime = self.identify_market_regime(ohlcv_data)
        
        # 2. 收集各策略信號
        market_analyses = {}
        trade_setups = {}
        
        for name, strategy in self.strategies.items():
            try:
                # 市場分析
                analysis = strategy.analyze_market(ohlcv_data, additional_data)
                market_analyses[name] = analysis
                
                # 入場條件評估
                setup = strategy.evaluate_entry_conditions(analysis, ohlcv_data)
                
                # 應用非對稱過濾器 (基於事件評分)
                setup = self._apply_asymmetric_filter(name, setup, effective_event_score)
                
                trade_setups[name] = setup
                
                if setup:
                    signal.contributing_strategies.append(name)
                
            except Exception as e:
                logger.error(f"策略 {name} 分析失敗: {e}")
                trade_setups[name] = None
        
        signal.strategy_signals = trade_setups
        
        # 取第一個有效的市場狀態
        market_condition: Union[MarketCondition, str] = MarketCondition.SIDEWAYS
        for analysis in market_analyses.values():
            mc = analysis.get('market_condition')
            if mc:
                market_condition = mc
                break
        
        self.update_weights_for_market(market_condition, regime)
        
        # 4. 
        if self.fusion_method == FusionMethod.WEIGHTED_VOTE:
            self._fuse_by_weighted_vote(signal)
        elif self.fusion_method == FusionMethod.BEST_PERFORMER:
            self._fuse_by_best_performer(signal)
        elif self.fusion_method == FusionMethod.MARKET_ADAPTIVE:
            self._fuse_by_market_adaptive(signal, regime)
        elif self.fusion_method == FusionMethod.CONFIDENCE_BASED:
            self._fuse_by_confidence(signal)
        else:
            self._fuse_ensemble(signal, regime)
        
        # 5. 
        self._detect_and_resolve_conflicts(signal)
        
        # 6. 
        self._make_final_decision(signal)
        
        # 7. 
        self.fusion_history.append(signal)
        
        return signal
    
    def _fuse_by_weighted_vote(self, signal: FusionSignal):
        """"""
        long_votes = 0.0
        short_votes = 0.0
        total_weight = 0.0
        
        for name, setup in signal.strategy_signals.items():
            if setup is None:
                continue
            
            weight = self.strategy_weights[name].final_weight
            total_weight += weight
            
            if setup.direction == 'long':
                long_votes += weight
            else:
                short_votes += weight
        
        if total_weight == 0:
            return
        
        long_ratio = long_votes / total_weight if total_weight > 0 else 0
        short_ratio = short_votes / total_weight if total_weight > 0 else 0
        
        if long_ratio > short_ratio and long_ratio > self.min_consensus_strength:
            signal.consensus_direction = 'long'
            signal.consensus_strength = long_ratio
        elif short_ratio > long_ratio and short_ratio > self.min_consensus_strength:
            signal.consensus_direction = 'short'
            signal.consensus_strength = short_ratio
        
        signal.confidence_score = max(long_ratio, short_ratio)
        signal.fusion_method_used = FusionMethod.WEIGHTED_VOTE
    
    def _fuse_by_best_performer(self, signal: FusionSignal):
        """"""
        best_strategy = None
        best_score = -1.0
        
        for name, setup in signal.strategy_signals.items():
            if setup is None:
                continue
            
            weight = self.strategy_weights[name]
            
            # 
            score = (
                weight.win_rate * 0.4 +
                (weight.profit_factor / 3) * 0.3 +  #  profit_factor  3
                (weight.recent_wins / max(weight.recent_trades, 1)) * 0.3
            )
            
            if score > best_score:
                best_score = score
                best_strategy = name
        
        if best_strategy:
            setup = signal.strategy_signals[best_strategy]
            if setup:  #  setup  None
                signal.consensus_direction = setup.direction
                signal.consensus_strength = best_score
                signal.confidence_score = best_score
                signal.selected_setup = setup
        
        signal.fusion_method_used = FusionMethod.BEST_PERFORMER
    
    def _fuse_by_market_adaptive(self, signal: FusionSignal, regime: MarketRegime):
        """"""
        # 
        prioritized_strategies = regime.recommended_strategies
        
        best_setup = None
        best_score = 0.0
        
        for name, setup in signal.strategy_signals.items():
            if setup is None:
                continue
            
            # 
            score = self.strategy_weights[name].final_weight
            
            # 
            if name in prioritized_strategies:
                score *= 1.5
            
            # 
            if name in regime.avoid_strategies:
                score *= 0.5
            
            # 
            strength_multiplier = {
                SignalStrength.VERY_STRONG: 1.5,
                SignalStrength.STRONG: 1.2,
                SignalStrength.MODERATE: 1.0,
                SignalStrength.WEAK: 0.8,
                SignalStrength.VERY_WEAK: 0.5,
            }
            score *= strength_multiplier.get(setup.signal_strength, 1.0)
            
            if score > best_score:
                best_score = score
                best_setup = setup
        
        if best_setup:
            signal.consensus_direction = best_setup.direction
            signal.consensus_strength = min(best_score, 1.0)
            signal.confidence_score = min(best_score, 1.0)
            signal.selected_setup = best_setup
        
        signal.fusion_method_used = FusionMethod.MARKET_ADAPTIVE
    
    def _fuse_by_confidence(self, signal: FusionSignal):
        """"""
        best_setup = None
        best_confidence = 0.0
        
        for name, setup in signal.strategy_signals.items():
            if setup is None:
                continue
            
            # 
            confidence = setup.entry_confirmations / max(setup.required_confirmations, 1)
            
            # 
            adjusted_confidence = confidence * self.strategy_weights[name].final_weight
            
            if adjusted_confidence > best_confidence:
                best_confidence = adjusted_confidence
                best_setup = setup
        
        if best_setup:
            signal.consensus_direction = best_setup.direction
            signal.consensus_strength = best_confidence
            signal.confidence_score = best_confidence
            signal.selected_setup = best_setup
        
        signal.fusion_method_used = FusionMethod.CONFIDENCE_BASED
    
    def _fuse_ensemble(self, signal: FusionSignal, regime: MarketRegime):
        """"""
        # 1. 
        vote_signal = FusionSignal()
        vote_signal.strategy_signals = signal.strategy_signals
        self._fuse_by_weighted_vote(vote_signal)
        
        # 2. 
        adaptive_signal = FusionSignal()
        adaptive_signal.strategy_signals = signal.strategy_signals
        self._fuse_by_market_adaptive(adaptive_signal, regime)
        
        # 3. 
        confidence_signal = FusionSignal()
        confidence_signal.strategy_signals = signal.strategy_signals
        self._fuse_by_confidence(confidence_signal)
        
        # 
        directions = [
            vote_signal.consensus_direction,
            adaptive_signal.consensus_direction,
            confidence_signal.consensus_direction,
        ]
        
        # 
        long_count = directions.count('long')
        short_count = directions.count('short')
        
        if long_count > short_count:
            signal.consensus_direction = 'long'
        elif short_count > long_count:
            signal.consensus_direction = 'short'
        
        # 
        scores = [
            vote_signal.confidence_score,
            adaptive_signal.confidence_score,
            confidence_signal.confidence_score,
        ]
        mean_score = np.mean([s for s in scores if s > 0]) if any(scores) else 0
        signal.confidence_score = float(mean_score)
        signal.consensus_strength = signal.confidence_score
        
        # 
        if adaptive_signal.selected_setup:
            signal.selected_setup = adaptive_signal.selected_setup
        
        signal.fusion_method_used = FusionMethod.ENSEMBLE
    
    def _detect_and_resolve_conflicts(self, signal: FusionSignal):
        """"""
        long_strategies = []
        short_strategies = []
        
        for name, setup in signal.strategy_signals.items():
            if setup is None:
                continue
            if setup.direction == 'long':
                long_strategies.append(name)
            else:
                short_strategies.append(name)
        
        # 
        if long_strategies and short_strategies:
            signal.has_conflict = True
            signal.conflict_description = (
                f": ={long_strategies}, ={short_strategies}"
            )
            
            # 
            long_weight = sum(
                self.strategy_weights[s].final_weight for s in long_strategies
            )
            short_weight = sum(
                self.strategy_weights[s].final_weight for s in short_strategies
            )
            
            if abs(long_weight - short_weight) < self.conflict_threshold:
                # 
                signal.conflict_resolution = ""
                signal.should_trade = False
            else:
                # 
                if long_weight > short_weight:
                    signal.conflict_resolution = f" ({long_weight:.2f} vs {short_weight:.2f})"
                else:
                    signal.conflict_resolution = f" ({short_weight:.2f} vs {long_weight:.2f})"
    
    def _make_final_decision(self, signal: FusionSignal):
        """"""
        # 
        if not signal.consensus_direction:
            signal.should_trade = False
            return
        
        if signal.confidence_score < self.min_confidence_score:
            signal.should_trade = False
            return
        
        if signal.has_conflict and "" in signal.conflict_resolution:
            signal.should_trade = False
            return
        
        # 
        if not signal.selected_setup:
            # 
            best_setup = None
            best_score = 0.0
            
            for name, setup in signal.strategy_signals.items():
                if setup and setup.direction == signal.consensus_direction:
                    score = self.strategy_weights[name].final_weight
                    if score > best_score:
                        best_score = score
                        best_setup = setup
            
            signal.selected_setup = best_setup
        
        signal.should_trade = signal.selected_setup is not None
    
    # ========================
    # 
    # ========================
    
    def execute_fusion_signal(
        self,
        signal: FusionSignal,
        connector: Any,
    ) -> Optional[TradeExecution]:
        """"""
        if not signal.should_trade or not signal.selected_setup:
            return None
        
        # 
        active_strategy_name = None
        for name, setup in signal.strategy_signals.items():
            if setup == signal.selected_setup:
                active_strategy_name = name
                break
        
        if not active_strategy_name:
            logger.error("")
            return None
        
        strategy = self.strategies[active_strategy_name]
        
        # 
        execution = strategy.execute_entry(signal.selected_setup, connector)
        
        if execution:
            self._active_trade = execution
            self._active_strategy = active_strategy_name
            
            logger.info(
                f": {signal.signal_id}, "
                f": {active_strategy_name}, "
                f": {signal.consensus_direction}, "
                f": {signal.confidence_score:.2f}"
            )
        
        return execution
    
    def manage_active_trade(
        self,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> Optional[PositionManagement]:
        """"""
        if not self._active_trade or not self._active_strategy:
            return None
        
        strategy = self.strategies[self._active_strategy]
        
        # 
        self._active_trade.average_exit_price = current_price
        
        # 
        management = strategy.manage_position(
            self._active_trade,
            current_price,
            ohlcv_data
        )
        
        return management
    
    def check_exit_conditions(
        self,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> Tuple[bool, str]:
        """"""
        if not self._active_trade or not self._active_strategy:
            return False, ""
        
        strategy = self.strategies[self._active_strategy]
        
        return strategy.evaluate_exit_conditions(
            self._active_trade,
            current_price,
            ohlcv_data
        )
    
    def execute_exit(
        self,
        reason: str,
        connector: Any,
    ) -> bool:
        """"""
        if not self._active_trade or not self._active_strategy:
            return False
        
        strategy = self.strategies[self._active_strategy]
        
        success = strategy.execute_exit(
            self._active_trade,
            reason,
            connector
        )
        
        if success:
            # 
            trade_result = {
                'strategy': self._active_strategy,
                'r_multiple': self._active_trade.calculate_r_multiple(),
                'pnl': self._active_trade.realized_pnl,
                'reason': reason,
                'timestamp': datetime.now().isoformat(),
            }
            
            self.trade_outcomes.append(trade_result)
            self.update_weights_from_performance(
                self._active_strategy,
                trade_result
            )
            
            # 
            self._active_trade = None
            self._active_strategy = None
        
        return success
    
    # ========================
    # 
    # ========================
    
    def get_strategy_report(self) -> Dict[str, Any]:
        """"""
        report: Dict[str, Any] = {
            'fusion_method': self.fusion_method.value,
            'total_fusion_signals': len(self.fusion_history),
            'total_trades': len(self.trade_outcomes),
            'current_regime': self.current_regime.__dict__ if self.current_regime else None,
            'strategy_weights': {},
            'recent_performance': {},
        }
        
        for name, weight in self.strategy_weights.items():
            report['strategy_weights'][name] = {
                'final_weight': weight.final_weight,
                'base_weight': weight.base_weight,
                'performance_weight': weight.performance_weight,
                'market_condition_weight': weight.market_condition_weight,
                'win_rate': weight.win_rate,
                'total_trades': weight.total_trades,
            }
        
        # 
        if self.trade_outcomes:
            recent = self.trade_outcomes[-20:]
            wins = sum(1 for t in recent if t.get('r_multiple', 0) > 0)
            total_r = sum(t.get('r_multiple', 0) for t in recent)
            
            report['recent_performance'] = {
                'trades': len(recent),
                'wins': wins,
                'win_rate': wins / len(recent) if recent else 0,
                'total_r': total_r,
                'avg_r': total_r / len(recent) if recent else 0,
            }
        
        return report
    
    def save_state(self, filepath: str):
        """"""
        state = {
            'weights': {
                name: {
                    'base_weight': w.base_weight,
                    'performance_weight': w.performance_weight,
                    'win_rate': w.win_rate,
                    'total_trades': w.total_trades,
                    'recent_trades': w.recent_trades,
                    'recent_wins': w.recent_wins,
                }
                for name, w in self.strategy_weights.items()
            },
            'trade_outcomes': self.trade_outcomes[-100:],  #  100 
            'fusion_method': self.fusion_method.value,
            'saved_at': datetime.now().isoformat(),
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f" {filepath}")
    
    def load_state(self, filepath: str):
        """"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            # 
            for name, data in state.get('weights', {}).items():
                if name in self.strategy_weights:
                    w = self.strategy_weights[name]
                    w.base_weight = data.get('base_weight', w.base_weight)
                    w.performance_weight = data.get('performance_weight', 0)
                    w.win_rate = data.get('win_rate', 0.5)
                    w.total_trades = data.get('total_trades', 0)
                    w.recent_trades = data.get('recent_trades', 0)
                    w.recent_wins = data.get('recent_wins', 0)
            
            self.trade_outcomes = state.get('trade_outcomes', [])
            
            # 
            self._normalize_weights()
            
            logger.info(f" {filepath} ")
            
        except Exception as e:
            logger.error(f": {e}")
