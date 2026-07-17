# 步驟 1 決策表（檢查完成版）

> **日期**：2026-07-17  
> **範圍**：git `9f6e271^` 的 `archived/` purge 文字／腳本／報告（約 136 路徑；mirror 約 132 檔）  
> **步驟 1 完成定義**：每一類都有明確決策；無「unknown 懸空」。

圖例：**HOME** 移回現役｜**MERGE** 步驟 4 併入手冊｜**KEEP-NEW** 現役已優｜**NEVER** 禁止現役｜**ARCH** 只留 mirror 考古｜**SKIP** 不做

---

## A. 程式 code_backtest（5）

| 舊路徑 | 決策 | 步驟 2 處理 |
|--------|------|-------------|
| `backtesting/walk_forward.py` | **HOME** | ✅ 已移：rolling + metrics + **param_grid IS 優化** |
| `backtesting/cost_calculator.py` | **KEEP-NEW** | 不移；`config/trading_costs.py` 更完整 |
| `backtesting/historical_backtest.py` | **KEEP-NEW** | 不移；現役 `backtest/` + 本地 zip |
| `backtesting/README.md` | **ARCH** | mirror 保留 |
| `backtesting/__init__.py` | **ARCH** | 不移 |

## B. 其它舊 .py（3）

| 舊路徑 | 決策 | 理由 |
|--------|------|------|
| `core.py` | **NEVER** | 舊神經元實驗 |
| `hundred_million_net.py` | **NEVER** | 舊網路 |
| `pytorch_100m_model.py` | **NEVER** | 舊 MLP |

## C. old_scripts（19）

| 決策 | 說明 |
|------|------|
| **全部 SKIP／ARCH** | 入口已由 `main.py` CLI 覆蓋；test_* 屬 pytest 路線明確不做 |

逐支：`check_db`、`debug_strategy_signals`、`migrate_to_database`、`run_ai_trading`、`run_backtest_demo`、`simulate_*`、`test_*`、`use_*`、`validate_*` → **不移回 src**；mirror 可查。

## D. docs_user（docs_v2_1_legacy + docs_v3，約 28）

| 決策 | 說明 |
|------|------|
| **KEEP-NEW 或 MERGE@步驟4** | 現役 `docs/manuals/00–20` 已取代操作入口 |
| 例外 **MERGE 已部分做** | SOP 應急→14/18；DATA_SOURCES→15；蒸餾→12（步驟 4 仍會系統修手冊） |
| **NEVER** | `NEWS_ANALYZER_GUIDE`（多源 CryptoPanic 方向） |

步驟 1 檢查結論：無「缺了就無法跑主線」的獨有操作手冊；**不需在步驟 2 把舊 manuals 整包移進 manuals/**（那是步驟 4 的改寫，不是移檔）。

## E. docs_old（約 20）

| 決策 | 說明 |
|------|------|
| **ARCH** | 歷史狀態／誠實報告／能力清單 |
| **MERGE@步驟4（可選）** | 知識蒸餾、權重分類（已有別名抽出） |
| **NEVER** | 把舊 SUMMARY 當現況 |

## F. reports + reports_20260215（約 30）

| 決策 | 說明 |
|------|------|
| **全部 ARCH** | 時點報告；不進現役、不進使用者手冊正文 |

## G. tech（5）

| 舊 | 決策 |
|----|------|
| MARKET_KEYWORDS_SYSTEM | KEEP-NEW（505 keywords） |
| TINYLLM_MODEL_GUIDE | NEVER（v1 512 維） |
| MODULAR_ARCHITECTURE / COMPLEXITY / tech README | ARCH／KEEP-NEW vs ARCHITECTURE_OVERVIEW |

## H. snapshots / jules / json / db

| 決策 | 說明 |
|------|------|
| **全部 SKIP** | 一次性快照；不移 |

## I. misc 根引導

| 舊 | 決策 |
|----|------|
| ARCHIVE_INDEX / README | ARCH（由 WORK_ORDER + 本表取代索引角色） |
| DATABASE_UPGRADE_GUIDE | ARCH；遷移急救 |
| EVOLUTION_SYSTEM_PLAN | MERGE@步驟4 願景；程式不整包移（Arena 已有） |
| BINANCE_API_IMPLEMENTATION | KEEP-NEW（connector 已有） |
| MOCK / PROJECT_STATUS_* 等 | ARCH |

## J. v1 封存（磁碟 `archived/legacy_v1_20260711/`）

| 決策 | 說明 |
|------|------|
| **NEVER 現役** | 權重／tiny_llm／teacher／auto_evolve／rag_system 正確留封存 |

---

## 步驟 1 完成宣告

- [x] 路徑枚舉  
- [x] mirror 抽出（檢查用）  
- [x] 每類決策寫死（上表）  
- [x] 程式能力差距核對（WF param_grid 列為 HOME → 步驟 2 移回）  

**步驟 1：完成（2026-07-17）。**

---

## 步驟 2 完成條件（對照）

| HOME 項 | 狀態 |
|---------|------|
| WF 多窗 + 指標 | ✅ |
| WF param_grid IS 優化 | ✅（本輪接回；CLI `--wf-param-grid`） |
| 其它 HOME | 無（其餘 KEEP-NEW／NEVER／ARCH／SKIP） |

**步驟 2：在 param_grid 落地後完成。**
