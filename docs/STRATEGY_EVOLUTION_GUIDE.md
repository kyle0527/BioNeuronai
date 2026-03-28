# 「養蠱式」策略進化系統 - 完整使用指南
> **創建日期**: 2026-02-14  
> **系統版本**: v2.3  
> **作者**: BioNeuronAI Team


## 📑 目錄

1. 🎯 系統概述
2. 📦 三大核心組件
3. 🚀 完整工作流程
4. 🎨 進階自定義
5. 📊 性能評估指標
6. 🔧 系統依賴
7. 💡 最佳實踐建議
8. 🐛 常見問題
9. 📚 相關文檔
10. 🎯 下一步計劃

---

## 🎯 系統概述

這是一個三層架構的策略優化系統，實現「養蠱式」策略競爭與進化：

```
┌─────────────────────────────────────────────────────────┐
│  第一層: 策略競技場 (Strategy Arena)                       │
│  功能: 多策略並行回測，優勝劣汰，參數優化                    │
│  輸出: 各策略的最優參數配置                                 │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  第二層: 階段路由器 (Phase Router)                         │
│  功能: 識別交易階段，動態路由到不同策略                      │
│  輸出: 開盤用A、中盤用B、收盤用C 的階段化策略                │
└───────────────────┬─────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────────────────────┐
│  第三層: 策略組合優化器 (Portfolio Optimizer)              │
│  功能: 遺傳算法優化整個策略組合                             │
│  輸出: 全局最優的多階段策略配置                             │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 三大核心組件

### 1️⃣ 策略競技場 (`strategy_arena.py`)

**用途**: 讓多個策略「打擂台」，找出各策略的最優參數

**核心機制**:
- 多策略並行回測
- 多維度性能評估（夏普比率、回撤、勝率等）
- 遺傳算法自動優化參數
- 支持多進程加速

**使用示例**:
```python
from bioneuronai.strategies.strategy_arena import StrategyArena, ArenaConfig

# 配置競技場
config = ArenaConfig(
    symbol="BTCUSDT",
    interval="1h",
    start_date="2024-01-01",
    end_date="2024-12-31",
    population_size=20,        # 每代20個策略候選者
    max_generations=10,        # 進化10代
    survival_rate=0.3,         # 前30%晉級
    mutation_rate=0.2,         # 20%突變率
    score_weights={            # 評分權重
        'sharpe_ratio': 0.3,
        'sortino_ratio': 0.2,
        'max_drawdown': 0.2,
        'win_rate': 0.1,
        'profit_factor': 0.1,
        'consistency': 0.1,
    }
)

# 創建競技場
arena = StrategyArena(config)

# 運行進化（自動優化）
best_strategy = arena.run()

print(f"最優策略: {best_strategy.name}")
print(f"策略類型: {best_strategy.strategy_type}")
print(f"參數: {best_strategy.parameters}")
print(f"夏普比率: {best_strategy.sharpe_ratio:.2f}")
print(f"總回報: {best_strategy.total_return*100:.1f}%")
```

**輸出結果**:
```
第 1/10 代
================================================================================
📊 開始評估第 0 代（單進程）...
   [1/20] 評估 trend_following_0...
   [2/20] 評估 trend_following_1...
   ...

🏆 第 0 代排名完成:
   - 前 3 名:
     #1: trend_following_3 | 評分=2.5431 | 夏普=3.21 | 回報=45.3%
     #2: breakout_trading_2 | 評分=2.1234 | 夏普=2.87 | 回報=38.7%
     #3: swing_trading_5 | 評分=1.9876 | 夏普=2.54 | 回報=32.1%
   - 晉級數量: 6/20

🧬 開始進化第 1 代...
   - 精英保留: 2
   - 新一代數量: 20

... (迭代10代)

🎉 策略競技場完成！
🏆 最優策略: trend_following_gen8_abc123
   - 評分: 3.1234
   - 夏普比率: 3.84
   - 總回報: 52.7%
```

---

### 2️⃣ 階段路由器 (`phase_router.py`)

**用途**: 根據交易階段動態切換策略（開盤、盤中、收盤等）

**核心機制**:
- 自動識別9種交易階段
- 每個階段配置不同策略
- 支持新聞事件、波動率特殊處理
- 階段過渡平滑切換

**預設階段配置**:

| 階段 | 時間 (UTC) | 主策略 | 倉位倍數 | 風險倍數 | 說明 |
|------|-----------|--------|---------|---------|------|
| 🌅 開盤 | 00:00-02:00 | 突破交易 | 0.7x | 1.2x | 高波動，減倉 |
| 🌄 早盤 | 02:00-08:00 | 趨勢跟隨 | 1.0x | 1.0x | 趨勢建立 |
| ☀️ 盤中 | 08:00-16:00 | 趨勢跟隨 | 1.2x | 1.0x | 主趨勢，增倉 |
| 🌆 尾盤 | 16:00-22:00 | 波段交易 | 0.8x | 1.0x | 減倉整理 |
| 🌃 收盤 | 22:00-24:00 | 均值回歸 | 0.5x | 1.0x | 強制平倉 |
| 📰 新聞前 | 事件前30分鐘 | 波段交易 | 0.3x | 0.5x | 保守觀望 |
| 📢 新聞後 | 事件後30分鐘 | 突破交易 | 0.8x | 1.5x | 快速反應 |
| 🔥 高波動 | 波動率>0.7 | 突破交易 | 0.6x | 1.3x | 波動大，減倉 |
| 😴 低波動 | 波動率<0.2 | 均值回歸 | 1.1x | 1.0x | 震盪市 |

**使用示例**:
```python
from bioneuronai.strategies.phase_router import TradingPhaseRouter
from datetime import datetime

# 創建路由器
router = TradingPhaseRouter(timeframe="1h")

# 準備市場數據
market_data = {
    'price': 50000.0,
    'volatility': 0.5,
    'market_condition': MarketCondition.UPTREND,
    'has_news_event': False,
    'volume': 1000000,
}

# 路由決策
decision = router.route_trading_decision(
    current_time=datetime.now(),
    market_data=market_data,
    has_position=False,
)

print(f"當前階段: {decision['phase']}")
print(f"使用策略: {decision['strategy_used']}")
print(f"倉位倍數: {decision['config']['position_size_multiplier']}")
print(f"允許動作: {decision['config']['preferred_actions']}")

# 自定義階段配置
from bioneuronai.strategies.phase_router import PhaseConfig, TradingPhase

custom_config = PhaseConfig(
    phase=TradingPhase.MARKET_OPEN,
    start_hour=0,
    end_hour=2,
    primary_strategy="breakout_trading",
    position_size_multiplier=0.5,  # 開盤只用50%倉位
    risk_multiplier=1.5,           # 但風險設置加大
    forbidden_actions=[PhaseAction.SCALE_IN],  # 禁止加倉
)

router.phase_configs[TradingPhase.MARKET_OPEN] = custom_config
```

**輸出示例**:
```
時間: 01:30  →  📍 階段路由: market_open | 策略: BreakoutTradingStrategy
時間: 05:00  →  📍 階段路由: early_session | 策略: TrendFollowingStrategy
時間: 12:00  →  📍 階段路由: mid_session | 策略: TrendFollowingStrategy
時間: 18:00  →  📍 階段路由: late_session | 策略: SwingTradingStrategy
時間: 23:00  →  📍 階段路由: market_close | 策略: MeanReversionStrategy
```

---

### 3️⃣ 策略組合優化器 (`portfolio_optimizer.py`)

**用途**: 使用遺傳算法找出全局最優的策略組合配置

**核心機制**:
- 染色體編碼多階段策略配置
- 遺傳算法全局優化
- 自動發現策略協同效應
- 可導出為 PhaseRouter 配置

**優化維度**:
1. 每個階段使用哪個策略
2. 各策略的權重分配
3. 倉位大小倍數
4. 風險參數設置
5. 入場/出場閾值
6. 全局風險限制

**使用示例**:
```python
from bioneuronai.strategies.portfolio_optimizer import (
    StrategyPortfolioOptimizer,
    OptimizerConfig,
    OptimizationObjective
)

# 配置優化器
config = OptimizerConfig(
    population_size=30,           # 種群大小
    max_generations=20,           # 進化代數
    survival_rate=0.3,            # 存活率
    mutation_rate=0.2,            # 突變率
    crossover_rate=0.6,           # 交叉率
    elite_count=2,                # 精英保留數
    objective=OptimizationObjective.BALANCED,  # 綜合優化
    output_dir="optimization_results",
)

# 創建優化器
optimizer = StrategyPortfolioOptimizer(config)

# 運行優化
best_portfolio = optimizer.run()

# 查看結果
print(f"最優組合 ID: {best_portfolio.id}")
print(f"適應度: {best_portfolio.fitness:.4f}")
print(f"夏普比率: {best_portfolio.sharpe_ratio:.2f}")
print(f"總回報: {best_portfolio.total_return*100:.1f}%")

print("\n各階段策略配置:")
for phase, gene in best_portfolio.genes.items():
    print(f"  {phase.value}:")
    print(f"    策略: {gene.strategy_type}")
    print(f"    權重: {gene.strategy_weight:.2f}")
    print(f"    倉位倍數: {gene.position_size_multiplier:.2f}")
    print(f"    風險倍數: {gene.risk_multiplier:.2f}")

# 導出為配置文件（可直接用於 PhaseRouter）
optimizer.export_to_phase_router_config("optimized_config.json")
```

**輸出示例**:
```
第 1/20 代
================================================================================
📊 評估第 0 代...
   [1/30] 評估染色體 abc123...
   [2/30] 評估染色體 def456...
   ...

🏆 第 0 代排名:
   #1: abc123 | 適應度=3.2145 | 夏普=3.54 | 回報=48.2%
   #2: def456 | 適應度=2.9876 | 夏普=3.21 | 回報=43.1%
   #3: ghi789 | 適應度=2.7654 | 夏普=2.98 | 回報=39.7%

🧬 進化第 1 代...

... (迭代20代)

🎉 優化完成！
🏆 最優策略組合: xyz999
   - 適應度: 4.1234
   - 夏普比率: 4.21
   - 總回報: 67.8%

各階段策略配置:
  market_open:
    策略: breakout_trading
    權重: 0.85
    倉位倍數: 0.62
    風險倍數: 1.35
  mid_session:
    策略: trend_following
    權重: 1.00
    倉位倍數: 1.15
    風險倍數: 1.02
  market_close:
    策略: mean_reversion
    權重: 0.75
    倉位倍數: 0.48
    風險倍數: 0.88
```

---

## 🚀 完整工作流程

### 步驟1: 策略競技場 - 找出各策略最優參數

```python
# 1. 配置競技場
arena_config = ArenaConfig(
    symbol="BTCUSDT",
    interval="1h",
    start_date="2024-01-01",
    end_date="2024-12-31",
    population_size=20,
    max_generations=10,
)

# 2. 運行競技場
arena = StrategyArena(arena_config)
arena.run()

# 3. 獲取各策略的最優參數
best_candidates = arena.population[:4]  # 取前4名
for candidate in best_candidates:
    print(f"{candidate.strategy_type}: {candidate.parameters}")
```

### 步驟2: 階段路由器 - 配置階段化策略

```python
# 1. 創建路由器
router = TradingPhaseRouter(timeframe="1h")

# 2. 根據競技場結果，更新各階段的策略配置
# 例如：開盤階段用最優的突破策略
router.phase_configs[TradingPhase.MARKET_OPEN].primary_strategy = "breakout_trading"

# 3. 保存配置
router.save_phase_configs("phase_config.json")
```

### 步驟3: 組合優化器 - 全局優化

```python
# 1. 配置優化器
optimizer_config = OptimizerConfig(
    population_size=30,
    max_generations=20,
    objective=OptimizationObjective.BALANCED,
)

# 2. 運行優化
optimizer = StrategyPortfolioOptimizer(optimizer_config)
best_portfolio = optimizer.run()

# 3. 導出最優配置
optimizer.export_to_phase_router_config("final_optimized_config.json")
```

### 步驟4: 部署到實盤

```python
from bioneuronai.core.trading_engine import TradingEngine

# 1. 載入優化後的配置
router = TradingPhaseRouter(timeframe="1h")
router.load_phase_configs("final_optimized_config.json")

# 2. 整合到交易引擎
trading_engine = TradingEngine(
    connector=binance_connector,
    phase_router=router,
    enable_live_trading=True,
)

# 3. 啟動交易
trading_engine.start()
```

---

## 🎨 進階自定義

### 自定義評分函數

```python
# 在 StrategyArena 中自定義評分權重
config = ArenaConfig(
    score_weights={
        'sharpe_ratio': 0.5,      # 更重視夏普比率
        'max_drawdown': 0.3,      # 重視回撤控制
        'consistency': 0.2,       # 重視穩定性
        # 不考慮勝率和盈虧比
    }
)
```

### 自定義交易階段

```python
# 創建自定義階段（例如：亞洲盤、歐洲盤、美國盤）
asian_session = PhaseConfig(
    phase=TradingPhase.EARLY_SESSION,
    start_hour=0,
    end_hour=8,
    primary_strategy="mean_reversion",  # 亞洲盤波動小，用均值回歸
    position_size_multiplier=0.8,
)

european_session = PhaseConfig(
    phase=TradingPhase.MID_SESSION,
    start_hour=8,
    end_hour=16,
    primary_strategy="trend_following",  # 歐洲盤趨勢明顯
    position_size_multiplier=1.2,
)

us_session = PhaseConfig(
    phase=TradingPhase.LATE_SESSION,
    start_hour=16,
    end_hour=24,
    primary_strategy="breakout_trading",  # 美國盤波動大
    position_size_multiplier=1.0,
)
```

### 自定義優化目標

```python
# 如果你只想最大化回報（不管波動）
config = OptimizerConfig(
    objective=OptimizationObjective.MAXIMIZE_RETURN,
)

# 如果你想最小化回撤（保守風格）
config = OptimizerConfig(
    objective=OptimizationObjective.MINIMIZE_DRAWDOWN,
)
```

---

## 📊 性能評估指標

系統使用以下指標評估策略性能：

1. **夏普比率** (Sharpe Ratio): 風險調整後收益
2. **索提諾比率** (Sortino Ratio): 下行風險調整後收益
3. **最大回撤** (Max Drawdown): 最大虧損幅度
4. **勝率** (Win Rate): 盈利交易比例
5. **盈虧比** (Profit Factor): 總盈利/總虧損
6. **一致性** (Consistency): 月度正回報比例
7. **平均交易回報** (Avg Trade Return): 單筆平均盈利

---

## 🔧 系統依賴

```bash
# 必需依賴
pip install numpy pandas

# 可選依賴（建議安裝）
pip install stable-baselines3  # RL 強化學習（如果使用 RLFusionAgent）
pip install gymnasium          # RL 環境
pip install torch             # 深度學習

# 回測數據
# 需要歷史 K 線數據（CSV 格式）
# 數據結構見 backtest/data_stream.py
```

---

## 💡 最佳實踐建議

### 1. 數據準備
```python
# 確保有足夠的歷史數據（至少1年）
# 數據應包含：timestamp, open, high, low, close, volume
```

### 2. 參數調優順序
```
第一步：策略競技場（找出各策略最優參數）
第二步：階段路由器（手動配置初始階段）
第三步：組合優化器（遺傳算法全局優化）
```

### 3. 風險控制
```python
# 在所有層級都設置風險限制
arena_config.initial_balance = 10000.0
optimizer.best_chromosome.global_risk_limit = 0.02  # 單筆2%風險
```

### 4. 過擬合預防
```python
# 使用 Walk-Forward 驗證
# 將數據分為：訓練集(70%) + 驗證集(15%) + 測試集(15%)
```

### 5. 性能監控
```python
# 定期檢查各階段性能
stats = router.get_phase_statistics()
print(json.dumps(stats, indent=2))
```

---

## 🐛 常見問題

### Q1: 為什麼回測結果不理想？
**A**: 
- 確保數據質量（無缺失、無異常值）
- 增加回測數據量（至少6個月）
- 調整評分權重，可能過於重視某個指標
- 檢查交易成本設置是否合理

### Q2: 優化時間太長？
**A**:
- 減少 `population_size` (例如從30降到15)
- 減少 `max_generations` (例如從20降到10)
- 啟用多進程 `use_multiprocessing=True`
- 使用更粗的時間框架（如4h代替1h）

### Q3: 如何整合到現有 TradingEngine？
**A**:
```python
# 在 TradingEngine 中添加
self.phase_router = TradingPhaseRouter(timeframe)

# 在生成信號時
decision = self.phase_router.route_trading_decision(
    current_time=datetime.now(),
    market_data=self.market_data,
    has_position=self.has_position,
)
signal = decision['signal']
```

### Q4: 可以用於實盤嗎？
**A**: 
- 必須先經過充分回測驗證
- 建議先在模擬盤運行1-2個月
- 實盤初期使用小倉位（10-20%資金）
- 持續監控並記錄性能偏差

---

## 📚 相關文檔

- [策略基類文檔](base_strategy.py)
- [回測引擎文檔](../backtest/README.md)
- [風險管理文檔](../trading/risk_manager.py)
- [數據模型文檔](../../schemas/README.md)

---

## 🎯 下一步計劃

- [ ] 整合真實回測引擎（目前使用模擬數據）
- [ ] 添加 Bayesian Optimization 加速參數搜索
- [ ] 實現在線學習（Online Learning）持續優化
- [ ] 添加更多評估指標（如 Calmar Ratio、Kelly Criterion）
- [ ] 可視化工具（進化過程、性能曲線）
- [ ] 支持多交易對同時優化

---

**祝交易順利！** 🚀💰
