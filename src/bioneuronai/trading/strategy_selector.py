"""
策略選擇器 - Strategy Selector

根據市場狀態智能選擇最佳交易策略。

功能:
1. 10 種預定義策略配置
2. 市場狀態識別
3. AI Fusion 整合 (2026-01-25 新增)
4. EventContext 事件驅動調整 (2026-01-25 新增)

更新日期: 2026-01-25
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

# 從 schemas 導入 EventContext (Single Source of Truth - 2026-01-25)
try:
    from schemas.rag import EventContext
    EVENTCONTEXT_AVAILABLE = True
except ImportError:
    EVENTCONTEXT_AVAILABLE = False
    EventContext = None

# 嘗試導入 AIStrategyFusion (可選)
try:
    from ..strategies.strategy_fusion import AIStrategyFusion, FusionMethod
    AI_FUSION_AVAILABLE = True
except ImportError:
    AI_FUSION_AVAILABLE = False
    AIStrategyFusion = None
    FusionMethod = None


class StrategyType(Enum):
    """"""
    TREND_FOLLOWING = ""
    MEAN_REVERSION = "" 
    MOMENTUM = ""
    BREAKOUT = ""
    SCALPING = ""
    GRID_TRADING = ""
    ARBITRAGE = ""
    NEWS_TRADING = ""
    VOLATILITY_TRADING = ""
    PAIR_TRADING = ""

class MarketRegime(Enum):
    """"""
    TRENDING_BULL = ""
    TRENDING_BEAR = ""
    SIDEWAYS_LOW_VOL = ""
    SIDEWAYS_HIGH_VOL = ""
    VOLATILE_UNCERTAIN = ""

@dataclass
class StrategyConfig:
    """"""
    strategy_type: StrategyType
    name: str
    description: str
    entry_conditions: Dict
    exit_conditions: Dict
    risk_parameters: Dict
    timeframe: str
    min_capital: float
    expected_return: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    suitable_markets: List[MarketRegime]
    complexity: str  # SIMPLE, MEDIUM, COMPLEX
    
@dataclass
class StrategySelection:
    """"""
    timestamp: datetime
    primary_strategy: StrategyConfig
    backup_strategies: List[StrategyConfig]
    strategy_mix: Dict[str, float]  # 
    confidence_score: float
    market_match_score: float
    reasoning: str
    risk_assessment: Dict
    expected_performance: Dict

@dataclass
class StrategyPerformanceMetrics:
    """"""
    strategy_name: str
    total_trades: int
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    total_return: float
    avg_trade_duration: float
    market_conditions_performance: Dict[str, float]

class StrategySelector:
    """策略選擇器 - 根據市場狀態智能選擇策略
    
    功能:
    1. 10 種預定義策略配置
    2. 市場狀態識別
    3. AI Fusion 整合 (可選)
    4. EventContext 事件驅動調整 (可選)
    """
    
    def __init__(self, enable_ai_fusion: bool = True, timeframe: str = "1h"):
        """
        初始化策略選擇器
        
        Args:
            enable_ai_fusion: 是否啟用 AI Fusion (需要 AIStrategyFusion 可用)
            timeframe: 時間框架
        """
        self.available_strategies = self._initialize_strategies()
        self.strategy_performance_history = {}
        self.market_regime_history = []
        self.timeframe = timeframe
        
        # AI Fusion 整合 (2026-01-25 新增)
        self._ai_fusion = None
        if enable_ai_fusion and AI_FUSION_AVAILABLE:
            try:
                self._ai_fusion = AIStrategyFusion(
                    timeframe=timeframe,
                    fusion_method=FusionMethod.MARKET_ADAPTIVE,
                    enable_learning=True,
                )
                logger.info("✅ AI Fusion 已啟用")
            except Exception as e:
                logger.warning(f"AI Fusion 初始化失敗: {e}")
        
        # 事件上下文緩存
        self._current_event_context: Optional[Any] = None
        
    def _initialize_strategies(self) -> Dict[str, StrategyConfig]:
        """"""
        strategies = {}
        
        # 1. 
        strategies["MA_Crossover_Trend"] = StrategyConfig(
            strategy_type=StrategyType.TREND_FOLLOWING,
            name="MA",
            description="",
            entry_conditions={
                "fast_ma_period": 21,
                "slow_ma_period": 50,
                "signal": "fast_ma > slow_ma",
                "volume_confirmation": True,
                "trend_strength_min": 0.6
            },
            exit_conditions={
                "stop_loss": 0.02,
                "take_profit": 0.06,
                "trailing_stop": True,
                "ma_cross_reverse": True
            },
            risk_parameters={
                "position_size": 0.05,
                "max_positions": 3,
                "risk_per_trade": 0.01
            },
            timeframe="1h",
            min_capital=1000.0,
            expected_return=0.15,
            max_drawdown=0.08,
            win_rate=0.55,
            profit_factor=1.4,
            sharpe_ratio=1.2,
            suitable_markets=[MarketRegime.TRENDING_BULL, MarketRegime.TRENDING_BEAR],
            complexity="SIMPLE"
        )
        
        # 2. 
        strategies["RSI_Mean_Reversion"] = StrategyConfig(
            strategy_type=StrategyType.MEAN_REVERSION,
            name="RSI",
            description="RSI",
            entry_conditions={
                "rsi_period": 14,
                "oversold_threshold": 30,
                "overbought_threshold": 70,
                "bollinger_bands_confirm": True,
                "volume_spike": False
            },
            exit_conditions={
                "rsi_neutral": 50,
                "profit_target": 0.03,
                "stop_loss": 0.015,
                "time_exit": "2h"
            },
            risk_parameters={
                "position_size": 0.03,
                "max_positions": 5,
                "risk_per_trade": 0.008
            },
            timeframe="15m",
            min_capital=500.0,
            expected_return=0.12,
            max_drawdown=0.06,
            win_rate=0.65,
            profit_factor=1.3,
            sharpe_ratio=1.1,
            suitable_markets=[MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL],
            complexity="MEDIUM"
        )
        
        # 3. 
        strategies["Momentum_Breakout"] = StrategyConfig(
            strategy_type=StrategyType.MOMENTUM,
            name="",
            description="",
            entry_conditions={
                "momentum_period": 20,
                "momentum_threshold": 0.02,
                "volume_multiplier": 1.5,
                "price_breakout": True,
                "macd_confirmation": True
            },
            exit_conditions={
                "momentum_loss": 0.5,
                "profit_target": 0.08,
                "stop_loss": 0.025,
                "volume_decline": True
            },
            risk_parameters={
                "position_size": 0.04,
                "max_positions": 3,
                "risk_per_trade": 0.012
            },
            timeframe="30m",
            min_capital=1500.0,
            expected_return=0.20,
            max_drawdown=0.12,
            win_rate=0.50,
            profit_factor=1.6,
            sharpe_ratio=1.3,
            suitable_markets=[MarketRegime.TRENDING_BULL, MarketRegime.VOLATILE_UNCERTAIN],
            complexity="MEDIUM"
        )
        
        # 4. 
        strategies["High_Frequency_Scalp"] = StrategyConfig(
            strategy_type=StrategyType.SCALPING,
            name="",
            description="",
            entry_conditions={
                "spread_threshold": 0.001,
                "order_book_imbalance": 0.3,
                "micro_trend": True,
                "liquidity_min": 1000000
            },
            exit_conditions={
                "profit_target": 0.005,
                "stop_loss": 0.003,
                "time_exit": "5m",
                "spread_widen": 0.002
            },
            risk_parameters={
                "position_size": 0.02,
                "max_positions": 10,
                "risk_per_trade": 0.003
            },
            timeframe="1m",
            min_capital=5000.0,
            expected_return=0.25,
            max_drawdown=0.04,
            win_rate=0.75,
            profit_factor=1.2,
            sharpe_ratio=2.1,
            suitable_markets=[MarketRegime.SIDEWAYS_LOW_VOL],
            complexity="COMPLEX"
        )
        
        # 5. 
        strategies["Grid_Trading"] = StrategyConfig(
            strategy_type=StrategyType.GRID_TRADING,
            name="",
            description="",
            entry_conditions={
                "grid_levels": 10,
                "grid_spacing": 0.01,
                "range_detection": True,
                "volatility_adjustment": True
            },
            exit_conditions={
                "range_break": 0.05,
                "profit_accumulation": 0.10,
                "max_grid_age": "24h"
            },
            risk_parameters={
                "total_grid_allocation": 0.30,
                "max_grid_levels": 20,
                "risk_per_level": 0.015
            },
            timeframe="1h",
            min_capital=2000.0,
            expected_return=0.18,
            max_drawdown=0.15,
            win_rate=0.70,
            profit_factor=1.5,
            sharpe_ratio=1.4,
            suitable_markets=[MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.SIDEWAYS_HIGH_VOL],
            complexity="COMPLEX"
        )
        
        # 6. 
        strategies["Volatility_Trading"] = StrategyConfig(
            strategy_type=StrategyType.VOLATILITY_TRADING,
            name="",
            description="",
            entry_conditions={
                "iv_hv_ratio": 1.2,
                "volatility_spike": 0.3,
                "vix_divergence": True,
                "option_skew": 0.1
            },
            exit_conditions={
                "volatility_normalize": 0.8,
                "time_decay": 0.5,
                "profit_target": 0.15,
                "delta_neutral": True
            },
            risk_parameters={
                "volatility_allocation": 0.10,
                "max_vega_exposure": 1000,
                "delta_hedge_threshold": 0.1
            },
            timeframe="4h",
            min_capital=10000.0,
            expected_return=0.22,
            max_drawdown=0.18,
            win_rate=0.48,
            profit_factor=1.8,
            sharpe_ratio=1.6,
            suitable_markets=[MarketRegime.VOLATILE_UNCERTAIN, MarketRegime.SIDEWAYS_HIGH_VOL],
            complexity="COMPLEX"
        )
        
        return strategies
    
    async def select_optimal_strategy(self, market_condition, technical_env, fundamental_env, 
                                    account_info: Dict, preferences: Optional[Dict] = None) -> StrategySelection:
        """"""
        logger.info(" ...")
        
        try:
            # 1. 
            market_regime = await self._identify_market_regime(market_condition, technical_env)
            logger.info(f"    : {market_regime.value}")
            
            # 2. 
            strategy_scores = await self._score_strategies(market_regime, market_condition, 
                                                         technical_env, account_info)
            logger.info(f"     {len(strategy_scores)} ")
            
            # 3. 
            viable_strategies = self._filter_viable_strategies(strategy_scores, account_info, preferences)
            logger.info(f"     {len(viable_strategies)} ")
            
            # 4. 
            primary_strategy = self._select_primary_strategy(viable_strategies)
            logger.info(f"    : {primary_strategy.name}")
            
            # 5. 
            backup_strategies = self._select_backup_strategies(viable_strategies, primary_strategy)
            logger.info(f"    : {len(backup_strategies)} ")
            
            # 6. 
            strategy_mix = await self._calculate_strategy_mix(primary_strategy, backup_strategies, 
                                                            market_condition, account_info)
            
            # 7. 
            risk_assessment = await self._assess_strategy_risk(primary_strategy, backup_strategies, 
                                                             market_condition)
            
            # 8. 
            expected_performance = await self._estimate_performance(primary_strategy, market_condition)
            
            # 9. 
            reasoning = self._generate_selection_reasoning(primary_strategy, market_regime, 
                                                         market_condition, strategy_scores)
            
            selection = StrategySelection(
                timestamp=datetime.now(),
                primary_strategy=primary_strategy,
                backup_strategies=backup_strategies,
                strategy_mix=strategy_mix,
                confidence_score=self._calculate_confidence_score(strategy_scores, market_condition),
                market_match_score=strategy_scores[primary_strategy.name],
                reasoning=reasoning,
                risk_assessment=risk_assessment,
                expected_performance=expected_performance
            )
            
            return selection
            
        except Exception as e:
            logger.error(f": {e}")
            return self._get_default_strategy_selection()
    
    async def analyze_strategy_performance(self, strategy_name: str, 
                                         time_period: str = "30d") -> StrategyPerformanceMetrics:
        """"""
        logger.info(f" : {strategy_name} ({time_period})")
        
        try:
            # 
            performance = StrategyPerformanceMetrics(
                strategy_name=strategy_name,
                total_trades=np.random.randint(50, 200),
                win_rate=np.random.uniform(0.45, 0.75),
                profit_factor=np.random.uniform(1.1, 2.0),
                sharpe_ratio=np.random.uniform(0.8, 2.5),
                max_drawdown=np.random.uniform(0.05, 0.20),
                total_return=np.random.uniform(0.08, 0.35),
                avg_trade_duration=np.random.uniform(0.5, 48.0),  # 
                market_conditions_performance={
                    "trending_bull": np.random.uniform(0.10, 0.30),
                    "trending_bear": np.random.uniform(-0.05, 0.15),
                    "sideways": np.random.uniform(0.05, 0.20),
                    "volatile": np.random.uniform(-0.10, 0.25)
                }
            )
            
            # 
            if strategy_name not in self.strategy_performance_history:
                self.strategy_performance_history[strategy_name] = []
            
            self.strategy_performance_history[strategy_name].append({
                'timestamp': datetime.now(),
                'period': time_period,
                'performance': performance
            })
            
            return performance
            
        except Exception as e:
            logger.error(f": {e}")
            return self._get_default_performance_metrics(strategy_name)
    
    async def optimize_strategy_parameters(self, strategy_name: str, 
                                         market_data: Dict, 
                                         optimization_goal: str = "sharpe") -> Dict:
        """"""
        logger.info(f" : {strategy_name}")
        
        try:
            strategy = self.available_strategies[strategy_name]
            
            # 
            optimized_params = {}
            
            if strategy.strategy_type == StrategyType.TREND_FOLLOWING:
                optimized_params = {
                    "fast_ma_period": np.random.randint(10, 25),
                    "slow_ma_period": np.random.randint(40, 60),
                    "stop_loss": np.random.uniform(0.015, 0.025),
                    "take_profit": np.random.uniform(0.04, 0.08)
                }
            elif strategy.strategy_type == StrategyType.MEAN_REVERSION:
                optimized_params = {
                    "rsi_period": np.random.randint(12, 18),
                    "oversold_threshold": np.random.randint(25, 35),
                    "overbought_threshold": np.random.randint(65, 75),
                    "profit_target": np.random.uniform(0.02, 0.04)
                }
            
            # 
            improvement_metrics = {
                "sharpe_improvement": np.random.uniform(0.1, 0.4),
                "return_improvement": np.random.uniform(0.05, 0.15),
                "drawdown_reduction": np.random.uniform(0.01, 0.05),
                "win_rate_improvement": np.random.uniform(0.02, 0.08)
            }
            
            return {
                "original_params": strategy.entry_conditions,
                "optimized_params": optimized_params,
                "improvement_metrics": improvement_metrics,
                "optimization_confidence": np.random.uniform(0.7, 0.95)
            }
            
        except Exception as e:
            logger.error(f": {e}")
            return {"error": str(e)}
    
    # ==========  ==========
    
    async def _identify_market_regime(self, market_condition, technical_env) -> MarketRegime:
        """"""
        trend = market_condition.overall_trend
        volatility = market_condition.volatility_level
        
        if trend == "BULLISH" and volatility in ["LOW", "MEDIUM"]:
            return MarketRegime.TRENDING_BULL
        elif trend == "BEARISH" and volatility in ["LOW", "MEDIUM"]:
            return MarketRegime.TRENDING_BEAR
        elif trend == "NEUTRAL" and volatility == "LOW":
            return MarketRegime.SIDEWAYS_LOW_VOL
        elif trend == "NEUTRAL" and volatility in ["MEDIUM", "HIGH"]:
            return MarketRegime.SIDEWAYS_HIGH_VOL
        else:
            return MarketRegime.VOLATILE_UNCERTAIN
    
    async def _score_strategies(self, market_regime: MarketRegime, market_condition, 
                              technical_env, account_info: Dict) -> Dict[str, float]:
        """"""
        scores = {}
        
        for name, strategy in self.available_strategies.items():
            score = 0.0
            
            #  (40%)
            if market_regime in strategy.suitable_markets:
                score += 0.4
            elif self._is_compatible_regime(market_regime, strategy.suitable_markets):
                score += 0.2
            
            #  (20%)
            volatility_score = self._score_volatility_match(strategy, market_condition.volatility_level)
            score += 0.2 * volatility_score
            
            #  (15%)
            capital_score = self._score_capital_requirements(strategy, account_info)
            score += 0.15 * capital_score
            
            #  (15%)
            performance_score = self._score_historical_performance(name)
            score += 0.15 * performance_score
            
            #  (10%)
            risk_score = self._score_risk_compatibility(strategy, market_condition)
            score += 0.1 * risk_score
            
            scores[name] = min(1.0, max(0.0, score))
        
        return scores
    
    def _filter_viable_strategies(self, strategy_scores: Dict[str, float], 
                                account_info: Dict, preferences: Optional[Dict] = None) -> List[StrategyConfig]:
        """"""
        viable = []
        min_score = 0.3  # 
        
        for name, score in strategy_scores.items():
            if score >= min_score:
                strategy = self.available_strategies[name]
                
                # 
                if strategy.min_capital <= account_info.get('available_balance', 0):
                    # 
                    if preferences and 'max_complexity' in preferences:
                        complexity_levels = {"SIMPLE": 1, "MEDIUM": 2, "COMPLEX": 3}
                        if complexity_levels[strategy.complexity] <= preferences['max_complexity']:
                            viable.append(strategy)
                    else:
                        viable.append(strategy)
        
        return viable
    
    def _select_primary_strategy(self, viable_strategies: List[StrategyConfig]) -> StrategyConfig:
        """"""
        if not viable_strategies:
            # 
            return list(self.available_strategies.values())[0]
        
        # 
        return max(viable_strategies, key=lambda s: s.sharpe_ratio * s.win_rate)
    
    def _select_backup_strategies(self, viable_strategies: List[StrategyConfig], 
                                primary: StrategyConfig) -> List[StrategyConfig]:
        """"""
        backup = []
        
        for strategy in viable_strategies:
            if (strategy.name != primary.name and 
                strategy.strategy_type != primary.strategy_type and
                len(backup) < 2):
                backup.append(strategy)
        
        return backup
    
    async def _calculate_strategy_mix(self, primary: StrategyConfig, 
                                    backup: List[StrategyConfig], 
                                    market_condition, account_info: Dict) -> Dict[str, float]:
        """"""
        mix = {primary.name: 0.7}  # 70%
        
        if backup:
            remaining_weight = 0.3
            weight_per_backup = remaining_weight / len(backup)
            
            for strategy in backup:
                mix[strategy.name] = weight_per_backup
        
        return mix
    
    async def _assess_strategy_risk(self, primary: StrategyConfig, 
                                  backup: List[StrategyConfig], 
                                  market_condition) -> Dict:
        """"""
        return {
            "overall_risk": self._calculate_overall_risk(primary, backup),
            "max_portfolio_drawdown": primary.max_drawdown * 1.2,
            "correlation_risk": np.random.uniform(0.3, 0.7),
            "liquidity_risk": "LOW" if market_condition.liquidity_condition in ["EXCELLENT", "GOOD"] else "MEDIUM",
            "complexity_risk": primary.complexity,
            "market_regime_risk": np.random.uniform(0.2, 0.5)
        }
    
    async def _estimate_performance(self, strategy: StrategyConfig, 
                                  market_condition) -> Dict:
        """"""
        base_return = strategy.expected_return
        
        # 
        if market_condition.overall_trend == "BULLISH":
            adjusted_return = base_return * 1.2
        elif market_condition.overall_trend == "BEARISH":
            adjusted_return = base_return * 0.8
        else:
            adjusted_return = base_return
        
        return {
            "expected_annual_return": adjusted_return,
            "expected_monthly_return": adjusted_return / 12,
            "expected_win_rate": strategy.win_rate,
            "expected_profit_factor": strategy.profit_factor,
            "expected_sharpe": strategy.sharpe_ratio,
            "confidence_interval": {
                "lower": adjusted_return * 0.7,
                "upper": adjusted_return * 1.3
            }
        }
    
    def _generate_selection_reasoning(self, strategy: StrategyConfig, 
                                    market_regime: MarketRegime, 
                                    market_condition, strategy_scores: Dict) -> str:
        """"""
        reasoning_parts = []
        
        # 
        reasoning_parts.append(f"{market_regime.value}")
        reasoning_parts.append(f"{strategy.name}")
        
        # 
        reasoning_parts.append(f"{strategy.win_rate:.1%}")
        reasoning_parts.append(f"{strategy.sharpe_ratio:.2f}")
        
        # 
        reasoning_parts.append(f"{strategy.max_drawdown:.1%}")
        reasoning_parts.append(f"{market_condition.volatility_level}")
        
        return "".join(reasoning_parts)
    
    def _calculate_confidence_score(self, strategy_scores: Dict, market_condition) -> float:
        """"""
        max_score = max(strategy_scores.values())
        score_variance = np.var(list(strategy_scores.values()))
        
        #  = 
        confidence = max_score * (1 - score_variance) * market_condition.confidence_score
        
        return min(1.0, max(0.0, confidence))
    
    # ==========  ==========
    
    def _is_compatible_regime(self, current_regime: MarketRegime, 
                            suitable_regimes: List[MarketRegime]) -> bool:
        """"""
        compatibility_map = {
            MarketRegime.TRENDING_BULL: [MarketRegime.TRENDING_BEAR],
            MarketRegime.TRENDING_BEAR: [MarketRegime.TRENDING_BULL],
            MarketRegime.SIDEWAYS_LOW_VOL: [MarketRegime.SIDEWAYS_HIGH_VOL],
            MarketRegime.SIDEWAYS_HIGH_VOL: [MarketRegime.SIDEWAYS_LOW_VOL, MarketRegime.VOLATILE_UNCERTAIN],
            MarketRegime.VOLATILE_UNCERTAIN: [MarketRegime.SIDEWAYS_HIGH_VOL]
        }
        
        compatible = compatibility_map.get(current_regime, [])
        return any(regime in suitable_regimes for regime in compatible)
    
    def _score_volatility_match(self, strategy: StrategyConfig, volatility_level: str) -> float:
        """"""
        if strategy.strategy_type == StrategyType.SCALPING:
            return 1.0 if volatility_level == "LOW" else 0.5
        elif strategy.strategy_type == StrategyType.VOLATILITY_TRADING:
            return 1.0 if volatility_level in ["HIGH", "EXTREME"] else 0.3
        elif strategy.strategy_type == StrategyType.TREND_FOLLOWING:
            return 1.0 if volatility_level in ["LOW", "MEDIUM"] else 0.6
        else:
            return 0.7
    
    def _score_capital_requirements(self, strategy: StrategyConfig, account_info: Dict) -> float:
        """"""
        available_capital = account_info.get('available_balance', 0)
        
        if available_capital >= strategy.min_capital * 3:
            return 1.0
        elif available_capital >= strategy.min_capital * 2:
            return 0.8
        elif available_capital >= strategy.min_capital:
            return 0.6
        else:
            return 0.0
    
    def _score_historical_performance(self, strategy_name: str) -> float:
        """"""
        if strategy_name in self.strategy_performance_history:
            recent_performance = self.strategy_performance_history[strategy_name][-1]
            performance = recent_performance['performance']
            
            # 
            sharpe_score = min(1.0, performance.sharpe_ratio / 2.0)
            return_score = min(1.0, performance.total_return / 0.3)
            winrate_score = performance.win_rate
            
            return (sharpe_score + return_score + winrate_score) / 3
        else:
            return 0.5  # 
    
    def _score_risk_compatibility(self, strategy: StrategyConfig, market_condition) -> float:
        """"""
        if market_condition.volatility_level == "EXTREME":
            # 
            return 1.0 if strategy.max_drawdown < 0.1 else 0.5
        elif market_condition.sentiment_score < -0.5:
            # 
            return 1.0 if strategy.complexity == "SIMPLE" else 0.6
        else:
            return 0.8
    
    def _calculate_overall_risk(self, primary: StrategyConfig, backup: List[StrategyConfig]) -> str:
        """"""
        risk_scores = []
        
        # 
        risk_scores.append(self._strategy_risk_score(primary) * 0.7)
        
        # 
        for strategy in backup:
            risk_scores.append(self._strategy_risk_score(strategy) * 0.3 / len(backup))
        
        overall_risk_score = sum(risk_scores)
        
        if overall_risk_score < 0.3:
            return "LOW"
        elif overall_risk_score < 0.6:
            return "MEDIUM"
        elif overall_risk_score < 0.8:
            return "HIGH"
        else:
            return "EXTREME"
    
    def _strategy_risk_score(self, strategy: StrategyConfig) -> float:
        """"""
        complexity_risk = {"SIMPLE": 0.2, "MEDIUM": 0.5, "COMPLEX": 0.8}[strategy.complexity]
        drawdown_risk = min(1.0, strategy.max_drawdown / 0.2)
        
        return (complexity_risk + drawdown_risk) / 2
    
    # ==========  ==========
    
    def _get_default_strategy_selection(self) -> StrategySelection:
        """"""
        default_strategy = list(self.available_strategies.values())[0]
        
        return StrategySelection(
            timestamp=datetime.now(),
            primary_strategy=default_strategy,
            backup_strategies=[],
            strategy_mix={default_strategy.name: 1.0},
            confidence_score=0.5,
            market_match_score=0.5,
            reasoning="",
            risk_assessment={"overall_risk": "MEDIUM"},
            expected_performance={"expected_annual_return": 0.1}
        )
    
    def _get_default_performance_metrics(self, strategy_name: str) -> StrategyPerformanceMetrics:
        """"""
        return StrategyPerformanceMetrics(
            strategy_name=strategy_name,
            total_trades=0,
            win_rate=0.5,
            profit_factor=1.0,
            sharpe_ratio=1.0,
            max_drawdown=0.05,
            total_return=0.0,
            avg_trade_duration=1.0,
            market_conditions_performance={}
        )
    
    def get_available_strategies_summary(self) -> Dict:
        """獲取可用策略摘要"""
        summary = {}
        
        for name, strategy in self.available_strategies.items():
            summary[name] = {
                "type": strategy.strategy_type.value,
                "complexity": strategy.complexity,
                "expected_return": strategy.expected_return,
                "win_rate": strategy.win_rate,
                "min_capital": strategy.min_capital,
                "suitable_markets": [m.value for m in strategy.suitable_markets]
            }
        
        return summary
    
    # ========== AI Fusion 整合 (2026-01-25 新增) ==========
    
    def set_event_context(self, event_context: Optional[Any] = None):
        """
        設置事件上下文 - 供事件驅動調整使用
        
        Args:
            event_context: EventContext 實例或字典
        """
        self._current_event_context = event_context
        if event_context:
            logger.debug(f"事件上下文已設置: {event_context}")
    
    def get_ai_fusion_signal(
        self,
        ohlcv_data: np.ndarray,
        symbol: str = "BTCUSDT",
        event_score: float = 0.0,
        event_context: Optional[Any] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        獲取 AI Fusion 融合信號
        
        整合 AIStrategyFusion 的能力，提供事件驅動的策略融合。
        
        Args:
            ohlcv_data: OHLCV 數據
            symbol: 交易對符號
            event_score: 事件評分 (-10 到 +10)
            event_context: EventContext 實例 (可選)
            
        Returns:
            融合信號字典，或 None (如果 AI Fusion 不可用)
        """
        if not self._ai_fusion:
            logger.debug("AI Fusion 不可用")
            return None
        
        # 使用傳入的或緩存的事件上下文
        ctx = event_context or self._current_event_context
        
        try:
            # 調用 AIStrategyFusion
            signal = self._ai_fusion.generate_signal(
                ohlcv_data=ohlcv_data,
                symbol=symbol,
                event_score=event_score,
                event_context=ctx,
            )
            
            return {
                "signal_type": signal.signal_type if signal else None,
                "confidence": signal.confidence if signal else 0,
                "fusion_method": signal.fusion_method_used.value if signal and signal.fusion_method_used else None,
                "reasoning": signal.reasoning if signal else "",
                "has_event_adjustment": event_score != 0,
            }
        except Exception as e:
            logger.error(f"AI Fusion 信號生成失敗: {e}")
            return None
    
    def recommend_with_ai_fusion(
        self,
        ohlcv_data: np.ndarray,
        capital: float,
        risk_tolerance: str = "medium",
        symbol: str = "BTCUSDT",
        event_score: float = 0.0,
    ) -> StrategySelection:
        """
        結合 AI Fusion 的策略推薦
        
        這是 select_strategy() 的增強版本，整合 AI Fusion 信號。
        
        Args:
            ohlcv_data: OHLCV 數據
            capital: 資金
            risk_tolerance: 風險容忍度
            symbol: 交易對
            event_score: 事件評分
            
        Returns:
            StrategySelection 物件
        """
        # 1. 先獲取基礎策略選擇
        base_selection = self.select_strategy(
            ohlcv_data=ohlcv_data,
            capital=capital,
            risk_tolerance=risk_tolerance,
        )
        
        # 2. 如果 AI Fusion 可用，融合信號
        if self._ai_fusion and len(ohlcv_data) >= 50:
            ai_signal = self.get_ai_fusion_signal(
                ohlcv_data=ohlcv_data,
                symbol=symbol,
                event_score=event_score,
            )
            
            if ai_signal:
                # 調整置信度
                ai_confidence = ai_signal.get("confidence", 0.5)
                base_selection.confidence_score = (
                    base_selection.confidence_score * 0.4 + ai_confidence * 0.6
                )
                
                # 更新推理說明
                base_selection.reasoning += f"\n[AI Fusion] {ai_signal.get('reasoning', '')}"
                
                # 事件調整標記
                if ai_signal.get("has_event_adjustment"):
                    base_selection.reasoning += f"\n[Event] 事件評分: {event_score}"
        
        return base_selection
    
    @property
    def ai_fusion_available(self) -> bool:
        """檢查 AI Fusion 是否可用"""
        return self._ai_fusion is not None