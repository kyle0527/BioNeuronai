"""
AI 自我進化系統 - 基因演算法養蠱場 (Evolutionary Battle Royale System)
==========================================================================

核心理念：優勝劣汰 + 基因演算法
不再是簡單的「參數調整」，而是「策略生物競爭」

核心機制：
1. 策略族群管理 (Population Management)
   - 每個策略實例是一隻生物
   - 具備獨特的「基因」（參數配置）
   
2. 生存競爭 (Survival of the Fittest)
   - 每日回測評估績效
   - 最差 20% 直接淘汰（死亡）
   - 最優 20% 進行繁衍（交配 + 突變）
   
3. 基因遺傳與突變 (Genetic Inheritance & Mutation)
   - 繁衍：混合優秀策略的參數
   - 突變：隨機微調參數，創造新可能
   - 多樣性：保持族群基因多樣性

4. 適者生存 (Adaptive Evolution)
   - 只有適應當前市場的策略能存活
   - 持續演化，永遠保持競爭力
   
使用場景：
- 每日收盤後自動運行
- 30 天歷史數據回測
- 動態調整策略池
- 實盤只使用存活者
"""

import torch
import json
import random
import copy
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any, Union, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# 策略基因定義 (Strategy Gene)
# ============================================================================

@dataclass
class StrategyGene:
    """
    策略基因 - 定義一個策略實例的所有參數
    這就是策略的「DNA」
    """
    # 基因ID
    gene_id: str = field(default_factory=lambda: f"GENE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}")
    
    # 策略類型
    strategy_type: str = "trend_following"  # trend_following, mean_reversion, breakout, swing
    
    # 技術指標參數（基因編碼）
    ma_fast: int = 20  # 快速均線
    ma_slow: int = 50  # 慢速均線
    rsi_period: int = 14  # RSI 周期
    rsi_overbought: float = 70.0  # RSI 超買
    rsi_oversold: float = 30.0  # RSI 超賣
    atr_period: int = 14  # ATR 周期
    bb_period: int = 20  # 布林帶周期
    bb_std: float = 2.0  # 布林帶標準差
    
    # 風險管理參數
    stop_loss_atr_multiplier: float = 2.0  # 止損倍數
    take_profit_atr_multiplier: float = 3.0  # 止盈倍數
    position_size_pct: float = 0.02  # 倉位比例 (2%)
    
    # 進場條件參數
    min_confirmations: int = 2  # 最少確認信號數
    confirmation_threshold: float = 0.6  # 確認閾值
    
    # 績效記錄
    fitness_score: float = 0.0  # 適應度評分
    total_trades: int = 0
    win_rate: float = 0.5
    profit_factor: float = 1.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    total_return: float = 0.0
    
    # 血統記錄
    generation: int = 0  # 第幾代
    parent_ids: List[str] = field(default_factory=list)  # 父母基因ID
    birth_time: datetime = field(default_factory=datetime.now)
    is_mutant: bool = False  # 是否為突變體
    
    def clone(self) -> 'StrategyGene':
        """克隆基因"""
        new_gene = copy.deepcopy(self)
        new_gene.gene_id = f"GENE_{datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000, 9999)}"
        new_gene.birth_time = datetime.now()
        return new_gene
    
    def to_dict(self) -> Dict:
        """轉換為字典"""
        d = asdict(self)
        d['birth_time'] = self.birth_time.isoformat()
        return d


class FitnessMetric(Enum):
    """適應度計算方式"""
    SHARPE_RATIO = "sharpe_ratio"  # 夏普比率優先
    PROFIT_FACTOR = "profit_factor"  # 盈虧比優先
    WIN_RATE = "win_rate"  # 勝率優先
    TOTAL_RETURN = "total_return"  # 總收益優先
    BALANCED = "balanced"  # 平衡（綜合評分）


@dataclass
class BacktestResult:
    """回測結果"""
    gene_id: str
    total_return: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    fitness_score: float
    tested_at: datetime = field(default_factory=datetime.now)


    tested_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# 演化引擎 (Evolution Engine)
# ============================================================================

class EvolutionEngine:
    """
    演化引擎 - 管理策略族群的生存競爭
    
    核心流程：
    1. 評估（Evaluation）：回測所有策略
    2. 選擇（Selection）：淘汰弱者，選出強者
    3. 繁衍（Reproduction）：交配生成新策略
    4. 突變（Mutation）：隨機變異創造多樣性
    5. 更新（Update）：更新族群
    """
    
    def __init__(
        self,
        population_size: int = 100,
        survival_rate: float = 0.20,  # 存活率 20%
        reproduction_rate: float = 0.20,  # 繁衍率 20%
        mutation_rate: float = 0.15,  # 突變率 15%
        elite_rate: float = 0.10,  # 精英率 10%（直接保留）
        fitness_metric: FitnessMetric = FitnessMetric.BALANCED,
        data_dir: str = "./evolution_data",
    ):
        self.population_size = population_size
        self.survival_rate = survival_rate
        self.reproduction_rate = reproduction_rate
        self.mutation_rate = mutation_rate
        self.elite_rate = elite_rate
        self.fitness_metric = fitness_metric
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # 策略族群
        self.population: List[StrategyGene] = []
        self.generation = 0
        
        # 歷史記錄
        self.history: List[Dict] = []
        self.best_genes: List[StrategyGene] = []
        
        # 回測結果緩存
        self.backtest_results: Dict[str, BacktestResult] = {}
        
        logger.info(f"🧬 演化引擎初始化: 族群={population_size}, 存活率={survival_rate}, 突變率={mutation_rate}")
    
    def initialize_population(self, strategy_types: Optional[List[str]] = None):
        """
        初始化族群 - 創建第一代策略
        
        Args:
            strategy_types: 策略類型列表，如 ['trend_following', 'mean_reversion']
        """
        if strategy_types is None:
            strategy_types = ['trend_following', 'mean_reversion', 'breakout', 'swing']
        
        self.population = []
        strategies_per_type = self.population_size // len(strategy_types)
        
        for strategy_type in strategy_types:
            for _ in range(strategies_per_type):
                gene = self._create_random_gene(strategy_type, generation=0)
                self.population.append(gene)
        
        # 補齊到目標數量
        while len(self.population) < self.population_size:
            random_type = random.choice(strategy_types)
            gene = self._create_random_gene(random_type, generation=0)
            self.population.append(gene)
        
        logger.info(f"✅ 族群初始化完成: {len(self.population)} 個策略")
        self._save_population()
    
    def _create_random_gene(self, strategy_type: str, generation: int) -> StrategyGene:
        """創建隨機基因"""
        return StrategyGene(
            strategy_type=strategy_type,
            ma_fast=random.randint(5, 30),
            ma_slow=random.randint(40, 100),
            rsi_period=random.randint(7, 21),
            rsi_overbought=random.uniform(65, 80),
            rsi_oversold=random.uniform(20, 35),
            atr_period=random.randint(10, 20),
            bb_period=random.randint(15, 25),
            bb_std=random.uniform(1.5, 2.5),
            stop_loss_atr_multiplier=random.uniform(1.5, 3.0),
            take_profit_atr_multiplier=random.uniform(2.0, 5.0),
            position_size_pct=random.uniform(0.01, 0.05),
            min_confirmations=random.randint(1, 3),
            confirmation_threshold=random.uniform(0.5, 0.8),
            generation=generation,
        )
    
    def evaluate_population(
        self,
        backtest_func: Callable,
        market_data: Any,
    ) -> List[BacktestResult]:
        """
        評估族群 - 對所有策略進行回測
        
        Args:
            backtest_func: 回測函數，接收 (gene, market_data) 返回 BacktestResult
            market_data: 市場數據
            
        Returns:
            回測結果列表
        """
        import time
        eval_start = time.time()
        logger.info(f"📊 開始評估第 {self.generation} 代族群 ({len(self.population)} 個策略)...")
        logger.info(f"=" * 80)
        
        results = []
        for i, gene in enumerate(self.population):
            logger.info(f"\n[{i+1}/{len(self.population)}] 策略評估中...")
            try:
                # 執行回測
                result = backtest_func(gene, market_data)
                
                # 計算適應度
                fitness = self._calculate_fitness(result)
                result.fitness_score = fitness
                gene.fitness_score = fitness
                
                # 更新基因績效
                gene.total_trades = result.total_trades
                gene.win_rate = result.win_rate
                gene.profit_factor = result.profit_factor
                gene.sharpe_ratio = result.sharpe_ratio
                gene.max_drawdown = result.max_drawdown
                gene.total_return = result.total_return
                
                results.append(result)
                self.backtest_results[gene.gene_id] = result
                
                if (i + 1) % 10 == 0:
                    logger.info(f"  進度: {i+1}/{len(self.population)}")
                
            except Exception as e:
                logger.error(f"❌ 評估失敗 {gene.gene_id}: {e}")
                # 失敗的策略給予最低適應度
                gene.fitness_score = -999
        
        # 排序：適應度從高到低
        results.sort(key=lambda x: x.fitness_score, reverse=True)
        
        eval_elapsed = time.time() - eval_start
        logger.info(f"\n" + "=" * 80)
        logger.info(f"✅ 評估完成! 最佳適應度: {results[0].fitness_score:.4f} | 總耗時: {eval_elapsed:.2f}s")
        
        trades_count = sum(1 for r in results if r.total_trades > 0)
        logger.info(f"   平均每策略: {eval_elapsed/len(self.population):.2f}s | 有交易策略: {trades_count}/{len(results)}")
        return results
    
    def _calculate_fitness(self, result: BacktestResult) -> float:
        """
        計算適應度分數
        
        根據不同的適應度指標計算綜合評分
        """
        if self.fitness_metric == FitnessMetric.SHARPE_RATIO:
            return result.sharpe_ratio
        
        elif self.fitness_metric == FitnessMetric.PROFIT_FACTOR:
            return result.profit_factor
        
        elif self.fitness_metric == FitnessMetric.WIN_RATE:
            return result.win_rate
        
        elif self.fitness_metric == FitnessMetric.TOTAL_RETURN:
            return result.total_return
        
        else:  # BALANCED - 綜合評分
            # 正規化各指標並加權
            sharpe_score = max(0, min(result.sharpe_ratio / 3.0, 1.0))  # 0-3 映射到 0-1
            pf_score = max(0, min(result.profit_factor / 3.0, 1.0))  # 0-3 映射到 0-1
            wr_score = result.win_rate  # 已經是 0-1
            return_score = max(0, min(result.total_return / 0.5, 1.0))  # 0-50% 映射到 0-1
            dd_penalty = max(0, 1 - abs(result.max_drawdown) / 0.3)  # 回撤懲罰
            
            # 加權平均
            fitness = (
                sharpe_score * 0.25 +
                pf_score * 0.25 +
                wr_score * 0.20 +
                return_score * 0.20 +
                dd_penalty * 0.10
            )
            
            return fitness
    
    def select_survivors(self) -> Tuple[List[StrategyGene], List[StrategyGene]]:
        """
        選擇存活者 - 實施優勝劣汰
        
        Returns:
            (存活者, 被淘汰者)
        """
        # 按適應度排序
        self.population.sort(key=lambda g: g.fitness_score, reverse=True)
        
        # 精英直接保留（最優的 elite_rate%）
        elite_count = max(1, int(self.population_size * self.elite_rate))
        elites = self.population[:elite_count]
        
        # 存活者（前 survival_rate%）
        survivor_count = max(elite_count, int(self.population_size * self.survival_rate))
        survivors = self.population[:survivor_count]
        
        # 被淘汰者
        eliminated = self.population[survivor_count:]
        
        logger.info(f"⚔️  自然選擇: 精英={len(elites)}, 存活={len(survivors)}, 淘汰={len(eliminated)}")
        logger.info(f"   最佳適應度: {survivors[0].fitness_score:.4f}")
        logger.info(f"   最差適應度: {eliminated[-1].fitness_score if eliminated else 'N/A'}")
        
        return survivors, eliminated
    
    def reproduce(self, survivors: List[StrategyGene]) -> List[StrategyGene]:
        """
        繁衍新策略 - 交配 + 突變
        
        Args:
            survivors: 存活的策略
            
        Returns:
            新生成的策略列表
        """
        offspring = []
        
        # 需要生成的新策略數量
        needed = self.population_size - len(survivors)
        
        # 繁衍者（表現最好的 reproduction_rate%）
        breeder_count = max(2, int(len(survivors) * self.reproduction_rate / self.survival_rate))
        breeders = survivors[:breeder_count]
        
        logger.info(f"🧬 開始繁衍: 繁衍者={len(breeders)}, 需生成={needed}")
        
        for _ in range(needed):
            # 隨機選擇兩個父母
            parent1 = random.choice(breeders)
            parent2 = random.choice(breeders)
            
            # 交配生成子代
            child = self._crossover(parent1, parent2)
            
            # 突變
            if random.random() < self.mutation_rate:
                child = self._mutate(child)
                child.is_mutant = True
            
            offspring.append(child)
        
        logger.info(f"✅ 繁衍完成: 生成 {len(offspring)} 個新策略")
        return offspring
    
    def _crossover(self, parent1: StrategyGene, parent2: StrategyGene) -> StrategyGene:
        """
        交配 - 混合兩個父母的基因
        """
        child = StrategyGene(
            strategy_type=random.choice([parent1.strategy_type, parent2.strategy_type]),
            generation=self.generation + 1,
            parent_ids=[parent1.gene_id, parent2.gene_id],
        )
        
        # 參數混合（隨機從兩個父母中選擇）
        child.ma_fast = random.choice([parent1.ma_fast, parent2.ma_fast])
        child.ma_slow = random.choice([parent1.ma_slow, parent2.ma_slow])
        child.rsi_period = random.choice([parent1.rsi_period, parent2.rsi_period])
        child.rsi_overbought = random.choice([parent1.rsi_overbought, parent2.rsi_overbought])
        child.rsi_oversold = random.choice([parent1.rsi_oversold, parent2.rsi_oversold])
        child.atr_period = random.choice([parent1.atr_period, parent2.atr_period])
        child.bb_period = random.choice([parent1.bb_period, parent2.bb_period])
        child.bb_std = random.choice([parent1.bb_std, parent2.bb_std])
        child.stop_loss_atr_multiplier = random.choice([parent1.stop_loss_atr_multiplier, parent2.stop_loss_atr_multiplier])
        child.take_profit_atr_multiplier = random.choice([parent1.take_profit_atr_multiplier, parent2.take_profit_atr_multiplier])
        child.position_size_pct = random.choice([parent1.position_size_pct, parent2.position_size_pct])
        child.min_confirmations = random.choice([parent1.min_confirmations, parent2.min_confirmations])
        child.confirmation_threshold = random.choice([parent1.confirmation_threshold, parent2.confirmation_threshold])
        
        return child
    
    def _mutate(self, gene: StrategyGene) -> StrategyGene:
        """
        突變 - 隨機改變某些參數
        """
        # 隨機選擇 1-3 個參數進行突變
        mutation_count = random.randint(1, 3)
        params = ['ma_fast', 'ma_slow', 'rsi_period', 'rsi_overbought', 'rsi_oversold',
                  'atr_period', 'bb_period', 'bb_std', 'stop_loss_atr_multiplier',
                  'take_profit_atr_multiplier', 'position_size_pct']
        
        for _ in range(mutation_count):
            param = random.choice(params)
            
            if param == 'ma_fast':
                gene.ma_fast = max(5, min(30, gene.ma_fast + random.randint(-5, 5)))
            elif param == 'ma_slow':
                gene.ma_slow = max(40, min(100, gene.ma_slow + random.randint(-10, 10)))
            elif param == 'rsi_period':
                gene.rsi_period = max(7, min(21, gene.rsi_period + random.randint(-3, 3)))
            elif param == 'rsi_overbought':
                gene.rsi_overbought = max(65, min(80, gene.rsi_overbought + random.uniform(-5, 5)))
            elif param == 'rsi_oversold':
                gene.rsi_oversold = max(20, min(35, gene.rsi_oversold + random.uniform(-5, 5)))
            elif param == 'atr_period':
                gene.atr_period = max(10, min(20, gene.atr_period + random.randint(-3, 3)))
            elif param == 'bb_period':
                gene.bb_period = max(15, min(25, gene.bb_period + random.randint(-3, 3)))
            elif param == 'bb_std':
                gene.bb_std = max(1.5, min(2.5, gene.bb_std + random.uniform(-0.3, 0.3)))
            elif param == 'stop_loss_atr_multiplier':
                gene.stop_loss_atr_multiplier = max(1.5, min(3.0, gene.stop_loss_atr_multiplier + random.uniform(-0.3, 0.3)))
            elif param == 'take_profit_atr_multiplier':
                gene.take_profit_atr_multiplier = max(2.0, min(5.0, gene.take_profit_atr_multiplier + random.uniform(-0.5, 0.5)))
            elif param == 'position_size_pct':
                gene.position_size_pct = max(0.01, min(0.05, gene.position_size_pct + random.uniform(-0.01, 0.01)))
        
        return gene
    
    def evolve(
        self,
        backtest_func: Callable,
        market_data: Any,
    ) -> Dict[str, Any]:
        """
        執行一代演化
        
        完整流程：評估 → 選擇 → 繁衍 → 更新
        
        Returns:
            演化統計信息
        """
        logger.info(f"🔄 ===== 第 {self.generation} 代演化開始 =====")
        
        # 1. 評估
        self.evaluate_population(backtest_func, market_data)
        
        # 2. 選擇
        survivors, eliminated = self.select_survivors()
        
        # 3. 繁衍
        offspring = self.reproduce(survivors)
        
        # 4. 更新族群
        self.population = survivors + offspring
        
        # 5. 記錄歷史
        best_gene = survivors[0]
        self.best_genes.append(best_gene.clone())
        
        generation_stats = {
            'generation': self.generation,
            'best_fitness': best_gene.fitness_score,
            'avg_fitness': np.mean([g.fitness_score for g in self.population]),
            'best_gene_id': best_gene.gene_id,
            'best_strategy_type': best_gene.strategy_type,
            'survivors': len(survivors),
            'eliminated': len(eliminated),
            'offspring': len(offspring),
            'timestamp': datetime.now().isoformat(),
        }
        
        self.history.append(generation_stats)
        
        # 6. 保存狀態
        self._save_population()
        self._save_history()
        
        self.generation += 1
        
        logger.info(f"✅ ===== 第 {generation_stats['generation']} 代演化完成 =====")
        logger.info(f"   最佳適應度: {generation_stats['best_fitness']:.4f}")
        logger.info(f"   平均適應度: {generation_stats['avg_fitness']:.4f}")
        
        return generation_stats
    
    def get_best_strategies(self, top_n: int = 10) -> List[StrategyGene]:
        """獲取最優策略"""
        sorted_pop = sorted(self.population, key=lambda g: g.fitness_score, reverse=True)
        return sorted_pop[:top_n]
    
    def get_strategy_by_type(self, strategy_type: str, top_n: int = 5) -> List[StrategyGene]:
        """獲取特定類型的最優策略"""
        typed = [g for g in self.population if g.strategy_type == strategy_type]
        sorted_typed = sorted(typed, key=lambda g: g.fitness_score, reverse=True)
        return sorted_typed[:top_n]
    
    def _save_population(self):
        """保存族群"""
        filepath = self.data_dir / f"population_gen{self.generation}.json"
        data = {
            'generation': self.generation,
            'population_size': len(self.population),
            'genes': [g.to_dict() for g in self.population],
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _save_history(self):
        """保存演化歷史"""
        filepath = self.data_dir / "evolution_history.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
    
    def load_population(self, filepath: str):
        """載入族群"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.generation = data['generation']
        self.population = []
        
        for gene_data in data['genes']:
            gene_data['birth_time'] = datetime.fromisoformat(gene_data['birth_time'])
            gene = StrategyGene(**gene_data)
            self.population.append(gene)
        
        logger.info(f"📂 載入族群: 第 {self.generation} 代, {len(self.population)} 個策略")


# ============================================================================
# 族群管理器 (Population Manager)
# ============================================================================

class PopulationManager:
    """
    族群管理器 - 高層接口
    
    提供簡單的接口來管理整個演化過程
    """
    
    def __init__(
        self,
        evolution_engine: EvolutionEngine,
        backtest_engine: Any,
    ):
        self.evolution_engine = evolution_engine
        self.backtest_engine = backtest_engine
        
        logger.info("🎮 族群管理器初始化完成")
    
    def run_daily_evolution(self, market_data: Any, days: int = 30):
        """
        每日演化任務
        
        Args:
            market_data: 過去 N 天的市場數據
            days: 回測天數
        """
        logger.info(f"🌅 開始每日演化任務（回測期: {days} 天）")
        
        # 執行一代演化
        stats = self.evolution_engine.evolve(
            backtest_func=self._backtest_wrapper,
            market_data=market_data,
        )
        
        # 生成報告
        self._generate_report(stats)
        
        return stats
    
    def _backtest_wrapper(self, gene: StrategyGene, market_data: Any) -> BacktestResult:
        """回測包裝函數 - 使用真實的技術指標策略回測"""
        import time
        start_time = time.time()
        
        try:
            # 使用傳入的 MockBinanceConnector
            from ..backtest import MockBinanceConnector
            
            if not isinstance(market_data, dict) or 'connector' not in market_data:
                raise ValueError("market_data 必須包含 'connector' (MockBinanceConnector 實例)")
            
            connector = market_data['connector']
            
            logger.info(f"   🧬 測試策略 {gene.gene_id[-8:]}: {gene.strategy_type} | MA({gene.ma_fast},{gene.ma_slow}) RSI({gene.rsi_period})")
            
            # 重置 connector 到起始狀態
            connector.data_stream.state.current_index = 0
            connector.virtual_account.reset()
            
            # 根據 gene 參數執行策略
            trades = []
            positions = {}
            
            while connector.next_tick():
                bar = connector._current_bar
                if not bar:
                    continue
                
                symbol = bar.symbol
                price = bar.close
                
                # 獲取足夠的歷史數據計算指標
                klines = connector.data_stream.get_klines_until_now(max(gene.ma_slow, gene.bb_period) + 10)
                if len(klines) < gene.ma_slow:
                    continue
                
                # 計算技術指標
                closes = [k['close'] for k in klines]
                
                # 均線
                ma_fast = sum(closes[-gene.ma_fast:]) / gene.ma_fast
                ma_slow = sum(closes[-gene.ma_slow:]) / gene.ma_slow
                
                # RSI
                gains = []
                losses = []
                for i in range(1, min(gene.rsi_period + 1, len(closes))):
                    change = closes[-i] - closes[-(i+1)]
                    if change > 0:
                        gains.append(change)
                        losses.append(0)
                    else:
                        gains.append(0)
                        losses.append(abs(change))
                
                avg_gain = sum(gains) / len(gains) if gains else 0
                avg_loss = sum(losses) / len(losses) if losses else 0
                rs = avg_gain / avg_loss if avg_loss > 0 else 100
                rsi = 100 - (100 / (1 + rs))
                
                # 檢查持倉
                account = connector.get_account_info()
                pos = None
                for p in account["positions"]:
                    if p["symbol"] == symbol and abs(p["positionAmt"]) > 0:
                        pos = p
                        break
                
                # 策略信號
                signal = None
                
                if gene.strategy_type == "trend_following":
                    if ma_fast > ma_slow and rsi < gene.rsi_overbought:
                        signal = "long"
                    elif ma_fast < ma_slow and rsi > gene.rsi_oversold:
                        signal = "short"
                        
                elif gene.strategy_type == "mean_reversion":
                    if rsi < gene.rsi_oversold:
                        signal = "long"
                    elif rsi > gene.rsi_overbought:
                        signal = "short"
                
                # 執行交易
                if signal == "long" and (not pos or float(pos["positionAmt"]) <= 0):
                    if pos and float(pos["positionAmt"]) < 0:
                        connector.place_order(symbol, "BUY", "MARKET", abs(float(pos["positionAmt"])))
                    order = connector.place_order(symbol, "BUY", "MARKET", gene.position_size_pct)
                    if order:
                        trades.append({'type': 'long', 'price': price, 'size': gene.position_size_pct})
                        
                elif signal == "short" and (not pos or float(pos["positionAmt"]) >= 0):
                    if pos and float(pos["positionAmt"]) > 0:
                        connector.place_order(symbol, "SELL", "MARKET", float(pos["positionAmt"]))
                    order = connector.place_order(symbol, "SELL", "MARKET", gene.position_size_pct)
                    if order:
                        trades.append({'type': 'short', 'price': price, 'size': gene.position_size_pct})
            
            # 平所有倉位
            account = connector.get_account_info()
            for p in account["positions"]:
                if abs(p["positionAmt"]) > 0:
                    side = "SELL" if float(p["positionAmt"]) > 0 else "BUY"
                    connector.place_order(p["symbol"], side, "MARKET", abs(float(p["positionAmt"])))
            
            # 獲取統計
            stats = connector.virtual_account.get_stats()
            elapsed = time.time() - start_time
            
            logger.info(f"      ✅ 完成: 交易{stats['total_trades']}筆 | 回報{stats['total_return']:.2f}% | 勝率{stats['win_rate']:.1f}% | 用時{elapsed:.2f}s")
            
            return BacktestResult(
                gene_id=gene.gene_id,
                total_return=stats['total_return'] / 100.0,
                win_rate=stats['win_rate'] / 100.0,
                profit_factor=stats.get('profit_factor', 1.0),
                sharpe_ratio=stats.get('sharpe_ratio', 0.0),
                max_drawdown=stats.get('max_drawdown', 0.0) / 100.0,
                total_trades=stats['total_trades'],
                fitness_score=0.0,
            )
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"      ❌ 回測失敗 ({gene.gene_id[-8:]}): {e} | 用時{elapsed:.2f}s")
            return BacktestResult(
                gene_id=gene.gene_id,
                total_return=-0.5,
                win_rate=0.0,
                profit_factor=0.0,
                sharpe_ratio=-5.0,
                max_drawdown=1.0,
                total_trades=0,
                fitness_score=-999,
            )
    
    def _generate_report(self, stats: Dict):
        """生成演化報告"""
        logger.info("📊 ===== 演化報告 =====")
        logger.info(f"   第 {stats['generation']} 代")
        logger.info(f"   最佳適應度: {stats['best_fitness']:.4f}")
        logger.info(f"   平均適應度: {stats['avg_fitness']:.4f}")
        logger.info(f"   最佳策略: {stats['best_strategy_type']} ({stats['best_gene_id']})")
        logger.info(f"   存活: {stats['survivors']}, 淘汰: {stats['eliminated']}, 新生: {stats['offspring']}")
    
    def get_production_strategies(self, top_n: int = 10) -> List[StrategyGene]:
        """
        獲取生產環境策略
        
        只有最優秀的策略才能用於實盤交易
        """
        return self.evolution_engine.get_best_strategies(top_n)


# ============================================================================
# 自我改進系統 (Compatibility Layer)
# ============================================================================

class SelfImprovementSystem:
    """AI 自我改進系統 - 基因演算法版本（兼容舊接口）"""
    
    def __init__(self, data_dir: str = "./evolution_data"):
        # 創建演化引擎
        self.evolution_engine = EvolutionEngine(data_dir=data_dir)
        self.population_manager = PopulationManager(
            evolution_engine=self.evolution_engine,
            backtest_engine=None,  # 需要外部提供
        )
        
        self.data_dir = Path(data_dir)
        logger.info("🧠 自我改進系統初始化完成（演化模式）")
    
    def initialize(self, strategy_types: Optional[List[str]] = None):
        """初始化策略族群"""
        self.evolution_engine.initialize_population(strategy_types)
    
    def evolve_once(self, market_data: Any) -> Dict:
        """執行一次演化"""
        return self.population_manager.run_daily_evolution(market_data)
    
    def get_best_strategies(self, top_n: int = 10) -> List[StrategyGene]:
        """獲取最優策略"""
        return self.evolution_engine.get_best_strategies(top_n)
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return {
            "generation": self.evolution_engine.generation,
            "population_size": len(self.evolution_engine.population),
            "best_fitness": self.evolution_engine.population[0].fitness_score if self.evolution_engine.population else 0,
            "history_length": len(self.evolution_engine.history),
        }


def create_self_improvement_system(data_dir: str = "./evolution_data") -> SelfImprovementSystem:
    """創建自我改進系統"""
    return SelfImprovementSystem(data_dir)


# ============================================================================
# 使用示例和測試
# ============================================================================

if __name__ == "__main__":
    from pathlib import Path
    
    print("=" * 80)
    print("🧬 基因演算法養蠱場 - 策略演化系統 (真實回測)")
    print("=" * 80)
    
    # 導入真實的回測引擎
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from bioneuronai.backtest import MockBinanceConnector
    
    # 創建真實數據連接器
    print("\n準備真實歷史數據...")
    data_dir = Path(__file__).parent.parent.parent.parent / "training_data" / "data_downloads" / "binance_historical"
    
    connector = MockBinanceConnector(
        symbol="ETHUSDT",
        interval="15m",
        start_date="2026-01-10",
        end_date="2026-01-15",
        initial_balance=10000,
        data_dir=str(data_dir)
    )
    
    market_data = {'connector': connector}
    print(f"✅ 載入 {connector.data_stream.state.total_bars} 根 K 線")
    
    # 初始化系統
    system = create_self_improvement_system("./test_evolution")
    
    # 初始化族群
    print("\n1️⃣  初始化策略族群...")
    system.initialize(strategy_types=['trend_following', 'mean_reversion'])
    
    # 真實演化
    print("\n2️⃣  開始真實策略演化...")
    for gen in range(3):
        print(f"\n{'='*60}")
        print(f"第 {gen} 代演化 - 真實歷史數據回測")
        print(f"{'='*60}")
        
        try:
            stats = system.evolve_once(market_data)
            
            print(f"\n✅ 第 {gen} 代演化完成!")
            print(f"   最佳回報率: {stats['best_fitness']*100:.2f}%")
            print(f"   平均回報率: {stats['avg_fitness']*100:.2f}%")
            print(f"   最佳策略: {stats['best_strategy_type']}")
            print(f"   存活: {stats['survivors']}, 淘汰: {stats['eliminated']}, 新生: {stats['offspring']}")
            
        except Exception as e:
            import traceback
            print(f"❌ 演化失敗: {e}")
            traceback.print_exc()
            break
    
    # 獲取最優策略
    print("\n3️⃣  獲取最優策略...")
    best_strategies = system.get_best_strategies(top_n=5)
    
    print("\n🏆 Top 5 真實回測策略:")
    print(f"{'='*80}")
    for i, gene in enumerate(best_strategies, 1):
        print(f"\n{i}. {gene.strategy_type.upper()}")
        print(f"   適應度分數: {gene.fitness_score:.4f}")
        print(f"   參數: MA({gene.ma_fast},{gene.ma_slow}), RSI({gene.rsi_period}, {gene.rsi_overbought:.0f}/{gene.rsi_oversold:.0f})")
        print(f"   績效: 總回報={gene.total_return*100:.2f}%, 勝率={gene.win_rate:.2%}, PF={gene.profit_factor:.2f}")
        print(f"   風險: 最大回撤={gene.max_drawdown*100:.2f}%, Sharpe={gene.sharpe_ratio:.2f}")
        print(f"   交易: {gene.total_trades} 筆")
    
    # 統計信息
    print("\n4️⃣  系統統計...")
    stats = system.get_statistics()
    for key, value in stats.items():
        print(f"   • {key}: {value}")
    
    print("\n" + "=" * 80)
    print("🎉 真實策略演化系統測試完成!")
    print("=" * 80)

