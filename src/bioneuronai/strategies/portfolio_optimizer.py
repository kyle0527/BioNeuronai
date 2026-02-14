"""
策略組合優化器 (Strategy Portfolio Optimizer)
============================================

核心理念：使用遺傳算法找出最優策略組合
不僅優化單個策略參數，更重要的是找出策略之間的最佳組合方式

優化目標：
1. 找出每個階段的最優策略
2. 優化策略之間的權重分配
3. 發現策略組合的協同效應
4. 自動調整策略切換規則

遺傳算法流程：
1. 初始化：生成多個策略組合基因
2. 評估：回測每個組合的性能
3. 選擇：保留高性能組合
4. 交叉：混合優秀組合的基因
5. 突變：隨機修改部分參數
6. 迭代：重複2-5直到收斂

基因編碼：
[
    開盤策略類型, 開盤策略權重, 開盤參數1, 開盤參數2, ...,
    盤中策略類型, 盤中策略權重, 盤中參數1, 盤中參數2, ...,
    收盤策略類型, 收盤策略權重, 收盤參數1, 收盤參數2, ...,
    切換閾值1, 切換閾值2, ...
]

創建日期：2026-02-14
"""

import logging
import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np
import copy

from .phase_router import TradingPhase, TradingPhaseRouter, PhaseConfig
from .strategy_arena import StrategyArena, ArenaConfig, StrategyCandidate

logger = logging.getLogger(__name__)


class OptimizationObjective(Enum):
    """優化目標"""
    MAXIMIZE_RETURN = "maximize_return"           # 最大化回報
    MAXIMIZE_SHARPE = "maximize_sharpe"           # 最大化夏普比率
    MINIMIZE_DRAWDOWN = "minimize_drawdown"       # 最小化回撤
    MAXIMIZE_CONSISTENCY = "maximize_consistency" # 最大化穩定性
    BALANCED = "balanced"                         # 綜合平衡


@dataclass
class StrategyGene:
    """
    策略基因 - 單個階段的策略配置
    """
    phase: TradingPhase
    strategy_type: str  # 'trend_following', 'mean_reversion', etc.
    strategy_weight: float = 1.0  # 0-1
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # 階段行為參數
    position_size_multiplier: float = 1.0
    risk_multiplier: float = 1.0
    entry_threshold: float = 0.5  # 入場信號強度閾值
    exit_threshold: float = 0.3   # 出場信號強度閾值
    
    def mutate(self, mutation_rate: float = 0.2, rng: Optional[np.random.Generator] = None) -> 'StrategyGene':
        """基因突變"""
        if rng is None:
            # 回退情況: 使用默認種子 42
            rng = np.random.default_rng(42)
        
        mutated = copy.deepcopy(self)
        
        if rng.random() < mutation_rate:
            # 突變策略類型
            strategies = ['trend_following', 'swing_trading', 'mean_reversion', 'breakout_trading']
            mutated.strategy_type = rng.choice(strategies)
        
        if rng.random() < mutation_rate:
            # 突變權重
            mutated.strategy_weight = float(np.clip(
                mutated.strategy_weight + rng.uniform(-0.2, 0.2),
                0.1, 1.0
            ))
        
        if rng.random() < mutation_rate:
            # 突變倉位倍數
            mutated.position_size_multiplier = float(np.clip(
                mutated.position_size_multiplier + rng.uniform(-0.3, 0.3),
                0.3, 2.0
            ))
        
        if rng.random() < mutation_rate:
            # 突變閾值
            mutated.entry_threshold = float(np.clip(
                mutated.entry_threshold + rng.uniform(-0.2, 0.2),
                0.2, 0.8
            ))
        
        return mutated


@dataclass
class StrategyPortfolioChromosome:
    """
    策略組合染色體 - 完整的多階段策略配置
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    generation: int = 0
    
    # 各階段的策略基因
    genes: Dict[TradingPhase, StrategyGene] = field(default_factory=dict)
    
    # 全局參數
    global_risk_limit: float = 0.02  # 單筆風險上限
    max_position_count: int = 3       # 最大持倉數
    correlation_limit: float = 0.7    # 相關性限制
    
    # 階段切換規則
    phase_transition_rules: Dict[str, float] = field(default_factory=dict)
    
    # 性能指標
    fitness: float = 0.0
    total_return: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    consistency: float = 0.0
    
    backtest_result: Optional[Dict] = None
    
    def calculate_fitness(
        self,
        objective: OptimizationObjective = OptimizationObjective.BALANCED
    ) -> float:
        """計算適應度"""
        
        if objective == OptimizationObjective.MAXIMIZE_RETURN:
            fitness = self.total_return
        
        elif objective == OptimizationObjective.MAXIMIZE_SHARPE:
            fitness = self.sharpe_ratio
        
        elif objective == OptimizationObjective.MINIMIZE_DRAWDOWN:
            fitness = 1.0 + self.max_drawdown  # 回撤是負數，轉為正數
        
        elif objective == OptimizationObjective.MAXIMIZE_CONSISTENCY:
            fitness = self.consistency
        
        else:  # BALANCED
            # 綜合評分
            fitness = (
                self.sharpe_ratio * 0.3 +
                self.total_return * 0.2 +
                (1.0 + self.max_drawdown) * 0.2 +
                self.consistency * 0.15 +
                (self.profit_factor - 1.0) * 0.15
            )
        
        self.fitness = max(0, fitness)  # 確保非負
        return self.fitness
    
    def crossover(self, other: 'StrategyPortfolioChromosome', rng: Optional[np.random.Generator] = None) -> 'StrategyPortfolioChromosome':
        """染色體交叉（繁殖）"""
        if rng is None:
            # 回退情況: 使用默認種子 42
            rng = np.random.default_rng(42)
        
        child = StrategyPortfolioChromosome()
        child.generation = max(self.generation, other.generation) + 1
        
        # 隨機繼承各階段的基因
        for phase in TradingPhase:
            if phase in self.genes and phase in other.genes:
                # 50%機率從父母之一繼承
                if rng.random() < 0.5:
                    child.genes[phase] = copy.deepcopy(self.genes[phase])
                else:
                    child.genes[phase] = copy.deepcopy(other.genes[phase])
            elif phase in self.genes:
                child.genes[phase] = copy.deepcopy(self.genes[phase])
            elif phase in other.genes:
                child.genes[phase] = copy.deepcopy(other.genes[phase])
        
        # 繼承全局參數（取平均）
        child.global_risk_limit = (self.global_risk_limit + other.global_risk_limit) / 2
        child.max_position_count = int((self.max_position_count + other.max_position_count) / 2)
        child.correlation_limit = (self.correlation_limit + other.correlation_limit) / 2
        
        return child
    
    def mutate(self, mutation_rate: float = 0.2, rng: Optional[np.random.Generator] = None) -> 'StrategyPortfolioChromosome':
        """染色體突變"""
        if rng is None:
            # 回退情況: 使用默認種子 42
            rng = np.random.default_rng(42)
        
        mutated = copy.deepcopy(self)
        
        # 突變各階段基因
        for phase in mutated.genes:
            if rng.random() < mutation_rate:
                mutated.genes[phase] = mutated.genes[phase].mutate(mutation_rate, rng)
        
        # 突變全局參數
        if rng.random() < mutation_rate:
            mutated.global_risk_limit = float(np.clip(
                mutated.global_risk_limit + rng.uniform(-0.01, 0.01),
                0.005, 0.05
            ))
        
        if rng.random() < mutation_rate:
            mutated.max_position_count = int(np.clip(
                mutated.max_position_count + rng.integers(-1, 2),
                1, 10
            ))
        
        return mutated


@dataclass
class OptimizerConfig:
    """優化器配置"""
    # 遺傳算法
    population_size: int = 30
    max_generations: int = 20
    survival_rate: float = 0.3
    mutation_rate: float = 0.2
    crossover_rate: float = 0.6
    elite_count: int = 2
    
    # 隨機種子
    random_seed: Optional[int] = 42
    
    # 優化目標
    objective: OptimizationObjective = OptimizationObjective.BALANCED
    
    # 回測配置（用於評估）
    backtest_config: Optional[ArenaConfig] = None
    
    # 輸出
    output_dir: str = "strategy_portfolio_optimization"
    verbose: bool = True


class StrategyPortfolioOptimizer:
    """
    策略組合優化器
    
    使用遺傳算法優化多階段策略組合，找出最優配置
    """
    
    def __init__(self, config: OptimizerConfig):
        self.config = config
        self.current_generation = 0
        self.population: List[StrategyPortfolioChromosome] = []
        self.history: List[Dict] = []
        self.best_chromosome: Optional[StrategyPortfolioChromosome] = None
                # 創建隨機數生成器
        self.rng = np.random.default_rng(config.random_seed)
                # 創建輸出目錄
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        
        logger.info("🧬 策略組合優化器已初始化")
        logger.info(f"   - 種群大小: {config.population_size}")
        logger.info(f"   - 最大代數: {config.max_generations}")
        logger.info(f"   - 優化目標: {config.objective.value}")
    
    def initialize_population(self) -> List[StrategyPortfolioChromosome]:
        """初始化種群"""
        population = []
        
        strategy_types = ['trend_following', 'swing_trading', 'mean_reversion', 'breakout_trading']
        
        # 關鍵階段（優先優化）
        key_phases = [
            TradingPhase.MARKET_OPEN,
            TradingPhase.EARLY_SESSION,
            TradingPhase.MID_SESSION,
            TradingPhase.LATE_SESSION,
            TradingPhase.MARKET_CLOSE,
        ]
        
        for _ in range(self.config.population_size):
            chromosome = StrategyPortfolioChromosome(generation=0)
            
            # 為每個關鍵階段生成基因
            for phase in key_phases:
                strategy_type = self.rng.choice(strategy_types)
                
                gene = StrategyGene(
                    phase=phase,
                    strategy_type=strategy_type,
                    strategy_weight=float(self.rng.uniform(0.5, 1.0)),
                    position_size_multiplier=float(self.rng.uniform(0.5, 1.5)),
                    risk_multiplier=float(self.rng.uniform(0.8, 1.5)),
                    entry_threshold=float(self.rng.uniform(0.3, 0.7)),
                    exit_threshold=float(self.rng.uniform(0.2, 0.5)),
                )
                
                chromosome.genes[phase] = gene
            
            # 全局參數
            chromosome.global_risk_limit = float(self.rng.uniform(0.01, 0.03))
            chromosome.max_position_count = int(self.rng.integers(2, 5))
            chromosome.correlation_limit = float(self.rng.uniform(0.5, 0.8))
            
            population.append(chromosome)
        
        self.population = population
        logger.info(f"✅ 初始種群已創建: {len(population)} 個染色體")
        
        return population
    
    def evaluate_population(self) -> List[StrategyPortfolioChromosome]:
        """評估種群 - 回測每個染色體"""
        logger.info(f"📊 評估第 {self.current_generation} 代...")
        
        for i, chromosome in enumerate(self.population):
            logger.info(f"   [{i+1}/{len(self.population)}] 評估染色體 {chromosome.id}...")
            
            # 運行回測評估
            self._evaluate_chromosome(chromosome)
            
            # 計算適應度
            chromosome.calculate_fitness(self.config.objective)
        
        return self.population
    
    def _evaluate_chromosome(self, chromosome: StrategyPortfolioChromosome):
        """評估單個染色體（運行回測）"""
        try:
            # NOTE: 實際使用時需要整合真實的回測引擎
            # 這裡需要：
            # 1. 根據染色體配置創建 PhaseRouter
            # 2. 運行完整回測
            # 3. 提取性能指標
            
            # 暫時使用模擬結果
            result = self._simulate_backtest()
            
            chromosome.total_return = result['total_return']
            chromosome.sharpe_ratio = result['sharpe_ratio']
            chromosome.max_drawdown = result['max_drawdown']
            chromosome.win_rate = result['win_rate']
            chromosome.profit_factor = result['profit_factor']
            chromosome.consistency = result['consistency']
            chromosome.backtest_result = result
            
        except Exception as e:
            logger.error(f"評估失敗: {e}")
            chromosome.fitness = -999.0
    
    def _simulate_backtest(self) -> Dict[str, Any]:
        """模擬回測結果（臨時）"""
        return {
            'total_return': float(self.rng.uniform(-0.1, 0.6)),
            'sharpe_ratio': float(self.rng.uniform(-0.5, 3.5)),
            'max_drawdown': float(self.rng.uniform(-0.4, -0.05)),
            'win_rate': float(self.rng.uniform(0.4, 0.7)),
            'profit_factor': float(self.rng.uniform(0.8, 3.5)),
            'consistency': float(self.rng.uniform(0.4, 0.9)),
        }
    
    def rank_and_select(self) -> List[StrategyPortfolioChromosome]:
        """排名並選擇"""
        # 按適應度排序
        self.population.sort(key=lambda x: x.fitness, reverse=True)
        
        # 選擇存活者
        survivors_count = max(2, int(len(self.population) * self.config.survival_rate))
        survivors = self.population[:survivors_count]
        
        # 更新最佳染色體
        self.best_chromosome = self.population[0]
        
        logger.info(f"🏆 第 {self.current_generation} 代排名:")
        for i in range(min(3, len(self.population))):
            c = self.population[i]
            logger.info(f"   #{i+1}: {c.id} | 適應度={c.fitness:.4f} | "
                       f"夏普={c.sharpe_ratio:.2f} | 回報={c.total_return*100:.1f}%")
        
        return survivors
    
    def evolve_next_generation(
        self,
        survivors: List[StrategyPortfolioChromosome]
    ) -> List[StrategyPortfolioChromosome]:
        """進化下一代"""
        next_generation = []
        
        # 精英保留
        elites = survivors[:self.config.elite_count]
        next_generation.extend(elites)
        
        logger.info(f"🧬 進化第 {self.current_generation + 1} 代...")
        
        # 繁殖新個體
        while len(next_generation) < self.config.population_size:
            # 選擇父母
            parent1 = self._tournament_selection(survivors)
            parent2 = self._tournament_selection(survivors)
            
            # 交叉
            if self.rng.random() < self.config.crossover_rate:
                child = parent1.crossover(parent2, self.rng)
            else:
                child = copy.deepcopy(parent1)
            
            # 突變
            if self.rng.random() < self.config.mutation_rate:
                child = child.mutate(self.config.mutation_rate, self.rng)
            
            next_generation.append(child)
        
        self.population = next_generation
        return next_generation
    
    def _tournament_selection(
        self,
        population: List[StrategyPortfolioChromosome],
        tournament_size: int = 3
    ) -> StrategyPortfolioChromosome:
        """錦標賽選擇"""
        tournament_indices = self.rng.choice(len(population), size=tournament_size, replace=False)
        tournament = [population[i] for i in tournament_indices]
        return max(tournament, key=lambda x: x.fitness)
    
    def run(self) -> StrategyPortfolioChromosome:
        """運行完整優化過程"""
        logger.info("🚀 策略組合優化開始...")
        
        # 初始化
        self.initialize_population()
        
        # 進化循環
        for gen in range(self.config.max_generations):
            self.current_generation = gen
            
            logger.info(f"\n{'='*60}")
            logger.info(f"第 {gen + 1}/{self.config.max_generations} 代")
            logger.info(f"{'='*60}")
            
            # 評估
            self.evaluate_population()
            
            # 選擇
            survivors = self.rank_and_select()
            
            # 記錄
            self._record_generation()
            
            # 保存
            if (gen + 1) % 5 == 0 or gen == self.config.max_generations - 1:
                self.save_results()
            
            # 進化（除了最後一代）
            if gen < self.config.max_generations - 1:
                self.evolve_next_generation(survivors)
        
        logger.info("\n🎉 優化完成！")
        
        # 類型守衛：確保 best_chromosome 不為 None
        if self.best_chromosome is None:
            raise RuntimeError("優化運行完成但未找到最優染色體！")
        
        logger.info(f"🏆 最優策略組合: {self.best_chromosome.id}")
        logger.info(f"   - 適應度: {self.best_chromosome.fitness:.4f}")
        logger.info(f"   - 夏普比率: {self.best_chromosome.sharpe_ratio:.2f}")
        logger.info(f"   - 總回報: {self.best_chromosome.total_return*100:.1f}%")
        
        return self.best_chromosome
    
    def _record_generation(self):
        """記錄歷史"""
        gen_stats = {
            'generation': self.current_generation,
            'timestamp': datetime.now().isoformat(),
            'best_fitness': self.population[0].fitness,
            'avg_fitness': np.mean([c.fitness for c in self.population]),
            'best_sharpe': self.population[0].sharpe_ratio,
            'best_return': self.population[0].total_return,
        }
        self.history.append(gen_stats)
    
    def save_results(self):
        """保存結果"""
        output_dir = Path(self.config.output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 保存最優組合（如果存在）
        if self.best_chromosome is None:
            logger.warning("沒有最優染色體可保存")
            return
        
        best_file = output_dir / f"best_portfolio_{timestamp}.json"
        with open(best_file, 'w', encoding='utf-8') as f:
            # 轉換為可序列化格式
            best_dict = {
                'id': self.best_chromosome.id,
                'generation': self.best_chromosome.generation,
                'fitness': self.best_chromosome.fitness,
                'total_return': self.best_chromosome.total_return,
                'sharpe_ratio': self.best_chromosome.sharpe_ratio,
                'max_drawdown': self.best_chromosome.max_drawdown,
                'genes': {
                    phase.value: {
                        'strategy_type': gene.strategy_type,
                        'strategy_weight': gene.strategy_weight,
                        'position_size_multiplier': gene.position_size_multiplier,
                        'risk_multiplier': gene.risk_multiplier,
                        'entry_threshold': gene.entry_threshold,
                        'exit_threshold': gene.exit_threshold,
                    }
                    for phase, gene in self.best_chromosome.genes.items()
                }
            }
            json.dump(best_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 結果已保存: {output_dir}")
    
    def export_to_phase_router_config(self, filepath: str):
        """導出為 PhaseRouter 配置文件"""
        if not self.best_chromosome:
            logger.error("沒有最優染色體可導出")
            return
        
        router_config = {}
        
        for phase, gene in self.best_chromosome.genes.items():
            router_config[phase.value] = {
                'primary_strategy': gene.strategy_type,
                'position_size_multiplier': gene.position_size_multiplier,
                'risk_multiplier': gene.risk_multiplier,
                'entry_threshold': gene.entry_threshold,
                'exit_threshold': gene.exit_threshold,
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(router_config, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📤 已導出 PhaseRouter 配置: {filepath}")


# ============================================================================
# 使用示例
# ============================================================================

def demo():
    """演示優化器使用"""
    
    config = OptimizerConfig(
        population_size=20,
        max_generations=10,
        objective=OptimizationObjective.BALANCED,
    )
    
    optimizer = StrategyPortfolioOptimizer(config)
    best = optimizer.run()
    
    print("\n最優策略組合:")
    print(f"ID: {best.id}")
    print(f"適應度: {best.fitness:.4f}")
    print(f"夏普比率: {best.sharpe_ratio:.2f}")
    print(f"總回報: {best.total_return*100:.1f}%")
    
    print("\n各階段策略配置:")
    for phase, gene in best.genes.items():
        print(f"  {phase.value}:")
        print(f"    策略: {gene.strategy_type}")
        print(f"    權重: {gene.strategy_weight:.2f}")
        print(f"    倉位倍數: {gene.position_size_multiplier:.2f}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    demo()
