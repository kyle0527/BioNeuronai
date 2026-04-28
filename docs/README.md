# docs/ — 文檔索引
> **更新日期**: 2026-04-17

---

## 📑 目錄

<!-- toc -->

- [🎯 核心指南 (必讀)](#%F0%9F%8E%AF-%E6%A0%B8%E5%BF%83%E6%8C%87%E5%8D%97-%E5%BF%85%E8%AE%80)
- [� API 與操作手冊](#%F0%9F%94%8C-api-%E8%88%87%E6%93%8D%E4%BD%9C%E6%89%8B%E5%86%8A)
- [�🗄️ 數據與存儲](#%F0%9F%97%84%EF%B8%8F-%E6%95%B8%E6%93%9A%E8%88%87%E5%AD%98%E5%84%B2)
- [🧠 策略與 RAG 系統](#%F0%9F%A7%A0-%E7%AD%96%E7%95%A5%E8%88%87-rag-%E7%B3%BB%E7%B5%B1)
- [🛠️ 開發與治理](#%F0%9F%9B%A0%EF%B8%8F-%E9%96%8B%E7%99%BC%E8%88%87%E6%B2%BB%E7%90%86)
- [📚 歸檔文件](#%F0%9F%93%9A-%E6%AD%B8%E6%AA%94%E6%96%87%E4%BB%B6)
- [項目管理](#%E9%A0%85%E7%9B%AE%E7%AE%A1%E7%90%86)

<!-- tocstop -->

---

## 🎯 核心指南 (必讀)

| 文檔 | 說明 |
|------|------|
| [BIONEURONAI_MASTER_MANUAL.md](BIONEURONAI_MASTER_MANUAL.md) | ⭐️ 系統主守則：開發與導覽的單一入口 |
| [QUICKSTART_V2.1.md](QUICKSTART_V2.1.md) | v2.1 快速開始指南 (Docker + 環境變數) |
| [OPERATION_MANUAL.md](OPERATION_MANUAL.md) | v2.1 連線、排程與 CLI 實際操作手冊 |
| [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | 系統整體架構總覽 (資料流與模組分工) |
| [PROJECT_HANDOVER_MAP.md](PROJECT_HANDOVER_MAP.md) | 模組依賴圖與開發接手地圖 |
| [SRC_DIRECTORY_ANALYSIS.md](SRC_DIRECTORY_ANALYSIS.md) | `src/` 目錄結構分析 |
| [BACKTEST_SYSTEM_GUIDE.md](BACKTEST_SYSTEM_GUIDE.md) | 回測系統使用準則 |

---

## � API 與操作手冊

| 文檔 | 說明 |
|------|------|
| [API_USER_MANUAL.md](API_USER_MANUAL.md) | REST API 完整端點參考（20 REST + 3 WebSocket）|
| [FRONTEND_DASHBOARD_MANUAL.md](FRONTEND_DASHBOARD_MANUAL.md) | DevOps Dashboard 操作手冊（8 個面板）|
| [DOCKER_DEPLOYMENT_MANUAL.md](DOCKER_DEPLOYMENT_MANUAL.md) | Docker Compose 部署指南（9 個服務）|
| [RISK_MANAGEMENT_USER_MANUAL.md](RISK_MANAGEMENT_USER_MANUAL.md) | 風險管理使用手冊（4 個風險等級）|
| [ANALYSIS_MODULE_USER_MANUAL.md](ANALYSIS_MODULE_USER_MANUAL.md) | 分析模組操作手冊（news / plan / pretrade）|
| [STRATEGY_MODULE_USER_MANUAL.md](STRATEGY_MODULE_USER_MANUAL.md) | 策略模組操作手冊（strategy-backtest）|

---

## �🗄️ 數據與存儲

| 文檔 | 說明 |
|------|------|
| [DATA_PIPELINE_AND_SCHEMA.md](DATA_PIPELINE_AND_SCHEMA.md) | 資料管線、儲存分層與核心 SQLite 綱要 |
| [BACKTEST_DATA_SOURCE.md](BACKTEST_DATA_SOURCE.md) | 歷史回測數據來源 |

---

## 🧠 策略與 RAG 系統

| 文檔 | 說明 |
|------|------|
| [RAG_TECHNICAL_MANUAL.md](RAG_TECHNICAL_MANUAL.md) | 檢索增強生成 (RAG) 模組技術手冊 |
| [KNOWHOW_ANALYSIS.md](KNOWHOW_ANALYSIS.md) | 核心交易邏輯與知識庫分析 |
| [NLP_TRAINING_GUIDE.md](NLP_TRAINING_GUIDE.md) | NLP 自然語言處理訓練與微調計畫 |
| [STRATEGY_FUSION_ROADMAP_OVERVIEW.md](STRATEGY_FUSION_ROADMAP_OVERVIEW.md) | 策略融合系統未來發展路線圖總覽 |
| [STRATEGY_FUSION_PLAN_B_ML_METALEARNER.md](STRATEGY_FUSION_PLAN_B_ML_METALEARNER.md) | 方案 B：ML Meta-Learner 堆疊融合 |
| [STRATEGY_FUSION_PLAN_C_REGIME_ROUTING.md](STRATEGY_FUSION_PLAN_C_REGIME_ROUTING.md) | 方案 C：硬性體制路由 |
| [STRATEGY_FUSION_PLAN_D_RL_AGENT.md](STRATEGY_FUSION_PLAN_D_RL_AGENT.md) | 方案 D：深度強化學習 Agent |

---

## 🛠️ 開發與治理

| 文檔 | 說明 |
|------|------|
| [CODE_FIX_GUIDE.md](CODE_FIX_GUIDE.md) | 代碼修復與架構維護規範 |
| [DOCUMENTATION_GOVERNANCE_PLAN.md](DOCUMENTATION_GOVERNANCE_PLAN.md) | 文件治理與清理規範 (核心守則) |
| [DEVELOPMENT_TOOLS.md](DEVELOPMENT_TOOLS.md) | 目錄產生等 PowerShell 開發腳本說明 |
| [TESTING_AND_VALIDATION_GUIDE.md](TESTING_AND_VALIDATION_GUIDE.md) | 測試哲學、核心測試路徑與 CI Smoke Test |
| [V2.2_ROADMAP_AND_SPEC.md](V2.2_ROADMAP_AND_SPEC.md) | v2.2 路線圖與功能規格 |

---

## 📚 歸檔文件

以下文件為 v2.1 收斂前的歷史快照，保留於 `archived/docs_v2_1_legacy/` 供考古比對。
若同名文件已恢復到 `docs/` 根目錄，請以 `docs/` 內版本為目前相容入口。

| 文檔 | 說明 |
|------|------|
| [../archived/docs_v2_1_legacy/BIONEURONAI_MASTER_MANUAL.legacy_20260405.md](../archived/docs_v2_1_legacy/BIONEURONAI_MASTER_MANUAL.legacy_20260405.md) | v2.1 收斂前舊版主手冊 |
| [../archived/docs_v2_1_legacy/MANUAL_IMPLEMENTATION_STATUS.legacy_20260405.md](../archived/docs_v2_1_legacy/MANUAL_IMPLEMENTATION_STATUS.legacy_20260405.md) | v2.1 收斂前舊版手冊實作狀態 |
| [../archived/docs_v2_1_legacy/FEATURE_STATUS.legacy_20260405.md](../archived/docs_v2_1_legacy/FEATURE_STATUS.legacy_20260405.md) | v2.1 收斂前舊版功能狀態總覽 |
| [../archived/docs_v2_1_legacy/ARCHITECTURE_OVERVIEW.legacy_20260406.md](../archived/docs_v2_1_legacy/ARCHITECTURE_OVERVIEW.legacy_20260406.md) | v2.1 收斂前舊版架構總覽 |
| [../archived/docs_v2_1_legacy/SRC_DIRECTORY_ANALYSIS.legacy_20260406.md](../archived/docs_v2_1_legacy/SRC_DIRECTORY_ANALYSIS.legacy_20260406.md) | v2.1 收斂前舊版 src 目錄分析 |
| [../archived/docs_v2_1_legacy/PROJECT_HANDOVER_MAP.legacy_20260406.md](../archived/docs_v2_1_legacy/PROJECT_HANDOVER_MAP.legacy_20260406.md) | v2.1 收斂前舊版接手地圖 |
| [../archived/docs_v2_1_legacy/OPERATION_MANUAL.legacy_20260406.md](../archived/docs_v2_1_legacy/OPERATION_MANUAL.legacy_20260406.md) | v2.1 收斂前舊版操作手冊 |
| [../archived/docs_v2_1_legacy/QUICKSTART_V2.1.legacy_20260406.md](../archived/docs_v2_1_legacy/QUICKSTART_V2.1.legacy_20260406.md) | v2.1 收斂前含有舊版 API 幻覺的快速開始指南 |
| [../archived/docs_v2_1_legacy/BACKTEST_SYSTEM_GUIDE.legacy_20260406.md](../archived/docs_v2_1_legacy/BACKTEST_SYSTEM_GUIDE.legacy_20260406.md) | v2.1 收斂前舊版回測系統指南 |
| [../archived/docs_v2_1_legacy/DAILY_REPORT_CHECKLIST.legacy_20260406.md](../archived/docs_v2_1_legacy/DAILY_REPORT_CHECKLIST.legacy_20260406.md) | 舊版 `daily_market_report.py` 之純 To-Do 確認清單 |
| [../archived/docs_v2_1_legacy/DATA_SOURCES_GUIDE.legacy_20260406.md](../archived/docs_v2_1_legacy/DATA_SOURCES_GUIDE.legacy_20260406.md) | 舊版外部數據 API 調用指南 (充斥舊版 `market_scanner.py` 位址) |
| [../archived/docs_v2_1_legacy/PROJECT_STRUCTURE.legacy_20260406.md](../archived/docs_v2_1_legacy/PROJECT_STRUCTURE.legacy_20260406.md) | 舊版存在多處執行檔幻覺的目錄結構總覽 |
| [../archived/docs_v2_1_legacy/TRADING_PLAN_10_STEPS.legacy_20260406.md](../archived/docs_v2_1_legacy/TRADING_PLAN_10_STEPS.legacy_20260406.md) | 舊版交易計畫架構 (引用不存在的 `trading_plan/` 路徑) |
| [../archived/docs_v2_1_legacy/TRADING_COSTS_GUIDE.legacy_20260406.md](../archived/docs_v2_1_legacy/TRADING_COSTS_GUIDE.legacy_20260406.md) | 舊版交易成本計算器規劃文件 |
| [../archived/docs_v2_1_legacy/BINANCE_TESTNET_STEP_BY_STEP.legacy_20260406.md](../archived/docs_v2_1_legacy/BINANCE_TESTNET_STEP_BY_STEP.legacy_20260406.md) | 舊版測試網教學 (基於互動式選單 CLI) |
| [../archived/docs_v2_1_legacy/STRATEGIES_QUICK_REFERENCE.legacy_20260406.md](../archived/docs_v2_1_legacy/STRATEGIES_QUICK_REFERENCE.legacy_20260406.md) | 舊版三策略參考 (基於過時啟動腳本) |
| [../archived/docs_v2_1_legacy/CODE_FIX_GUIDE.legacy_20260406.md](../archived/docs_v2_1_legacy/CODE_FIX_GUIDE.legacy_20260406.md) | 舊版代碼維護規範 (存在舊版腳本驗證幻覺) |
| [../archived/docs_v2_1_legacy/STRATEGY_EVOLUTION_GUIDE.legacy_20260406.md](../archived/docs_v2_1_legacy/STRATEGY_EVOLUTION_GUIDE.legacy_20260406.md) | 舊版進化系統指南 (引用 `trading/risk_manager.py`) |
| [../archived/docs_v2_1_legacy/STRATEGY_EVOLUTION_WEB_INTEGRATION_PLAN.legacy_20260406.md](../archived/docs_v2_1_legacy/STRATEGY_EVOLUTION_WEB_INTEGRATION_PLAN.legacy_20260406.md) | 舊版 Web 整合計畫 (未實作/過期) |
| [../archived/docs_v2_1_legacy/ANALYSIS_RAG_INTEGRATION_IMPROVEMENT_PLAN.legacy_20260406.md](../archived/docs_v2_1_legacy/ANALYSIS_RAG_INTEGRATION_IMPROVEMENT_PLAN.legacy_20260406.md) | 舊版 RAG 整合計畫 (與當前架構脫節) |
| [../archived/docs_v2_1_legacy/RISK_MANAGEMENT_MANUAL.legacy_20260406.md](../archived/docs_v2_1_legacy/RISK_MANAGEMENT_MANUAL.legacy_20260406.md) | 舊版風險管理手冊 (引用不存在的 `risk_management/` 目錄) |

---

## 項目管理

> 歷次錯誤修復報告與驗證結果位於 `docs/` 根目錄，供開發追蹤使用。

---

> 📖 上層目錄：[根目錄 README](../README.md)
