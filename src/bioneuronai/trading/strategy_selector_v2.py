"""
 v2 - 
====================================


"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

# 
from ..strategies import (
    BaseStrategy,
    TradeSetup,
    TradeExecution,
    TrendFollowingStrategy,
    SwingTradingStrategy,
    MeanReversionStrategy,
    BreakoutTradingStrategy,
    AIStrategyFusion,
    FusionMethod,
    MarketRegime as FusionMarketRegime,
)
from ..strategies.base_strategy import MarketCondition, SignalStrength

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """"""
    TRENDING_BULL = ""
    TRENDING_BEAR = ""
    SIDEWAYS_LOW_VOL = ""
    SIDEWAYS_HIGH_VOL = ""
    VOLATILE_UNCERTAIN = ""
    BREAKOUT_POTENTIAL = ""


class StrategyType(Enum):
    """ - """
    TREND_FOLLOWING = ""
    SWING_TRADING = ""
    MEAN_REVERSION = ""
    BREAKOUT = ""
    AI_FUSION = "AI"


@dataclass
class StrategyRecommendation:
    """"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 
    primary_strategy: StrategyType = StrategyType.TREND_FOLLOWING
    primary_confidence: float = 0.5
    
    # 
    market_regime: MarketRegime = MarketRegime.SIDEWAYS_LOW_VOL
    market_condition: str = "NORMAL"  #  MarketCondition.NORMAL
    
    # 
    strategy_weights: Dict[str, float] = field(default_factory=dict)
    
    # 
    reasoning: List[str] = field(default_factory=list)
    
    # 
    risk_level: str = "medium"  # low, medium, high
    suggested_position_size: float = 0.02  # 2% 
    
    # 
    avoid_strategies: List[StrategyType] = field(default_factory=list)


class StrategySelector:
    """
     - 
    
    
    1. /
    2.  15 
    3.  AI 
    4. 
    """
    
    def __init__(self, timeframe: str = "1h"):
        self.timeframe = timeframe
        
        # 
        self.strategies: Dict[str, BaseStrategy] = {
            'trend_following': TrendFollowingStrategy(timeframe),
            'swing_trading': SwingTradingStrategy(timeframe),
            'mean_reversion': MeanReversionStrategy(timeframe),
            'breakout': BreakoutTradingStrategy(timeframe),
        }
        
        # AI 
        self.ai_fusion = AIStrategyFusion(
            timeframe=timeframe,
            fusion_method=FusionMethod.MARKET_ADAPTIVE,
            enable_learning=True,
        )
        
        # 
        self._strategy_market_fit = {
            StrategyType.TREND_FOLLOWING: {
                'best': [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
                'good': [MarketRegime.BREAKOUT_POTENTIAL],
                'avoid': [MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.VOLATILE_UNCERTAIN],
            },
            StrategyType.SWING_TRADING: {
                'best': [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
                'good': [MarketRegime.SIDEWAYS_HIGH_VOL],
                'avoid': [],
            },
            StrategyType.MEAN_REVERSION: {
                'best': [MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL],
                'good': [],
                'avoid': [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
            },
            StrategyType.BREAKOUT: {
                'best': [MarketRegime.BREAKOUT_POTENTIAL, MarketRegime.SIDEWAYS_LOW_VOL],
                'good': [],
                'avoid': [MarketRegime.VOLATILE_UNCERTAIN],
            },
            StrategyType.AI_FUSION: {
                'best': [],  # AI 
                'good': [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR,
                        MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL,
                        MarketRegime.VOLATILE_UNCERTAIN, MarketRegime.BREAKOUT_POTENTIAL],
                'avoid': [],
            },
        }
        
        # 
        self.performance_history: Dict[str, List[Dict]] = {
            name: [] for name in self.strategies
        }
    
    def identify_market_regime(self, ohlcv_data: np.ndarray) -> MarketRegime:
        """"""
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        volume = ohlcv_data[:, 5]
        
        n = len(close)
        if n < 50:
            return MarketRegime.SIDEWAYS_LOW_VOL
        
        # 
        sma_20 = np.mean(close[-20:])
        sma_50 = np.mean(close[-50:])
        
        # 
        trend_strength = (close[-1] - sma_50) / sma_50 * 100
        
        # 
        returns = np.diff(close[-21:]) / close[-21:-1]
        volatility = np.std(returns)
        avg_vol = np.std(np.diff(close[-50:-20]) / close[-50:-20])
        vol_ratio = volatility / avg_vol if avg_vol > 0 else 1
        
        # 
        range_20 = (max(high[-20:]) - min(low[-20:])) / np.mean(close[-20:])
        
        # ADX ()
        adx = self._calculate_adx_simple(high, low, close)
        
        # 
        if adx > 25:
            if close[-1] > sma_20 > sma_50 and trend_strength > 3:
                return MarketRegime.TRENDING_BULL
            elif close[-1] < sma_20 < sma_50 and trend_strength < -3:
                return MarketRegime.TRENDING_BEAR
        
        if vol_ratio > 1.5:
            return MarketRegime.VOLATILE_UNCERTAIN
        
        if range_20 < 0.04 and vol_ratio < 0.8:
            # 
            return MarketRegime.BREAKOUT_POTENTIAL
        
        if range_20 < 0.06:
            if vol_ratio < 1:
                return MarketRegime.SIDEWAYS_LOW_VOL
            else:
                return MarketRegime.SIDEWAYS_HIGH_VOL
        
        return MarketRegime.SIDEWAYS_HIGH_VOL
    
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
            return 20.0
        
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
        
        atr = np.mean(tr[-period:])
        if atr == 0:
            return 20.0
            
        plus_di = 100 * np.mean(plus_dm[-period:]) / atr
        minus_di = 100 * np.mean(minus_dm[-period:]) / atr
        
        if plus_di + minus_di == 0:
            return 20.0
            
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        return float(dx)
    
    def recommend_strategy(
        self,
        ohlcv_data: np.ndarray,
        account_balance: float = 10000.0,
        use_ai_fusion: bool = True,
    ) -> StrategyRecommendation:
        """
        
        
        Args:
            ohlcv_data: OHLCV 
            account_balance: 
            use_ai_fusion:  AI 
            
        Returns:
            StrategyRecommendation
        """
        recommendation = StrategyRecommendation()
        
        # 1. 
        market_regime = self.identify_market_regime(ohlcv_data)
        recommendation.market_regime = market_regime
        recommendation.reasoning.append(f": {market_regime.value}")
        
        # 2. 
        weights = {}
        avoid = []
        
        for strategy_type in StrategyType:
            if strategy_type == StrategyType.AI_FUSION:
                continue
                
            fit = self._strategy_market_fit[strategy_type]
            
            # 
            weight = 0.25
            
            if market_regime in fit['best']:
                weight += 0.3
            elif market_regime in fit['good']:
                weight += 0.1
            elif market_regime in fit['avoid']:
                weight -= 0.3
                avoid.append(strategy_type)
            
            weights[strategy_type.value] = max(0.0, weight)
        
        # 
        total = sum(weights.values())
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}
        
        recommendation.strategy_weights = weights
        recommendation.avoid_strategies = avoid
        
        # 3. 
        if weights:
            best_strategy = max(weights.items(), key=lambda x: x[1])
            recommendation.primary_strategy = StrategyType(best_strategy[0])
            recommendation.primary_confidence = best_strategy[1]
        
        # 4.  AI 
        if use_ai_fusion:
            fusion_signal = self.ai_fusion.generate_fusion_signal(ohlcv_data)
            
            if fusion_signal.should_trade:
                # AI 
                recommendation.reasoning.append(
                    f"AI : {fusion_signal.consensus_direction}, "
                    f": {fusion_signal.confidence_score:.2f}"
                )
                
                if fusion_signal.confidence_score > 0.7:
                    recommendation.primary_strategy = StrategyType.AI_FUSION
                    recommendation.primary_confidence = fusion_signal.confidence_score
            
            # 
            fusion_regime = self.ai_fusion.current_regime
            if fusion_regime:
                recommendation.reasoning.append(
                    f"AI : {fusion_regime.regime_type}, "
                    f": {fusion_regime.recommended_strategies}"
                )
        
        # 5. 
        close = ohlcv_data[:, 4]
        returns = np.diff(close[-20:]) / close[-20:-1]
        volatility = np.std(returns)
        
        if volatility > 0.03:
            recommendation.risk_level = "high"
            recommendation.suggested_position_size = 0.01  # 1%
            recommendation.reasoning.append("")
        elif volatility < 0.01:
            recommendation.risk_level = "low"
            recommendation.suggested_position_size = 0.03  # 3%
            recommendation.reasoning.append("")
        else:
            recommendation.risk_level = "medium"
            recommendation.suggested_position_size = 0.02  # 2%
        
        # 6. 
        self._add_strategy_reasons(recommendation, market_regime)
        
        return recommendation
    
    def _add_strategy_reasons(
        self,
        recommendation: StrategyRecommendation,
        market_regime: MarketRegime
    ):
        """"""
        strategy = recommendation.primary_strategy
        
        if strategy == StrategyType.TREND_FOLLOWING:
            if market_regime == MarketRegime.TRENDING_BULL:
                recommendation.reasoning.append(
                    ""
                )
            elif market_regime == MarketRegime.TRENDING_BEAR:
                recommendation.reasoning.append(
                    ""
                )
        
        elif strategy == StrategyType.SWING_TRADING:
            recommendation.reasoning.append(
                "/"
            )
        
        elif strategy == StrategyType.MEAN_REVERSION:
            recommendation.reasoning.append(
                ""
            )
        
        elif strategy == StrategyType.BREAKOUT:
            recommendation.reasoning.append(
                ""
            )
        
        elif strategy == StrategyType.AI_FUSION:
            recommendation.reasoning.append(
                "AI "
            )
    
    def get_strategy_signals(
        self,
        ohlcv_data: np.ndarray,
    ) -> Dict[str, Optional[TradeSetup]]:
        """
        
        
        Returns:
            
        """
        signals = {}
        
        for name, strategy in self.strategies.items():
            try:
                # 
                analysis = strategy.analyze_market(ohlcv_data)
                
                # 
                setup = strategy.evaluate_entry_conditions(analysis, ohlcv_data)
                signals[name] = setup
                
            except Exception as e:
                logger.error(f" {name} : {e}")
                signals[name] = None
        
        return signals
    
    def get_ai_fusion_signal(
        self,
        ohlcv_data: np.ndarray,
    ) -> Dict[str, Any]:
        """
         AI 
        
        Returns:
            
        """
        signal = self.ai_fusion.generate_fusion_signal(ohlcv_data)
        
        return {
            'should_trade': signal.should_trade,
            'direction': signal.consensus_direction,
            'confidence': signal.confidence_score,
            'consensus_strength': signal.consensus_strength,
            'contributing_strategies': signal.contributing_strategies,
            'has_conflict': signal.has_conflict,
            'conflict_description': signal.conflict_description,
            'selected_setup': signal.selected_setup,
            'fusion_method': signal.fusion_method_used.value,
        }
    
    def record_trade_result(
        self,
        strategy_name: str,
        trade_result: Dict[str, Any]
    ):
        """
        
        
        Args:
            strategy_name: 
            trade_result:  r_multiple, pnl 
        """
        if strategy_name in self.performance_history:
            self.performance_history[strategy_name].append({
                'timestamp': datetime.now(),
                **trade_result
            })
        
        #  AI 
        self.ai_fusion.update_weights_from_performance(
            strategy_name,
            trade_result
        )
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """"""
        summary = {
            'available_strategies': list(self.strategies.keys()),
            'timeframe': self.timeframe,
            'ai_fusion_enabled': True,
            'strategy_performance': {},
        }
        
        # 
        for name, history in self.performance_history.items():
            if history:
                trades = len(history)
                wins = sum(1 for t in history if t.get('r_multiple', 0) > 0)
                total_r = sum(t.get('r_multiple', 0) for t in history)
                
                summary['strategy_performance'][name] = {
                    'trades': trades,
                    'win_rate': wins / trades if trades > 0 else 0,
                    'avg_r': total_r / trades if trades > 0 else 0,
                }
        
        # AI 
        summary['ai_fusion_report'] = self.ai_fusion.get_strategy_report()
        
        return summary
    
    def save_state(self, filepath: str):
        """"""
        self.ai_fusion.save_state(filepath)
    
    def load_state(self, filepath: str):
        """"""
        self.ai_fusion.load_state(filepath)


# 
def get_recommended_strategy(
    ohlcv_data: np.ndarray,
    timeframe: str = "1h",
    use_ai_fusion: bool = True,
) -> StrategyRecommendation:
    """
    
    
    Args:
        ohlcv_data: OHLCV  (timestamp, open, high, low, close, volume)
        timeframe: 
        use_ai_fusion:  AI 
        
    Returns:
        StrategyRecommendation
    """
    selector = StrategySelector(timeframe)
    return selector.recommend_strategy(ohlcv_data, use_ai_fusion=use_ai_fusion)
