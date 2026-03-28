# 策略模組 (Strategies)

**路徑**: `src/bioneuronai/strategies/`  
**版本**: v4.3.1
**更新日期**: 2026-03-16
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

策略模組是 BioNeuronai 的核心競爭力所在，實現了從基礎交易策略到 AI 融合再到遺傳演算法進化的三層策略體系。包含 **6 種基礎策略**、AI 融合系統、智能選擇器與完整的進化架構。

### 模組職責
- ✅ 6 種基礎交易策略（趨勢 / 波段 / 均值回歸 / 突破 / 方向變化 / 配對交易）
- ✅ AI 策略融合（整合全部 6 種基礎策略，動態加權）
- ✅ 智能策略選擇器（市場體制識別 → 策略推薦 / 詳細選擇）
- ✅ 策略競技場（遺傳算法單策略優化，支援多進程並行）
- ✅ 階段路由器（9 交易階段動態切換）
- ✅ 組合優化器（全局多階段最優解）
- ✅ 強化學習融合代理（PPO 自主學習，via stable-baselines3）

---

## 🏗️ 架構總覽

```
src/bioneuronai/strategies/
├── __init__.py                    # 模組入口 (102 行)
├── base_strategy.py               # 策略抽象基類 (778 行)
│
├── trend_following.py             # 趨勢跟隨策略 (1,192 行)
├── swing_trading.py               # 波段交易策略 (1,338 行)
├── mean_reversion.py              # 均值回歸策略 (1,295 行)
├── breakout_trading.py            # 突破交易策略 (1,194 行)
├── direction_change_strategy.py   # 方向變化策略 DC (2026-03-09)
├── pair_trading_strategy.py       # 配對交易策略 (2026-03-09)
│
├── strategy_fusion.py             # AI 策略融合 (1,159 行)
├── strategy_arena.py              # 策略競技場 GA (642 行)
├── phase_router.py                # 階段路由器 (947 行)
├── portfolio_optimizer.py         # 組合優化器 (590 行)
├── rl_fusion_agent.py             # RL 融合代理 (669 行)
│
└── selector/                      # 策略選擇子模組
    ├── __init__.py                # 子模組入口
    ├── core.py                    # 選擇器核心
    ├── evaluator.py               # 目前主路徑市場評估器
    ├── evaluator_new.py           # 保留中的替代評估器
    ├── configs.py                 # 策略配置模板
    ├── types.py                   # 型別定義
    └── README.md                  # 子模組詳細說明
```

---

## 🏛️ 三層策略體系

```
╔══════════════════════════════════════════════════════╗
║        Layer 3: PortfolioOptimizer                   ║
║        全局多階段策略組合優化（遺傳算法）                  ║
╚════════════════╦═════════════════════════════════════╝
                 │
        ┌────────┼────────┐
        │        │        │
    ┌───┴───┐ ┌──┴──┐ ┌───┴──┐
    │ OPEN  │ │ MID │ │CLOSE │  (via StrategyArena × 3)
    └───┬───┘ └──┬──┘ └──┬───┘
        │        │       │
    ┌───┴────────┴───────┴────┐
    │   Layer 2: PhaseRouter   │
    │   9 交易階段動態路由         │
    └─────────┬───────────────┘
              │
   ┌──────────┴──────────┐
   │  AIStrategyFusion    │   ← PPO RL Agent (rl_fusion_agent)
   │  (strategy_fusion)   │
   └──────────┬───────────┘
              │  整合全部 6 種基礎策略
   ┌──────────┼──────────────────────┐
   │          │            │         │
 ┌─┴──┐  ┌───┴──┐  ┌──────┴┐  ┌────┴────┐  ┌────┐  ┌────┐
 │Tre.│  │Swing │  │Mean   │  │Breakout │  │ DC │  │Pair│
 │Fol.│  │Trade │  │Rev.   │  │Trade    │  │    │  │Trd.│
 └────┘  └──────┘  └───────┘  └─────────┘  └────┘  └────┘
               Layer 1: 基礎策略 (BaseStrategy)
```

**PhaseRouter 9 個交易階段**:  
`MARKET_OPEN` · `EARLY_SESSION` · `MID_SESSION` · `LATE_SESSION` · `MARKET_CLOSE`  
`PRE_NEWS` · `POST_NEWS` · `HIGH_VOLATILITY` · `LOW_VOLATILITY`

---

## 📊 基礎策略

### `base_strategy.py` — 策略抽象基類 (779 行)

所有策略的 ABC 基類，定義統一接口與交易生命週期（analyze_market → entry → manage_position → exit → risk_control）。

**核心 Enum / dataclass**:
- `StrategyState` · `SignalStrength` · `MarketCondition`
- `TradeSetup` · `TradeExecution` · `PositionManagement`
- `RiskParameters` · `StrategyPerformance` · `StrategyRegistry`

### 六種基礎策略

| 策略 | 檔案 | 核心指標 | 適用場景 |
|------|------|---------|---------|
| 趨勢跟隨 | `trend_following.py` | EMA(21/55/200), MACD, ADX, ATR | 明確趨勢市 |
| 波段交易 | `swing_trading.py` | 支撐阻力 Pivot, RSI, Stochastic | 區間震盪市 |
| 均值回歸 | `mean_reversion.py` | Bollinger Bands, Keltner, Z-Score, RSI | 低波動偏離市 |
| 突破交易 | `breakout_trading.py` | 盤整區識別, 放量突破, ATR, 回踩確認 | 整理後突破 |
| 方向變化 | `direction_change_strategy.py` | DC 事件 θ 閾值, Overshoot (OS) 比率 | 趨勢轉折捕捉 |
| 配對交易 | `pair_trading_strategy.py` | 對數 Spread Z-Score, 協整檢驗 | 市場中性套利 |

#### `direction_change_strategy.py` — 方向變化策略 (DC 算法)

基於事件驅動的 Directional Change (DC) 理論，以價格方向變化事件作為分析基礎，取代傳統固定時間框架。

**核心類**:
- `DCEventType(Enum)` — `UPWARD` / `DOWNWARD`
- `DCEvent` — DC 事件記錄（觸發時間、幅度、前高/低點）
- `DCStrategyAnalysis` — 分析結果（事件序列、OS 比率、趨勢方向）
- `DirectionChangeStrategy(BaseStrategy)` — 主策略類

**交易邏輯**: 確認連續 DC 事件形成趨勢 → 在 OS 回調位進場（逆 OS、順 DC）→ 止損設在前 DC 極值 → 目標 2R/4R/6R

**優勢**: 過濾短期噪音、自適應市場波動（θ 可動態調整）、比固定時框更早發現反轉

#### `pair_trading_strategy.py` — 配對交易策略 (統計套利)

利用兩個具有長期協整關係的加密貨幣（如 BTC/ETH）之間對數價格比率的均值回歸特性進行統計套利。

**核心類**:
- `PairAnalysis` — 配對分析結果（相關係數、協整分數、Z-Score 歷史）
- `PairTradingStrategy(BaseStrategy)` — 主策略類

**交易邏輯**:
- 計算兩資產對數 Spread 的滾動 Z-Score
- Z > +閾值 → 做空 Spread；Z < -閾值 → 做多 Spread
- |Z| 回歸出場閾值 → 平倉

**資料輸入**: `ohlcv_data`（主資產）+ `additional_data['secondary_ohlcv']`（次要資產）

---

## 🤖 策略融合

### `strategy_fusion.py` — AI 策略融合系統 (1,144 行)

整合**全部 6 種基礎策略**的信號，動態加權融合輸出最終交易決策。依市場體制（MarketRegime）自動調整各策略權重。

**主要類**: `AIStrategyFusion`
**dataclass**: `StrategyWeight` · `FusionSignal` · `MarketRegime`
**Enum**: `FusionMethod`

**整合策略**: `TrendFollowingStrategy` · `SwingTradingStrategy` · `MeanReversionStrategy` · `BreakoutTradingStrategy` · `DirectionChangeStrategy` · `PairTradingStrategy`

**融合方法** (`FusionMethod`，5 種)：

| 值 | 說明 |
|----|------|
| `WEIGHTED_VOTE` | 加權投票融合（預設） |
| `BEST_PERFORMER` | 歷史最佳策略優先 |
| `MARKET_ADAPTIVE` | 依市場體制動態調整權重 |
| `CONFIDENCE_BASED` | 依信心分數動態加權 |
| `ENSEMBLE` | 集成融合（綜合以上方法） |

**`MarketRegime`（dataclass，非 Enum）**：

```python
@dataclass
class MarketRegime:
    regime_type: str   # 'trending' | 'ranging' | 'volatile' | 'quiet' | 'transitioning'
    confidence: float  # 0.0 ~ 1.0
    duration_bars: int
    recommended_strategies: List[str]
    avoid_strategies: List[str]
```

**外部依賴**: `from schemas.rag import EventContext`（新聞事件調整權重）

---

## 🔍 策略選擇器 (`selector/` 子模組)

`selector/` 是 `strategies/` 內部的**下一層子模組**，責任比上層 README 更聚焦。  
上層 `strategies/README.md` 只保留架構摘要與定位；`selector/` 的檔案職責、型別邊界、主路徑 / 替代實作、詳細接口與限制，請直接看子模組文件：

- [selector/README.md](C:/D/E/BioNeuronai/src/bioneuronai/strategies/selector/README.md)

### 這一層只強調 4 個重點

1. `selector/` 負責「市場體制 → 策略推薦 / 詳細選擇」，不是基礎策略本身。
2. 目前主路徑是 `core.py + evaluator.py + configs.py + types.py`。
3. `evaluator_new.py` 目前存在，但不是主流程依賴。
4. 這個子模組已取代較舊的 `trading/strategy_selector.py` 系列，且已被 `plan_controller.py` 實際使用。

### 對外主要接口

```python
selector = StrategySelector(timeframe="1h")
recommendation = selector.recommend_strategy(ohlcv_data)
selection = await selector.select_optimal_strategy(ohlcv_data)
```

### 為什麼這裡不重複寫完整細節

因為 `selector/README.md` 和本文件是**不同層級**：

- 本文件：`strategies/` 模組總覽
- 子文件：`selector/` 子模組詳解

因此像以下內容，只保留在子 README：

- `types.py` 的模組專屬型別細節
- `configs.py` 10 種模板的完整說明
- `core.py` 的資料流與方法分工
- `evaluator.py` / `evaluator_new.py` 的主從關係
- selector 與 `schemas/` 的精確邊界

這樣可以避免上下兩層文件重複，並降低後續維護成本。

---

## 🧬 策略進化系統

### StrategyArena — 策略競技場 (`strategy_arena.py`, 629 行)

「養蠱式」遺傳算法驅動的單策略參數優化，讓策略互相競爭、優勝劣汰、自動進化。

**主要類**: `StrategyArena` · `ArenaConfig` · `StrategyCandidate` · `RankMetric(Enum)`

**排名指標** (`RankMetric`，9 種)：

| 值 | 說明 |
|----|------|
| `SHARPE_RATIO` | 夏普比率 |
| `SORTINO_RATIO` | 索提諾比率 |
| `CALMAR_RATIO` | 卡爾瑪比率 |
| `MAX_DRAWDOWN` | 最大回撤 |
| `WIN_RATE` | 勝率 |
| `PROFIT_FACTOR` | 盈虧比 |
| `TOTAL_RETURN` | 總回報 |
| `AVG_TRADE_RETURN` | 平均交易回報 |
| `CONSISTENCY` | 一致性（月度正回報比例） |

**特色**: 多進程並行回測（`ProcessPoolExecutor`）、參數網格搜索

**整合所有 6 種基礎策略**: 可對 TrendFollowing、SwingTrading、MeanReversion、BreakoutTrading、DirectionChange、PairTrading 分別進行 GA 優化。

### PhaseRouter — 階段路由器 (`phase_router.py`, 948 行)

依交易時段與市場事件（極端波動、新聞發布等）動態切換策略。

**主要類**: `TradingPhaseRouter` · `TradingPhase(Enum)` · `TradeActionPhase(Enum)` · `PhaseConfig` · `PhaseState` · `StrategyPerformanceRecord`

**9 個交易階段** (`TradingPhase`):

| 階段 | 說明 |
|------|------|
| `MARKET_OPEN` | 開盤衝擊期 |
| `EARLY_SESSION` | 盤初方向確認 |
| `MID_SESSION` | 主力盤中 |
| `LATE_SESSION` | 盤末調整 |
| `MARKET_CLOSE` | 收盤結算 |
| `PRE_NEWS` | 新聞前靜默期 |
| `POST_NEWS` | 新聞後波動期 |
| `HIGH_VOLATILITY` | 極端高波動 |
| `LOW_VOLATILITY` | 極端低波動 |

### PortfolioOptimizer — 組合優化器 (`portfolio_optimizer.py`, 591 行)

整合 `PhaseRouter` + `StrategyArena`，以遺傳算法尋找全局最優多階段策略組合。

**主要類**: `StrategyPortfolioOptimizer` · `OptimizationObjective(Enum)`

**優化目標** (`OptimizationObjective`):  
`MAXIMIZE_RETURN` · `MAXIMIZE_SHARPE` · `MINIMIZE_DRAWDOWN` · `MAXIMIZE_CONSISTENCY`

**基因編碼**: 各階段的「策略類型 + 策略權重 + 參數向量 + 切換閾值」拼接而成的扁平向量。

### RLFusionAgent — 強化學習融合代理 (`rl_fusion_agent.py`, 670 行)

PPO 強化學習代理，自主學習如何融合多策略信號做出最佳交易決策。

**輸入狀態**: 全部子策略信號 + 市場狀態特徵 + 新聞情緒分數  
**輸出動作**: `long%` / `short%` / `hold` 分配比例

**依賴** (支援可選安裝):
```
gymnasium          # RL 環境框架
stable-baselines3  # PPO 算法實現
torch.nn           # 策略網絡
```
> `SB3_AVAILABLE` 旗標控制，未安裝時降級為規則型融合，不影響核心運作。

---

## 📦 導出 API

```python
from bioneuronai.strategies import (
    # 基類
    BaseStrategy,
    StrategyState, TradeSetup, TradeExecution,
    PositionManagement, RiskParameters, StrategyPerformance,

    # 6 種基礎策略
    TrendFollowingStrategy,
    SwingTradingStrategy,
    MeanReversionStrategy,
    BreakoutTradingStrategy,
    DirectionChangeStrategy,   # DC 事件驅動策略 (2026-03-09)
    PairTradingStrategy,       # 統計套利配對策略 (2026-03-09)

    # AI 融合（整合全部 6 種基礎策略）
    AIStrategyFusion, FusionMethod, FusionSignal, MarketRegime,

    # 階段路由
    TradingPhaseRouter, TradingPhase, TradeActionPhase,
    PhaseConfig, PhaseState, StrategyPerformanceRecord,

    # 策略選擇器
    StrategySelector,
    StrategyType,
    StrategyConfigTemplate,
    StrategySelectionResult,
    StrategyRecommendation,
    MarketEvaluator,
    get_recommended_strategy,

    # 進化系統
    StrategyArena,
    TradingPhaseRouter,
    TradingPhase,
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

### DC 方向變化策略
```python
from bioneuronai.strategies import DirectionChangeStrategy

dc = DirectionChangeStrategy(theta=0.005)  # 0.5% 閾值
analysis = dc.analyze(ohlcv_data)
print(f"DC 趨勢方向: {analysis.trend_direction}, OS 比率: {analysis.overshoot_ratio}")
```

### 配對交易策略
```python
from bioneuronai.strategies import PairTradingStrategy

pair = PairTradingStrategy(entry_z=2.0, exit_z=0.5)
signal = pair.analyze(btc_ohlcv, additional_data={"secondary_ohlcv": eth_ohlcv})
print(f"配對信號: {signal.direction}, Z-Score: {signal.z_score:.2f}")
```

### AI 融合（整合全部 6 種策略）
```python
from bioneuronai.strategies import AIStrategyFusion, FusionMethod

fusion = AIStrategyFusion(fusion_method=FusionMethod.CONFIDENCE_BASED)
signal = fusion.generate_fusion_signal(ohlcv_data, event_score=0.0)
print(f"融合信號: {signal.consensus_direction}, 信心: {signal.confidence_score:.2%}")
```

### 智能策略選擇器
```python
from bioneuronai.strategies import StrategySelector

selector = StrategySelector(timeframe="1h")
result = selector.recommend_strategy(ohlcv_data)       # 同步，回傳 StrategyRecommendation
print(f"推薦策略: {result.strategy_name}, 市場體制: {result.market_regime}")
```

### 策略進化競技場
```python
from bioneuronai.strategies.strategy_arena import StrategyArena, ArenaConfig

arena = StrategyArena(config=ArenaConfig(population_size=50))
best = arena.run()  # 執行完整進化流程，回傳 StrategyCandidate
print(f"最優候選: {best.strategy_name}, Sharpe: {best.metrics.get('sharpe_ratio', 0):.2f}")
```

---

## 📚 相關文檔

- **策略進化指南**: [STRATEGY_EVOLUTION_GUIDE.md](../../../docs/STRATEGY_EVOLUTION_GUIDE.md)
- **策略快速參考**: [STRATEGIES_QUICK_REFERENCE.md](../../../docs/STRATEGIES_QUICK_REFERENCE.md)
- **策略選擇器子模組**: [selector/README.md](C:/D/E/BioNeuronai/src/bioneuronai/strategies/selector/README.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026 年 3 月 16 日

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
