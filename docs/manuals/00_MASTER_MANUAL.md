# BioNeuronAI 系統主手冊 (Master Manual)

> **套件版本**：v2.1（`pyproject.toml`）  
> **更新日期**：2026-07-11  
> **方向權威**：[`../CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)  
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)  
> **v2.2**：僅 roadmap／訓練後驗證期用語，非已發布套件版

---

## 目錄

1. [系統總覽](#1-系統總覽)
   - [1.1 本階段要先達成什麼](#11-本階段要先達成什麼)
   - [1.2 三條執行路徑（不可混用驗收標準）](#12-三條執行路徑不可混用驗收標準)
2. [核心導覽地圖](#2-核心導覽地圖)
   - [2.1 入門與操作](#21-入門與操作)
   - [2.2 分析、策略與交易](#22-分析策略與交易)
   - [2.3 API 與部署](#23-api-與部署)
   - [2.4 訓練與作業](#24-訓練與作業)
   - [2.5 架構與全景](#25-架構與全景)
   - [2.6 實際操作驗證](#26-實際操作驗證)
3. [架構哲學 (v2.1 核心精神)](#3-架構哲學-v21-核心精神)
   - [3.1 全局單一事實來源](#31-全局單一事實來源-single-source-of-truth)
   - [3.2 決策與執行的分水嶺](#32-決策與執行的分水嶺)
   - [3.3 狀態管理逐步集中](#33-狀態管理逐步集中)
   - [3.4 現行優先級與驗證哲學](#34-現行優先級與驗證哲學)
4. [快速跳轉指南](#4-快速跳轉指南)
5. [模組職責劃分](#5-模組職責劃分)
6. [開發與維護準則](#6-開發與維護準則)

---

## 1. 系統總覽

BioNeuronAI 是面向加密貨幣期貨的 **自我成長 AI 交易系統**（套件 **v2.1**）：以虛擬帳戶／Paper 為訓練場，目標是 **交易即訓練**。

- **方向與優先級**：[`CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)  
- **模組完成度**：[`PROJECT_STATUS.md`](../PROJECT_STATUS.md)

### 1.1 本階段要先達成什麼

1. **工程自主**：預設流程能自己跑（決策→虛擬帳戶下單→平倉→**正確記帳**）。  
2. **穩定確認**：長跑／重啟／卡單行為可預期。  
3. **之後**才基線訓練與開滿在線改善。  
4. **終局**：自主運行時直接改善——不是永久只跑不學。  

**多帳戶、API 認證等商用周邊：後續再加，不阻塞本階段。**

### 1.2 三條執行路徑（不可混用驗收標準）

| 路徑 | 入口 | 角色 | 產物重點 |
|------|------|------|----------|
| **主線 B（預設 AI 自主）** | `autonomous`（主要 CLI） | 定時規劃閉環長跑 | `decision_ledger.jsonl` + shared 執行／平倉學習鏈 |
| **主線 A（即時 tick）** | `trade` / API `trade/start` | WebSocket 監控與 T0–T2 觀測 | ActionRecord、`memory/`、LoRA／Hub |
| **Replay 回測（長期）** | `backtest` / `strategy-backtest` | 先下載歷史再驗證大區間 | `backtest/runtime/` |

核心原則：

- **決策與執行分層**：`planning/` 編排；`trading/`／TradingEngine 執行事實。  
- **契約化**：`src/schemas/` 為跨模組資料單一來源。  
- **單一模型**：`unified_v2_100m` shared；可 `trained: false`（工程可驗，智能未成立）。  
- **正式驗收**：真實 CLI／Paper／歷史回測產物；**不是** pytest。  
- **模型可初始化 ≠ 績效已驗證**：見 `config/active_model.json`。

---

## 2. 核心導覽地圖

技術細節與操作守則分散在專用手冊；以下為導航索引。

### 2.1 入門與操作

- [02_STARTUP_AND_SHUTDOWN.md](02_STARTUP_AND_SHUTDOWN.md)：開機與關機  
- [03_QUICKSTART.md](03_QUICKSTART.md)：快速開始（建議先讀）  
- [04_CLI_OPERATION.md](04_CLI_OPERATION.md)：CLI 全參數  
- [06_FRONTEND_DASHBOARD.md](06_FRONTEND_DASHBOARD.md)：Operations Dashboard  
- [20_UI_END_TO_END_OPERATION.md](20_UI_END_TO_END_OPERATION.md)：UI 端到端  

### 2.2 分析、策略與交易

- [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md)：歷史回測（長期驗證）  
- [09_ANALYSIS_MODULE.md](09_ANALYSIS_MODULE.md)：news / plan / pretrade  
- [10_STRATEGY_MODULE.md](10_STRATEGY_MODULE.md)：strategy-backtest  
- [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md)：風控  
- [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md)：paper / autonomous / testnet / live  
- [15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md)：歷史資料取得  
- [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md)：產物與對帳  

### 2.3 API 與部署

- [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md)  
- [07_DOCKER_DEPLOYMENT.md](07_DOCKER_DEPLOYMENT.md)  
- [17_ENVIRONMENT_VARIABLES.md](17_ENVIRONMENT_VARIABLES.md)  
- [18_OPERATION_TROUBLESHOOTING.md](18_OPERATION_TROUBLESHOOTING.md)  
- [19_DASHBOARD_TROUBLESHOOTING.md](19_DASHBOARD_TROUBLESHOOTING.md)  

### 2.4 訓練與作業

- [12_NLP_TRAINING.md](12_NLP_TRAINING.md)：訓練手冊（階段 3，非本階段主線）  
- [13_CLOUD_TRAINING_RUNBOOK.md](13_CLOUD_TRAINING_RUNBOOK.md)：雲端 GPU  

### 2.5 架構與全景

- [ARCHITECTURE_OVERVIEW.md](../ARCHITECTURE_OVERVIEW.md)  
- [PROJECT_HANDOVER_MAP.md](../PROJECT_HANDOVER_MAP.md)  
- [SRC_DIRECTORY_ANALYSIS.md](../SRC_DIRECTORY_ANALYSIS.md)  
- [CURRENT_DIRECTION.md](../CURRENT_DIRECTION.md)  

### 2.6 實際操作驗證

- [01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md)：手冊式驗收矩陣（含 Level 2.5 自主 paper）  
- [TESTING_AND_VALIDATION_GUIDE.md](../TESTING_AND_VALIDATION_GUIDE.md)：驗證哲學  

---

## 3. 架構哲學 (v2.1 核心精神)

### 3.1 全局單一事實來源 (Single Source of Truth)

所有資料結構（市場、訂單、新聞結果等）的**唯一**定義在 `src/schemas/`。禁止模組私自重複定義相同概念的 `BaseModel`。

### 3.2 決策與執行的分水嶺

- **`planning/`**：plan、pretrade、`AutonomousOperator`、decision ledger、adaptation。  
- **`core/TradingEngine`**：主線 A 的 WebSocket 管線；亦為 B 線 paper 的**共用執行與平倉學習入口**。  
- **`trading/`**：VirtualAccount、訂單與持倉事實。  

主線 B 執行層（2026-06-15 起已對齊的部分）：

- `--execute-paper` **優先** pretrade `quantity`（× risk）；無效才 fallback notional fraction。  
- 已有持倉跳過進場（`existing_position`）。  
- 平倉 shared callback → 引擎學習鏈 + ledger。  

仍須在真實 paper 長跑中確認穩定（本階段 P0），見 [`CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)。

### 3.3 狀態管理逐步集中

- 正式方向：B 不再維護第二套正式 paper 執行器  
- `trading/virtual_account.py` 為帳戶事實核心  
- `backtest/` 依賴同一帳戶語意  
- 持久化與跨進程狀態仍持續收斂（**不是**本階段的多租戶產品）

### 3.4 現行優先級與驗證哲學

- **先工程自主與記帳，再訓練改善；終局邊自主邊改善。**  
- **日常**：幣安虛擬帳戶／Paper 真實操作。  
- **長期**：先下載歷史，再 backtest／readiness-gate。  
- **正式驗收不用 pytest／test 檔。**  
- **多帳戶／API 認證等：延後。**  

詳見 [`TESTING_AND_VALIDATION_GUIDE.md`](../TESTING_AND_VALIDATION_GUIDE.md)。

---

## 4. 快速跳轉指南

| 情境 | 去哪 |
|------|------|
| 現行優先級與什麼叫流程跑通 | [`CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md) |
| 快速啟動 | [03_QUICKSTART.md](03_QUICKSTART.md) |
| 驗 AI 自主長跑（預設流程） | [04_CLI_OPERATION.md](04_CLI_OPERATION.md) + [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) |
| 只靠 UI 操作 | [20_UI_END_TO_END_OPERATION.md](20_UI_END_TO_END_OPERATION.md) |
| 歷史長期驗證 | [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md)、[15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md) |
| 正式怎麼驗收、為何不用單元測試 | [01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md)、[`TESTING_AND_VALIDATION_GUIDE.md`](../TESTING_AND_VALIDATION_GUIDE.md) |
| 接手開發從哪看 | [`PROJECT_HANDOVER_MAP.md`](../PROJECT_HANDOVER_MAP.md)，再讀 `src/bioneuronai/cli/main.py` |
| 訂單 Schema 有無停損欄位 | `src/schemas/trading.py` |

---

## 5. 模組職責劃分

| 模組分層 | 職責簡述 |
|----------|----------|
| **`core/`** | 交易引擎、AI 推理、ActionRecord、Hub／LoRA 閉環 |
| **`schemas/`** | 全域共用 Pydantic 契約 |
| **`planning/`** | 計劃、盤前、自主迴圈、ledger、adaptation |
| **`trading/`** | 虛擬帳戶、持倉與執行事實 |
| **`api/`** | FastAPI 入口 |
| **`cli/`** | `main.py` 指令列入口 |

---

## 6. 開發與維護準則

1. **方向變更時**：先更新 `CURRENT_DIRECTION.md` 與 `PROJECT_STATUS.md`，再改手冊。  
2. **文件治理**：大幅改碼前同步操作手冊（見 `DOCUMENTATION_GOVERNANCE_PLAN.md`）。  
3. **禁止把密碼寫入檔案**：API Keys 只在 `.env`。  
4. **正式入口**：`main.py`、`src/bioneuronai/cli/main.py`、`src/bioneuronai/api/app.py`。舊腳本／pytest **不是**功能完成證明。  
5. **驗收**：用虛擬帳戶真實操作或歷史回測產物；勿以 test 檔充當本階段完成標準。  
6. **未訓練模型**：可驗證工程閉環；勿用 PnL 宣稱智能達成。  
7. **修改後重建目錄**：章節增刪後必須重做本檔「目錄」，避免錨點失效。  
