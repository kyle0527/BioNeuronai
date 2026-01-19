"""
AI 策略融合系統 (AI Strategy Fusion System)
==========================================

核心理念：
沒有任何一種交易方法是可以永遠適用的，
AI 需要學習如何在不同市場環境中動態融合多種策略

系統功能：
1. 策略權重學習
2. 市場環境識別
3. 動態策略選擇
4. 衝突解決機制
5. 績效追蹤與優化

融合方法：
- 加權投票
- 貝葉斯組合
- 強化學習優化
- 績效驅動調整
"""

import numpy as np
import logging
from typing import Optional, Dict, Any, List, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
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
    StrategyPerformance,
)
from .trend_following import TrendFollowingStrategy
from .swing_trading import SwingTradingStrategy
from .mean_reversion import MeanReversionStrategy
from .breakout_trading import BreakoutTradingStrategy

logger = logging.getLogger(__name__)


class FusionMethod(Enum):
    """融合方法"""
    WEIGHTED_VOTE = "weighted_vote"          # 加權投票
    BEST_PERFORMER = "best_performer"        # 最佳績效者
    MARKET_ADAPTIVE = "market_adaptive"      # 市場適應性
    CONFIDENCE_BASED = "confidence_based"    # 信心度基礎
    ENSEMBLE = "ensemble"                     # 集成方法


@dataclass
class StrategyWeight:
    """策略權重"""
    strategy_name: str
    base_weight: float = 0.25  # 基礎權重
    performance_weight: float = 0.0  # 績效調整權重
    market_condition_weight: float = 0.0  # 市場條件權重
    recent_performance_weight: float = 0.0  # 近期績效權重
    final_weight: float = 0.25  # 最終權重
    
    # 績效指標
    win_rate: float = 0.5
    profit_factor: float = 1.0
    avg_r_multiple: float = 0.0
    total_trades: int = 0
    recent_trades: int = 0
    recent_wins: int = 0
    
    # 市場條件適應性
    best_conditions: List[MarketCondition] = field(default_factory=list)
    worst_conditions: List[MarketCondition] = field(default_factory=list)


@dataclass
class FusionSignal:
    """融合訊號"""
    signal_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 來源策略
    contributing_strategies: List[str] = field(default_factory=list)
    strategy_signals: Dict[str, Optional[TradeSetup]] = field(default_factory=dict)
    
    # 融合結果
    consensus_direction: Optional[str] = None  # 'long', 'short', None
    consensus_strength: float = 0.0  # 0-1
    confidence_score: float = 0.0  # 0-1
    
    # 最終決策
    should_trade: bool = False
    selected_setup: Optional[TradeSetup] = None
    fusion_method_used: FusionMethod = FusionMethod.WEIGHTED_VOTE
    
    # 衝突資訊
    has_conflict: bool = False
    conflict_description: str = ""
    conflict_resolution: str = ""


@dataclass
class MarketRegime:
    """市場狀態判定"""
    regime_type: str = "normal"  # 'trending', 'ranging', 'volatile', 'quiet', 'transitioning'
    confidence: float = 0.5
    duration_bars: int = 0
    
    # 建議策略
    recommended_strategies: List[str] = field(default_factory=list)
    avoid_strategies: List[str] = field(default_factory=list)


class AIStrategyFusion:
    """
    AI 策略融合系統
    
    整合多個交易策略，通過學習和適應來動態調整策略權重
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
        
        # 初始化策略
        self.strategies: Dict[str, BaseStrategy] = {
            'trend_following': TrendFollowingStrategy(timeframe),
            'swing_trading': SwingTradingStrategy(timeframe),
            'mean_reversion': MeanReversionStrategy(timeframe),
            'breakout': BreakoutTradingStrategy(timeframe),
        }
        
        # 初始化策略權重
        self.strategy_weights: Dict[str, StrategyWeight] = {}
        self._initialize_weights()
        
        # 市場狀態偏好 (基於策略特性)
        self._market_preference = {
            'trend_following': {
                'best': [MarketCondition.STRONG_UPTREND, MarketCondition.STRONG_DOWNTREND,
                        MarketCondition.UPTREND, MarketCondition.DOWNTREND],
                'worst': [MarketCondition.SIDEWAYS, MarketCondition.HIGH_VOLATILITY],
            },
            'swing_trading': {
                'best': [MarketCondition.UPTREND, MarketCondition.DOWNTREND, 
                        "NORMAL"],  # 暫時使用字串
                'worst': [MarketCondition.STRONG_UPTREND, MarketCondition.STRONG_DOWNTREND],
            },
            'mean_reversion': {
                'best': [MarketCondition.SIDEWAYS, MarketCondition.LOW_VOLATILITY],
                'worst': [MarketCondition.STRONG_UPTREND, MarketCondition.STRONG_DOWNTREND],
            },
            'breakout': {
                'best': [MarketCondition.LOW_VOLATILITY],  # 擠壓後突破
                'worst': [MarketCondition.SIDEWAYS, MarketCondition.HIGH_VOLATILITY],
            },
        }
        
        # 學習歷史
        self.fusion_history: List[FusionSignal] = []
        self.trade_outcomes: List[Dict[str, Any]] = []
        
        # 當前狀態
        self.current_regime: Optional[MarketRegime] = None
        self._active_trade: Optional[TradeExecution] = None
        self._active_strategy: Optional[str] = None
        
        # 學習參數
        self.learning_rate = 0.1
        self.performance_decay = 0.95  # 舊績效衰減
        self.min_weight = 0.05
        self.max_weight = 0.60
        
        # 決策門檻
        self.min_consensus_strength = 0.4
        self.min_confidence_score = 0.5
        self.conflict_threshold = 0.3
    
    def _initialize_weights(self):
        """初始化策略權重"""
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
    # 市場狀態判斷
    # ========================
    
    def identify_market_regime(
        self,
        ohlcv_data: np.ndarray,
    ) -> MarketRegime:
        """識別當前市場狀態"""
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        
        regime = MarketRegime()
        
        if len(close) < 50:
            return regime
        
        # 計算趨勢指標
        sma_20 = np.mean(close[-20:])
        sma_50 = np.mean(close[-50:])
        
        # 計算波動率
        returns = np.diff(close[-21:]) / close[-21:-1]
        volatility = np.std(returns) * np.sqrt(252)  # 年化波動率
        avg_volatility = np.std(np.diff(close[-50:-20]) / close[-50:-20]) * np.sqrt(252)
        
        # 計算區間
        range_20 = (max(high[-20:]) - min(low[-20:])) / np.mean(close[-20:])
        
        # 計算趨勢強度
        trend_strength = abs(sma_20 - sma_50) / sma_50 * 100
        
        # ADX 計算 (簡化版)
        adx = self._calculate_adx_simple(high, low, close)
        
        # 判斷市場狀態
        if adx > 30 and trend_strength > 3:
            if close[-1] > sma_20 > sma_50:
                regime.regime_type = "trending"
                regime.recommended_strategies = ['trend_following', 'breakout']
                regime.avoid_strategies = ['mean_reversion']
            elif close[-1] < sma_20 < sma_50:
                regime.regime_type = "trending"
                regime.recommended_strategies = ['trend_following', 'breakout']
                regime.avoid_strategies = ['mean_reversion']
            regime.confidence = 0.7 + (adx - 30) / 100
        
        elif range_20 < 0.05 and volatility < avg_volatility * 0.8:
            regime.regime_type = "quiet"
            regime.recommended_strategies = ['breakout']  # 等待突破
            regime.avoid_strategies = ['trend_following', 'swing_trading']
            regime.confidence = 0.6
        
        elif volatility > avg_volatility * 1.5:
            regime.regime_type = "volatile"
            regime.recommended_strategies = ['swing_trading']  # 波動中找波段
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
        
        # 計算持續時間
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
        """簡化的 ADX 計算"""
        n = len(close)
        if n < period * 2:
            return 20.0  # 預設值
        
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
        
        # 平滑
        atr = np.mean(tr[-period:]) if len(tr) >= period else 0
        plus_di = 100 * np.mean(plus_dm[-period:]) / atr if atr > 0 else 0
        minus_di = 100 * np.mean(minus_dm[-period:]) / atr if atr > 0 else 0
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0
        
        return float(dx)
    
    def _estimate_regime_duration(
        self,
        close: np.ndarray,
        high: np.ndarray,
        low: np.ndarray,
        regime_type: str
    ) -> int:
        """估計狀態持續時間"""
        duration = 0
        n = len(close)
        
        for i in range(1, min(100, n)):
            idx = -1 - i
            if abs(idx) >= n:
                break
            
            # 簡化判斷：檢查與當前狀態一致的時間
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
    # 策略權重計算
    # ========================
    
    def update_weights_for_market(
        self,
        market_condition: Union[MarketCondition, str],
        regime: MarketRegime
    ):
        """根據市場狀態更新策略權重"""
        for name, weight in self.strategy_weights.items():
            # 1. 基礎權重
            condition_weight = 0.0
            
            # 2. 市場條件適應性
            if market_condition in weight.best_conditions:
                condition_weight += 0.3
            elif market_condition in weight.worst_conditions:
                condition_weight -= 0.3
            
            # 3. 市場狀態建議
            if name in regime.recommended_strategies:
                condition_weight += 0.2
            if name in regime.avoid_strategies:
                condition_weight -= 0.2
            
            weight.market_condition_weight = condition_weight
            
            # 4. 計算最終權重
            total = (
                weight.base_weight +
                weight.performance_weight +
                weight.market_condition_weight +
                weight.recent_performance_weight
            )
            
            # 限制範圍
            weight.final_weight = max(self.min_weight, min(self.max_weight, total))
        
        # 正規化權重
        self._normalize_weights()
    
    def update_weights_from_performance(self, strategy_name: str, trade_result: Dict):
        """根據交易結果更新策略權重"""
        if not self.enable_learning:
            return
        
        weight = self.strategy_weights.get(strategy_name)
        if not weight:
            return
        
        # 更新績效統計
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
        
        # 更新近期績效
        weight.recent_trades = min(weight.recent_trades + 1, 20)  # 最多追蹤 20 筆
        if is_win:
            weight.recent_wins += 1
        
        # 計算近期勝率
        recent_win_rate = weight.recent_wins / weight.recent_trades if weight.recent_trades > 0 else 0.5
        
        # 更新績效權重
        performance_score = (weight.win_rate - 0.5) * 2  # -1 到 1
        recent_score = (recent_win_rate - 0.5) * 2
        
        weight.performance_weight = performance_score * 0.15
        weight.recent_performance_weight = recent_score * 0.1
        
        # 衰減舊績效的影響
        if weight.recent_trades >= 20:
            # 模擬滑動窗口
            weight.recent_wins = int(weight.recent_wins * self.performance_decay)
            weight.recent_trades = int(weight.recent_trades * self.performance_decay)
        
        logger.info(
            f"更新 {strategy_name} 權重: "
            f"勝率={weight.win_rate:.1%}, "
            f"近期勝率={recent_win_rate:.1%}, "
            f"最終權重={weight.final_weight:.2f}"
        )
    
    def _normalize_weights(self):
        """正規化權重使總和為 1"""
        total = sum(w.final_weight for w in self.strategy_weights.values())
        
        if total > 0:
            for weight in self.strategy_weights.values():
                weight.final_weight /= total
    
    # ========================
    # 策略融合
    # ========================
    
    def generate_fusion_signal(
        self,
        ohlcv_data: np.ndarray,
        additional_data: Optional[Dict] = None
    ) -> FusionSignal:
        """生成融合訊號"""
        signal = FusionSignal(
            signal_id=f"FS_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(),
        )
        
        # 1. 識別市場狀態
        regime = self.identify_market_regime(ohlcv_data)
        
        # 2. 收集各策略訊號
        market_analyses = {}
        trade_setups = {}
        
        for name, strategy in self.strategies.items():
            try:
                # 分析市場
                analysis = strategy.analyze_market(ohlcv_data, additional_data)
                market_analyses[name] = analysis
                
                # 評估進場條件
                setup = strategy.evaluate_entry_conditions(analysis, ohlcv_data)
                trade_setups[name] = setup
                
                if setup:
                    signal.contributing_strategies.append(name)
                
            except Exception as e:
                logger.error(f"策略 {name} 分析失敗: {e}")
                trade_setups[name] = None
        
        signal.strategy_signals = trade_setups
        
        # 3. 更新市場條件權重
        # 取第一個有效分析的市場條件
        market_condition = "NORMAL"  # 預設使用字串
        for analysis in market_analyses.values():
            mc = analysis.get('market_condition')
            if mc:
                market_condition = mc
                break
        
        self.update_weights_for_market(market_condition, regime)
        
        # 4. 融合訊號
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
        
        # 5. 檢測和解決衝突
        self._detect_and_resolve_conflicts(signal)
        
        # 6. 最終決策
        self._make_final_decision(signal)
        
        # 7. 記錄
        self.fusion_history.append(signal)
        
        return signal
    
    def _fuse_by_weighted_vote(self, signal: FusionSignal):
        """加權投票融合"""
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
        """選擇最佳績效策略"""
        best_strategy = None
        best_score = -1
        
        for name, setup in signal.strategy_signals.items():
            if setup is None:
                continue
            
            weight = self.strategy_weights[name]
            
            # 計算綜合分數
            score = (
                weight.win_rate * 0.4 +
                (weight.profit_factor / 3) * 0.3 +  # 假設 profit_factor 最高 3
                (weight.recent_wins / max(weight.recent_trades, 1)) * 0.3
            )
            
            if score > best_score:
                best_score = score
                best_strategy = name
        
        if best_strategy:
            setup = signal.strategy_signals[best_strategy]
            if setup:  # 確保 setup 不為 None
                signal.consensus_direction = setup.direction
                signal.consensus_strength = best_score
                signal.confidence_score = best_score
                signal.selected_setup = setup
        
        signal.fusion_method_used = FusionMethod.BEST_PERFORMER
    
    def _fuse_by_market_adaptive(self, signal: FusionSignal, regime: MarketRegime):
        """市場適應性融合"""
        # 優先考慮推薦策略
        prioritized_strategies = regime.recommended_strategies
        
        best_setup = None
        best_score = 0
        
        for name, setup in signal.strategy_signals.items():
            if setup is None:
                continue
            
            # 基礎分數
            score = self.strategy_weights[name].final_weight
            
            # 推薦策略加分
            if name in prioritized_strategies:
                score *= 1.5
            
            # 避免策略減分
            if name in regime.avoid_strategies:
                score *= 0.5
            
            # 訊號強度加權
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
        """信心度基礎融合"""
        best_setup = None
        best_confidence = 0
        
        for name, setup in signal.strategy_signals.items():
            if setup is None:
                continue
            
            # 計算信心度
            confidence = setup.entry_confirmations / max(setup.required_confirmations, 1)
            
            # 結合策略權重
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
        """集成方法：結合多種融合策略"""
        # 1. 加權投票
        vote_signal = FusionSignal()
        vote_signal.strategy_signals = signal.strategy_signals
        self._fuse_by_weighted_vote(vote_signal)
        
        # 2. 市場適應
        adaptive_signal = FusionSignal()
        adaptive_signal.strategy_signals = signal.strategy_signals
        self._fuse_by_market_adaptive(adaptive_signal, regime)
        
        # 3. 信心度
        confidence_signal = FusionSignal()
        confidence_signal.strategy_signals = signal.strategy_signals
        self._fuse_by_confidence(confidence_signal)
        
        # 集成結果
        directions = [
            vote_signal.consensus_direction,
            adaptive_signal.consensus_direction,
            confidence_signal.consensus_direction,
        ]
        
        # 多數決定方向
        long_count = directions.count('long')
        short_count = directions.count('short')
        
        if long_count > short_count:
            signal.consensus_direction = 'long'
        elif short_count > long_count:
            signal.consensus_direction = 'short'
        
        # 平均信心度
        scores = [
            vote_signal.confidence_score,
            adaptive_signal.confidence_score,
            confidence_signal.confidence_score,
        ]
        mean_score = np.mean([s for s in scores if s > 0]) if any(scores) else 0
        signal.confidence_score = float(mean_score)
        signal.consensus_strength = signal.confidence_score
        
        # 選擇最佳設置
        if adaptive_signal.selected_setup:
            signal.selected_setup = adaptive_signal.selected_setup
        
        signal.fusion_method_used = FusionMethod.ENSEMBLE
    
    def _detect_and_resolve_conflicts(self, signal: FusionSignal):
        """檢測和解決策略衝突"""
        long_strategies = []
        short_strategies = []
        
        for name, setup in signal.strategy_signals.items():
            if setup is None:
                continue
            if setup.direction == 'long':
                long_strategies.append(name)
            else:
                short_strategies.append(name)
        
        # 檢測衝突
        if long_strategies and short_strategies:
            signal.has_conflict = True
            signal.conflict_description = (
                f"多空衝突: 做多策略={long_strategies}, 做空策略={short_strategies}"
            )
            
            # 衝突解決
            long_weight = sum(
                self.strategy_weights[s].final_weight for s in long_strategies
            )
            short_weight = sum(
                self.strategy_weights[s].final_weight for s in short_strategies
            )
            
            if abs(long_weight - short_weight) < self.conflict_threshold:
                # 衝突太激烈，不交易
                signal.conflict_resolution = "衝突嚴重，建議觀望"
                signal.should_trade = False
            else:
                # 傾向權重較高的方向
                if long_weight > short_weight:
                    signal.conflict_resolution = f"權重傾向做多 ({long_weight:.2f} vs {short_weight:.2f})"
                else:
                    signal.conflict_resolution = f"權重傾向做空 ({short_weight:.2f} vs {long_weight:.2f})"
    
    def _make_final_decision(self, signal: FusionSignal):
        """做出最終交易決策"""
        # 檢查基本條件
        if not signal.consensus_direction:
            signal.should_trade = False
            return
        
        if signal.confidence_score < self.min_confidence_score:
            signal.should_trade = False
            return
        
        if signal.has_conflict and "觀望" in signal.conflict_resolution:
            signal.should_trade = False
            return
        
        # 選擇最佳設置
        if not signal.selected_setup:
            # 從同方向的策略中選擇
            best_setup = None
            best_score = 0
            
            for name, setup in signal.strategy_signals.items():
                if setup and setup.direction == signal.consensus_direction:
                    score = self.strategy_weights[name].final_weight
                    if score > best_score:
                        best_score = score
                        best_setup = setup
            
            signal.selected_setup = best_setup
        
        signal.should_trade = signal.selected_setup is not None
    
    # ========================
    # 交易執行
    # ========================
    
    def execute_fusion_signal(
        self,
        signal: FusionSignal,
        connector: Any,
    ) -> Optional[TradeExecution]:
        """執行融合訊號"""
        if not signal.should_trade or not signal.selected_setup:
            return None
        
        # 找到對應的策略
        active_strategy_name = None
        for name, setup in signal.strategy_signals.items():
            if setup == signal.selected_setup:
                active_strategy_name = name
                break
        
        if not active_strategy_name:
            logger.error("無法找到對應策略")
            return None
        
        strategy = self.strategies[active_strategy_name]
        
        # 執行進場
        execution = strategy.execute_entry(signal.selected_setup, connector)
        
        if execution:
            self._active_trade = execution
            self._active_strategy = active_strategy_name
            
            logger.info(
                f"融合訊號執行: {signal.signal_id}, "
                f"策略: {active_strategy_name}, "
                f"方向: {signal.consensus_direction}, "
                f"信心: {signal.confidence_score:.2f}"
            )
        
        return execution
    
    def manage_active_trade(
        self,
        current_price: float,
        ohlcv_data: np.ndarray,
    ) -> Optional[PositionManagement]:
        """管理活躍交易"""
        if not self._active_trade or not self._active_strategy:
            return None
        
        strategy = self.strategies[self._active_strategy]
        
        # 更新價格
        self._active_trade.average_exit_price = current_price
        
        # 使用策略管理部位
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
        """檢查出場條件"""
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
        """執行出場"""
        if not self._active_trade or not self._active_strategy:
            return False
        
        strategy = self.strategies[self._active_strategy]
        
        success = strategy.execute_exit(
            self._active_trade,
            reason,
            connector
        )
        
        if success:
            # 記錄結果並更新權重
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
            
            # 重置狀態
            self._active_trade = None
            self._active_strategy = None
        
        return success
    
    # ========================
    # 報告和分析
    # ========================
    
    def get_strategy_report(self) -> Dict[str, Any]:
        """獲取策略報告"""
        report = {
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
        
        # 最近績效
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
        """保存狀態"""
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
            'trade_outcomes': self.trade_outcomes[-100:],  # 只保留最近 100 筆
            'fusion_method': self.fusion_method.value,
            'saved_at': datetime.now().isoformat(),
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"狀態已保存到 {filepath}")
    
    def load_state(self, filepath: str):
        """載入狀態"""
        try:
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            # 恢復權重
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
            
            # 重新計算最終權重
            self._normalize_weights()
            
            logger.info(f"狀態已從 {filepath} 載入")
            
        except Exception as e:
            logger.error(f"載入狀態失敗: {e}")
