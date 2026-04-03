# 交易管理模組 (Trading Management)

**路徑**: `src/bioneuronai/trading/`  
**版本**: v4.2
**更新日期**: 2026-04-02  
**架構層級**: Layer 3 — 交易管理層

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [架構總覽](#架構總覽)
3. [核心組件](#核心組件)
4. [自動化流程](#自動化流程)
5. [導出 API](#導出-api)
6. [使用示例](#使用示例)
7. [相關文檔](#相關文檔)

---

## 🎯 模組概述

交易管理模組負責從市場分析到訂單執行的完整交易流程管理。它將底層的 data、strategies、risk_management 模組串聯起來，提供 10 步驟系統化交易計劃、SOP 自動化、交易前檢查等高層業務邏輯。

### 模組職責
- ✅ 10 步驟系統化交易計劃控制
- ✅ SOP 每日市場分析自動化
- ✅ 交易前自動檢查（Fail Fast）
- ✅ 智能策略選擇與切換
- ✅ 市場環境全面分析
- ✅ 風險管理（向後兼容封裝）
- ✅ 交易對篩選

---

## 🏗️ 架構總覽

```
src/bioneuronai/trading/
├── __init__.py              # 模組入口 (52 行)
├── plan_controller.py       # 10 步驟交易計劃控制器 (766 行)
├── market_analyzer.py       # 市場環境分析器 (1,078 行)
├── risk_manager.py          # 風險管理器封裝 (1,394 行)
├── pretrade_automation.py   # 交易前檢查系統 (1,156 行)
├── trading_plan_system.py   # TradingPlanGenerator 相容層（57 行，委派 plan_controller）
└── pair_selector.py         # 交易對選擇器 (109 行)
                               ─────────
                               合計 ~4,612 行（實測）
```

---

## 🎯 核心組件

### `plan_controller.py` — 10 步驟交易計劃控制器 (766 行)

系統化交易流程的總指揮，按序執行 10 個步驟。

**主要類**: `TradingPlanController`

**10 步驟流程**:

| 步驟 | 名稱 | 說明 |
|------|------|------|
| 1 | 系統環境檢查 | API 連接 · 帳戶狀態 |
| 2 | 宏觀掃描 | 全球股市 · 經濟事件 |
| 3 | 技術分析 | K 線 · 指標 · 型態 |
| 4 | 基本面情緒 | 新聞 · 恐慌貪婪 |
| 5 | 策略評估 | 市場體制→策略匹配 |
| 6 | 策略權重 | 動態權重分配 |
| 7 | 風險參數 | 倉位 · 槓桿 · 止損 |
| 8 | 資金管理 | 總風險曝險控制 |
| 9 | 交易對篩選 | 流動性 · 波動率 |
| 10 | 執行監控 | 訂單執行 · 回報 |

---

### `market_analyzer.py` — 市場環境分析器 (1,078 行)

整合外部數據源進行全面市場狀態評估。

**主要 dataclass**:
- `MarketCondition` — 趨勢 / 波動率 / 恐貪指數
- `TechnicalEnvironment` — 支撐阻力 / 指標 / 突破概率
- `FundamentalEnvironment` — 基本面環境

---

### `strategies/selector/` — 智能策略選擇器（主實作）

根據市場狀態選擇最佳交易策略，支持 10 種策略類型。

**主要類**: `StrategyType` (Enum) — 趨勢跟隨 / 均值回歸 / 動量 / 突破 / 網格等  
**整合**: `AIStrategyFusion` · `EventContext` 事件驅動調整

> ✅ 已統一使用 `src/bioneuronai/strategies/selector/`。`plan_controller.py` 也已切換到此路徑。

---

### `pretrade_automation.py` — 交易前檢查系統 (1,156 行)

單筆交易前的自動化檢查系統（SOP 第二步），遇錯即停。

**主要類**: `PreTradeCheckSystem`
**檢查項目**: `TechnicalSignalCheck` (RSI/MACD/布林帶) · `FundamentalCheck` (資金流/成交量/深度) · `RiskCalculation`

**新聞檢查路徑（2026-03-30 更新）**：`_check_major_news()` 採 **RAG 單一路徑** 設計：
1. 透過 `_get_news_adapter()` 延遲初始化 `NewsAdapter`，取得結構化新聞結果（含 `sentiment_score`）與事件分數（`RuleBasedEvaluator.get_current_event_score()`）。
2. **不做 legacy fallback**，避免把系統失敗誤判為「無重大利空」。
3. 重大利空判定閾值：`SENTIMENT_THRESHOLD = -0.3`、`EVENT_THRESHOLD = -0.5`。
4. 回傳 dict 統一包含：`status`（`OK` / `NO_DATA` / `ERROR`）、`has_major_negative`、`sentiment_score`、`event_score`、`articles_count`、`rag_available`。

---

### `analysis/daily_report/__init__.py` — SOP 每日報告系統（主實作）

每日開盤前自動生成市場分析報告。

**主要類**: `SOPAutomationSystem`  
**報告內容**: `MarketEnvironmentCheck` (全球股市/加密情緒/經濟事件) · `TradingPlanCheck` (策略/風險/交易對)

---

### `risk_manager.py` — 風險管理器封裝 (1,394 行)

向後兼容的風險管理接口，實際類別與參數統一從 `risk_management.position_manager` 導入。

**主要類**: `RiskManager`  
**導入的類型**: `RiskLevel` · `PositionType` · `RiskParameters` · `PositionSizing` · `PortfolioRisk` · `RiskAlert`

---

### 其他組件

| 檔案 | 行數 | 說明 |
|------|------|------|
| `trading_plan_system.py` | 57 行 | 保留 `TradingPlanGenerator` 舊入口，實際委派 `TradingPlanController`（單一路徑） |
| `pair_selector.py` | 109 行 | 交易對篩選（骨架實現，回傳預設 BTC/ETH/BNB） |

---

## 🔄 自動化流程

```
每日開盤前                      單筆交易前
┌──────────────┐              ┌─────────────────┐
│ SOPAutomation │             │ PreTradeCheck    │
│              │              │                 │
│ ① 全球市場掃描│              │ ① 技術信號驗證   │
│ ② 加密情緒分析│              │ ② 基本面檢查     │
│ ③ 經濟日曆    │              │ ③ 風險計算       │
│ ④ 策略建議    │              │ ④ 倉位計算       │
│ ⑤ 風險參數    │              │ ⑤ Go/No-Go 決策 │
└──────┬───────┘              └────────┬────────┘
       │                               │
       └──────────┬────────────────────┘
                  ↓
         TradingPlanController
         (10 步驟執行)
```

---

## 📦 導出 API

```python
from bioneuronai.trading import (
    TradingPlanController,   # 10 步驟計劃控制器
    MarketAnalyzer,          # 市場環境分析器
    StrategySelector,        # 智能策略選擇器 (from strategies.selector)
    RiskManager,             # 風險管理器
    PairSelector,            # 交易對選擇器
    PreTradeCheckSystem,     # 交易前檢查
    TradingPlanGenerator,    # 相容入口（內部委派 TradingPlanController）
)
```

---

## 💡 使用示例

### SOP 自動化
```python
from bioneuronai.analysis.daily_report import SOPAutomationSystem

sop = SOPAutomationSystem(connector=connector)
report = sop.execute_daily_premarket_check()
```

### 交易前檢查
```python
from bioneuronai.trading import PreTradeCheckSystem

checker = PreTradeCheckSystem()
result = checker.execute_pretrade_check(
    symbol="BTCUSDT",
    intended_action="LONG",
)
if result.get("overall_passed"):
    print("✅ 通過所有檢查，可以交易")
```

### 策略選擇
```python
from bioneuronai.trading import StrategySelector

selector = StrategySelector(enable_ai_fusion=True)
recommendation = selector.recommend_strategy(market_data)
print(f"推薦策略: {recommendation.strategy_type}")
```

---

## 📚 相關文檔

- **交易計劃 10 步**: [TRADING_PLAN_10_STEPS.md](../../../docs/TRADING_PLAN_10_STEPS.md)
- **每日報告清單**: [DAILY_REPORT_CHECKLIST.md](../../../docs/DAILY_REPORT_CHECKLIST.md)
- **交易成本指南**: [TRADING_COSTS_GUIDE.md](../../../docs/TRADING_COSTS_GUIDE.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026-04-02

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
