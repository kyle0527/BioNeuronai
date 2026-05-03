# BioNeuronAI 手冊盤點與實際操作驗收計畫

> 版本：v2.1 / v2.2 過渡期  
> 建立日期：2026-05-02  
> 目的：用「使用者手冊能否帶著操作者完成真實操作」作為專案可用性的判斷標準。本文不以 smoke test 作為主要驗收依據，而是以 CLI、API、Dashboard、Docker、Backtest、Testnet 等實際入口驗證。

---

## 📑 目錄

- [1. 判斷原則](#1-判斷原則)
- [2. 目前已有的主要使用手冊](#2-目前已有的主要使用手冊)
- [3. 目前缺少或應補強的手冊](#3-目前缺少或應補強的手冊)
- [4. 建議驗收順序](#4-建議驗收順序)
  - [Level 0：不用金鑰、不用 Docker](#level-0不用金鑰不用-docker)
  - [Level 1：本地 API + Dashboard](#level-1本地-api-dashboard)
  - [Level 2：需要外部網路或新聞 API](#level-2需要外部網路或新聞-api)
  - [Level 3：Testnet 交易驗收](#level-3testnet-交易驗收)
  - [Level 4：Live 前驗收](#level-4live-前驗收)
- [5. 目前已完成的手冊式實際印證紀錄](#5-目前已完成的手冊式實際印證紀錄)
  - [2026-05-02 第一冊 02STARTUPAND_SHUTDOWN.md 實際操作驗證](#2026-05-02-第一冊-02startupandshutdownmd-實際操作驗證)
- [6. 下一步](#6-下一步)
  - [2026-05-02 後續使用者操作手冊實際驗證](#2026-05-02-後續使用者操作手冊實際驗證)
  - [2026-05-02 Docker image 重建前全面檢查](#2026-05-02-docker-image-重建前全面檢查)
  - [尚未完成的 image 層驗證](#尚未完成的-image-層驗證)

---

## 1. 判斷原則

一項功能只有在同時滿足以下條件時，才視為「手冊可用」：

1. 有對應手冊或章節。
2. 手冊列出的命令、URL、環境變數與目前程式碼一致。
3. 使用者可以照手冊從啟動到完成操作。
4. 操作完成後有可觀察輸出，例如 CLI 結果、API JSON、Dashboard 畫面、runtime 目錄、模型權重或報告檔。
5. 若功能需要 API key、Docker、GPU 或實盤資金，手冊必須明確標示前置條件與安全限制。

---

## 2. 目前已有的主要使用手冊

| 類別 | 文件 | 目前用途 | 初步狀態 |
|---|---|---|---|
| 總入口 | `docs/manuals/00_MASTER_MANUAL.md` | 專案總覽與閱讀順序 | 可用，但偏導覽 |
| 開機開始 | `docs/manuals/02_STARTUP_AND_SHUTDOWN.md` | 本地 CLI、API + Dashboard、Docker 的開機與關機流程 | 新增，可用 |
| 快速開始 | `docs/manuals/03_QUICKSTART.md` | 安裝、`.env`、status、news、plan、pretrade、trade、chat | 可用，與 02 有少量重疊 |
| 日常操作 | `docs/manuals/04_CLI_OPERATION.md` | CLI 指令與標準 SOP | 可用，但部分操作需再用真實入口逐條核對 |
| API | `docs/manuals/05_API_USER_MANUAL.md` | FastAPI 端點、PowerShell 範例 | 初步與 route 清單一致，需逐端點實測 |
| 前端 | `docs/manuals/06_FRONTEND_DASHBOARD.md` | DevOps Dashboard 面板操作 | 可用，需補本地 5173 與 Docker 3000 的差異驗收 |
| Docker | `docs/manuals/07_DOCKER_DEPLOYMENT.md` | Compose 服務、volume、healthcheck | 可用，需完整 docker compose 實測 |
| 回測 | `docs/manuals/08_BACKTEST_SYSTEM.md` | backtest / simulate / BacktestEngine | 可用，需補可快速完成的短區間驗收指令 |
| Backtest 子系統 | `backtest/docs/USER_MANUAL.md` | Backtest 子系統操作 | 需與根目錄回測手冊合併或交叉索引 |
| 分析 | `docs/manuals/09_ANALYSIS_MODULE.md` | news / plan / pretrade | 可用，需核對 API request schema 是否完全一致 |
| 策略 | `docs/manuals/10_STRATEGY_MODULE.md` | strategy-backtest / strategy-run | 可用，需實測短區間 strategy-backtest |
| 風控 | `docs/manuals/11_RISK_MANAGEMENT.md` | 風險等級、倉位計算、pretrade 整合 | 可用，但偏概念，缺少可執行驗收步驟 |
| RAG | `docs/RAG_TECHNICAL_MANUAL.md` | RAG 技術架構 | 技術手冊，不是使用者操作手冊 |
| NLP 訓練 | `docs/manuals/12_NLP_TRAINING.md` | TinyLLM / unified trainer | 可用，但屬訓練手冊，不是日常操作 |
| 雲端訓練 | `docs/manuals/13_CLOUD_TRAINING_RUNBOOK.md` | GPU 訓練 dry-run、resume、artifact 回收 | 可用，需與目前 signal tensor 狀態同步 |
| 架構 | `docs/ARCHITECTURE_OVERVIEW.md` | 模組與資料流 | 可用，非操作手冊 |
| 交接 | `docs/PROJECT_HANDOVER_MAP.md` | 接手開發路徑 | 可用，非一般使用者手冊 |

---

## 3. 目前缺少或應補強的手冊

| 優先級 | 建議新增/補強文件 | 原因 |
|---|---|---|
| P0 | `docs/manuals/14_META_LEARNER.md` | v2.2 已有 `meta_learner` 初版與模型權重，但目前主要記在開發日誌與 roadmap，不夠像使用手冊。 |
| P0 | `docs/manuals/15_TESTNET_AND_LIVE_TRADING.md` | `trade --testnet` 與 `trade --live` 風險很高，應獨立成手冊，包含啟動、停止、金鑰、倉位限制、緊急停止。 |
| P1 | `docs/manuals/16_DATA_ACQUISITION.md` | 歷史資料下載、catalog、資料路徑、資料缺失排查目前分散在多處。 |
| P1 | `docs/manuals/17_RUNTIME_ARTIFACTS.md` | backtest/runtime、logs、output、data/processed、rl_models 的產物位置與保留策略需集中說明。 |
| P1 | `docs/manuals/18_ENVIRONMENT_VARIABLES.md` | `.env.example` 很長，Docker、API、交易、新聞、CORS 的環境變數應集中成參考表。 |
| P2 | `docs/manuals/19_INCIDENT_RESPONSE.md` | 實盤或長時間監控時，應有 API 掛掉、交易卡住、餘額異常、新聞 API 失敗的處理流程。 |
| P2 | `docs/manuals/20_RELEASE_READINESS_CHECKLIST.md` | 每次要標記版本前，按手冊驗收結果確認是否可發布。 |

---

## 4. 建議驗收順序

### Level 0：不用金鑰、不用 Docker

| 手冊 | 實際入口 | 成功標準 |
|---|---|---|
| Quickstart / Operation | `python main.py --help` | CLI 顯示所有正式命令 |
| Quickstart / Operation | `python main.py status` | 顯示核心模組 `[OK]`，版本可讀 |
| Backtest | `python main.py backtest-data --symbol BTCUSDT --interval 1h` | 能列出本地歷史資料 |
| Backtest | 短區間 `simulate` | 能產生 `backtest/runtime/<run_id>` |
| Backtest | 短區間 `backtest` | 能產生交易統計與 runtime |
| Frontend | `cd frontend/devops-d && npm run build` | build 成功並產生 `dist/` |

### Level 1：本地 API + Dashboard

| 手冊 | 實際入口 | 成功標準 |
|---|---|---|
| API | 啟動 `uvicorn bioneuronai.api.app:app` | API 可訪問 |
| API | `GET /api/v1/status` | `all_ok=true` |
| API | `GET /api/v1/backtest/catalog` | 可列出 dataset |
| Frontend | `npm run dev` 或 Docker frontend | Dashboard 可開啟並打到 API |
| Frontend | Status / Backtest / API Playground | 前端操作能得到後端回應 |

### Level 2：需要外部網路或新聞 API

| 手冊 | 實際入口 | 成功標準 |
|---|---|---|
| Analysis | `python main.py news --symbol BTCUSDT` | 能完成新聞分析或明確降級 |
| Analysis | `python main.py plan --symbol BTCUSDT` | 能產出計畫或明確列出外部資料失敗原因 |
| Analysis | `python main.py pretrade --symbol BTCUSDT --action long` | 能產出 PROCEED / CAUTION / REJECT 與理由 |

### Level 3：Testnet 交易驗收

| 手冊 | 實際入口 | 成功標準 |
|---|---|---|
| 待建立：Testnet/Live Trading | `python main.py trade --symbol BTCUSDT --testnet` | 能啟動監控、讀取價格、可用 Ctrl+C 停止 |
| API | `POST /api/v1/trade/start` / `stop` | API 可啟停交易 task，不殘留背景程序 |
| Dashboard | TradeControlPanel | UI 可啟停並看到狀態 |

### Level 4：Live 前驗收

| 手冊 | 實際入口 | 成功標準 |
|---|---|---|
| 待建立：Live Trading | `trade --live` 前檢查 | 必須完成人工二次確認、金鑰、餘額、槓桿、最大倉位限制 |
| Backtest / Strategy | 長區間 OOS / walk-forward | 有固定資料區間、命令、結果檔與績效摘要 |
| Risk | pretrade + risk settings | 最大單筆風險、每日風險、最大回撤限制都可查證 |

---

## 5. 目前已完成的手冊式實際印證紀錄

以下是 2026-05-02 已用實際入口完成的操作，不屬於 smoke test：

| 操作 | 結果 |
|---|---|
| `python main.py --help` | 成功列出 CLI 命令 |
| `python main.py status` | 成功，核心模組顯示 OK，版本 v2.1 |
| `python main.py backtest-data --symbol BTCUSDT --interval 1h` | 成功，找到 BTCUSDT 1h，2020-01-01 到 2023-12-31，共 1461 個 zip |
| 短區間 `simulate` | 成功，產生 runtime |
| 短區間 `backtest` | 成功，實際產生開平倉與回測統計 |
| `frontend/devops-d npm run build` | 成功，Vite production build 完成 |
| 本地 API 啟動 + `GET /api/v1/status` | 成功，`all_ok=true` |
| 本地 API `GET /api/v1/backtest/catalog` | 成功，`success=true`，dataset_count=1 |

### 2026-05-02 第一冊 `02_STARTUP_AND_SHUTDOWN.md` 實際操作驗證

| 路線 | 操作 | 結果 |
|---|---|---|
| 前置檢查 | `python main.py --help` | 通過，CLI 命令完整列出 |
| 前置檢查 | `python main.py status` | 通過，核心模組 OK，版本 v2.1 |
| 前置檢查 | `.env` 存在與 `git check-ignore .env` | 通過，`.env` 存在且被 Git ignore |
| 資料檢查 | `python main.py backtest-data --symbol BTCUSDT --interval 1h` | 通過，BTCUSDT 1h，2020-01-01 到 2023-12-31，共 1461 zip |
| CLI 路線 | 短區間 `simulate` | 通過，Run ID `20260502_112029_d82dca91` |
| CLI 路線 | 短區間 `backtest` | 通過，Run ID `20260502_112029_6f4947a5`，總交易 9 筆 |
| 本地 API | 啟動 uvicorn 後 `GET /api/v1/status` | 通過，`all_ok=true` |
| 本地 API | `GET /api/v1/backtest/catalog` | 通過，`success=true`，dataset_count=1 |
| 本地 Dashboard | `npm run dev -- --host 127.0.0.1 --port 5173` | 通過，HTTP 200 |
| Docker | `docker compose config --services` | 通過，列出 status/api/backtest/frontend/news/plan/pretrade/simulate |
| Docker | `docker compose ps` | 通過，`bioneuron-api` 與 `bioneuron-frontend` 已 running 且 healthy |
| Docker API | `GET http://127.0.0.1:8000/api/v1/status` | 通過，`all_ok=true` |
| Docker Frontend | `GET http://127.0.0.1:3000` | 通過，HTTP 200 |
| 關機檢查 | 查詢本地 uvicorn / Vite / trade 殘留程序 | 通過，未發現本輪啟動的殘留程序 |

---

## 6. 下一步

### 2026-05-02 後續使用者操作手冊實際驗證

以下操作均使用正式入口執行，未使用 `tests/`、未執行 smoke test、未建立測試檔。

| 手冊 | 實際入口 | 結果 |
|---|---|---|
| `03_QUICKSTART.md` | `status`、`news`、`plan`、`pretrade`、`chat` | 通過；`pretrade` 正常回傳 `REJECT` 風控結果，屬有效操作結果 |
| `04_CLI_OPERATION.md` | CLI help / status / data / simulate / backtest / news / plan / pretrade / chat | 通過；均可由目前 CLI 入口執行 |
| `05_API_USER_MANUAL.md` | 本地 API `127.0.0.1:8001` 逐端點呼叫 | 通過；REST 端點與三個 WebSocket 端點均可連線並取得回應 |
| `06_FRONTEND_DASHBOARD.md` | `npm run build`、本地 Vite HTTP 200、Docker frontend HTTP 200 | 通過；production build 成功 |
| `07_DOCKER_DEPLOYMENT.md` | `docker compose config --quiet`、`docker compose run --rm status`、`docker compose run --rm backtest` | 部分通過；source compose 已修正並通過 config，舊 image 的 `backtest` 可執行；`simulate` 需等 image 重建後重跑 |
| `08_BACKTEST_SYSTEM.md` | 短區間 `simulate` / `backtest`、API run、runtime 查詢 | 通過；產生實際 runtime |
| `09_ANALYSIS_MODULE.md` | `news`、`plan`、`pretrade`、API `news` / `pretrade` | 通過；外部新聞可正常降級或回傳分析結果 |
| `10_STRATEGY_MODULE.md` | `strategy-backtest` 短區間、API `/api/v1/backtest/strategy-run` | 通過；10 個策略模板均可執行並產生 runtime |
| `11_RISK_MANAGEMENT.md` | `pretrade` 風控檢查與 Dashboard risk snapshot | 通過；風控結果可觀察，未繞過 REJECT |
| `14_TESTNET_AND_LIVE_TRADING.md` | API `trade/start` + `trade/stop`，`testnet=true` | 通過；可啟動並停止測試網監控。Live 未執行，依手冊安全限制保留人工確認 |
| `15_DATA_ACQUISITION.md` | `backtest-data`、API catalog / inspect | 通過；BTCUSDT 1h 本地資料可列出並載入 |
| `16_RUNTIME_ARTIFACTS.md` | `backtest-runs`、runtime 目錄檢查 | 通過；可列出最新 runs，runtime 內含 summary/status/account/result/orders |
| `17_ENVIRONMENT_VARIABLES.md` | `.env` 存在、`.env` 被 ignore、key 名稱檢查、`.env.example` 對齊 compose | 通過；未輸出任何 secret 值 |
| `18_OPERATION_TROUBLESHOOTING.md` | CLI/API/Docker 狀態與殘留程序檢查 | 通過；本輪啟動的本地 API/Vite/trade 未殘留 |
| `19_DASHBOARD_TROUBLESHOOTING.md` | API status、frontend HTTP、WebSocket 實際連線 | 通過；REST 與 WebSocket 入口可用 |

### 2026-05-02 Docker image 重建前全面檢查

| 檢查項目 | 結果 |
|---|---|
| 中斷後殘留建置程序 | 已停止本輪殘留的 `docker compose build api frontend` process |
| Python 語法解析 | 通過；正式程式範圍 157 個 `.py` 檔案可 AST parse |
| Docker command 對 CLI parser | 通過；`status/news/pretrade/plan/backtest/simulate/trade` command 均符合目前 CLI |
| 前端 API 呼叫對後端 route | 通過；DevOps Dashboard 使用的 API path 均有後端 route |
| 環境變數一致性 | 通過；已修正 CryptoPanic 舊 key 名稱，統一使用 `CRYPTOPANIC_API_TOKEN` |
| Docker compose 結構 | 通過；`docker compose config --quiet` 無錯誤 |
| 前端 production build | 通過；`frontend/devops-d npm run build` 成功 |

### 尚未完成的 image 層驗證

目前 running Docker image 是舊版，已觀察到舊 API image 尚未包含目前 source 的 `/api/v1/backtest/strategy-run` route。下一步應在完成上述 source 檢查後，一次性重建 image，然後重跑：

1. `docker compose build api frontend`
2. `docker compose up -d api frontend`
3. `docker compose run --rm status`
4. `docker compose run --rm backtest`
5. `docker compose run --rm simulate`
6. Docker API `/api/v1/status`、`/api/v1/backtest/strategy-run`
7. Docker frontend `http://127.0.0.1:3000`

Live trading 仍不納入自動驗證；只保留 testnet 啟停與人工二次確認流程。
