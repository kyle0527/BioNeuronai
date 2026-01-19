"""
策略選擇器 - Strategy Selector
根據市場狀況智能選擇和配置最適合的交易策略
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    """策略類型枚舉"""
    TREND_FOLLOWING = "趨勢跟隨"
    MEAN_REVERSION = "均值回歸" 
    MOMENTUM = "動量交易"
    BREAKOUT = "突破交易"
    SCALPING = "剝頭皮"
    GRID_TRADING = "網格交易"
    ARBITRAGE = "套利交易"
    NEWS_TRADING = "新聞交易"
    VOLATILITY_TRADING = "波動率交易"
    PAIR_TRADING = "對沖交易"

class MarketRegime(Enum):
    """市場制度枚舉"""
    TRENDING_BULL = "上升趨勢"
    TRENDING_BEAR = "下降趨勢"
    SIDEWAYS_LOW_VOL = "橫盤低波動"
    SIDEWAYS_HIGH_VOL = "橫盤高波動"
    VOLATILE_UNCERTAIN = "高波動不確定"

@dataclass
class StrategyConfig:
    """策略配置數據結構"""
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
    """策略選擇結果"""
    timestamp: datetime
    primary_strategy: StrategyConfig
    backup_strategies: List[StrategyConfig]
    strategy_mix: Dict[str, float]  # 策略名稱到權重比例
    confidence_score: float
    market_match_score: float
    reasoning: str
    risk_assessment: Dict
    expected_performance: Dict

@dataclass
class StrategyPerformanceMetrics:
    """策略表現指標"""
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
    """策略選擇器 - 智能策略選擇和配置"""
    
    def __init__(self):
        self.available_strategies = self._initialize_strategies()
        self.strategy_performance_history = {}
        self.market_regime_history = []
        
    def _initialize_strategies(self) -> Dict[str, StrategyConfig]:
        """初始化可用策略"""
        strategies = {}
        
        # 1. 趨勢跟隨策略
        strategies["MA_Crossover_Trend"] = StrategyConfig(
            strategy_type=StrategyType.TREND_FOLLOWING,
            name="MA交叉趨勢跟隨",
            description="使用移動平均線交叉信號進行趨勢跟隨",
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
        
        # 2. 均值回歸策略
        strategies["RSI_Mean_Reversion"] = StrategyConfig(
            strategy_type=StrategyType.MEAN_REVERSION,
            name="RSI均值回歸",
            description="基於RSI指標的超買超賣均值回歸策略",
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
        
        # 3. 動量交易策略
        strategies["Momentum_Breakout"] = StrategyConfig(
            strategy_type=StrategyType.MOMENTUM,
            name="動量突破",
            description="基於價格動量和成交量的突破策略",
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
        
        # 4. 剝頭皮策略
        strategies["High_Frequency_Scalp"] = StrategyConfig(
            strategy_type=StrategyType.SCALPING,
            name="高頻剝頭皮",
            description="短期價格波動中獲取小幅利潤",
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
        
        # 5. 網格交易策略
        strategies["Grid_Trading"] = StrategyConfig(
            strategy_type=StrategyType.GRID_TRADING,
            name="智能網格",
            description="在價格區間內建立買賣網格",
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
        
        # 6. 波動率交易策略
        strategies["Volatility_Trading"] = StrategyConfig(
            strategy_type=StrategyType.VOLATILITY_TRADING,
            name="波動率交易",
            description="基於隱含波動率與歷史波動率差異的交易",
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
        """選擇最優策略組合"""
        logger.info("🎯 開始策略選擇分析...")
        
        try:
            # 1. 識別市場制度
            market_regime = await self._identify_market_regime(market_condition, technical_env)
            logger.info(f"   ✓ 市場制度識別: {market_regime.value}")
            
            # 2. 策略適配性評分
            strategy_scores = await self._score_strategies(market_regime, market_condition, 
                                                         technical_env, account_info)
            logger.info(f"   ✓ 評估了 {len(strategy_scores)} 個策略")
            
            # 3. 過濾可行策略
            viable_strategies = self._filter_viable_strategies(strategy_scores, account_info, preferences)
            logger.info(f"   ✓ 篩選出 {len(viable_strategies)} 個可行策略")
            
            # 4. 選擇主要策略
            primary_strategy = self._select_primary_strategy(viable_strategies)
            logger.info(f"   ✓ 主要策略: {primary_strategy.name}")
            
            # 5. 選擇備用策略
            backup_strategies = self._select_backup_strategies(viable_strategies, primary_strategy)
            logger.info(f"   ✓ 備用策略: {len(backup_strategies)} 個")
            
            # 6. 計算策略組合權重
            strategy_mix = await self._calculate_strategy_mix(primary_strategy, backup_strategies, 
                                                            market_condition, account_info)
            
            # 7. 風險評估
            risk_assessment = await self._assess_strategy_risk(primary_strategy, backup_strategies, 
                                                             market_condition)
            
            # 8. 預期表現分析
            expected_performance = await self._estimate_performance(primary_strategy, market_condition)
            
            # 9. 生成推理說明
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
            logger.error(f"策略選擇失敗: {e}")
            return self._get_default_strategy_selection()
    
    async def analyze_strategy_performance(self, strategy_name: str, 
                                         time_period: str = "30d") -> StrategyPerformanceMetrics:
        """分析策略歷史表現"""
        logger.info(f"📊 分析策略表現: {strategy_name} ({time_period})")
        
        try:
            # 模擬策略表現數據
            performance = StrategyPerformanceMetrics(
                strategy_name=strategy_name,
                total_trades=np.random.randint(50, 200),
                win_rate=np.random.uniform(0.45, 0.75),
                profit_factor=np.random.uniform(1.1, 2.0),
                sharpe_ratio=np.random.uniform(0.8, 2.5),
                max_drawdown=np.random.uniform(0.05, 0.20),
                total_return=np.random.uniform(0.08, 0.35),
                avg_trade_duration=np.random.uniform(0.5, 48.0),  # 小時
                market_conditions_performance={
                    "trending_bull": np.random.uniform(0.10, 0.30),
                    "trending_bear": np.random.uniform(-0.05, 0.15),
                    "sideways": np.random.uniform(0.05, 0.20),
                    "volatile": np.random.uniform(-0.10, 0.25)
                }
            )
            
            # 記錄到歷史
            if strategy_name not in self.strategy_performance_history:
                self.strategy_performance_history[strategy_name] = []
            
            self.strategy_performance_history[strategy_name].append({
                'timestamp': datetime.now(),
                'period': time_period,
                'performance': performance
            })
            
            return performance
            
        except Exception as e:
            logger.error(f"策略表現分析失敗: {e}")
            return self._get_default_performance_metrics(strategy_name)
    
    async def optimize_strategy_parameters(self, strategy_name: str, 
                                         market_data: Dict, 
                                         optimization_goal: str = "sharpe") -> Dict:
        """優化策略參數"""
        logger.info(f"⚙️ 優化策略參數: {strategy_name}")
        
        try:
            strategy = self.available_strategies[strategy_name]
            
            # 模擬參數優化
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
            
            # 計算優化效果
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
            logger.error(f"策略參數優化失敗: {e}")
            return {"error": str(e)}
    
    # ========== 私有方法 ==========
    
    async def _identify_market_regime(self, market_condition, technical_env) -> MarketRegime:
        """識別市場制度"""
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
        """為每個策略評分"""
        scores = {}
        
        for name, strategy in self.available_strategies.items():
            score = 0.0
            
            # 市場適配性評分 (40%)
            if market_regime in strategy.suitable_markets:
                score += 0.4
            elif self._is_compatible_regime(market_regime, strategy.suitable_markets):
                score += 0.2
            
            # 波動性匹配評分 (20%)
            volatility_score = self._score_volatility_match(strategy, market_condition.volatility_level)
            score += 0.2 * volatility_score
            
            # 資金要求評分 (15%)
            capital_score = self._score_capital_requirements(strategy, account_info)
            score += 0.15 * capital_score
            
            # 歷史表現評分 (15%)
            performance_score = self._score_historical_performance(name)
            score += 0.15 * performance_score
            
            # 風險匹配評分 (10%)
            risk_score = self._score_risk_compatibility(strategy, market_condition)
            score += 0.1 * risk_score
            
            scores[name] = min(1.0, max(0.0, score))
        
        return scores
    
    def _filter_viable_strategies(self, strategy_scores: Dict[str, float], 
                                account_info: Dict, preferences: Optional[Dict] = None) -> List[StrategyConfig]:
        """過濾可行策略"""
        viable = []
        min_score = 0.3  # 最低評分閾值
        
        for name, score in strategy_scores.items():
            if score >= min_score:
                strategy = self.available_strategies[name]
                
                # 檢查資金要求
                if strategy.min_capital <= account_info.get('available_balance', 0):
                    # 檢查復雜度偏好
                    if preferences and 'max_complexity' in preferences:
                        complexity_levels = {"SIMPLE": 1, "MEDIUM": 2, "COMPLEX": 3}
                        if complexity_levels[strategy.complexity] <= preferences['max_complexity']:
                            viable.append(strategy)
                    else:
                        viable.append(strategy)
        
        return viable
    
    def _select_primary_strategy(self, viable_strategies: List[StrategyConfig]) -> StrategyConfig:
        """選擇主要策略"""
        if not viable_strategies:
            # 返回最簡單的策略作為後備
            return list(self.available_strategies.values())[0]
        
        # 基於綜合評分選擇最佳策略
        return max(viable_strategies, key=lambda s: s.sharpe_ratio * s.win_rate)
    
    def _select_backup_strategies(self, viable_strategies: List[StrategyConfig], 
                                primary: StrategyConfig) -> List[StrategyConfig]:
        """選擇備用策略"""
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
        """計算策略組合權重"""
        mix = {primary.name: 0.7}  # 主策略70%
        
        if backup:
            remaining_weight = 0.3
            weight_per_backup = remaining_weight / len(backup)
            
            for strategy in backup:
                mix[strategy.name] = weight_per_backup
        
        return mix
    
    async def _assess_strategy_risk(self, primary: StrategyConfig, 
                                  backup: List[StrategyConfig], 
                                  market_condition) -> Dict:
        """評估策略風險"""
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
        """預期表現估算"""
        base_return = strategy.expected_return
        
        # 根據市場狀況調整
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
        """生成選擇推理說明"""
        reasoning_parts = []
        
        # 市場適配性
        reasoning_parts.append(f"當前市場制度為{market_regime.value}，")
        reasoning_parts.append(f"{strategy.name}策略在此環境下具有良好適配性")
        
        # 策略優勢
        reasoning_parts.append(f"該策略勝率{strategy.win_rate:.1%}，")
        reasoning_parts.append(f"夏普比率{strategy.sharpe_ratio:.2f}，表現穩健")
        
        # 風險考量
        reasoning_parts.append(f"最大回撤控制在{strategy.max_drawdown:.1%}，")
        reasoning_parts.append(f"符合當前{market_condition.volatility_level}波動環境")
        
        return "".join(reasoning_parts)
    
    def _calculate_confidence_score(self, strategy_scores: Dict, market_condition) -> float:
        """計算選擇信心度"""
        max_score = max(strategy_scores.values())
        score_variance = np.var(list(strategy_scores.values()))
        
        # 高分策略且分數差異大 = 高信心度
        confidence = max_score * (1 - score_variance) * market_condition.confidence_score
        
        return min(1.0, max(0.0, confidence))
    
    # ========== 輔助方法 ==========
    
    def _is_compatible_regime(self, current_regime: MarketRegime, 
                            suitable_regimes: List[MarketRegime]) -> bool:
        """檢查市場制度兼容性"""
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
        """波動性匹配評分"""
        if strategy.strategy_type == StrategyType.SCALPING:
            return 1.0 if volatility_level == "LOW" else 0.5
        elif strategy.strategy_type == StrategyType.VOLATILITY_TRADING:
            return 1.0 if volatility_level in ["HIGH", "EXTREME"] else 0.3
        elif strategy.strategy_type == StrategyType.TREND_FOLLOWING:
            return 1.0 if volatility_level in ["LOW", "MEDIUM"] else 0.6
        else:
            return 0.7
    
    def _score_capital_requirements(self, strategy: StrategyConfig, account_info: Dict) -> float:
        """資金要求評分"""
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
        """歷史表現評分"""
        if strategy_name in self.strategy_performance_history:
            recent_performance = self.strategy_performance_history[strategy_name][-1]
            performance = recent_performance['performance']
            
            # 基於多個指標綜合評分
            sharpe_score = min(1.0, performance.sharpe_ratio / 2.0)
            return_score = min(1.0, performance.total_return / 0.3)
            winrate_score = performance.win_rate
            
            return (sharpe_score + return_score + winrate_score) / 3
        else:
            return 0.5  # 無歷史數據時給予中性評分
    
    def _score_risk_compatibility(self, strategy: StrategyConfig, market_condition) -> float:
        """風險兼容性評分"""
        if market_condition.volatility_level == "EXTREME":
            # 極端波動時偏好低風險策略
            return 1.0 if strategy.max_drawdown < 0.1 else 0.5
        elif market_condition.sentiment_score < -0.5:
            # 極度恐慌時偏好保守策略
            return 1.0 if strategy.complexity == "SIMPLE" else 0.6
        else:
            return 0.8
    
    def _calculate_overall_risk(self, primary: StrategyConfig, backup: List[StrategyConfig]) -> str:
        """計算整體風險等級"""
        risk_scores = []
        
        # 主策略風險
        risk_scores.append(self._strategy_risk_score(primary) * 0.7)
        
        # 備用策略風險
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
        """單一策略風險評分"""
        complexity_risk = {"SIMPLE": 0.2, "MEDIUM": 0.5, "COMPLEX": 0.8}[strategy.complexity]
        drawdown_risk = min(1.0, strategy.max_drawdown / 0.2)
        
        return (complexity_risk + drawdown_risk) / 2
    
    # ========== 預設值方法 ==========
    
    def _get_default_strategy_selection(self) -> StrategySelection:
        """預設策略選擇"""
        default_strategy = list(self.available_strategies.values())[0]
        
        return StrategySelection(
            timestamp=datetime.now(),
            primary_strategy=default_strategy,
            backup_strategies=[],
            strategy_mix={default_strategy.name: 1.0},
            confidence_score=0.5,
            market_match_score=0.5,
            reasoning="使用預設策略配置",
            risk_assessment={"overall_risk": "MEDIUM"},
            expected_performance={"expected_annual_return": 0.1}
        )
    
    def _get_default_performance_metrics(self, strategy_name: str) -> StrategyPerformanceMetrics:
        """預設表現指標"""
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