# 規劃模組 (Planning)

> 路徑：`src/bioneuronai/planning/`
> 更新日期：2026-04-23
> 架構層級：Layer 3 — 高階規劃與交易前檢查

`planning` 負責把分析結果整理成可執行的交易計畫與進場前檢查結論。這一層不處理實際訂單與帳戶事實，也不直接承載基礎策略實作。

---

## 目錄

1. [模組定位](#模組定位)
2. [實際結構](#實際結構)
3. [主流程](#主流程)
4. [核心檔案](#核心檔案)
5. [對外匯出](#對外匯出)
6. [維護邊界](#維護邊界)

---

## 模組定位

`planning` 目前承接 4 類工作：

1. 10 步驟交易計畫建立
2. 市場環境分析與風險摘要
3. 交易對篩選
4. 單筆交易前檢查

和相鄰模組的邊界：

1. `analysis/` 提供新聞、關鍵字、daily report 等分析能力
2. `strategies/` 提供策略選擇與策略訊號能力
3. `trading/` 提供交易執行事實與虛擬帳戶狀態

---

## 實際結構

```text
planning/
├── __init__.py
├── plan_controller.py     # 10 步驟交易計畫主控制器
├── market_analyzer.py     # 市場條件 / 技術 / 基本面整合分析
├── pair_selector.py       # 依真實 24h 行情篩選交易對
├── pretrade_automation.py # 單筆交易前檢查自動化
└── README.md
```

檔案對照：
1. [__init__.py](__init__.py)
2. [plan_controller.py](plan_controller.py)
3. [market_analyzer.py](market_analyzer.py)
4. [pair_selector.py](pair_selector.py)
5. [pretrade_automation.py](pretrade_automation.py)

這個資料夾目前沒有更深一層的 README 子文件，因此本文件直接維護到檔案與主流程層級。

---

## 主流程

### 交易計畫路徑

```text
TradingPlanController
  -> MarketAnalyzer
  -> StrategySelector / PairSelector
  -> RiskManager
  -> 10-step plan result
```

### 單筆進場前檢查路徑

```text
PreTradeCheckSystem
  -> BinanceFuturesConnector
  -> NewsAdapter / RAG
  -> TradingCostCalculator
  -> risk / liquidity / news / order checks
```

---

## 核心檔案

### `plan_controller.py`

1. 主類：`TradingPlanController`
2. 主入口：`create_comprehensive_plan()`
3. 定位：整合 10 步驟流程，不直接做低階交易執行

### `market_analyzer.py`

1. 主類：`MarketAnalyzer`
2. 提供市場條件、技術環境、基本面環境分析
3. 被 `plan_controller.py` 作為上游分析器使用

### `pair_selector.py`

1. 主類：`PairSelector`
2. 依 Binance 24h 行情做候選交易對篩選
3. connector 不可用時會回退到保守預設清單

### `pretrade_automation.py`

1. 主類：`PreTradeCheckSystem`
2. 專注於單筆交易前檢查，不等同於每日完整交易計畫
3. 已接通 `NewsAdapter` / `InternalKnowledgeBase` / `TradingCostCalculator`

---

## 對外匯出

```python
from bioneuronai.planning import (
    TradingPlanController,
    MarketAnalyzer,
    PairSelector,
    PreTradeCheckSystem,
    get_trading_plan_controller,
)
```

補充：
1. `get_trading_plan_controller()` 會回傳 `TradingPlanController` 實例
2. 目前這是便利工廠，不是另一條獨立規劃主線

---

## 維護邊界

1. 本文件維護 `planning/` 的責任切分與主流程。
2. 若後續在此目錄下新增子目錄與子 README，上層 `src/bioneuronai/README.md` 應加上對應連結。
3. 不在這層文件重複記錄 `analysis/`、`strategies/`、`trading/` 的內部細節。

---

> 上層目錄：[BioNeuronai README](../README.md)
