"""
策略進化系統 - 完整示例腳本
================================

演示如何完整使用三層策略優化系統

運行方式:
    python demo_strategy_evolution.py

創建日期：2026-02-14
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path

# 導入三大核心組件
from bioneuronai.strategies.strategy_arena import StrategyArena, ArenaConfig
from bioneuronai.strategies.phase_router import TradingPhaseRouter, TradingPhase, MarketCondition
from bioneuronai.strategies.portfolio_optimizer import (
    StrategyPortfolioOptimizer,
    OptimizerConfig,
    OptimizationObjective
)

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('strategy_evolution.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def demo_strategy_arena():
    """
    演示1: 策略競技場
    目標：找出各策略的最優參數
    """
    print("\n" + "="*80)
    print("🏟️  演示1: 策略競技場 - 養蠱式參數優化")
    print("="*80)
    
    # 配置
    config = ArenaConfig(
        symbol="BTCUSDT",
        interval="1h",
        start_date="2024-01-01",
        end_date="2024-06-30",
        initial_balance=10000.0,
        population_size=10,      # 演示用小規模
        max_generations=5,       # 演示用少代數
        survival_rate=0.3,
        mutation_rate=0.2,
        score_weights={
            'sharpe_ratio': 0.3,
            'sortino_ratio': 0.2,
            'max_drawdown': 0.2,
            'win_rate': 0.15,
            'profit_factor': 0.15,
        },
        use_multiprocessing=False,  # 演示用單進程
        output_dir="demo_results/arena",
        verbose=True,
    )
    
    # 創建並運行
    arena = StrategyArena(config)
    best_strategy = arena.run()
    
    print("\n✅ 策略競技場完成！")
    print(f"   最優策略: {best_strategy.name}")
    print(f"   策略類型: {best_strategy.strategy_type}")
    print(f"   評分: {best_strategy.score:.4f}")
    print(f"   夏普比率: {best_strategy.sharpe_ratio:.2f}")
    print(f"   總回報: {best_strategy.total_return*100:.1f}%")
    print(f"   最大回撤: {best_strategy.max_drawdown*100:.1f}%")
    print(f"   勝率: {best_strategy.win_rate*100:.1f}%")
    
    # 保存結果
    result_file = Path("demo_results/arena/best_strategy_summary.json")
    result_file.parent.mkdir(parents=True, exist_ok=True)
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'name': best_strategy.name,
            'type': best_strategy.strategy_type,
            'parameters': best_strategy.parameters,
            'score': best_strategy.score,
            'sharpe_ratio': best_strategy.sharpe_ratio,
            'total_return': best_strategy.total_return,
            'max_drawdown': best_strategy.max_drawdown,
            'win_rate': best_strategy.win_rate,
        }, f, indent=2, ensure_ascii=False)
    
    print(f"   結果已保存: {result_file}")
    
    return best_strategy


def demo_phase_router():
    """
    演示2: 階段路由器
    目標：實現「開盤用A、中盤用B、收盤用C」
    """
    print("\n" + "="*80)
    print("🎯 演示2: 階段路由器 - 階段化策略選擇")
    print("="*80)
    
    # 創建路由器
    router = TradingPhaseRouter(timeframe="1h")
    
    # 模擬一天內不同時間點的決策
    test_times = [
        (1, "開盤階段"),
        (5, "早盤階段"),
        (12, "盤中階段"),
        (18, "尾盤階段"),
        (23, "收盤階段"),
    ]
    
    print("\n模擬一天內的策略路由:")
    print("-" * 80)
    
    decisions = []
    for hour, phase_name in test_times:
        current_time = datetime(2024, 1, 1, hour, 0)
        
        # 模擬市場數據
        market_data = {
            'price': 50000.0,
            'volatility': 0.5,
            'market_condition': MarketCondition.UPTREND,
            'has_news_event': False,
            'volume': 1000000,
        }
        
        # 路由決策
        decision = router.route_trading_decision(
            current_time=current_time,
            market_data=market_data,
            has_position=False,
        )
        
        decisions.append(decision)
        
        print(f"⏰ {hour:02d}:00 | {phase_name:8s} | "
              f"策略: {decision['strategy_used']:25s} | "
              f"倉位倍數: {decision['config']['position_size_multiplier']:.2f}x | "
              f"風險倍數: {decision['config']['risk_multiplier']:.2f}x")
    
    # 保存配置
    config_file = Path("demo_results/router/phase_config.json")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    router.save_phase_configs(str(config_file))
    
    print("\n✅ 階段路由器演示完成！")
    print(f"   配置已保存: {config_file}")
    
    # 展示階段統計
    print("\n階段統計（需實際交易後才有數據）:")
    stats = router.get_phase_statistics()
    if stats:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print("   暫無統計數據")
    
    return router


def demo_portfolio_optimizer():
    """
    演示3: 策略組合優化器
    目標：遺傳算法找出全局最優配置
    """
    print("\n" + "="*80)
    print("🧬 演示3: 策略組合優化器 - 遺傳算法全局優化")
    print("="*80)
    
    # 配置
    config = OptimizerConfig(
        population_size=15,      # 演示用小規模
        max_generations=5,       # 演示用少代數
        survival_rate=0.3,
        mutation_rate=0.2,
        crossover_rate=0.6,
        elite_count=2,
        objective=OptimizationObjective.BALANCED,
        output_dir="demo_results/optimizer",
        verbose=True,
    )
    
    # 創建並運行
    optimizer = StrategyPortfolioOptimizer(config)
    best_portfolio = optimizer.run()
    
    print("\n✅ 組合優化完成！")
    print(f"   最優組合 ID: {best_portfolio.id}")
    print(f"   適應度: {best_portfolio.fitness:.4f}")
    print(f"   夏普比率: {best_portfolio.sharpe_ratio:.2f}")
    print(f"   總回報: {best_portfolio.total_return*100:.1f}%")
    print(f"   最大回撤: {best_portfolio.max_drawdown*100:.1f}%")
    print(f"   勝率: {best_portfolio.win_rate*100:.1f}%")
    
    print("\n各階段策略配置:")
    print("-" * 80)
    for phase, gene in best_portfolio.genes.items():
        print(f"  📍 {phase.value:20s}:")
        print(f"     策略類型: {gene.strategy_type:20s} | 權重: {gene.strategy_weight:.2f}")
        print(f"     倉位倍數: {gene.position_size_multiplier:.2f}x | 風險倍數: {gene.risk_multiplier:.2f}x")
        print(f"     入場閾值: {gene.entry_threshold:.2f} | 出場閾值: {gene.exit_threshold:.2f}")
    
    # 導出為路由器配置
    export_file = Path("demo_results/optimizer/optimized_phase_config.json")
    optimizer.export_to_phase_router_config(str(export_file))
    
    print(f"\n   優化配置已導出: {export_file}")
    print("   可直接用於 PhaseRouter.load_phase_configs()")
    
    return best_portfolio


def demo_complete_workflow():
    """
    完整工作流程演示
    """
    print("\n" + "="*80)
    print("🚀 完整工作流程演示")
    print("="*80)
    print("\n將依次運行:")
    print("1. 策略競技場 → 找出各策略最優參數")
    print("2. 階段路由器 → 配置階段化策略")
    print("3. 組合優化器 → 全局優化策略組合")
    print("\n預計耗時: 5-10分鐘（取決於電腦性能）")
    
    input("\n按 Enter 繼續...")
    
    # 第一步：策略競技場
    best_strategy = demo_strategy_arena()
    
    input("\n按 Enter 進入下一步...")
    
    # 第二步：階段路由器
    _ = demo_phase_router()  # 用於演示,不需返回值
    
    input("\n按 Enter 進入下一步...")
    
    # 第三步：組合優化器
    best_portfolio = demo_portfolio_optimizer()
    
    # 總結
    print("\n" + "="*80)
    print("🎉 完整工作流程演示完成！")
    print("="*80)
    
    print("\n📊 最終結果:")
    print(f"   - 最優單策略: {best_strategy.strategy_type} (夏普比率: {best_strategy.sharpe_ratio:.2f})")
    print(f"   - 最優組合: {best_portfolio.id} (適應度: {best_portfolio.fitness:.4f})")
    
    print("\n📁 生成的文件:")
    print("   - demo_results/arena/          (策略競技場結果)")
    print("   - demo_results/router/         (階段路由器配置)")
    print("   - demo_results/optimizer/      (組合優化器結果)")
    print("   - strategy_evolution.log       (完整日誌)")
    
    print("\n📖 下一步:")
    print("   1. 檢查生成的配置文件")
    print("   2. 使用實際歷史數據進行回測驗證")
    print("   3. 在模擬盤測試1-2個月")
    print("   4. 小倉位實盤驗證")
    
    print("\n詳細文檔: docs/STRATEGY_EVOLUTION_GUIDE.md")


def main():
    """主函數"""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " " * 20 + "策略進化系統 - 完整演示" + " " * 28 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  三層架構:" + " " * 66 + "║")
    print("║" + "    1. 策略競技場 (Strategy Arena)" + " " * 43 + "║")
    print("║" + "    2. 階段路由器 (Phase Router)" + " " * 45 + "║")
    print("║" + "    3. 組合優化器 (Portfolio Optimizer)" + " " * 38 + "║")
    print("║" + " " * 78 + "║")
    print("║" + "  創建日期: 2026-02-14" + " " * 56 + "║")
    print("╚" + "="*78 + "╝")
    
    print("\n請選擇演示模式:")
    print("  1. 策略競技場演示（單獨）")
    print("  2. 階段路由器演示（單獨）")
    print("  3. 組合優化器演示（單獨）")
    print("  4. 完整工作流程（推薦）")
    print("  0. 退出")
    
    choice = input("\n請輸入選項 (0-4): ").strip()
    
    try:
        if choice == "1":
            demo_strategy_arena()
        elif choice == "2":
            demo_phase_router()
        elif choice == "3":
            demo_portfolio_optimizer()
        elif choice == "4":
            demo_complete_workflow()
        elif choice == "0":
            print("\n再見！")
            return
        else:
            print("\n❌ 無效選項！")
            return
        
        print("\n✅ 演示完成！")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  演示被中斷")
    except Exception as e:
        logger.error(f"演示過程中發生錯誤: {e}", exc_info=True)
        print(f"\n❌ 錯誤: {e}")
        print("詳細錯誤信息請查看 strategy_evolution.log")


if __name__ == "__main__":
    main()
