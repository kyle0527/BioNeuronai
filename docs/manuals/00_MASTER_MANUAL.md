# BioNeuronAI 系統主手冊 (Master Manual)

> **版本**: v2.1  
> **更新日期**: 2026-05-05
> **系統狀態**: 目前正式主線文件

---

## 📑 目錄

- [🌟 1. 系統總覽](#🌟-1-系統總覽)
- [🗺️ 2. 核心導覽地圖](#🗺-2-核心導覽地圖)
  - [🎯 入門與操作](#🎯-入門與操作)
  - [📊 分析、策略與交易](#📊-分析策略與交易)
  - [🔌 API 與部署](#🔌-api-與部署)
  - [📚 訓練與作業](#📚-訓練與作業)
  - [🧠 架構與全景](#🧠-架構與全景)
  - [🧪 測試與驗證](#🧪-測試與驗證)
- [🏗️ 3. 架構哲學 (v2.1 核心精神)](#🏗-3-架構哲學-v21-核心精神)
  - [A. 全局單一事實來源 (Single Source of Truth)](#a-全局單一事實來源-single-source-of-truth)
  - [B. 決策與執行的分水嶺](#b-決策與執行的分水嶺)
  - [C. 狀態管理逐步集中](#c-狀態管理逐步集中)
- [🚀 4. 快速跳轉指南](#🚀-4-快速跳轉指南)
- [📂 5. 模組職責劃分](#📂-5-模組職責劃分)
- [💡 6. 開發與維護準則](#💡-6-開發與維護準則)

---

## 🌟 1. 系統總覽

BioNeuronAI 是一套面向加密貨幣期貨市場的 AI 交易系統。  
目前 `v2.1` 的正式主線，已從早期混合式 CLI 腳本收斂成較清楚的模組分層，重點是：

* **決策與執行分層**：目前已把高階規劃 (`planning`) 與訂單 / 帳戶事實層 (`trading`) 分開。
* **契約化資料模型**：跨模組資料交換以 `src/schemas/` 為單一事實來源。
* **多入口運行**：目前同時保留 CLI 與 FastAPI 入口；Docker 與服務化部署能力已存在，但不應把所有執行方式都寫成唯一正式形態。

---

## 🗺️ 2. 核心導覽地圖

為了維持文件系統的單一事實來源 (Single Source of Truth)，我們將所有技術細節與操作守則分散拆解成各自獨立、專業的文件中。以下是您導航本專案的指標：

### 🎯 入門與操作
* **[02_STARTUP_AND_SHUTDOWN.md](02_STARTUP_AND_SHUTDOWN.md)**: 開機與關機主入口，涵蓋本地 CLI、本地 API + Dashboard、Docker 的啟停流程。
* **[03_QUICKSTART.md](03_QUICKSTART.md)**: ⭐ 新手必看。教您如何用最快的速度架設 Docker、設定 `.env`、並驗證系統是否正常啟動。
* **[04_CLI_OPERATION.md](04_CLI_OPERATION.md)**: 🛠️ 實戰必看。收錄所有 CLI 驅動指令（如 `python main.py plan`）、以及如何透過 API 觸發自動化任務。
* **[06_FRONTEND_DASHBOARD.md](06_FRONTEND_DASHBOARD.md)**: 🖥️ DevOps Dashboard 操作手冊。詳細說明 Dashboard 的主要面板與操作視圖（狀態、新聞、預交易、回測、AI 對話、交易控制、API 測試台、歷史紀錄、資料目錄、風控設定）。
* **[20_UI_END_TO_END_OPERATION.md](20_UI_END_TO_END_OPERATION.md)**: UI 端到端操作手冊。從開啟 Dashboard、確認狀態、跑資料目錄/回測/新聞/pretrade/chat，到 testnet 啟停與關機。

### 📊 分析、策略與交易
* **[08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md)**: 📈 回測系統專用指南。說明如何透過 Mock Connector 與 CLI 工具打磨交易策略，而不消耗真實資金。
* **[09_ANALYSIS_MODULE.md](09_ANALYSIS_MODULE.md)**: 新聞、交易計畫與進場前驗核操作手冊，涵蓋 `news`、`plan`、`pretrade`。
* **[10_STRATEGY_MODULE.md](10_STRATEGY_MODULE.md)**: 策略模組操作手冊，涵蓋 `strategy-backtest`、API `strategy-run` 與策略 runtime 輸出。
* **[11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md)**: 🛡️ 風險管理使用手冊。涵蓋風險等級、倉位計算邏輯與 pretrade 風險解讀。
* **[14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md)**: Testnet / live 交易啟停手冊，明確區分 `monitor_only`、`testnet_auto`、`live_auto` 與 live guard。
* **[15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md)**: 歷史資料、catalog、inspect 與資料取得操作手冊。
* **[16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md)**: runtime、logs、output、模型與資料產物位置手冊。

### 🔌 API 與部署
* **[05_API_USER_MANUAL.md](05_API_USER_MANUAL.md)**: 📡 REST API 與 WebSocket 端點參考，含請求/回應範例與 PowerShell 指令。
* **[07_DOCKER_DEPLOYMENT.md](07_DOCKER_DEPLOYMENT.md)**: 🐳 Docker Compose 部署指南。說明預設 8 個服務與 `trade` profile 服務的啟動方式、`.env` 環境變數設定、Volume 備份與常見問題排除。
* **[17_ENVIRONMENT_VARIABLES.md](17_ENVIRONMENT_VARIABLES.md)**: `.env`、API key、交易安全開關與 Compose 環境變數手冊。
* **[18_OPERATION_TROUBLESHOOTING.md](18_OPERATION_TROUBLESHOOTING.md)**: CLI、API、Docker、Backtest、Pretrade 操作排查手冊。
* **[19_DASHBOARD_TROUBLESHOOTING.md](19_DASHBOARD_TROUBLESHOOTING.md)**: Dashboard、API 連線、CORS、WebSocket 與前端啟動排查手冊。

### 📚 訓練與作業
* **[12_NLP_TRAINING.md](12_NLP_TRAINING.md)**: NLP / TinyLLM / unified trainer 訓練手冊，屬訓練作業，不是一般日常操作主線。
* **[13_CLOUD_TRAINING_RUNBOOK.md](13_CLOUD_TRAINING_RUNBOOK.md)**: 雲端 GPU 訓練 runbook，涵蓋真實資料短流程、resume 與 artifact 回收。

### 🧠 架構與全景
* **[ARCHITECTURE_OVERVIEW.md](../ARCHITECTURE_OVERVIEW.md)**: 🗺️ 系統全局視野。解釋 v2.1 從資料獲取到訂單送出的全資料流。
* **[PROJECT_HANDOVER_MAP.md](../PROJECT_HANDOVER_MAP.md)**: 🤝 開發者交接地圖。提供各模組的依賴關係與「舊版殘留區」的避坑指南。
* **[SRC_DIRECTORY_ANALYSIS.md](../SRC_DIRECTORY_ANALYSIS.md)**: 📁 目錄結構詳解。告訴你每個資料夾為什麼存在、裡面放什麼。

### 🧪 測試與驗證
* **[01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md)**: 使用者手冊實際入口驗收矩陣，記錄 CLI、API、Dashboard、Docker 與 UI 端到端驗證狀態。

---

## 🏗️ 3. 架構哲學 (v2.1 核心精神)

### A. 全局單一事實來源 (Single Source of Truth)
所有資料結構（包含市場數據、訂單狀態、甚至新聞分析結果）**唯一**的定義來源是在 `src/schemas/` 目錄中。禁止任何模組私自重複定義相同概念的 `BaseModel`。

### B. 決策與執行的分水嶺
過往的架構常將「該不該買」與「怎麼買」混在一起，在 v2.1 裡：
* **`planning/` (總經理)**：負責宏觀市場分析、資金流動觀察，產出「建議交易計畫」。
* **`trading/` (執行長)**：不帶主觀看法，嚴格依照計畫限額、目前風險暴露狀態，將計算好的數量安全地拋單給交易所。

### C. 狀態管理逐步集中
目前系統正在把訂單、帳戶、持倉、資金等執行事實，逐步集中到 `trading/`。  
這條線已開始落地，但不應寫成「所有狀態都已完全統一持久化」；較精確的說法是：

* 正式方向已確立
* `trading/virtual_account.py` 已成為第一個正式帳戶事實模組
* `backtest/` 已開始依賴這一層
* 其餘訂單狀態與同步邏輯仍在持續收斂

---

## 🚀 4. 快速跳轉指南

常見的開發者/使用者情境：

**💬 「我想知道怎麼啟動這個專案跑跑看...」**
👉 左轉：[03_QUICKSTART.md](03_QUICKSTART.md)

**💬 「我想只靠 UI 從開始操作到結束...」**
👉 左轉：[20_UI_END_TO_END_OPERATION.md](20_UI_END_TO_END_OPERATION.md)

**💬 「我想用自己寫的歷史策略來驗證勝率...」**
👉 左轉：[08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md)

**💬 「如果我是一個接手專案的新開發者，我該從哪支程式看起？」**
👉 第一步先看：[PROJECT_HANDOVER_MAP.md](../PROJECT_HANDOVER_MAP.md)，接著直接去讀 `src/bioneuronai/cli/main.py` 這個全系統的總入口。

**💬 「我不確定新的訂單 Schema 還有沒包含停損欄位...」**
👉 直接去看程式碼：`src/schemas/trading.py`，那是唯一的真相。

---

## 📂 5. 模組職責劃分

本章節為速記，詳細分析請見架構總覽。

| 模組分層 | 職責簡述 |
| :--- | :--- |
| **`core/`** | 核心交易引擎、AI 推理與主流程整合。 |
| **`schemas/`** | 全域共用的 Pydantic 資料結構。 |
| **`planning/`** | 高階計劃、盤前檢查、市場分析與交易對選擇。 |
| **`trading/`** | 訂單、帳戶、持倉、資金等執行事實層，目前核心檔案為 `virtual_account.py`。 |
| **`api/`** | FastAPI Web 伺服器入口，提供外部監控視角與呼叫接口。 |
| **`cli/`** | 開發人員與定時任務 (cron) 直接驅動系統任務的指令列入口。 |

---

## 💡 6. 開發與維護準則

若您準備為 BioNeuronAI 提交 PR (Pull Request) 或修改設定，請務必遵守：

1. **依賴 `DOCUMENTATION_GOVERNANCE_PLAN.md` 規範**：在大幅修改程式碼前，請同步調整對應的文件，確保文件不落後。
2. **禁止把密碼寫入檔案中**：所有 API Keys 必須存在 `.env` 並從環境變數載入，不應寫死在設定檔或腳本內。
3. **辨識正式入口與歷史工具**：目前正式入口是 `main.py`、`src/bioneuronai/cli/main.py`、`src/bioneuronai/api/app.py`。若遇到舊腳本或舊測試工具，應先確認其是否已被歸檔或退出主線。
