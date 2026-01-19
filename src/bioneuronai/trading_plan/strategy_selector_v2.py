"""
策略選擇器 v2 - 整合完整交易策略模組
====================================

整合新的完整策略系統，移除不適用於零售交易者的策略（如剝頭皮、高頻交易）
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np

# 導入新的策略系統
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
    """市場狀態"""
    TRENDING_BULL = "上升趨勢"
    TRENDING_BEAR = "下降趨勢"
    SIDEWAYS_LOW_VOL = "橫盤低波動"
    SIDEWAYS_HIGH_VOL = "橫盤高波動"
    VOLATILE_UNCERTAIN = "高波動不確定"
    BREAKOUT_POTENTIAL = "潛在突破"


class StrategyType(Enum):
    """策略類型 - 僅保留適合零售交易者的策略"""
    TREND_FOLLOWING = "趨勢跟隨"
    SWING_TRADING = "波段交易"
    MEAN_REVERSION = "均值回歸"
    BREAKOUT = "突破交易"
    AI_FUSION = "AI融合策略"


@dataclass
class StrategyRecommendation:
    """策略推薦結果"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # 主要推薦
    primary_strategy: StrategyType = StrategyType.TREND_FOLLOWING
    primary_confidence: float = 0.5
    
    # 市場分析
    market_regime: MarketRegime = MarketRegime.SIDEWAYS_LOW_VOL
    market_condition: MarketCondition = MarketCondition.NORMAL
    
    # 策略權重
    strategy_weights: Dict[str, float] = field(default_factory=dict)
    
    # 推薦理由
    reasoning: List[str] = field(default_factory=list)
    
    # 風險評估
    risk_level: str = "medium"  # low, medium, high
    suggested_position_size: float = 0.02  # 2% 風險
    
    # 不建議使用的策略
    avoid_strategies: List[StrategyType] = field(default_factory=list)


class StrategySelector:
    """
    策略選擇器 - 適合零售交易者的版本
    
    特點：
    1. 不包含剝頭皮/高頻交易策略
    2. 適合 15 分鐘以上時間框架
    3. 整合 AI 策略融合系統
    4. 動態權重調整
    """
    
    def __init__(self, timeframe: str = "1h"):
        self.timeframe = timeframe
        
        # 初始化完整策略
        self.strategies: Dict[str, BaseStrategy] = {
            'trend_following': TrendFollowingStrategy(timeframe),
            'swing_trading': SwingTradingStrategy(timeframe),
            'mean_reversion': MeanReversionStrategy(timeframe),
            'breakout': BreakoutTradingStrategy(timeframe),
        }
        
        # AI 融合系統
        self.ai_fusion = AIStrategyFusion(
            timeframe=timeframe,
            fusion_method=FusionMethod.MARKET_ADAPTIVE,
            enable_learning=True,
        )
        
        # 策略與市場狀態的適配性
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
                'best': [],  # AI 融合適合所有市場
                'good': [MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR,
                        MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL,
                        MarketRegime.VOLATILE_UNCERTAIN, MarketRegime.BREAKOUT_POTENTIAL],
                'avoid': [],
            },
        }
        
        # 歷史表現追蹤
        self.performance_history: Dict[str, List[Dict]] = {
            name: [] for name in self.strategies
        }
    
    def identify_market_regime(self, ohlcv_data: np.ndarray) -> MarketRegime:
        """識別市場狀態"""
        close = ohlcv_data[:, 4]
        high = ohlcv_data[:, 2]
        low = ohlcv_data[:, 3]
        volume = ohlcv_data[:, 5]
        
        n = len(close)
        if n < 50:
            return MarketRegime.SIDEWAYS_LOW_VOL
        
        # 計算指標
        sma_20 = np.mean(close[-20:])
        sma_50 = np.mean(close[-50:])
        
        # 趨勢強度
        trend_strength = (close[-1] - sma_50) / sma_50 * 100
        
        # 波動率
        returns = np.diff(close[-21:]) / close[-21:-1]
        volatility = np.std(returns)
        avg_vol = np.std(np.diff(close[-50:-20]) / close[-50:-20])
        vol_ratio = volatility / avg_vol if avg_vol > 0 else 1
        
        # 區間寬度
        range_20 = (max(high[-20:]) - min(low[-20:])) / np.mean(close[-20:])
        
        # ADX (簡化)
        adx = self._calculate_adx_simple(high, low, close)
        
        # 判斷市場狀態
        if adx > 25:
            if close[-1] > sma_20 > sma_50 and trend_strength > 3:
                return MarketRegime.TRENDING_BULL
            elif close[-1] < sma_20 < sma_50 and trend_strength < -3:
                return MarketRegime.TRENDING_BEAR
        
        if vol_ratio > 1.5:
            return MarketRegime.VOLATILE_UNCERTAIN
        
        if range_20 < 0.04 and vol_ratio < 0.8:
            # 低波動盤整，可能即將突破
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
        """簡化的 ADX 計算"""
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
        return dx
    
    def recommend_strategy(
        self,
        ohlcv_data: np.ndarray,
        account_balance: float = 10000.0,
        use_ai_fusion: bool = True,
    ) -> StrategyRecommendation:
        """
        推薦最適合的交易策略
        
        Args:
            ohlcv_data: OHLCV 數據
            account_balance: 帳戶餘額
            use_ai_fusion: 是否使用 AI 融合系統
            
        Returns:
            StrategyRecommendation
        """
        recommendation = StrategyRecommendation()
        
        # 1. 識別市場狀態
        market_regime = self.identify_market_regime(ohlcv_data)
        recommendation.market_regime = market_regime
        recommendation.reasoning.append(f"市場狀態識別: {market_regime.value}")
        
        # 2. 計算各策略權重
        weights = {}
        avoid = []
        
        for strategy_type in StrategyType:
            if strategy_type == StrategyType.AI_FUSION:
                continue
                
            fit = self._strategy_market_fit[strategy_type]
            
            # 基礎權重
            weight = 0.25
            
            if market_regime in fit['best']:
                weight += 0.3
            elif market_regime in fit['good']:
                weight += 0.1
            elif market_regime in fit['avoid']:
                weight -= 0.3
                avoid.append(strategy_type)
            
            weights[strategy_type.value] = max(0.0, weight)
        
        # 正規化權重
        total = sum(weights.values())
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}
        
        recommendation.strategy_weights = weights
        recommendation.avoid_strategies = avoid
        
        # 3. 選擇主要策略
        if weights:
            best_strategy = max(weights.items(), key=lambda x: x[1])
            recommendation.primary_strategy = StrategyType(best_strategy[0])
            recommendation.primary_confidence = best_strategy[1]
        
        # 4. 如果啟用 AI 融合
        if use_ai_fusion:
            fusion_signal = self.ai_fusion.generate_fusion_signal(ohlcv_data)
            
            if fusion_signal.should_trade:
                # AI 融合有強信號，提高其權重
                recommendation.reasoning.append(
                    f"AI 融合系統信號: {fusion_signal.consensus_direction}, "
                    f"信心度: {fusion_signal.confidence_score:.2f}"
                )
                
                if fusion_signal.confidence_score > 0.7:
                    recommendation.primary_strategy = StrategyType.AI_FUSION
                    recommendation.primary_confidence = fusion_signal.confidence_score
            
            # 更新市場條件
            fusion_regime = self.ai_fusion.current_regime
            if fusion_regime:
                recommendation.reasoning.append(
                    f"AI 判斷市場: {fusion_regime.regime_type}, "
                    f"建議: {fusion_regime.recommended_strategies}"
                )
        
        # 5. 風險評估
        close = ohlcv_data[:, 4]
        returns = np.diff(close[-20:]) / close[-20:-1]
        volatility = np.std(returns)
        
        if volatility > 0.03:
            recommendation.risk_level = "high"
            recommendation.suggested_position_size = 0.01  # 1%
            recommendation.reasoning.append("高波動環境，建議降低部位")
        elif volatility < 0.01:
            recommendation.risk_level = "low"
            recommendation.suggested_position_size = 0.03  # 3%
            recommendation.reasoning.append("低波動環境，可適度增加部位")
        else:
            recommendation.risk_level = "medium"
            recommendation.suggested_position_size = 0.02  # 2%
        
        # 6. 生成推薦理由
        self._add_strategy_reasons(recommendation, market_regime)
        
        return recommendation
    
    def _add_strategy_reasons(
        self,
        recommendation: StrategyRecommendation,
        market_regime: MarketRegime
    ):
        """添加策略推薦理由"""
        strategy = recommendation.primary_strategy
        
        if strategy == StrategyType.TREND_FOLLOWING:
            if market_regime == MarketRegime.TRENDING_BULL:
                recommendation.reasoning.append(
                    "上升趨勢明確，適合順勢做多"
                )
            elif market_regime == MarketRegime.TRENDING_BEAR:
                recommendation.reasoning.append(
                    "下降趨勢明確，適合順勢做空或觀望"
                )
        
        elif strategy == StrategyType.SWING_TRADING:
            recommendation.reasoning.append(
                "市場有明顯波段，適合在支撐/阻力位操作"
            )
        
        elif strategy == StrategyType.MEAN_REVERSION:
            recommendation.reasoning.append(
                "市場處於區間震盪，價格偏離後傾向回歸均值"
            )
        
        elif strategy == StrategyType.BREAKOUT:
            recommendation.reasoning.append(
                "市場波動收縮，可能即將突破，等待確認信號"
            )
        
        elif strategy == StrategyType.AI_FUSION:
            recommendation.reasoning.append(
                "AI 融合系統結合多策略判斷，動態適應市場"
            )
    
    def get_strategy_signals(
        self,
        ohlcv_data: np.ndarray,
    ) -> Dict[str, Optional[TradeSetup]]:
        """
        獲取所有策略的信號
        
        Returns:
            各策略的交易設置（如有）
        """
        signals = {}
        
        for name, strategy in self.strategies.items():
            try:
                # 分析市場
                analysis = strategy.analyze_market(ohlcv_data)
                
                # 評估進場條件
                setup = strategy.evaluate_entry_conditions(analysis, ohlcv_data)
                signals[name] = setup
                
            except Exception as e:
                logger.error(f"策略 {name} 信號生成失敗: {e}")
                signals[name] = None
        
        return signals
    
    def get_ai_fusion_signal(
        self,
        ohlcv_data: np.ndarray,
    ) -> Dict[str, Any]:
        """
        獲取 AI 融合信號
        
        Returns:
            融合信號資訊
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
        記錄交易結果以更新策略表現
        
        Args:
            strategy_name: 策略名稱
            trade_result: 交易結果（包含 r_multiple, pnl 等）
        """
        if strategy_name in self.performance_history:
            self.performance_history[strategy_name].append({
                'timestamp': datetime.now(),
                **trade_result
            })
        
        # 更新 AI 融合系統的權重
        self.ai_fusion.update_weights_from_performance(
            strategy_name,
            trade_result
        )
    
    def get_strategy_summary(self) -> Dict[str, Any]:
        """獲取策略摘要報告"""
        summary = {
            'available_strategies': list(self.strategies.keys()),
            'timeframe': self.timeframe,
            'ai_fusion_enabled': True,
            'strategy_performance': {},
        }
        
        # 各策略績效
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
        
        # AI 融合報告
        summary['ai_fusion_report'] = self.ai_fusion.get_strategy_report()
        
        return summary
    
    def save_state(self, filepath: str):
        """保存選擇器狀態"""
        self.ai_fusion.save_state(filepath)
    
    def load_state(self, filepath: str):
        """載入選擇器狀態"""
        self.ai_fusion.load_state(filepath)


# 方便使用的函數
def get_recommended_strategy(
    ohlcv_data: np.ndarray,
    timeframe: str = "1h",
    use_ai_fusion: bool = True,
) -> StrategyRecommendation:
    """
    快速獲取策略推薦
    
    Args:
        ohlcv_data: OHLCV 數據 (timestamp, open, high, low, close, volume)
        timeframe: 時間框架
        use_ai_fusion: 是否使用 AI 融合
        
    Returns:
        StrategyRecommendation
    """
    selector = StrategySelector(timeframe)
    return selector.recommend_strategy(ohlcv_data, use_ai_fusion=use_ai_fusion)
