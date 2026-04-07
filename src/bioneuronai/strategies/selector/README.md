# 策略選擇器子模組 (`selector/`)

**路徑**: `src/bioneuronai/strategies/selector/`  
**架構層級**: `strategies/` 內的策略選擇子模組  
**定位**: 根據市場體制、波動率、策略適配度與可選事件資訊，輸出策略推薦或詳細策略組合結果

---

## 📑 目錄

1. 模組概述
2. 目前實際職責
3. 檔案結構
4. 主要資料流
5. 核心類與函式
6. Schema 與型別邊界
7. 主路徑與替代實作
8. 使用方式
9. 對外導出 API
10. 與其他模組的關係
11. 已知限制

---

## 模組概述

`selector/` 是 `strategies/` 下面專門負責「策略選擇」的子模組。它不是直接生成交易信號的基礎策略，而是站在更高一層，回答這些問題：

- 目前市場體制比較像哪一種？
- 哪些策略在這種體制下比較適合？
- 在目前資金條件下，哪些策略可行？
- 若啟用 AI Fusion，是否應提升 AI 融合策略的優先級？
- 若要輸出更完整結果，主策略、備援策略與策略 mix 應該怎麼給？

這個子模組目前已經取代較舊的：

- `src/bioneuronai/trading/strategy_selector.py`
- `src/bioneuronai/trading/strategy_selector_v2.py`

它的設計重點是：

- 保留 `v1` 的詳細配置模板與 async 詳細選擇結果
- 吸收 `v2` 的實際策略實例化與 AI Fusion 支援
- 讓 `strategies/` 本身成為策略選擇的主來源，而不是再回到 `trading/` 放另一套邏輯

---

## 目前實際職責

依目前工作樹，`selector/` 的實際職責可分成 4 類：

1. **市場體制識別**
   - 依 OHLCV 判斷 `MarketRegime`
   - 目前主邏輯由 `evaluator.py` 提供

2. **策略評分與可行性篩選**
   - 依市場體制、帳戶資金、策略模板等因素評分
   - 篩出可行策略，再選出主策略與備援策略

3. **AI Fusion 整合**
   - 若可用，將 `AIStrategyFusion` 納入推薦流程
   - 可根據 AI 融合信號提升 `AI_FUSION` 的優先度

4. **統一輸出接口**
   - 簡化版：`recommend_strategy(...) -> StrategyRecommendation`
   - 詳細版：`select_optimal_strategy(...) -> StrategySelectionResult`

---

## 檔案結構

```text
src/bioneuronai/strategies/selector/
├── __init__.py
├── core.py
├── evaluator.py
├── configs.py
└── types.py
```

各檔案職責如下：

### `__init__.py`

子模組統一入口，負責：

- 重新導出 `StrategySelector`
- 重新導出 `MarketEvaluator`
- 重新導出 `types.py` 中的型別
- 重新導出 `configs.py` 中的配置函式與常量

同時在檔頭明確標示：

- 建立日期：`2026-01-25`
- 取代：`trading/strategy_selector.py`、`trading/strategy_selector_v2.py`

### `core.py`

核心實作，定義：

- `StrategySelector`
- `get_recommended_strategy()`

這個檔案整合了：

- `v1` 的詳細策略配置與 async 詳細選擇 API
- `v2` 的實際策略實例化與 AI Fusion 原生支援

它也是目前整個子模組的**主路徑**。

### `evaluator.py`

目前 `core.py` 實際導入的主評估器：

- `MarketEvaluator`

負責：

- `identify_market_regime()`
- `calculate_volatility()`
- `score_strategies()`
- 單一策略評分與篩選

### `configs.py`

提供靜態策略配置模板與查找函式：

- `get_default_strategy_configs()`
- `get_strategy_by_type()`
- `STRATEGY_ALIASES`

目前內建 **10 種預定義策略配置模板**，包含：

- `MA_Crossover_Trend`
- `RSI_Mean_Reversion`
- `Momentum_Breakout`
- `High_Frequency_Scalp`
- `Grid_Trading`
- `Volatility_Trading`
- `News_Trading`
- `Breakout_Trading`
- `Swing_Trading`
- `Arbitrage_Trading`

注意：

- 這些是**配置模板**
- 不是所有模板都必然對應到 `strategies/` 內有完整的即時實例策略類

### `types.py`

只放**模組專屬內部型別**，同時從 `schemas` 重新導出通用型別。

模組專屬型別包括：

- `StrategyConfigTemplate`
- `StrategySelectionResult`
- `InternalPerformanceMetrics`

從 `schemas` 重新導出的包括：

- `StrategyType`
- `MarketRegime`
- `Complexity`
- `RiskLevel`
- `StrategyRecommendation`
- `STRATEGY_MARKET_FIT`

這個設計符合 `CODE_FIX_GUIDE.md` 的原則：

- 通用 schema 來自 `src/schemas/`
- 子模組只在本地保留真正模組專屬的內部結構

---

## 主要資料流

### 簡化推薦路徑

```text
OHLCV ndarray
   ↓
MarketEvaluator.identify_market_regime()
   ↓
StrategySelector._calculate_strategy_weights()
   ↓
StrategySelector._identify_avoid_strategies()
   ↓
可選：AI Fusion 調整
   ↓
RiskLevel / suggested_position_size
   ↓
StrategyRecommendation
```

### 詳細選擇路徑

```text
OHLCV ndarray
   ↓
MarketEvaluator.identify_market_regime()
   ↓
MarketEvaluator.score_strategies()
   ↓
MarketEvaluator.filter_viable_strategies()
   ↓
_select_primary()
_select_backups()
_calculate_mix()
_assess_risk()
_estimate_performance()
   ↓
StrategySelectionResult
```

---

## 核心類與函式

## `StrategySelector`

定義於 [core.py](C:/D/E/BioNeuronai/src/bioneuronai/strategies/selector/core.py)。

### 初始化參數

```python
StrategySelector(
    timeframe: str = "1h",
    enable_ai_fusion: bool = True,
    enable_learning: bool = True,
)
```

### 初始化時做的事

1. 載入 `configs.py` 的預設策略模板
2. 建立 `MarketEvaluator`
3. 嘗試實例化可用的實際策略：
   - `TrendFollowingStrategy`
   - `SwingTradingStrategy`
   - `MeanReversionStrategy`
   - `BreakoutTradingStrategy`
4. 若啟用，建立 `AIStrategyFusion`
5. 初始化績效歷史結構

### 重要方法

#### `recommend_strategy(...)`

```python
recommend_strategy(
    ohlcv_data: np.ndarray,
    account_balance: float = 10000.0,
    use_ai_fusion: bool = True,
    event_score: float = 0.0,
    event_context: Optional[Any] = None,
) -> StrategyRecommendation
```

用途：

- 較輕量的同步推薦 API
- 回傳 `schemas.strategy.StrategyRecommendation`

主要流程：

- 識別市場體制
- 計算策略權重
- 找出應避免的策略
- 可選套用 AI Fusion
- 根據波動率推估風險等級與建議倉位
- 補充策略原因說明

#### `select_optimal_strategy(...)`

```python
async select_optimal_strategy(
    ohlcv_data: np.ndarray,
    account_balance: float = 10000.0,
    preferences: Optional[Dict] = None,
) -> StrategySelectionResult
```

用途：

- 詳細版 async API
- 回傳 `StrategySelectionResult`

輸出內容包含：

- `primary_strategy`
- `backup_strategies`
- `strategy_mix`
- `confidence_score`
- `market_match_score`
- `reasoning`
- `risk_assessment`
- `expected_performance`

#### `get_strategy_signals(...)`

取得目前已實例化策略的原始信號結果。

注意：

- 只會對 `_strategies` 裡已成功初始化的策略執行
- 目前不涵蓋 `configs.py` 中全部 10 個模板

#### `get_ai_fusion_signal(...)`

若 AI Fusion 可用，回傳融合後的信號摘要字典。

#### `record_trade_result(...)`

將交易結果回寫給 evaluator，並在 AI Fusion 可用時更新權重。

#### `get_performance_summary(...)`

回傳目前 selector 已知的策略可用性與績效摘要。

#### `save_state(...)` / `load_state(...)`

若 AI Fusion 存在，委派其進行狀態保存與載入。

### 重要屬性

- `ai_fusion_available`
- `strategies_available`

---

## `MarketEvaluator`

定義於 [evaluator.py](C:/D/E/BioNeuronai/src/bioneuronai/strategies/selector/evaluator.py)。

### 目前主責

- 市場體制識別
- 波動率與風險等級估計
- 策略評分
- 可行策略篩選
- 績效追蹤

### 目前市場體制判斷基礎

主要依賴：

- `SMA 20 / SMA 50`
- 趨勢強度
- 近端波動率
- 波動率比率
- 價格區間
- `ADX`

可能回傳的 `MarketRegime` 例如：

- `TRENDING_BULL`
- `TRENDING_BEAR`
- `VOLATILE_UNCERTAIN`
- `BREAKOUT_POTENTIAL`
- `SIDEWAYS_LOW_VOL`
- `SIDEWAYS_HIGH_VOL`

---

## Schema 與型別邊界

這個子模組目前的型別邊界是清楚的：

### 來自 `src/schemas/`

通用、跨模組共享：

- `StrategyType`
- `MarketRegime`
- `Complexity`
- `RiskLevel`
- `StrategyRecommendation`
- `STRATEGY_MARKET_FIT`

### 留在 `selector/types.py`

只在 selector 內部較有意義的型別：

- `StrategyConfigTemplate`
- `StrategySelectionResult`
- `InternalPerformanceMetrics`

這個邊界是正確的，因為：

- `StrategyRecommendation` 已經是對外較穩定的通用結構
- `StrategySelectionResult` 還偏 selector 的內部詳細結果
- `StrategyConfigTemplate` 是靜態模板，不等於實際策略執行狀態

---

## 主路徑與替代實作

目前需特別注意以下實際狀況：

### 主路徑

- `core.py`
- `evaluator.py`
- `configs.py`
- `types.py`

目前 selector 只有一套正式評估器：

- `__init__.py` 匯出的是 `evaluator.py` 的 `MarketEvaluator`
- `core.py` 也直接 `from .evaluator import MarketEvaluator`

因此目前 README 與後續分析都應以 `evaluator.py` 為準。

---

## 使用方式

### 基本同步推薦

```python
import numpy as np
from bioneuronai.strategies.selector import StrategySelector

selector = StrategySelector(timeframe="1h")
ohlcv_data = np.array([...])  # columns: timestamp, open, high, low, close, volume

recommendation = selector.recommend_strategy(
    ohlcv_data,
    account_balance=10000.0,
)

print(recommendation.primary_strategy)
print(recommendation.market_regime)
```

### 使用 AI Fusion 與事件資訊

```python
selector = StrategySelector(timeframe="1h", enable_ai_fusion=True)

recommendation = selector.recommend_strategy(
    ohlcv_data,
    account_balance=10000.0,
    use_ai_fusion=True,
    event_score=2.5,
    event_context=event_context,
)
```

### 取得詳細策略選擇結果

```python
selection = await selector.select_optimal_strategy(
    ohlcv_data,
    account_balance=10000.0,
    preferences={"prefer_low_drawdown": True},
)

print(selection.primary_strategy.name if selection.primary_strategy else None)
print(selection.strategy_mix)
print(selection.reasoning)
```

### 便捷函式

```python
from bioneuronai.strategies.selector import get_recommended_strategy

recommendation = get_recommended_strategy(
    ohlcv_data,
    timeframe="1h",
    use_ai_fusion=True,
)
```

---

## 對外導出 API

透過 [__init__.py](C:/D/E/BioNeuronai/src/bioneuronai/strategies/selector/__init__.py) 對外導出的主要項目有：

### 核心類

- `StrategySelector`
- `MarketEvaluator`

### 型別

- `StrategyType`
- `MarketRegime`
- `Complexity`
- `StrategyConfigTemplate`
- `StrategySelectionResult`
- `StrategyRecommendation`
- `InternalPerformanceMetrics`

### 配置與常量

- `get_default_strategy_configs`
- `get_strategy_by_type`
- `STRATEGY_ALIASES`
- `STRATEGY_MARKET_FIT`

### 便捷函式

- `get_recommended_strategy`

---

## 與其他模組的關係

### 上游輸入

- `OHLCV numpy.ndarray`
- 可選 `event_score`
- 可選 `event_context`
- 可選 `preferences`

### 下游依賴

- `strategies/` 的實際策略類
- `strategy_fusion.py` 的 `AIStrategyFusion`
- `schemas/` 的通用 enum / recommendation schema

### 目前已知整合點

- [src/bioneuronai/strategies/__init__.py](C:/D/E/BioNeuronai/src/bioneuronai/strategies/__init__.py)
- [src/bioneuronai/trading/__init__.py](C:/D/E/BioNeuronai/src/bioneuronai/trading/__init__.py)
- [src/bioneuronai/trading/plan_controller.py](C:/D/E/BioNeuronai/src/bioneuronai/trading/plan_controller.py)

其中 [plan_controller.py](C:/D/E/BioNeuronai/src/bioneuronai/trading/plan_controller.py) 已經在步驟 5 / 6 使用 `StrategySelector`，所以這個子模組不是孤立實驗碼，而是主流程的一部分。

---

## 已知限制

1. `configs.py` 有 10 種模板，但 `_strategies` 目前只實例化 4 種真實策略類。

2. `event_context` 目前型別仍以 `Any` / 可選導入處理，邊界沒有完全收緊。

3. selector 目前同時承擔：
   - 市場體制識別
   - 策略模板管理
   - AI Fusion 整合
   - 績效摘要  
   功能偏多，後續若再擴充，需注意不要讓 `core.py` 繼續膨脹。

4. 舊版 `trading/strategy_selector.py` 已移除，閱讀或維護時以 `strategies/selector/` 為唯一實作來源。

---

**相關文件**

- [strategies README](C:/D/E/BioNeuronai/src/bioneuronai/strategies/README.md)
- [API integration baseline](C:/D/E/BioNeuronai/docs/API_INTEGRATION_BASELINE.md)
- [CODE_FIX_GUIDE](C:/D/E/BioNeuronai/docs/CODE_FIX_GUIDE.md)
