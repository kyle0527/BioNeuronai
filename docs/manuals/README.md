# BioNeuronAI 使用者操作手冊集中索引

> 建立日期：2026-05-12  
> 更新日期：2026-07-17  
> 方向權威：[`../CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)  
> 現況權威：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)  
> 工作順序權威：[`../archive/WORK_ORDER.md`](../archive/WORK_ORDER.md)  
> 目的：整理「使用者實際操作」手冊（開機、CLI、API、Dashboard、Docker、回測、風控、排查等）。  
> **本階段重點**：預設自主流程在虛擬帳戶／Paper 跑通；驗收用真實入口，**不用** pytest；多帳戶等商用周邊後續再加。  
>  
> **目前所在步驟 = 步驟 4（修本目錄手冊）**：步驟 1–3（檢查／移回／調整）核心已完成；  
> **在 manuals 改到可整本照做之前，不進入步驟 5（照手冊真實操作）。**

---

## 目錄

1. [本輪範圍](#1-本輪範圍)
2. [命名規則](#2-命名規則)
3. [本輪使用者操作主手冊](#3-本輪使用者操作主手冊)
4. [本輪輔助文件](#4-本輪輔助文件)
5. [重複與整併判斷](#5-重複與整併判斷)
6. [本輪老舊或需要修正的部分](#6-本輪老舊或需要修正的部分)
7. [本輪仍未列入但應建立的操作手冊](#7-本輪仍未列入但應建立的操作手冊)
8. [建議使用順序](#8-建議使用順序)
9. [維護規則](#9-維護規則)

---

## 1. 本輪範圍

本輪只處理「使用者操作」範圍。判斷標準很簡單：

1. 使用者會照著它啟動、操作、停止或排查系統。
2. 文件內容以命令、畫面、API、設定、錯誤處理為主。
3. 不整理純技術架構、roadmap、ADR、開發治理、部落格、研究計畫。
4. 沒有被這次移入或改到的文件，先不納入本輪整理；若之後修改到那個區域，再在該區域處理重複或移除。

---

## 2. 命名規則

`docs/manuals/` 以兩位數排序。使用者操作主線目前是：

- `02` 到 `07`：開機、CLI、API、前端、Docker
- `08` 到 `11`：回測、分析、策略、風控

`00` 與 `01` 是入口和驗收輔助，不是一般操作步驟。

`12` 與 `13` 是訓練/雲端作業，已移入但不列為本輪「一般使用者操作」主範圍；暫時保留，之後若整理訓練手冊再處理。

`14` 到 `20` 是本輪補齊的使用者操作缺冊。

---

## 3. 本輪使用者操作主手冊

| 編號 | 手冊 | 原始名稱 | 定位 | 目前狀態 |
|---:|---|---|---|---|
| 02 | [02_STARTUP_AND_SHUTDOWN.md](02_STARTUP_AND_SHUTDOWN.md) | `STARTUP_AND_SHUTDOWN_MANUAL.md` | 開機、關機、API、Dashboard、Docker | **2026-06-15** 釐清四入口 vs 雙主線；補 paper-live 開機與 ledger 驗收 |
| 03 | [03_QUICKSTART.md](03_QUICKSTART.md) | `QUICKSTART_V2.1.md` | 快速開始 | **2026-06-15** 對齊雙主線；與 02 部分重疊 |
| 04 | [04_CLI_OPERATION.md](04_CLI_OPERATION.md) | `OPERATION_MANUAL.md` | CLI 與標準 SOP | **2026-06-15** 完整重寫：雙主線、autonomous 參數表、產物路徑、已知 B 線限制 |
| 05 | [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md) | `API_USER_MANUAL.md` | REST API / WebSocket | **2026-06-15** 補 API 覆蓋範圍（無 autonomous/plan）；pretrade 風控層 |
| 06 | [06_FRONTEND_DASHBOARD.md](06_FRONTEND_DASHBOARD.md) | `FRONTEND_DASHBOARD_MANUAL.md` | Operations Dashboard | **2026-06-15** 雙主線與 UI 覆蓋表；修正 simulate/backtest 說明 |
| 07 | [07_DOCKER_DEPLOYMENT.md](07_DOCKER_DEPLOYMENT.md) | `DOCKER_DEPLOYMENT_MANUAL.md` | Docker Compose | **2026-06-15** 註明無 autonomous 服務；Docker 非本輪主驗證入口 |
| 08 | [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md) | `BACKTEST_SYSTEM_GUIDE.md` | 回測與 replay | **2026-06-15** 完整重寫：replay vs 雙主線、CLI 全命令、資料路徑、simulate/backtest 差異 |
| 09 | [09_ANALYSIS_MODULE.md](09_ANALYSIS_MODULE.md) | `ANALYSIS_MODULE_USER_MANUAL.md` | news / plan / pretrade | **2026-06-15** 補雙主線影響與 pretrade 風控層說明 |
| 10 | [10_STRATEGY_MODULE.md](10_STRATEGY_MODULE.md) | `STRATEGY_MODULE_USER_MANUAL.md` | strategy-backtest / strategy-run | **2026-06-15** 標明 Replay 路徑 vs 即時雙主線 |
| 11 | [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md) | `RISK_MANAGEMENT_USER_MANUAL.md` | 風控與 pretrade 風險解讀 | **2026-07-11** 對齊方向：B 線 quantity 優先 pretrade；學習可經 shared 回調 |
| 14 | [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) | 新增 | testnet / paper-live / autonomous / live 啟停與緊急停止 | **2026-06-15** 補雙主線對照與 B 線已知限制；live 依安全限制未執行 |
| 15 | [15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md) | 新增 | 歷史資料與 catalog 操作 | **2026-06-15** fallback 路徑、下載與 readiness 資料需求 |
| 16 | [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md) | 新增 | runtime、logs、output、模型產物位置 | **2026-06-15** 補 ledger / hub / memory / paper 路徑 |
| 17 | [17_ENVIRONMENT_VARIABLES.md](17_ENVIRONMENT_VARIABLES.md) | 新增 | `.env` 與環境變數 | **2026-06-15** 雙主線與 live 開關說明 |
| 18 | [18_OPERATION_TROUBLESHOOTING.md](18_OPERATION_TROUBLESHOOTING.md) | 新增 | CLI/API/Backtest/Pretrade 操作排查 | **2026-06-15** 新增雙主線混淆排查、`[rl]` FAQ |
| 19 | [19_DASHBOARD_TROUBLESHOOTING.md](19_DASHBOARD_TROUBLESHOOTING.md) | 新增 | Dashboard / CORS / API 連線 / 版面排查 | **2026-06-15** 補 autonomous 無 UI 說明 |
| 20 | [20_UI_END_TO_END_OPERATION.md](20_UI_END_TO_END_OPERATION.md) | 新增 | UI 端到端流程 | **2026-06-15** 補 B 線 CLI 前置步驟；修正 uvicorn 啟動說明 |

---

## 4. 本輪輔助文件

| 編號 | 手冊 | 定位 | 本輪處理方式 |
|---:|---|---|---|
| 00 | [00_MASTER_MANUAL.md](00_MASTER_MANUAL.md) | 總入口與閱讀順序 | **2026-06-15** 三徑架構、PROJECT_STATUS 權威 |
| 01 | [01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md) | 手冊操作驗收矩陣 | **2026-06-15** Level 2 autonomous、Level 3 paper-live |
| 12 | [12_NLP_TRAINING.md](12_NLP_TRAINING.md) | TinyLLM / unified trainer | 訓練手冊，暫不列入一般使用者操作主線 |
| 13 | [13_CLOUD_TRAINING_RUNBOOK.md](13_CLOUD_TRAINING_RUNBOOK.md) | 雲端 GPU 訓練 | 訓練/雲端手冊，暫不列入一般使用者操作主線 |
| 21 | [21_COLAB.md](21_COLAB.md) | Google Colab（micromamba 3.13 + GPU） | clone、安裝、smoke、可選短訓練；Paper 長跑仍用本機 |

---

## 5. 重複與整併判斷

| 重複區域 | 涉及手冊 | 判斷 | 建議 |
|---|---|---|---|
| 開機與基礎驗證 | 02、03、04 | 03/04 都有部分啟動與 status 指令 | 以 02 作為「開機關機」唯一入口，03 保留新手快速版，04 專注 CLI 指令參考 |
| backtest / simulate | 02、04、08 | 三份都有回測或模擬命令 | 02 只保留短驗收，08 保留完整回測說明，04 只列命令入口 |
| autonomous 值班 | 04、14 | 先前曾獨立成單檔，容易和 trade 主線平行重複 | 已整併回 04 的 CLI 命令說明與 14 的交易/自主值班操作，不再保留獨立平行手冊 |
| API 啟動 | 02、05、06、07 | 本地與 Docker 啟動資訊分散 | 02 放操作入口，05 放 API 規格，06 放前端操作，07 放 Docker 細節 |
| Chat 使用 | 04、05、06 | CLI、API、Dashboard 都會碰到 Chat | 04/05/06 只講使用，不在這裡整理模型訓練 |
| 風控 / pretrade | 09、11、05、06 | pretrade 既是分析、API、前端、風控交會點 | 09 講操作，11 講風控意義，05/06 只講入口 |
| 操作排查 | 18、19、各操作手冊 FAQ | 排查內容可能分散 | 18/19 做集中排查，各手冊只保留該功能最常見問題 |

---

## 6. 本輪老舊或需要修正的部分

| 問題 | 位置 | 狀態 | 建議 |
|---|---|---|---|
| 手冊原本散在 `docs/` 根目錄 | 多份手冊 | 已集中到 `docs/manuals/` | 後續新增操作手冊都放這裡 |
| Backtest 有兩份使用者入口 | `08_BACKTEST_SYSTEM.md`、`backtest/docs/USER_MANUAL.md` | 可能重疊 | 保留 `08` 當主入口，`backtest/docs/USER_MANUAL.md` 當子系統細節 |
| `12`、`13` 不屬一般使用者操作 | `12_NLP_TRAINING.md`、`13_CLOUD_TRAINING_RUNBOOK.md` | 暫時保留 | 本輪不擴充，之後整理訓練範圍時再處理 |
| 雙執行主線未在手冊中一致描述 | `docs/manuals/` 全系列 | **2026-06-15 已完成**（00–20 主手冊） | 權威：`PROJECT_STATUS` §1.4；`trade`≠`autonomous` |
| `pip install -e ".[rl]"` 誤導 | 04、DEVELOPMENT_TOOLS、18 | **2026-06-15 已修正** | `pyproject.toml` 無 `[rl]` extra |
| `docs/STARTUP_MODES.md` 與手冊不同步 | `docs/STARTUP_MODES.md` | **2026-06-15 已對齊** B 線限制 | 與 04/14 一致 |

---

## 7. 本輪仍未列入但應建立的操作手冊

| 建議編號 | 建議文件 | 優先級 | 原因 |
|---:|---|---|---|
| 21 | 待建立：Release readiness checklist | P2 | 若要正式對外發布，需要一份使用者角度的發版前操作確認表 |

目前下一個使用者可用性目標是先讓本機 Python 3.13 runtime、API/UI readiness、自然語言工具呼叫與交易判斷流程穩定；接著補齊 BTC/ETH `4h` 歷史資料，讓 readiness-gate 可以進入完整矩陣回測，最後長時間跑 paper-live / testnet monitor 並重建 Docker image。

---

## 8. 建議使用順序

第一次接手或做**本階段（工程自主）**驗收時：

1. [`../CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md) — 優先級與什麼叫跑通  
2. [03_QUICKSTART.md](03_QUICKSTART.md) — 安裝與預設驗證順序  
3. [04_CLI_OPERATION.md](04_CLI_OPERATION.md) — `autonomous`／`trade` 參數  
4. [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) — Paper／自主長跑  
5. [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md) — 記帳產物怎麼對  
6. [01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md) — Level 2.5 等矩陣  
7. [15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md) + [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md) — 長期歷史驗證  
8. [02_STARTUP_AND_SHUTDOWN.md](02_STARTUP_AND_SHUTDOWN.md)  
9. [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md)／[06_FRONTEND_DASHBOARD.md](06_FRONTEND_DASHBOARD.md)（可選）  
10. 其餘 09–11、17–20 依需要  

**不要**把「pytest 全綠」寫進手冊驗收通過條件。

---

## 9. 維護規則

1. 本輪只整理使用者操作手冊，不主動整理技術、架構、roadmap、開發治理文件。
2. 檔名必須保留兩位數排序。
3. 沒有被本輪修改到的文件，就算內容有重疊，先不處理。
4. 若未來修改到其他文件區域，再在該區域處理重複、老舊或移除。
5. 每次改 API route、CLI command、Docker service、Dashboard panel，都要同步更新對應操作手冊。
6. 若某手冊的命令未經實際入口驗證，必須在狀態欄標記「需實測」。
7. 每次改 Dashboard 使用者流程，都要同步更新 `20_UI_END_TO_END_OPERATION.md`，避免只更新面板參考卻漏掉端到端操作。
8. 方向／優先級變更時，先更新 `docs/CURRENT_DIRECTION.md` 與 `docs/PROJECT_STATUS.md`，再同步 `00`、`01`、`03`、`04`、`14` 與本索引。  
9. 手冊不得再寫成：pytest 即正式驗收；B 線無學習／永遠獨立 paper；現役 v1 stub；多帳戶為本階段 P0。
