# BioNeuronAI 系統主手冊 (Master Manual)

> **版本**: v2.1  
> **更新日期**: 2026-04-06  
> **系統狀態**: 目前正式主線文件

---

## 📑 目錄

<!-- toc -->

- [🌟 1. 系統總覽](#%F0%9F%8C%9F-1-%E7%B3%BB%E7%B5%B1%E7%B8%BD%E8%A6%BD)
- [🗺️ 2. 核心導覽地圖](#%F0%9F%97%BA%EF%B8%8F-2-%E6%A0%B8%E5%BF%83%E5%B0%8E%E8%A6%BD%E5%9C%B0%E5%9C%96)
  * [🎯 入門與操作](#%F0%9F%8E%AF-%E5%85%A5%E9%96%80%E8%88%87%E6%93%8D%E4%BD%9C)
  * [🧠 架構與全景](#%F0%9F%A7%A0-%E6%9E%B6%E6%A7%8B%E8%88%87%E5%85%A8%E6%99%AF)
  * [🧪 測試與驗證](#%F0%9F%A7%AA-%E6%B8%AC%E8%A9%A6%E8%88%87%E9%A9%97%E8%AD%89)
- [🏗️ 3. 架構哲學 (v2.1 核心精神)](#%F0%9F%8F%97%EF%B8%8F-3-%E6%9E%B6%E6%A7%8B%E5%93%B2%E5%AD%B8-v21-%E6%A0%B8%E5%BF%83%E7%B2%BE%E7%A5%9E)
  * [A. 全局單一事實來源 (Single Source of Truth)](#a-%E5%85%A8%E5%B1%80%E5%96%AE%E4%B8%80%E4%BA%8B%E5%AF%A6%E4%BE%86%E6%BA%90-single-source-of-truth)
  * [B. 決策與執行的分水嶺](#b-%E6%B1%BA%E7%AD%96%E8%88%87%E5%9F%B7%E8%A1%8C%E7%9A%84%E5%88%86%E6%B0%B4%E5%B6%BA)
  * [C. 狀態管理逐步集中](#c-%E7%8B%80%E6%85%8B%E7%AE%A1%E7%90%86%E9%80%90%E6%AD%A5%E9%9B%86%E4%B8%AD)
- [🚀 4. 快速跳轉指南](#%F0%9F%9A%80-4-%E5%BF%AB%E9%80%9F%E8%B7%B3%E8%BD%89%E6%8C%87%E5%8D%97)
- [📂 5. 模組職責劃分](#%F0%9F%93%82-5-%E6%A8%A1%E7%B5%84%E8%81%B7%E8%B2%AC%E5%8A%83%E5%88%86)
- [💡 6. 開發與維護準則](#%F0%9F%92%A1-6-%E9%96%8B%E7%99%BC%E8%88%87%E7%B6%AD%E8%AD%B7%E6%BA%96%E5%89%87)

<!-- tocstop -->

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
* **[QUICKSTART_V2.1.md](QUICKSTART_V2.1.md)**: ⭐ 新手必看。教您如何用最快的速度架設 Docker、設定 `.env`、並驗證系統是否正常啟動。
* **[OPERATION_MANUAL.md](OPERATION_MANUAL.md)**: 🛠️ 實戰必看。收錄所有 CLI 驅動指令（如 `python main.py plan`）、以及如何透過 API 觸發自動化任務。
* **[FRONTEND_DASHBOARD_MANUAL.md](FRONTEND_DASHBOARD_MANUAL.md)**: 🖥️ DevOps Dashboard 操作手冊。詳細說明 8 個面板（狀態/新聞/預交易/回測/AI對話/交易控制/API測試台/歷史紀錄）的使用方式。

### 🔌 API 與部署
* **[API_USER_MANUAL.md](API_USER_MANUAL.md)**: 📡 REST API 完整端點參考。涵蓋所有 20 個 REST 端點與 3 個 WebSocket 端點，含請求/回應範例與 PowerShell 指令。
* **[DOCKER_DEPLOYMENT_MANUAL.md](DOCKER_DEPLOYMENT_MANUAL.md)**: 🐳 Docker Compose 部署指南。說明 9 個服務的啟動方式、`.env` 環境變數設定、Volume 備份與常見問題排除。
* **[RISK_MANAGEMENT_USER_MANUAL.md](RISK_MANAGEMENT_USER_MANUAL.md)**: 🛡️ 風險管理使用手冊。涵蓋 4 個風險等級（CONSERVATIVE / MODERATE / AGGRESSIVE / HIGH_RISK）、倉位計算邏輯與警報系統說明。

### 🧠 架構與全景
* **[ARCHITECTURE_OVERVIEW.md](ARCHITECTURE_OVERVIEW.md)**: 🗺️ 系統全局視野。解釋 v2.1 從資料獲取到訂單送出的全資料流。
* **[PROJECT_HANDOVER_MAP.md](PROJECT_HANDOVER_MAP.md)**: 🤝 開發者交接地圖。提供各模組的依賴關係與「舊版殘留區」的避坑指南。
* **[SRC_DIRECTORY_ANALYSIS.md](SRC_DIRECTORY_ANALYSIS.md)**: 📁 目錄結構詳解。告訴你每個資料夾為什麼存在、裡面放什麼。

### 🧪 測試與驗證
* **[BACKTEST_SYSTEM_GUIDE.md](BACKTEST_SYSTEM_GUIDE.md)**: 📈 回測系統專用指南。說明如何透過 Mock Connector 與 CLI 工具打磨您的交易策略，而不消耗真實資金。

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
👉 左轉：[QUICKSTART_V2.1.md](QUICKSTART_V2.1.md)

**💬 「我想用自己寫的歷史策略來驗證勝率...」**
👉 左轉：[BACKTEST_SYSTEM_GUIDE.md](BACKTEST_SYSTEM_GUIDE.md)

**💬 「如果我是一個接手專案的新開發者，我該從哪支程式看起？」**
👉 第一步先看：[PROJECT_HANDOVER_MAP.md](PROJECT_HANDOVER_MAP.md)，接著直接去讀 `src/bioneuronai/cli/main.py` 這個全系統的總入口。

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
