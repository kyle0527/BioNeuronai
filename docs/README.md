# docs/ — 文檔索引

> **套件版本**：v2.1｜**更新日期**：2026-06-15
>
> **現況權威來源**：[`PROJECT_STATUS.md`](PROJECT_STATUS.md)（README 為其摘要）

---

## 目錄

1. [閱讀順序建議](#閱讀順序建議)
2. [核心指南（必讀）](#核心指南必讀)
3. [API 與操作手冊](#api-與操作手冊)
4. [數據與存儲](#數據與存儲)
5. [策略與 RAG 系統](#策略與-rag-系統)
6. [開發與治理](#開發與治理)
7. [歸檔文件（勿當現況）](#歸檔文件勿當現況)
8. [版本命名說明](#版本命名說明)

---

## 閱讀順序建議

1. [../README.md](../README.md) — 專案摘要
2. [PROJECT_STATUS.md](PROJECT_STATUS.md) — **最準確的模組現況與缺口**
3. [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) — 雙執行主線與架構圖
4. [manuals/03_QUICKSTART.md](manuals/03_QUICKSTART.md) — 快速上手

---

## 核心指南（必讀）

| 文檔 | 說明 |
|------|------|
| [PROJECT_STATUS.md](PROJECT_STATUS.md) | ⭐ 專案現況權威來源（含雙執行主線對照） |
| [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | 系統架構總覽、分層與部署模式 |
| [manuals/README.md](manuals/README.md) | 使用者手冊集中入口 |
| [manuals/00_MASTER_MANUAL.md](manuals/00_MASTER_MANUAL.md) | 系統主守則 |
| [manuals/03_QUICKSTART.md](manuals/03_QUICKSTART.md) | 快速開始（Python 3.13） |
| [manuals/02_STARTUP_AND_SHUTDOWN.md](manuals/02_STARTUP_AND_SHUTDOWN.md) | 開機與關機流程 |
| [STARTUP_MODES.md](STARTUP_MODES.md) | CLI / API / UI / Docker 入口差異 |
| [manuals/04_CLI_OPERATION.md](manuals/04_CLI_OPERATION.md) | CLI 完整參考（`trade` + `autonomous`） |
| [manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md](manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md) | 手冊驗收計劃（正式入口，非 pytest） |
| [TESTING_AND_VALIDATION_GUIDE.md](TESTING_AND_VALIDATION_GUIDE.md) | 驗證哲學與核心路徑 |
| [PROJECT_HANDOVER_MAP.md](PROJECT_HANDOVER_MAP.md) | 模組依賴與接手地圖 |
| [SRC_DIRECTORY_ANALYSIS.md](SRC_DIRECTORY_ANALYSIS.md) | `src/` 目錄結構分析 |
| [manuals/08_BACKTEST_SYSTEM.md](manuals/08_BACKTEST_SYSTEM.md) | 回測系統 |
| [manuals/13_CLOUD_TRAINING_RUNBOOK.md](manuals/13_CLOUD_TRAINING_RUNBOOK.md) | 雲端訓練 runbook |
| [OPERATION_VALIDATION_REPORT_20260603.md](OPERATION_VALIDATION_REPORT_20260603.md) | 較新操作驗證報告 |
| [assets/README.md](assets/README.md) | 績效圖表產出清單 |
| [blog/README.md](blog/README.md) | 技術部落格入口 |

---

## API 與操作手冊

| 文檔 | 說明 |
|------|------|
| [manuals/05_API_USER_MANUAL.md](manuals/05_API_USER_MANUAL.md) | REST API 與 WebSocket |
| [manuals/06_FRONTEND_DASHBOARD.md](manuals/06_FRONTEND_DASHBOARD.md) | Operations Dashboard |
| [manuals/07_DOCKER_DEPLOYMENT.md](manuals/07_DOCKER_DEPLOYMENT.md) | Docker Compose 部署 |
| [manuals/11_RISK_MANAGEMENT.md](manuals/11_RISK_MANAGEMENT.md) | 風險管理（傳統四等級） |
| [manuals/09_ANALYSIS_MODULE.md](manuals/09_ANALYSIS_MODULE.md) | news / plan / pretrade |
| [manuals/10_STRATEGY_MODULE.md](manuals/10_STRATEGY_MODULE.md) | strategy-backtest |

> AI 信心校準細節見 [`src/bioneuronai/risk_management/README.md`](../src/bioneuronai/risk_management/README.md)

---

## 數據與存儲

| 文檔 | 說明 |
|------|------|
| [DATA_PIPELINE_AND_SCHEMA.md](DATA_PIPELINE_AND_SCHEMA.md) | 資料管線與 SQLite 綱要 |
| [BACKTEST_DATA_SOURCE.md](BACKTEST_DATA_SOURCE.md) | 歷史回測資料來源 |

---

## 策略與 RAG 系統

| 文檔 | 說明 |
|------|------|
| [RAG_TECHNICAL_MANUAL.md](RAG_TECHNICAL_MANUAL.md) | RAG 技術手冊 |
| [KNOWHOW_ANALYSIS.md](KNOWHOW_ANALYSIS.md) | 核心交易邏輯分析 |
| [manuals/12_NLP_TRAINING.md](manuals/12_NLP_TRAINING.md) | NLP 訓練計畫 |
| [TRAINED_MODEL_TECHNICAL_REPORT_20260510.md](TRAINED_MODEL_TECHNICAL_REPORT_20260510.md) | `my_100m_model` 技術報告 |
| [STRATEGY_FUSION_ROADMAP_OVERVIEW.md](STRATEGY_FUSION_ROADMAP_OVERVIEW.md) | 策略融合路線圖總覽 |

---

## 開發與治理

| 文檔 | 說明 |
|------|------|
| [DOCUMENTATION_GOVERNANCE_PLAN.md](DOCUMENTATION_GOVERNANCE_PLAN.md) | 文件治理規範 |
| [DEVELOPMENT_TOOLS.md](DEVELOPMENT_TOOLS.md) | 開發腳本說明 |
| [adr/README.md](adr/README.md) | 架構決策紀錄 (ADR) |
| [V2.2_ROADMAP_AND_SPEC.md](V2.2_ROADMAP_AND_SPEC.md) | v2.2 **路線圖**（非已發布版本） |
| [EXECUTION_PLAN.md](EXECUTION_PLAN.md) | TinyLLM v2 / LoRA checkpoint 執行計劃（部分已過期，見檔頭免責） |
| [INTEGRATED_RECOMMENDATION.md](INTEGRATED_RECOMMENDATION.md) | 整合建議（規劃參考） |
| [CODE_FIX_GUIDE.md](CODE_FIX_GUIDE.md) | 代碼維護規範（靜態，非現況） |

---

## 歸檔文件（勿當現況）

以下文件保留歷史參考，**不代表目前實作狀態**。現況請以 `PROJECT_STATUS.md` 為準。

| 文檔 | 歸檔原因 |
|------|----------|
| [AGENTIC_PROFIT_UPGRADE_PLAN.md](AGENTIC_PROFIT_UPGRADE_PLAN.md) | 已被 INTEGRATED_RECOMMENDATION 取代 |
| [STRATEGY_FUSION_PLAN_B_ML_METALEARNER.md](STRATEGY_FUSION_PLAN_B_ML_METALEARNER.md) | 早期探索，已整合進主線 |
| [STRATEGY_FUSION_PLAN_C_REGIME_ROUTING.md](STRATEGY_FUSION_PLAN_C_REGIME_ROUTING.md) | 同上 |
| [STRATEGY_FUSION_PLAN_D_RL_AGENT.md](STRATEGY_FUSION_PLAN_D_RL_AGENT.md) | 同上 |
| [TECH_DEBT_STATUS_20260513.md](TECH_DEBT_STATUS_20260513.md) | 2026-05-13 快照 |
| [OPERATION_VALIDATION_REPORT_20260511.md](OPERATION_VALIDATION_REPORT_20260511.md) | 舊版驗證報告 |

---

## 版本命名說明

| 標記 | 含義 |
|------|------|
| **v2.1** | 套件正式版本（`pyproject.toml` / `__init__.py`） |
| **v2.2** | 僅用於 roadmap / 訓練後驗證期文件標題，**不是**已發布套件版 |
| **CHANGELOG v3.x / v4.x** | 歷史開發里程碑標籤，與目前 v2.1 套件版不衝突但勿混用 |

---

> 上層目錄：[根目錄 README](../README.md)