# docs/ — 文檔索引
> **更新日期**: 2026-05-19

---

## 📑 目錄

<!-- toc -->

- [🎯 核心指南 (必讀)](#%F0%9F%8E%AF-%E6%A0%B8%E5%BF%83%E6%8C%87%E5%8D%97-%E5%BF%85%E8%AE%80)
- [🔌 API 與操作手冊](#-api-與操作手冊)
- [🗄️ 數據與存儲](#️-數據與存儲)
- [🧠 策略與 RAG 系統](#%F0%9F%A7%A0-%E7%AD%96%E7%95%A5%E8%88%87-rag-%E7%B3%BB%E7%B5%B1)
- [🛠️ 開發與治理](#%F0%9F%9B%A0%EF%B8%8F-%E9%96%8B%E7%99%BC%E8%88%87%E6%B2%BB%E7%90%86)
- [📚 歸檔文件](#%F0%9F%93%9A-%E6%AD%B8%E6%AA%94%E6%96%87%E4%BB%B6)
- [項目管理](#%E9%A0%85%E7%9B%AE%E7%AE%A1%E7%90%86)

<!-- tocstop -->

---

## 🎯 核心指南 (必讀)

| 文檔 | 說明 |
|------|------|
| [manuals/README.md](manuals/README.md) | ⭐️ 使用者手冊集中入口：編號、狀態、重複/老舊檢查 |
| [manuals/00_MASTER_MANUAL.md](manuals/00_MASTER_MANUAL.md) | 系統主守則：開發與導覽的單一入口 |
| [manuals/03_QUICKSTART.md](manuals/03_QUICKSTART.md) | v2.1 / v2.2 訓練後驗證期快速開始指南（本機 Python 3.13 + 環境變數；Docker 最後重建） |
| [manuals/02_STARTUP_AND_SHUTDOWN.md](manuals/02_STARTUP_AND_SHUTDOWN.md) | 本地 CLI、API + Dashboard、Docker 的開機與關機流程 |
| [STARTUP_MODES.md](STARTUP_MODES.md) | CLI、API、UI、Docker 四種啟動入口的實際操作與功能差異 |
| [manuals/04_CLI_OPERATION.md](manuals/04_CLI_OPERATION.md) | v2.1 / v2.2 訓練後驗證期 CLI 實際操作手冊（含 `autonomous` 單輪值班與 `trade` 主線） |
| [manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md](manuals/01_MANUAL_OPERATION_VERIFICATION_PLAN.md) | 手冊盤點、缺口與實際操作驗收順序 |
| [ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md) | 系統整體架構總覽 (資料流與模組分工) |
| [TECH_DEBT_STATUS_20260513.md](TECH_DEBT_STATUS_20260513.md) | 2026-05-19 技術債截圖逐項核對、paper-live 修復與本機 runtime 複驗狀態 |
| [assets/README.md](assets/README.md) | README 視覺證據、Demo GIF、績效圖表產出清單 |
| [blog/README.md](blog/README.md) | 技術部落格與設計決策文章入口 |
| [PROJECT_HANDOVER_MAP.md](PROJECT_HANDOVER_MAP.md) | 模組依賴圖與開發接手地圖 |
| [SRC_DIRECTORY_ANALYSIS.md](SRC_DIRECTORY_ANALYSIS.md) | `src/` 目錄結構分析 |
| [manuals/08_BACKTEST_SYSTEM.md](manuals/08_BACKTEST_SYSTEM.md) | 回測系統使用準則 |
| [manuals/13_CLOUD_TRAINING_RUNBOOK.md](manuals/13_CLOUD_TRAINING_RUNBOOK.md) | 雲端 GPU 訓練準備、真實資料短流程、resume 與 artifact 回收流程 |

---

## 🔌 API 與操作手冊

| 文檔 | 說明 |
|------|------|
| [manuals/05_API_USER_MANUAL.md](manuals/05_API_USER_MANUAL.md) | REST API 與 WebSocket 端點參考 |
| [manuals/06_FRONTEND_DASHBOARD.md](manuals/06_FRONTEND_DASHBOARD.md) | Operations Dashboard 操作手冊（即時 K 線、操作總覽、新聞、預交易、回測、AI 對話、交易控制、paper-live、訓練/模型、API 測試台、歷史紀錄、資料目錄、風控設定；2026-05-19 已記錄版面溢出修復）|
| [manuals/07_DOCKER_DEPLOYMENT.md](manuals/07_DOCKER_DEPLOYMENT.md) | Docker Compose 部署指南（預設 8 個服務 + `trade` profile）|
| [manuals/11_RISK_MANAGEMENT.md](manuals/11_RISK_MANAGEMENT.md) | 風險管理使用手冊（4 個風險等級）|
| [manuals/09_ANALYSIS_MODULE.md](manuals/09_ANALYSIS_MODULE.md) | 分析模組操作手冊（news / plan / pretrade）|
| [manuals/10_STRATEGY_MODULE.md](manuals/10_STRATEGY_MODULE.md) | 策略模組操作手冊（strategy-backtest）|

---

## 🗄️ 數據與存儲

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
| [manuals/12_NLP_TRAINING.md](manuals/12_NLP_TRAINING.md) | NLP 自然語言處理訓練與微調計畫 |
| [TRAINED_MODEL_TECHNICAL_REPORT_20260510.md](TRAINED_MODEL_TECHNICAL_REPORT_20260510.md) | `my_100m_model` 重訓前後差異、數值驗證與限制說明 |
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
| [OPERATION_VALIDATION_REPORT_20260603.md](OPERATION_VALIDATION_REPORT_20260603.md) | 較新的實際操作驗證報告：補上 Testnet 真實下單、AI 自主分析管線與自主運作機制走查 |
| [adr/README.md](adr/README.md) | Architecture Decision Records：核心架構決策紀錄 |
| [V2.2_ROADMAP_AND_SPEC.md](V2.2_ROADMAP_AND_SPEC.md) | v2.2 路線圖與功能規格 |

---

## 項目管理

> 歷次錯誤修復報告與驗證結果位於 `docs/` 根目錄，供開發追蹤使用。

---

> 📖 上層目錄：[根目錄 README](../README.md)
