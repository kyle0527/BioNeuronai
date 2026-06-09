# BioNeuronAI 使用者操作手冊集中索引

> 建立日期：2026-05-12
> 更新日期：2026-05-19
> 目的：只整理「使用者實際操作系統時會用到的手冊」，包含開機、關機、CLI、API、Dashboard、Docker、回測、分析、策略、風控、常見問題與操作排查。

---

## 📑 目錄

- [1. 本輪範圍](#1-本輪範圍)
- [2. 命名規則](#2-命名規則)
- [3. 本輪使用者操作主手冊](#3-本輪使用者操作主手冊)
- [4. 本輪輔助文件](#4-本輪輔助文件)
- [5. 重複與整併判斷](#5-重複與整併判斷)
- [6. 本輪老舊或需要修正的部分](#6-本輪老舊或需要修正的部分)
- [7. 本輪仍未列入但應建立的操作手冊](#7-本輪仍未列入但應建立的操作手冊)
- [8. 建議使用順序](#8-建議使用順序)
- [9. 維護規則](#9-維護規則)

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
| 02 | [02_STARTUP_AND_SHUTDOWN.md](02_STARTUP_AND_SHUTDOWN.md) | `STARTUP_AND_SHUTDOWN_MANUAL.md` | 開機、關機、API、Dashboard、Docker | 新增，可用 |
| 03 | [03_QUICKSTART.md](03_QUICKSTART.md) | `QUICKSTART_V2.1.md` | 快速開始 | 可用，部分內容與 02 重疊 |
| 04 | [04_CLI_OPERATION.md](04_CLI_OPERATION.md) | `OPERATION_MANUAL.md` | CLI 與標準 SOP | 可用；已納入 `autonomous` 單輪值班入口 |
| 05 | [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md) | `API_USER_MANUAL.md` | REST API / WebSocket | 已用本地 API 逐端點驗證 |
| 06 | [06_FRONTEND_DASHBOARD.md](06_FRONTEND_DASHBOARD.md) | `FRONTEND_DASHBOARD_MANUAL.md` | Operations Dashboard | 已改為 Operations / Validation / Config / Dev Tools / Chat；已補 paper-live、Training / Model、Live Market Chart；2026-05-19 已修復 JSON/Request History/長文字版面溢出 |
| 07 | [07_DOCKER_DEPLOYMENT.md](07_DOCKER_DEPLOYMENT.md) | `DOCKER_DEPLOYMENT_MANUAL.md` | Docker Compose | 本輪先不作主要驗證；本機功能收斂後最後重建 image |
| 08 | [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md) | `BACKTEST_SYSTEM_GUIDE.md` | 回測與 replay | 已用短區間指令與 API 驗證 |
| 09 | [09_ANALYSIS_MODULE.md](09_ANALYSIS_MODULE.md) | `ANALYSIS_MODULE_USER_MANUAL.md` | news / plan / pretrade | 已用 CLI 與 API 驗證 |
| 10 | [10_STRATEGY_MODULE.md](10_STRATEGY_MODULE.md) | `STRATEGY_MODULE_USER_MANUAL.md` | strategy-backtest / strategy-run | 已用短區間 CLI 與 API 驗證 |
| 11 | [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md) | `RISK_MANAGEMENT_USER_MANUAL.md` | 風控與 pretrade 風險解讀 | 已用 pretrade / dashboard risk 驗證 |
| 14 | [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) | 新增 | testnet / paper-live / autonomous / live 啟停與緊急停止 | 已驗證本地 API 啟停與 AI 載入；live 依安全限制未執行 |
| 15 | [15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md) | 新增 | 歷史資料與 catalog 操作 | 已驗證 |
| 16 | [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md) | 新增 | runtime、logs、output、模型產物位置 | 已驗證 |
| 17 | [17_ENVIRONMENT_VARIABLES.md](17_ENVIRONMENT_VARIABLES.md) | 新增 | `.env` 與環境變數 | 已驗證 |
| 18 | [18_OPERATION_TROUBLESHOOTING.md](18_OPERATION_TROUBLESHOOTING.md) | 新增 | CLI/API/Backtest/Pretrade 操作排查 | 已驗證 |
| 19 | [19_DASHBOARD_TROUBLESHOOTING.md](19_DASHBOARD_TROUBLESHOOTING.md) | 新增 | Dashboard / CORS / API 連線 / 版面排查 | 已驗證 |
| 20 | [20_UI_END_TO_END_OPERATION.md](20_UI_END_TO_END_OPERATION.md) | 新增 | UI 從啟動到完成一輪操作的端到端流程 | 已完成 API/HTTP/build、本地瀏覽器操作與 API/frontend 複驗；Docker image 仍依本輪規劃留到最後重建 |

---

## 4. 本輪輔助文件

| 編號 | 手冊 | 定位 | 本輪處理方式 |
|---:|---|---|---|
| 00 | [00_MASTER_MANUAL.md](00_MASTER_MANUAL.md) | 總入口與閱讀順序 | 保留作入口，不主動擴充技術內容 |
| 01 | [01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md) | 手冊操作驗收矩陣 | 保留作操作驗收輔助 |
| 12 | [12_NLP_TRAINING.md](12_NLP_TRAINING.md) | TinyLLM / unified trainer | 訓練手冊，暫不列入一般使用者操作主線 |
| 13 | [13_CLOUD_TRAINING_RUNBOOK.md](13_CLOUD_TRAINING_RUNBOOK.md) | 雲端 GPU 訓練 | 訓練/雲端手冊，暫不列入一般使用者操作主線 |

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

---

## 7. 本輪仍未列入但應建立的操作手冊

| 建議編號 | 建議文件 | 優先級 | 原因 |
|---:|---|---|---|
| 21 | 待建立：Release readiness checklist | P2 | 若要正式對外發布，需要一份使用者角度的發版前操作確認表 |

目前下一個使用者可用性目標是先讓本機 Python 3.13 runtime、API/UI readiness、自然語言工具呼叫與交易判斷流程穩定；接著補齊 BTC/ETH `4h` 歷史資料，讓 readiness-gate 可以進入完整矩陣回測，最後長時間跑 paper-live / testnet monitor 並重建 Docker image。

---

## 8. 建議使用順序

第一次接手或驗收時，建議順序如下：

1. [02_STARTUP_AND_SHUTDOWN.md](02_STARTUP_AND_SHUTDOWN.md)
2. [03_QUICKSTART.md](03_QUICKSTART.md)
3. [04_CLI_OPERATION.md](04_CLI_OPERATION.md)
4. [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md)
5. [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md)
6. [06_FRONTEND_DASHBOARD.md](06_FRONTEND_DASHBOARD.md)
7. [09_ANALYSIS_MODULE.md](09_ANALYSIS_MODULE.md)
8. [10_STRATEGY_MODULE.md](10_STRATEGY_MODULE.md)
9. [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md)
10. [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md)
11. [15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md)
12. [16_RUNTIME_ARTIFACTS.md](16_RUNTIME_ARTIFACTS.md)
13. [17_ENVIRONMENT_VARIABLES.md](17_ENVIRONMENT_VARIABLES.md)
14. [18_OPERATION_TROUBLESHOOTING.md](18_OPERATION_TROUBLESHOOTING.md)
15. [19_DASHBOARD_TROUBLESHOOTING.md](19_DASHBOARD_TROUBLESHOOTING.md)
16. [20_UI_END_TO_END_OPERATION.md](20_UI_END_TO_END_OPERATION.md)
17. [01_MANUAL_OPERATION_VERIFICATION_PLAN.md](01_MANUAL_OPERATION_VERIFICATION_PLAN.md)

---

## 9. 維護規則

1. 本輪只整理使用者操作手冊，不主動整理技術、架構、roadmap、開發治理文件。
2. 檔名必須保留兩位數排序。
3. 沒有被本輪修改到的文件，就算內容有重疊，先不處理。
4. 若未來修改到其他文件區域，再在該區域處理重複、老舊或移除。
5. 每次改 API route、CLI command、Docker service、Dashboard panel，都要同步更新對應操作手冊。
6. 若某手冊的命令未經實際入口驗證，必須在狀態欄標記「需實測」。
7. 每次改 Dashboard 使用者流程，都要同步更新 `20_UI_END_TO_END_OPERATION.md`，避免只更新面板參考卻漏掉端到端操作。
