"""
策略競技場 - 養蠱式策略優化系統 (Strategy Arena)
================================================

核心理念：讓策略互相競爭，優勝劣汰，自動進化

工作流程：
1. 多策略並行回測
2. 多維度性能評估（夏普比率、最大回撤、勝率、盈虧比等）
3. 自動排名與淘汰
4. 參數優化與突變
5. 持續迭代進化

特色功能：
- 自動發現最優策略組合
- 支持參數網格搜索
- 貝葉斯優化加速
- 多進程並行回測
- 詳細性能報告

創建日期：2026-02-14
"""

import logging
import json
import uuid
import inspect
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from dataclasses import dataclass, field, asdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from enum import Enum
import numpy as np

from .base_strategy import BaseStrategy
from .breakout_trading import BreakoutTradingStrategy
from .direction_change_strategy import DirectionChangeStrategy
from .mean_reversion import MeanReversionStrategy
from .pair_trading_strategy import PairTradingStrategy
from .swing_trading import SwingTradingStrategy
from .trend_following import TrendFollowingStrategy

logger = logging.getLogger(__name__)


class RankMetric(Enum):
    """排名指標"""
    SHARPE_RATIO = "sharpe_ratio"           # 夏普比率
    SORTINO_RATIO = "sortino_ratio"         # 索提諾比率
    CALMAR_RATIO = "calmar_ratio"           # 卡爾瑪比率
    MAX_DRAWDOWN = "max_drawdown"           # 最大回撤
    WIN_RATE = "win_rate"                   # 勝率
    PROFIT_FACTOR = "profit_factor"         # 盈虧比
    TOTAL_RETURN = "total_return"           # 總回報
    AVG_TRADE_RETURN = "avg_trade_return"   # 平均交易回報
    CONSISTENCY = "consistency"             # 一致性（月度正回報比例）


@dataclass
class StrategyCandidate:
    """策略候選者"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    strategy_type: str = ""  # 'trend_following', 'mean_reversion', etc.
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 性能指標
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    total_trades: int = 0
    avg_trade_return: float = 0.0
    consistency: float = 0.0  # 月度正回報比例
    
    # 排名相關
    rank: int = 0
    score: float = 0.0  # 綜合評分
    generation: int = 0  # 第幾代
    parent_ids: List[str] = field(default_factory=list)
    
    # 回測結果
    backtest_result: Optional[Dict] = None
    
    def calculate_score(self, weights: Dict[str, float]) -> float:
        """計算綜合評分"""
        if self.total_trades <= 0:
            self.score = 0.0
            return self.score

        if self.backtest_result and self.backtest_result.get('error'):
            self.score = 0.0
            return self.score

        score = 0.0
        
        # 標準化各指標（避免量綱差異）
        if weights.get('sharpe_ratio', 0) > 0:
            score += max(0, self.sharpe_ratio) * weights['sharpe_ratio']
        
        if weights.get('sortino_ratio', 0) > 0:
            score += max(0, self.sortino_ratio) * weights['sortino_ratio']
        
        if weights.get('max_drawdown', 0) > 0:
            # 回撤越小越好（分數為正）
            score += (1.0 - abs(self.max_drawdown)) * weights['max_drawdown']
        
        if weights.get('win_rate', 0) > 0:
            score += self.win_rate * weights['win_rate']
        
        if weights.get('profit_factor', 0) > 0:
            # profit_factor > 1 才有意義
            score += max(0, (self.profit_factor - 1) / 2) * weights['profit_factor']
        
        if weights.get('total_return', 0) > 0:
            score += max(0, self.total_return) * weights['total_return']
        
        if weights.get('consistency', 0) > 0:
            score += self.consistency * weights['consistency']

        activity_factor = min(1.0, self.total_trades / 5.0)
        self.score = score * activity_factor
        return self.score


@dataclass
class ArenaConfig:
    """競技場配置"""
    # 回測設置
    data_dir: str = "backtest/data/binance_historical"
    symbol: str = "ETHUSDT"
    interval: str = "1h"
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_balance: float = 10000.0
    warmup_bars: int = 10
    
    # 競爭設置
    population_size: int = 20  # 每代策略數量
    survival_rate: float = 0.3  # 存活率（前30%晉級）
    mutation_rate: float = 0.2  # 突變率
    crossover_rate: float = 0.5  # 交叉率
    max_generations: int = 10  # 最大迭代代數
    random_seed: Optional[int] = None  # 隨機種子（可選，用於可重現性）
    
    # 評分權重
    score_weights: Dict[str, float] = field(default_factory=lambda: {
        'sharpe_ratio': 0.3,
        'sortino_ratio': 0.2,
        'max_drawdown': 0.2,
        'win_rate': 0.1,
        'profit_factor': 0.1,
        'consistency': 0.1,
    })
    
    # 並行化
    use_multiprocessing: bool = False  # 多進程加速
    max_workers: int = 4
    
    # 輸出
    output_dir: str = "strategy_arena_results"
    verbose: bool = True


class StrategyArena:
    """
    策略競技場 - 養蠱式優化系統
    
    通過回測、競爭、淘汰、進化，找出最優策略組合
    """
    
    def __init__(self, config: ArenaConfig):
        self.config = config
        self.current_generation = 0
        self.population: List[StrategyCandidate] = []
        self.history: List[Dict] = []  # 歷史記錄
        self.best_strategy: Optional[StrategyCandidate] = None
        
        # 創建隨機數生成器（替代 numpy legacy random）
        self.rng = np.random.default_rng(config.random_seed)
        
        # 創建輸出目錄
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info("🏟️  策略競技場已初始化")
        logger.info(f"   - 種群數量: {config.population_size}")
        logger.info(f"   - 存活率: {config.survival_rate * 100:.0f}%")
        logger.info(f"   - 最大代數: {config.max_generations}")
        logger.info(f"   - 預熱 K 線: {config.warmup_bars}")
        if config.random_seed is not None:
            logger.info(f"   - 隨機種子: {config.random_seed} (可重現)")
    
    def initialize_population(self) -> List[StrategyCandidate]:
        """初始化種群 - 創建多樣化的策略候選者"""
        population = []
        
        # 策略類型分布
        strategy_types = [
            'trend_following',
            'swing_trading',
            'mean_reversion',
            'breakout_trading',
            'direction_change',
            'pair_trading',
        ]
        
        # 為每種策略生成多個參數變體
        per_type = self.config.population_size // len(strategy_types)
        
        for strategy_type in strategy_types:
            for i in range(per_type):
                params = self._generate_random_parameters(strategy_type)
                candidate = StrategyCandidate(
                    name=f"{strategy_type}_{i}",
                    strategy_type=strategy_type,
                    parameters=params,
                    generation=0,
                )
                population.append(candidate)
        
        # 填充到目標數量
        while len(population) < self.config.population_size:
            strategy_type = self.rng.choice(strategy_types)
            params = self._generate_random_parameters(strategy_type)
            candidate = StrategyCandidate(
                name=f"{strategy_type}_extra_{len(population)}",
                strategy_type=strategy_type,
                parameters=params,
                generation=0,
            )
            population.append(candidate)
        
        self.population = population
        logger.info(f"✅ 初始種群已創建: {len(population)} 個策略候選者")
        
        return population
    
    def _generate_random_parameters(self, strategy_type: str) -> Dict[str, Any]:
        """生成隨機參數（根據策略類型）"""
        base_params: Dict[str, Any] = {
            'timeframe': self.config.interval,
        }
        
        if strategy_type == 'trend_following':
            trend_params: Dict[str, Any] = {
                'ema_fast': int(self.rng.integers(10, 34)),
                'ema_medium': int(self.rng.integers(34, 89)),
                'ema_slow': int(self.rng.integers(120, 260)),
                'min_adx_for_trend': int(self.rng.integers(18, 35)),
            }
            base_params.update(trend_params)
        
        elif strategy_type == 'swing_trading':
            swing_params: Dict[str, Any] = {
                'swing_lookback': int(self.rng.integers(3, 9)),
                'rsi_period': int(self.rng.integers(10, 21)),
                'required_confirmations': int(self.rng.integers(2, 5)),
            }
            base_params.update(swing_params)
        
        elif strategy_type == 'mean_reversion':
            mean_params: Dict[str, Any] = {
                'bb_period': int(self.rng.integers(14, 40)),
                'bb_std_dev': float(self.rng.uniform(1.5, 3.0)),
                'z_lookback': int(self.rng.integers(14, 40)),
            }
            base_params.update(mean_params)
        
        elif strategy_type == 'breakout_trading':
            breakout_params: Dict[str, Any] = {
                'range_lookback': int(self.rng.integers(10, 35)),
                'breakout_threshold': float(self.rng.uniform(0.3, 1.0)),
                'volume_threshold': float(self.rng.uniform(1.1, 2.5)),
            }
            base_params.update(breakout_params)

        elif strategy_type == 'direction_change':
            dc_params: Dict[str, Any] = {
                'dc_threshold': float(self.rng.uniform(0.003, 0.015)),  # 0.3% - 1.5%
                'min_consecutive_dc': int(self.rng.integers(2, 5)),
            }
            base_params.update(dc_params)

        elif strategy_type == 'pair_trading':
            pair_params: Dict[str, Any] = {
                'lookback_period': int(self.rng.integers(30, 120)),
                'entry_z_threshold': float(self.rng.uniform(1.5, 3.0)),
                'exit_z_threshold': float(self.rng.uniform(0.3, 0.8)),
                'min_correlation': float(self.rng.uniform(0.60, 0.85)),
            }
            base_params.update(pair_params)

        return base_params
    
    def evaluate_population(self) -> List[StrategyCandidate]:
        """評估整個種群 - 運行回測並計算性能"""
        
        if self.config.use_multiprocessing:
            return self._evaluate_parallel()
        else:
            return self._evaluate_sequential()
    
    def _evaluate_sequential(self) -> List[StrategyCandidate]:
        """串行評估（單進程）"""
        logger.info(f"📊 開始評估第 {self.current_generation} 代（單進程）...")
        
        for i, candidate in enumerate(self.population):
            logger.info(f"   [{i+1}/{len(self.population)}] 評估 {candidate.name}...")
            result = self._run_backtest(candidate)
            self._apply_backtest_result(candidate, result)
            candidate.calculate_score(self.config.score_weights)
        
        return self.population
    
    def _evaluate_parallel(self) -> List[StrategyCandidate]:
        """並行評估（多進程）"""
        logger.info(f"📊 開始評估第 {self.current_generation} 代（多進程: {self.config.max_workers} workers）...")
        
        with ProcessPoolExecutor(max_workers=self.config.max_workers) as executor:
            futures = {
                executor.submit(self._run_backtest, candidate): candidate
                for candidate in self.population
            }
            
            for i, future in enumerate(as_completed(futures)):
                candidate = futures[future]
                try:
                    result = future.result()
                    self._apply_backtest_result(candidate, result)
                    candidate.calculate_score(self.config.score_weights)
                    logger.info(f"   ✅ [{i+1}/{len(self.population)}] {candidate.name} 完成")
                except Exception as e:
                    logger.error(f"   ❌ {candidate.name} 評估失敗: {e}")
        
        return self.population
    
    def _run_backtest(self, candidate: StrategyCandidate) -> Dict[str, Any]:
        """為單個候選策略運行回測"""
        try:
            from backtest.service import run_strategy_instance_backtest

            strategy = self._create_strategy(candidate)
            return run_strategy_instance_backtest(
                strategy,
                symbol=self.config.symbol,
                interval=self.config.interval,
                balance=self.config.initial_balance,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                data_dir=self.config.data_dir,
                warmup_bars=self.config.warmup_bars,
            )
        except Exception as e:
            logger.error(f"回測失敗 {candidate.name}: {e}")
            return {
                'total_return': 0.0,
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0,
                'max_drawdown': 1.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'total_trades': 0,
                'consistency': 0.0,
                'error': str(e),
            }

    def _apply_backtest_result(self, candidate: StrategyCandidate, result: Dict[str, Any]) -> None:
        """將正式 replay 結果套用到候選策略。"""
        candidate.total_return = self._safe_metric(result.get('total_return', 0.0))
        candidate.sharpe_ratio = self._safe_metric(result.get('sharpe_ratio', 0.0))
        candidate.sortino_ratio = self._safe_metric(result.get('sortino_ratio', 0.0))
        candidate.max_drawdown = self._safe_metric(result.get('max_drawdown', 0.0))
        candidate.win_rate = self._safe_metric(result.get('win_rate', 0.0))
        candidate.profit_factor = self._safe_metric(result.get('profit_factor', 0.0))
        candidate.total_trades = int(result.get('total_trades', result.get('trade_count', 0)))
        candidate.avg_trade_return = (
            candidate.total_return / candidate.total_trades if candidate.total_trades > 0 else 0.0
        )
        candidate.consistency = self._calculate_consistency(result)
        candidate.backtest_result = result

    def _safe_metric(self, value: Any) -> float:
        """將 replay 指標轉成可比較的有限值。"""
        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return 0.0
        if not np.isfinite(numeric):
            return 0.0
        return numeric

    def _calculate_consistency(self, result: Dict[str, Any]) -> float:
        """以勝率與獲利因子估計一致性。"""
        win_rate = self._safe_metric(result.get('win_rate', 0.0))
        profit_factor = max(0.0, self._safe_metric(result.get('profit_factor', 0.0)))
        normalized_pf = min(profit_factor / 2.5, 1.0)
        return float((win_rate * 0.6) + (normalized_pf * 0.4))
    
    def _create_strategy(self, candidate: StrategyCandidate) -> BaseStrategy:
        """根據候選者配置創建策略實例"""
        strategy_map = {
            'trend_following': TrendFollowingStrategy,
            'swing_trading': SwingTradingStrategy,
            'mean_reversion': MeanReversionStrategy,
            'breakout_trading': BreakoutTradingStrategy,
            'direction_change': DirectionChangeStrategy,
            'pair_trading': PairTradingStrategy,
        }
        
        strategy_class = strategy_map.get(candidate.strategy_type)
        if not strategy_class:
            raise ValueError(f"未知策略類型: {candidate.strategy_type}")
        
        params = dict(candidate.parameters)
        init_sig = inspect.signature(strategy_class.__init__)
        init_kwargs = {
            key: value
            for key, value in params.items()
            if key in init_sig.parameters
        }
        strategy = cast(BaseStrategy, strategy_class(**init_kwargs))

        if candidate.strategy_type == 'trend_following':
            strategy.ema_periods = {
                'fast': int(params.get('ema_fast', strategy.ema_periods['fast'])),
                'medium': int(params.get('ema_medium', strategy.ema_periods['medium'])),
                'slow': int(params.get('ema_slow', strategy.ema_periods['slow'])),
            }
            strategy.min_adx_for_trend = int(params.get('min_adx_for_trend', strategy.min_adx_for_trend))
        elif candidate.strategy_type == 'swing_trading':
            strategy.swing_lookback = int(params.get('swing_lookback', strategy.swing_lookback))
            strategy.rsi_period = int(params.get('rsi_period', strategy.rsi_period))
            strategy.required_confirmations = int(params.get('required_confirmations', strategy.required_confirmations))
        elif candidate.strategy_type == 'mean_reversion':
            strategy.bb_period = int(params.get('bb_period', strategy.bb_period))
            strategy.bb_std_dev = float(params.get('bb_std_dev', strategy.bb_std_dev))
            strategy.z_lookback = int(params.get('z_lookback', strategy.z_lookback))
        elif candidate.strategy_type == 'breakout_trading':
            strategy.range_lookback = int(params.get('range_lookback', strategy.range_lookback))
            strategy.breakout_threshold = float(params.get('breakout_threshold', strategy.breakout_threshold))
            strategy.volume_threshold = float(params.get('volume_threshold', strategy.volume_threshold))
        elif candidate.strategy_type == 'direction_change':
            strategy.min_consecutive_dc = int(params.get('min_consecutive_dc', strategy.min_consecutive_dc))

        return strategy
    
    def rank_and_select(self) -> List[StrategyCandidate]:
        """排名並選擇優勝者"""
        # 按評分排序
        self.population.sort(key=lambda x: x.score, reverse=True)
        
        # 更新排名
        for rank, candidate in enumerate(self.population, 1):
            candidate.rank = rank
        
        # 計算存活數量
        survivors_count = max(2, int(len(self.population) * self.config.survival_rate))
        survivors = self.population[:survivors_count]
        
        # 更新最佳策略
        self.best_strategy = self.population[0]
        
        logger.info(f"🏆 第 {self.current_generation} 代排名完成:")
        logger.info("   - 前 3 名:")
        for i in range(min(3, len(self.population))):
            c = self.population[i]
            logger.info(f"     #{i+1}: {c.name} | 評分={c.score:.4f} | 夏普={c.sharpe_ratio:.2f} | 回報={c.total_return*100:.1f}%")
        
        logger.info(f"   - 晉級數量: {len(survivors)}/{len(self.population)}")
        
        return survivors
    
    def evolve_next_generation(self, survivors: List[StrategyCandidate]) -> List[StrategyCandidate]:
        """進化下一代 - 交叉、突變、繁殖"""
        next_generation = []
        
        # 保留精英（前幾名直接晉級）
        elite_count = max(1, int(len(survivors) * 0.2))
        elites = survivors[:elite_count]
        next_generation.extend(elites)
        
        logger.info(f"🧬 開始進化第 {self.current_generation + 1} 代...")
        logger.info(f"   - 精英保留: {len(elites)}")
        
        # 生成新個體直到達到種群數量
        while len(next_generation) < self.config.population_size:
            # 選擇父母（輪盤賭選擇）
            parent1 = self._select_parent(survivors)
            parent2 = self._select_parent(survivors)
            
            # 交叉繁殖
            if self.rng.random() < self.config.crossover_rate:
                child = self._crossover(parent1, parent2)
            else:
                child = self._clone(parent1)
            
            # 突變
            if self.rng.random() < self.config.mutation_rate:
                child = self._mutate(child)
            
            child.generation = self.current_generation + 1
            child.parent_ids = [parent1.id, parent2.id]
            next_generation.append(child)
        
        logger.info(f"   - 新一代數量: {len(next_generation)}")
        
        self.population = next_generation
        return next_generation
    
    def _select_parent(self, survivors: List[StrategyCandidate]) -> StrategyCandidate:
        """選擇父母（基於評分的輪盤賭）"""
        # 使用 softmax 轉換評分為概率
        scores = np.array([max(0, c.score) for c in survivors])
        if scores.sum() == 0:
            # 全是負分，均勻選擇
            probabilities = np.ones(len(survivors)) / len(survivors)
        else:
            probabilities = scores / scores.sum()
        
        selected_idx = self.rng.choice(len(survivors), p=probabilities)
        return survivors[selected_idx]
    
    def _crossover(self, parent1: StrategyCandidate, parent2: StrategyCandidate) -> StrategyCandidate:
        """交叉繁殖 - 混合兩個父母的參數"""
        # 如果策略類型相同，混合參數
        if parent1.strategy_type == parent2.strategy_type:
            child_params = {}
            for key in parent1.parameters:
                if key in parent2.parameters:
                    # 隨機選擇一個父母的參數值
                    if self.rng.random() < 0.5:
                        child_params[key] = parent1.parameters[key]
                    else:
                        child_params[key] = parent2.parameters[key]
                else:
                    child_params[key] = parent1.parameters[key]
            
            return StrategyCandidate(
                name=f"cross_{parent1.strategy_type}_{uuid.uuid4().hex[:6]}",
                strategy_type=parent1.strategy_type,
                parameters=child_params,
            )
        else:
            # 策略類型不同，隨機選一個
            parent = parent1 if self.rng.random() < 0.5 else parent2
            return self._clone(parent)
    
    def _clone(self, parent: StrategyCandidate) -> StrategyCandidate:
        """克隆父母"""
        return StrategyCandidate(
            name=f"clone_{parent.strategy_type}_{uuid.uuid4().hex[:6]}",
            strategy_type=parent.strategy_type,
            parameters=parent.parameters.copy(),
        )
    
    def _mutate(self, candidate: StrategyCandidate) -> StrategyCandidate:
        """突變 - 隨機修改參數"""
        mutated_params = candidate.parameters.copy()
        
        # 隨機選擇一個參數進行突變
        param_keys = list(mutated_params.keys())
        if not param_keys:
            return candidate
        
        mutate_key = self.rng.choice(param_keys)
        original_value = mutated_params[mutate_key]
        
        # 根據參數類型進行突變
        if isinstance(original_value, int):
            # 整數：加減隨機值
            delta = int(self.rng.integers(-5, 6))
            mutated_params[mutate_key] = max(1, original_value + delta)
        
        elif isinstance(original_value, float):
            # 浮點數：乘以隨機因子
            factor = float(self.rng.uniform(0.8, 1.2))
            mutated_params[mutate_key] = original_value * factor
        
        candidate.parameters = mutated_params
        candidate.name = f"mutant_{candidate.strategy_type}_{uuid.uuid4().hex[:6]}"
        
        return candidate
    
    def run(self) -> StrategyCandidate:
        """運行完整的進化過程"""
        logger.info("🚀 策略競技場開始運行...")
        
        # 初始化種群
        self.initialize_population()
        
        # 進化循環
        for gen in range(self.config.max_generations):
            self.current_generation = gen
            
            logger.info(f"\n{'='*60}")
            logger.info(f"第 {gen + 1}/{self.config.max_generations} 代")
            logger.info(f"{'='*60}")
            
            # 評估當前種群
            self.evaluate_population()
            
            # 排名並選擇優勝者
            survivors = self.rank_and_select()
            
            # 記錄歷史
            self._record_generation()
            
            # 保存中間結果
            if (gen + 1) % 5 == 0 or gen == self.config.max_generations - 1:
                self.save_results()
            
            # 進化下一代（最後一代不需要）
            if gen < self.config.max_generations - 1:
                self.evolve_next_generation(survivors)
        
        logger.info("\n🎉 策略競技場完成！")
        
        # 類型守衛：確保 best_strategy 不為 None
        if self.best_strategy is None:
            raise RuntimeError("競技場運行完成但未找到最優策略！")
        
        logger.info(f"🏆 最優策略: {self.best_strategy.name}")
        logger.info(f"   - 評分: {self.best_strategy.score:.4f}")
        logger.info(f"   - 夏普比率: {self.best_strategy.sharpe_ratio:.2f}")
        logger.info(f"   - 總回報: {self.best_strategy.total_return*100:.1f}%")
        
        return self.best_strategy
    
    def _record_generation(self):
        """記錄本代歷史"""
        gen_stats = {
            'generation': self.current_generation,
            'timestamp': datetime.now().isoformat(),
            'best_score': self.population[0].score,
            'avg_score': np.mean([c.score for c in self.population]),
            'best_sharpe': self.population[0].sharpe_ratio,
            'best_return': self.population[0].total_return,
            'top_3': [
                {
                    'name': c.name,
                    'type': c.strategy_type,
                    'score': c.score,
                    'sharpe': c.sharpe_ratio,
                    'return': c.total_return,
                }
                for c in self.population[:3]
            ]
        }
        self.history.append(gen_stats)
    
    def save_results(self):
        """保存結果"""
        output_dir = Path(self.config.output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存最優策略（如果存在）
        if self.best_strategy is not None:
            best_file = output_dir / f"best_strategy_{timestamp}.json"
            with open(best_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(self.best_strategy), f, indent=2, ensure_ascii=False, default=str)
        
        # 保存歷史
        history_file = output_dir / f"evolution_history_{timestamp}.json"
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
        
        # 保存當前種群
        population_file = output_dir / f"population_gen{self.current_generation}_{timestamp}.json"
        with open(population_file, 'w', encoding='utf-8') as f:
            population_data = [asdict(c) for c in self.population]
            json.dump(population_data, f, indent=2, ensure_ascii=False, default=str)
        
        logger.info(f"💾 結果已保存到 {output_dir}")


# ============================================================================
# 使用示例
# ============================================================================

def demo():
    """演示如何使用策略競技場"""
    
    # 配置競技場
    config = ArenaConfig(
        symbol="ETHUSDT",
        interval="1h",
        start_date="2024-01-01",
        end_date="2024-12-31",
        population_size=20,
        max_generations=10,
        survival_rate=0.3,
        use_multiprocessing=False,  # 單進程（避免序列化問題）
    )
    
    # 創建競技場
    arena = StrategyArena(config)
    
    # 運行進化
    best_strategy = arena.run()
    
    print("\n最優策略配置:")
    print(json.dumps(asdict(best_strategy), indent=2, default=str))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    demo()
