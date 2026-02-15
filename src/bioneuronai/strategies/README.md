# 策略模組 (Strategies)

**路徑**: `src/bioneuronai/strategies/`  
**版本**: v4.1  
**更新日期**: 2026-02-15  
**架構層級**: Layer 2 — 策略層

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [架構總覽](#架構總覽)
3. [三層策略體系](#三層策略體系)
4. [基礎策略](#基礎策略)
5. [策略融合](#策略融合)
6. [策略選擇器](#策略選擇器)
7. [策略進化系統](#策略進化系統)
8. [導出 API](#導出-api)
9. [使用示例](#使用示例)
10. [相關文檔](#相關文檔)

---

## 🎯 模組概述

策略模組是 BioNeuronai 的核心競爭力所在，實現了從基礎交易策略到 AI 融合再到遺傳演算法進化的三層策略體系。包含 4 種基礎策略、AI 融合系統、智能選擇器與完整的進化架構。

### 模組職責
- ✅ 4 種基礎交易策略（趨勢 / 波段 / 均值回歸 / 突破）
- ✅ AI 策略融合（多策略動態加權）
- ✅ 智能策略選擇器（市場狀態→最佳策略）
- ✅ 策略競技場（遺傳算法單策略優化）
- ✅ 階段路由器（9 階段動態切換）
- ✅ 組合優化器（全局多階段最優解）
- ✅ 強化學習融合代理（PPO 自主學習）

---

## 🏗️ 架構總覽

```
src/bioneuronai/strategies/
├── __init__.py              # 模組入口 (102 行)
├── base_strategy.py         # 策略抽象基類 (779 行)
│
├── trend_following.py       # 趨勢跟隨策略 (1,192 行)
├── swing_trading.py         # 波段交易策略 (1,338 行)
├── mean_reversion.py        # 均值回歸策略 (1,295 行)
├── breakout_trading.py      # 突破交易策略 (1,194 行)
│
├── strategy_fusion.py       # AI 策略融合 (1,144 行)
├── strategy_arena.py        # 策略競技場 GA (629 行)
├── phase_router.py          # 階段路由器 (948 行)
├── portfolio_optimizer.py   # 組合優化器 (591 行)
├── rl_fusion_agent.py       # RL 融合代理 (670 行)
│
└── selector/                # 策略選擇子模組
    ├── __init__.py          # 子模組入口 (80 行)
    ├── core.py              # 選擇器核心 (629 行)
    ├── evaluator.py         # 市場評估器 (355 行)
    ├── evaluator_new.py     # 市場評估器 v2 (392 行)
    ├── configs.py           # 策略配置模板 (391 行)
    └── types.py             # 型別定義 (119 行)
                               ─────────
                               合計 ~9,882 行
```

---

## 🏛️ 三層策略體系

```
╔══════════════════════════════════════════════╗
║     Layer 3: PortfolioOptimizer              ║
║     全局多階段策略組合優化                       ║
╚════════════════╦═════════════════════════════╝
                 │
        ┌────────┼────────┐
        │        │        │
    ┌───┴───┐ ┌──┴──┐ ┌───┴──┐
    │ OPEN  │ │ MID │ │CLOSE │
    └───┬───┘ └──┬──┘ └──┬───┘
        │        │       │
    ┌───┴────────┴───────┴───┐
    │  Layer 2: PhaseRouter   │
    │  (9 階段動態路由)         │
    └────────┬────────────────┘
             │
    ┌────────┼────────┐
    │        │        │
 ┌──┴──┐ ┌──┴──┐ ┌───┴──┐
 │Arena│ │Arena│ │Arena │
 │(GA) │ │(GA) │ │(GA)  │
 └──┬──┘ └──┬──┘ └──┬───┘
    │        │       │
 ┌──┴──┐ ┌──┴──┐ ┌──┴──┐ ┌──────┐
 │Trend│ │Swing│ │Mean │ │Break │
 │Foll.│ │Trade│ │Rev. │ │out   │
 └─────┘ └─────┘ └─────┘ └──────┘
     Layer 1: 基礎策略 (BaseStrategy)
```

---

## 📊 基礎策略

### `base_strategy.py` — 策略抽象基類 (779 行)

所有策略的 ABC 基類，定義統一接口。

**核心 Enum / dataclass**:
- `StrategyState` · `SignalStrength` · `MarketCondition`
- `TradeSetup` · `TradeExecution` · `PositionManagement`
- `RiskParameters` · `StrategyPerformance` · `StrategyRegistry`

### 四種基礎策略

| 策略 | 檔案 | 行數 | 核心指標 | 適用場景 |
|------|------|------|---------|---------|
| 趨勢跟隨 | `trend_following.py` | 1,192 | EMA(21/55/200), MACD, ADX, ATR | 明確趨勢市 |
| 波段交易 | `swing_trading.py` | 1,338 | 支撐阻力位, RSI, Stochastic | 區間震盪市 |
| 均值回歸 | `mean_reversion.py` | 1,295 | Bollinger, Keltner, Z-Score, RSI | 過度偏離 |
| 突破交易 | `breakout_trading.py` | 1,194 | 盤整區識別, 放量突破, 回踩確認 | 整理後突破 |

---

## 🤖 策略融合

### `strategy_fusion.py` — AI 策略融合系統 (1,144 行)

多策略信號動態加權融合，整合所有基礎策略的輸出。

**主要類**: `AIStrategyFusion`  
**Enum / dataclass**: `FusionMethod` · `FusionSignal` · `MarketRegime`

**融合方法**:
- 加權平均融合
- 投票機制融合
- 動態信心加權

---

## 🔍 策略選擇器 (`selector/` 子模組)

根據當前市場狀態智能推薦最佳策略。

| 檔案 | 行數 | 職責 |
|------|------|------|
| `core.py` | 629 | 選擇器主邏輯，整合 v1 配置 + v2 策略 + AI Fusion |
| `evaluator.py` | 355 | 市場評估器（ADX 體制識別、策略評分） |
| `evaluator_new.py` | 392 | 市場評估器 v2（擴充邏輯） |
| `configs.py` | 391 | 10 種預定義策略配置模板 |
| `types.py` | 119 | `StrategyConfigTemplate` · `StrategySelectionResult` 等型別 |

**統一接口**: `StrategySelector.recommend_strategy(market_data)` → `StrategySelectionResult`

---

## 🧬 策略進化系統

### StrategyArena — 策略競技場 (629 行)
遺傳算法驅動的單策略參數優化。支援多進程回測、自動排名淘汰。

**主要類**: `StrategyArena` · `ArenaConfig` · `StrategyCandidate` · `RankMetric` (Enum)

### PhaseRouter — 階段路由器 (948 行)
依照交易時段 / 事件動態切換策略，支援 9 個交易階段。

**主要類**: `TradingPhaseRouter` · `TradingPhase` (Enum) · `PhaseConfig`

### PortfolioOptimizer — 組合優化器 (591 行)
全局遺傳算法尋找最優多階段策略組合。

**主要類**: `StrategyPortfolioOptimizer` · `OptimizationObjective` (Enum)

### RLFusionAgent — 強化學習融合代理 (670 行)
PPO 強化學習代理，自主學習策略融合邏輯。

**依賴**: `gymnasium` · `stable-baselines3` · `torch.nn`

---

## 📦 導出 API

```python
from bioneuronai.strategies import (
    # 基類
    BaseStrategy,

    # 基礎策略
    TrendFollowingStrategy,
    SwingTradingStrategy,
    MeanReversionStrategy,
    BreakoutTradingStrategy,

    # 融合與選擇
    AIStrategyFusion,
    StrategySelector,

    # 進化系統
    StrategyArena,
    TradingPhaseRouter,
    StrategyPortfolioOptimizer,
)
```

---

## 💡 使用示例

### 基礎策略
```python
from bioneuronai.strategies import TrendFollowingStrategy

strategy = TrendFollowingStrategy()
setup = strategy.analyze(market_data)
if setup.is_valid:
    execution = strategy.generate_trade(setup)
```

### AI 融合
```python
from bioneuronai.strategies import AIStrategyFusion

fusion = AIStrategyFusion(strategies=[trend, swing, mean_rev, breakout])
signal = fusion.generate_fused_signal(market_data)
print(f"融合信號: {signal.direction}, 信心: {signal.confidence}")
```

### 策略進化
```python
from bioneuronai.strategies import StrategyArena

arena = StrategyArena(config=ArenaConfig(population_size=50))
best = arena.run_evolution(generations=100, market_data=historical)
print(f"最優策略: {best.name}, Sharpe: {best.sharpe_ratio}")
```

---

## 📚 相關文檔

- **策略進化指南**: [STRATEGY_EVOLUTION_GUIDE.md](../../../docs/STRATEGY_EVOLUTION_GUIDE.md)
- **策略快速參考**: [STRATEGIES_QUICK_REFERENCE.md](../../../docs/STRATEGIES_QUICK_REFERENCE.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026 年 2 月 15 日

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
