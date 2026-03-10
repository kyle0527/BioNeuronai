"""
策略選擇器核心 - Strategy Selector Core

整合 v1 和 v2 的功能:
- v1 的詳細策略配置和 async API
- v2 的實際策略實例化和 AI Fusion 原生支援

Created: 2026-01-25
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

import numpy as np

from .types import (
    StrategyType,
    MarketRegime,
    RiskLevel,
    StrategyConfigTemplate,
    StrategySelectionResult,
    StrategyRecommendation,
    InternalPerformanceMetrics,
    STRATEGY_MARKET_FIT,
)
from .configs import get_default_strategy_configs, get_strategy_by_type
from .evaluator import MarketEvaluator

# 導入實際策略 (來自 v2)
try:
    from ..base_strategy import BaseStrategy, MarketCondition, SignalStrength
    from ..trend_following import TrendFollowingStrategy
    from ..swing_trading import SwingTradingStrategy
    from ..mean_reversion import MeanReversionStrategy
    from ..breakout_trading import BreakoutTradingStrategy
    from ..strategy_fusion import AIStrategyFusion, FusionMethod
    STRATEGIES_AVAILABLE = True
except ImportError:
    STRATEGIES_AVAILABLE = False
    BaseStrategy = None              # type: ignore[assignment]
    MarketCondition = None           # type: ignore[assignment]
    SignalStrength = None            # type: ignore[assignment]
    TrendFollowingStrategy = None    # type: ignore[assignment]
    SwingTradingStrategy = None      # type: ignore[assignment]
    MeanReversionStrategy = None     # type: ignore[assignment]
    BreakoutTradingStrategy = None   # type: ignore[assignment]
    AIStrategyFusion = None          # type: ignore[assignment]
    FusionMethod = None              # type: ignore[assignment]

# 導入 EventContext (Single Source of Truth)
try:
    from schemas.rag import EventContext
    EVENTCONTEXT_AVAILABLE = True
except ImportError:
    EVENTCONTEXT_AVAILABLE = False
    EventContext = None

logger = logging.getLogger(__name__)


class StrategySelector:
    """
    策略選擇器 - 整合 v1 和 v2 的完整功能
    
    功能:
    1. 10 種預定義策略配置 (來自 v1)
    2. 實際策略實例化 (來自 v2)
    3. 市場體制識別
    4. AI Fusion 原生支援 (來自 v2)
    5. EventContext 事件驅動調整
    
    使用方式:
        from bioneuronai.strategies.selector import StrategySelector
        
        selector = StrategySelector(timeframe="1h")
        recommendation = selector.recommend_strategy(ohlcv_data)
    """
    
    def __init__(
        self,
        timeframe: str = "1h",
        enable_ai_fusion: bool = True,
        enable_learning: bool = True,
    ):
        """
        初始化策略選擇器
        
        Args:
            timeframe: 時間框架
            enable_ai_fusion: 是否啟用 AI Fusion
            enable_learning: 是否啟用學習 (用於 AI Fusion)
        """
        self.timeframe = timeframe
        
        # 策略配置 (來自 v1)
        self.strategy_configs = get_default_strategy_configs()
        
        # 市場評估器
        self._evaluator = MarketEvaluator()
        
        # 實際策略實例 (來自 v2)
        self._strategies: Dict[str, Any] = {}
        if STRATEGIES_AVAILABLE:
            assert TrendFollowingStrategy is not None
            assert SwingTradingStrategy is not None
            assert MeanReversionStrategy is not None
            assert BreakoutTradingStrategy is not None
            self._strategies = {
                'trend_following': TrendFollowingStrategy(timeframe),
                'swing_trading': SwingTradingStrategy(timeframe),
                'mean_reversion': MeanReversionStrategy(timeframe),
                'breakout': BreakoutTradingStrategy(timeframe),
            }
        
        # AI Fusion (來自 v2)
        self._ai_fusion: Optional[Any] = None
        if enable_ai_fusion and STRATEGIES_AVAILABLE:
            assert AIStrategyFusion is not None
            assert FusionMethod is not None
            try:
                self._ai_fusion = AIStrategyFusion(
                    timeframe=timeframe,
                    fusion_method=FusionMethod.MARKET_ADAPTIVE,
                    enable_learning=enable_learning,
                )
                logger.info("✅ AI Fusion 已啟用")
            except Exception as e:
                logger.warning(f"AI Fusion 初始化失敗: {e}")
        
        # 事件上下文緩存
        self._current_event_context: Optional[Any] = None
        
        # 績效歷史
        self._performance_history: Dict[str, List[Dict]] = {
            name: [] for name in self._strategies
        }
    
    # ========== 推薦 API (來自 v2，簡化版) ==========
    
    def recommend_strategy(
        self,
        ohlcv_data: np.ndarray,
        account_balance: float = 10000.0,
        use_ai_fusion: bool = True,
        event_score: float = 0.0,
        event_context: Optional[Any] = None,
    ) -> StrategyRecommendation:
        """
        根據市場狀況推薦策略 (整合事件系統)
        
        Args:
            ohlcv_data: OHLCV 數據
            account_balance: 帳戶餘額
            use_ai_fusion: 是否使用 AI 融合策略
            event_score: 環境評分 (-10 到 +10)
            event_context: 事件上下文
            
        Returns:
            StrategyRecommendation
        """
        recommendation = StrategyRecommendation()
        
        # 1. 識別市場體制
        market_regime = self._evaluator.identify_market_regime(ohlcv_data)
        recommendation.market_regime = market_regime
        recommendation.reasoning.append(f"市場體制: {market_regime.value}")
        
        # 2. 計算策略權重
        weights = self._calculate_strategy_weights(market_regime)
        recommendation.strategy_weights = weights
        
        # 3. 識別需避免的策略
        avoid = self._identify_avoid_strategies(market_regime)
        recommendation.avoid_strategies = avoid
        
        # 4. 選擇主要策略
        if weights:
            best_strategy = max(weights.items(), key=lambda x: x[1])
            recommendation.primary_strategy = StrategyType(best_strategy[0])
            recommendation.primary_confidence = best_strategy[1]
        
        # 5. AI Fusion 整合
        if use_ai_fusion and self._ai_fusion:
            self._apply_ai_fusion(
                recommendation, ohlcv_data, event_score, event_context
            )
        
        # 6. 風險評估
        volatility, risk_level = self._evaluator.calculate_volatility(ohlcv_data)
        recommendation.risk_level = RiskLevel(risk_level)
        recommendation.suggested_position_size = self._get_position_size(risk_level)
        recommendation.reasoning.append(f"風險等級: {risk_level}")
        
        # 7. 事件調整標記
        if event_score != 0:
            recommendation.has_event_adjustment = True
            recommendation.event_score = event_score
            recommendation.reasoning.append(f"事件評分: {event_score}")
        
        # 8. 添加策略說明
        self._add_strategy_reasons(recommendation, market_regime)
        
        return recommendation
    
    def _calculate_strategy_weights(
        self,
        market_regime: MarketRegime
    ) -> Dict[str, float]:
        """計算策略權重"""
        weights = {}
        
        for strategy_type in StrategyType:
            if strategy_type == StrategyType.AI_FUSION:
                continue
            
            fit = STRATEGY_MARKET_FIT.get(strategy_type, {})
            weight = 0.25  # 基礎權重
            
            if market_regime in fit.get('best', []):
                weight += 0.3
            elif market_regime in fit.get('good', []):
                weight += 0.1
            elif market_regime in fit.get('avoid', []):
                weight -= 0.3
            
            weights[strategy_type.value] = max(0.0, weight)
        
        # 正規化
        total = sum(weights.values())
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}
        
        return weights
    
    def _identify_avoid_strategies(
        self,
        market_regime: MarketRegime
    ) -> List[StrategyType]:
        """識別需避免的策略"""
        avoid = []
        for strategy_type in StrategyType:
            fit = STRATEGY_MARKET_FIT.get(strategy_type, {})
            if market_regime in fit.get('avoid', []):
                avoid.append(strategy_type)
        return avoid
    
    def _apply_ai_fusion(
        self,
        recommendation: StrategyRecommendation,
        ohlcv_data: np.ndarray,
        event_score: float,
        event_context: Optional[Any],
    ):
        """應用 AI Fusion 信號"""
        if self._ai_fusion is None:
            return
        try:
            fusion_signal = self._ai_fusion.generate_fusion_signal(
                ohlcv_data,
                event_score=event_score,
                event_context=event_context
            )
            
            if fusion_signal.should_trade:
                recommendation.reasoning.append(
                    f"AI Fusion: {fusion_signal.consensus_direction}, "
                    f"信心: {fusion_signal.confidence_score:.2f}"
                )
                
                if fusion_signal.confidence_score > 0.7:
                    recommendation.primary_strategy = StrategyType.AI_FUSION
                    recommendation.primary_confidence = fusion_signal.confidence_score
            
            # 更新市場體制資訊
            if self._ai_fusion.current_regime:
                recommendation.reasoning.append(
                    f"AI 體制: {self._ai_fusion.current_regime.regime_type}"
                )
        except Exception as e:
            logger.warning(f"AI Fusion 信號生成失敗: {e}")
    
    def _get_position_size(self, risk_level: str) -> float:
        """根據風險等級獲取建議倉位"""
        return {
            "low": 0.03,    # 3%
            "medium": 0.02, # 2%
            "high": 0.01,   # 1%
        }.get(risk_level, 0.02)
    
    def _add_strategy_reasons(
        self,
        recommendation: StrategyRecommendation,
        market_regime: MarketRegime
    ):
        """添加策略選擇原因說明"""
        strategy = recommendation.primary_strategy
        
        reasons = {
            StrategyType.TREND_FOLLOWING: {
                MarketRegime.TRENDING_BULL: "牛市趨勢明確，適合順勢做多",
                MarketRegime.TRENDING_BEAR: "熊市趨勢明確，適合順勢做空",
            },
            StrategyType.SWING_TRADING: {
                "default": "波段交易適合中期趨勢"
            },
            StrategyType.MEAN_REVERSION: {
                "default": "盤整行情適合均值回歸策略"
            },
            StrategyType.BREAKOUT: {
                "default": "識別到突破潛力，等待確認信號"
            },
            StrategyType.AI_FUSION: {
                "default": "AI 融合策略提供更高信心的交易信號"
            },
        }
        
        strategy_reasons = reasons.get(strategy, {})
        reason = strategy_reasons.get(market_regime, strategy_reasons.get("default", ""))
        if reason:
            recommendation.reasoning.append(reason)
    
    # ========== 詳細選擇 API (來自 v1) ==========
    
    async def select_optimal_strategy(
        self,
        ohlcv_data: np.ndarray,
        account_balance: float = 10000.0,
        preferences: Optional[Dict] = None
    ) -> StrategySelectionResult:
        """
        選擇最優策略 (詳細版本，來自 v1)
        
        Args:
            ohlcv_data: OHLCV 數據
            account_balance: 帳戶餘額
            preferences: 用戶偏好
            
        Returns:
            StrategySelectionResult 詳細結果
        """
        logger.info("開始策略選擇分析...")
        
        # 1. 識別市場體制
        market_regime = self._evaluator.identify_market_regime(ohlcv_data)
        logger.info(f"市場體制: {market_regime.value}")
        
        # 2. 評分所有策略
        scores = self._evaluator.score_strategies(
            market_regime, account_balance, preferences
        )
        
        # 3. 篩選可行策略
        viable = self._evaluator.filter_viable_strategies(
            scores, account_balance, preferences=preferences
        )
        logger.info(f"可行策略: {len(viable)} 個")
        
        # 4. 選擇主要策略
        primary = self._select_primary(viable)
        
        # 5. 選擇備選策略
        backups = self._select_backups(viable, primary)
        
        # 6. 計算策略組合
        strategy_mix = self._calculate_mix(primary, backups, market_regime)
        
        # 7. 風險評估
        risk_assessment = self._assess_risk(primary, ohlcv_data)
        
        # 8. 生成推理說明
        reasoning = self._generate_reasoning(
            primary, market_regime, scores
        )
        
        return StrategySelectionResult(
            timestamp=datetime.now(),
            primary_strategy=primary,
            backup_strategies=backups,
            strategy_mix=strategy_mix,
            confidence_score=self._calculate_confidence(scores, primary),
            market_match_score=scores.get(primary.name, 0.5) if primary else 0.5,
            reasoning=reasoning,
            risk_assessment=risk_assessment,
            expected_performance=self._estimate_performance(primary),
        )
    
    def _select_primary(self, viable: List[StrategyConfigTemplate]) -> Optional[StrategyConfigTemplate]:
        """選擇主要策略"""
        if not viable:
            return list(self.strategy_configs.values())[0]
        return max(viable, key=lambda s: s.sharpe_ratio * s.win_rate)
    
    def _select_backups(
        self,
        viable: List[StrategyConfigTemplate],
        primary: Optional[StrategyConfigTemplate]
    ) -> List[StrategyConfigTemplate]:
        """選擇備選策略"""
        if not primary:
            return []
        
        backups = []
        for config in viable:
            if config.name != primary.name:
                if config.strategy_type != primary.strategy_type:
                    backups.append(config)
                if len(backups) >= 2:
                    break
        return backups
    
    def _calculate_mix(
        self,
        primary: Optional[StrategyConfigTemplate],
        backups: List[StrategyConfigTemplate],
        market_regime: MarketRegime
    ) -> Dict[str, float]:
        """計算策略組合比例"""
        if not primary:
            return {}
        
        mix = {primary.name: 0.7}
        
        remaining = 0.3
        if backups:
            per_backup = remaining / len(backups)
            for backup in backups:
                mix[backup.name] = per_backup
        
        return mix
    
    def _assess_risk(
        self,
        primary: Optional[StrategyConfigTemplate],
        ohlcv_data: np.ndarray
    ) -> Dict[str, Any]:
        """評估風險"""
        volatility, risk_level = self._evaluator.calculate_volatility(ohlcv_data)
        
        return {
            "volatility": volatility,
            "risk_level": risk_level,
            "max_drawdown": primary.max_drawdown if primary else 0.1,
            "recommended_leverage": 1 if risk_level == "high" else (2 if risk_level == "medium" else 3),
        }
    
    def _calculate_confidence(
        self,
        scores: Dict[str, float],
        primary: Optional[StrategyConfigTemplate]
    ) -> float:
        """計算信心分數"""
        if not primary or primary.name not in scores:
            return 0.5
        
        primary_score = scores[primary.name]
        avg_score = sum(scores.values()) / len(scores) if scores else 0.5
        
        # 主策略分數相對於平均的優勢
        confidence = min(1.0, primary_score + (primary_score - avg_score) * 0.5)
        return max(0.3, confidence)
    
    def _generate_reasoning(
        self,
        primary: Optional[StrategyConfigTemplate],
        market_regime: MarketRegime,
        scores: Dict[str, float]
    ) -> str:
        """生成推理說明"""
        if not primary:
            return "無法選擇策略"
        
        parts = [
            f"市場體制: {market_regime.value}",
            f"選擇策略: {primary.name}",
            f"策略類型: {primary.strategy_type.value}",
            f"評分: {scores.get(primary.name, 0):.2f}",
            f"預期報酬: {primary.expected_return:.1%}",
            f"最大回撤: {primary.max_drawdown:.1%}",
        ]
        return " | ".join(parts)
    
    def _estimate_performance(
        self,
        primary: Optional[StrategyConfigTemplate]
    ) -> Dict[str, Any]:
        """估計績效"""
        if not primary:
            return {}
        
        return {
            "expected_return": primary.expected_return,
            "win_rate": primary.win_rate,
            "profit_factor": primary.profit_factor,
            "sharpe_ratio": primary.sharpe_ratio,
        }
    
    # ========== 策略信號 API (來自 v2) ==========
    
    def get_strategy_signals(self, ohlcv_data: np.ndarray) -> Dict[str, Any]:
        """
        獲取所有策略的信號 (來自 v2)
        
        Returns:
            策略名稱 -> TradeSetup 的字典
        """
        signals = {}
        
        for name, strategy in self._strategies.items():
            try:
                analysis = strategy.analyze_market(ohlcv_data)
                setup = strategy.evaluate_entry_conditions(analysis, ohlcv_data)
                signals[name] = setup
            except Exception as e:
                logger.error(f"策略 {name} 信號生成失敗: {e}")
                signals[name] = None
        
        return signals
    
    def get_ai_fusion_signal(
        self,
        ohlcv_data: np.ndarray,
        event_score: float = 0.0,
        event_context: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        獲取 AI Fusion 信號
        
        Args:
            ohlcv_data: OHLCV 數據
            event_score: 事件評分
            event_context: 事件上下文
            
        Returns:
            融合信號字典
        """
        if not self._ai_fusion:
            return None
        
        try:
            signal = self._ai_fusion.generate_fusion_signal(
                ohlcv_data,
                event_score=event_score,
                event_context=event_context
            )
            
            return {
                'should_trade': signal.should_trade,
                'direction': signal.consensus_direction,
                'confidence': signal.confidence_score,
                'consensus_strength': signal.consensus_strength,
                'contributing_strategies': signal.contributing_strategies,
                'has_conflict': signal.has_conflict,
                'fusion_method': signal.fusion_method_used.value,
            }
        except Exception as e:
            logger.error(f"AI Fusion 信號失敗: {e}")
            return None
    
    # ========== 事件上下文 API ==========
    
    def set_event_context(self, event_context: Optional[Any] = None):
        """設置事件上下文"""
        self._current_event_context = event_context
        if event_context:
            logger.debug(f"事件上下文已設置")
    
    # ========== 績效追蹤 API ==========
    
    def record_trade_result(self, strategy_name: str, trade_result: Dict[str, Any]):
        """記錄交易結果"""
        self._evaluator.record_performance(strategy_name, trade_result)
        
        # 更新 AI Fusion 權重
        if self._ai_fusion:
            self._ai_fusion.update_weights_from_performance(
                strategy_name, trade_result
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """獲取績效摘要"""
        summary = {
            'available_strategies': list(self._strategies.keys()),
            'strategy_configs': list(self.strategy_configs.keys()),
            'timeframe': self.timeframe,
            'ai_fusion_enabled': self._ai_fusion is not None,
            'performance': {},
        }
        
        for name in self._strategies:
            metrics = self._evaluator.get_performance_metrics(name)
            summary['performance'][name] = {
                'trades': metrics.total_trades,
                'win_rate': metrics.win_rate,
                'profit_factor': metrics.profit_factor,
            }
        
        return summary
    
    # ========== 狀態持久化 ==========
    
    def save_state(self, filepath: str):
        """保存狀態"""
        if self._ai_fusion:
            self._ai_fusion.save_state(filepath)
    
    def load_state(self, filepath: str):
        """載入狀態"""
        if self._ai_fusion:
            self._ai_fusion.load_state(filepath)
    
    # ========== 屬性 ==========
    
    @property
    def ai_fusion_available(self) -> bool:
        """AI Fusion 是否可用"""
        return self._ai_fusion is not None
    
    @property
    def strategies_available(self) -> bool:
        """實際策略是否可用"""
        return len(self._strategies) > 0


# ========== 便捷函數 ==========

def get_recommended_strategy(
    ohlcv_data: np.ndarray,
    timeframe: str = "1h",
    use_ai_fusion: bool = True,
) -> StrategyRecommendation:
    """
    快速獲取策略推薦
    
    Args:
        ohlcv_data: OHLCV 數據
        timeframe: 時間框架
        use_ai_fusion: 是否使用 AI Fusion
        
    Returns:
        StrategyRecommendation
    """
    selector = StrategySelector(timeframe, enable_ai_fusion=use_ai_fusion)
    return selector.recommend_strategy(ohlcv_data, use_ai_fusion=use_ai_fusion)

