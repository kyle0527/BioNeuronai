# 步驟 1 重做：完整檢查（進行中 → 本檔為檢查結果）

> **重置原因**：先前過早宣稱步驟 1／2 完成；步驟 3 無意義。依使用者要求 **回到步驟 1**。  
> **步驟 3／4／5：暫停。**

---

## 1. 檢查範圍

| 來源 | 內容 |
|------|------|
| A | git purge：`9f6e271^` 的 `archived/`（mirror 約 132 檔） |
| B | 磁碟封存：`archived/legacy_v1_20260711/` |
| C | 現役：`backtest/`、`src/bioneuronai/`、`config/`、`main.py` CLI |

---

## 2. 程式類深比（步驟 1 核心）

### 2.1 Walk-Forward（舊 `backtesting/walk_forward.py`）

| 舊能力 | 現役是否有**程式** | 證據（路徑／符號） | 步驟 1 結論 |
|--------|-------------------|-------------------|-------------|
| 滾動多窗 | ✅ 有 | `backtest/walk_forward.py` → `generate_rolling_windows` | 已在現役，步驟 2 要**驗證**非重寫 |
| 過擬合／穩健分 | ✅ 有 | `run_rolling_walk_forward` 回傳 overfitting_rate / robustness_score | 同上 |
| single 70/30 | ✅ 有 | `run_single_split_walk_forward` + service mode single | 同上 |
| IS param_grid 優化 | ✅ 有 | `expand_param_grid_candidates` / `optimize_parameters_on_train` | 同上 |
| CLI 入口 | ✅ 有 | `main.py strategy-backtest --walk-forward --wf-param-grid` | 同上 |
| 接 StrategySelector suite | ✅ 有 | `service.run_strategy_suite_backtest` 呼叫 `run_rolling_walk_forward` | 同上 |
| 舊 HistoricalBacktest 引擎 | ❌ 不需有 | 由現役 mock + template 取代 | **KEEP-NEW 不移舊引擎** |

**步驟 1 決策**：WF 屬 **HOME 已落地** → 列入步驟 2 清單清單「證明可跑」，不是「尚未移回」。

### 2.2 成本計算（舊 `cost_calculator.py`）

| 舊 | 現役 | 決策 |
|----|------|------|
| Maker/Taker/滑點/funding | `config/trading_costs.py` VIP 表 + funding + breakeven | **KEEP-NEW 不移** |

### 2.3 歷史回測引擎（舊 `historical_backtest.py`）

| 舊 | 現役 | 決策 |
|----|------|------|
| API 拉 K + 自寫 engine | `backtest/` 本地 zip + MockConnector + service | **KEEP-NEW 不移** |

### 2.4 v1 模型鏈（`legacy_v1_20260711`）

| 舊 | 現役 | 決策 |
|----|------|------|
| tiny_llm.py / .pth / teacher / auto_evolve / rag_system | tiny_llm_v2 + unified_trainer + src/rag | **NEVER 不移回現役** |

### 2.5 新聞方向契約（非 purge，屬現役殘留檢查）

| 檢查項 | 現役程式 | 決策 |
|--------|----------|------|
| fusion 不輸出 LONG/SHORT 規則 | `strategy_fusion.get_direction_bias` 強制 NEUTRAL | 已改；步驟 2 驗證 |
| pretrade 用 importance | `pretrade_automation` `event_importance` / `_HIGH_RISK_TYPES` | 已改；步驟 2 驗證 |
| should_trade 非主線閘門 | analyzer 標 Legacy | 已改 |

### 2.6 old_scripts（19）

| 決策 | 理由 |
|------|------|
| **全部 SKIP** | 現役 CLI 已有：trade / backtest / strategy-backtest / autonomous / news / pretrade / evolve / status / chat 等；test_* 不做 pytest 路線 |

無「缺了就無法用主線」的腳本必須移回 `src/`。

### 2.7 文件類（docs_v2/v3、reports、old_docs）

| 決策 | 理由 |
|------|------|
| **不在步驟 2 移進 manuals** | 步驟 4 才系統改使用者手冊 |
| **ARCH** mirror 保留供對照 | 檢查用，不可 import |
| NEVER | 多源新聞指南、v1 TinyLLM 指南當現況 |

---

## 3. 步驟 1 結論摘要

| 類型 | 數量感 | 決策 |
|------|--------|------|
| 必須當現役能力的 HOME | **WF 全套（已寫在現役）** | 步驟 2 = **驗證勾選** |
| KEEP-NEW | cost、historical、關鍵字 505、binance API | 不移舊檔 |
| NEVER | v1、舊多源新聞、舊實驗 .py | 不移 |
| SKIP | old_scripts、snapshots、tests | 不移 |
| ARCH | reports、舊 status、mirror | 不移進 src |

**沒有發現「還有整包舊模組沒搬、導致主線缺能力」的第二個 HOME 大項。**  
（若步驟 2 驗證發現 WF 某條證明失敗，再回頭修程式——那是步驟 2，不是假裝步驟 3。）

---

## 4. 步驟 1 完成定義勾選

- [x] 範圍列清  
- [x] 程式類逐項對現役  
- [x] scripts／docs／v1 決策  
- [x] 產出步驟 2 清單：`MOVE_BACK_CHECKLIST.md`  

**步驟 1：本輪重做後視為完成（2026-07-17）。**  
下一步只做 **步驟 2：依 MOVE_BACK_CHECKLIST 用程式證明／補洞**，不做步驟 3。
