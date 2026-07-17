# BioNeuronAI 手冊盤點與實際操作驗收計畫

> **套件版本**：v2.1（`pyproject.toml`）  
> **建立日期**：2026-05-02  
> **更新日期**：2026-07-11  
> **方向權威**：[`../CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)  
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)  
> **目的**：用「使用者手冊能否帶著操作者完成**真實操作**」作為可用性判斷。  
> **正式驗收**使用 CLI、虛擬帳戶／Paper、歷史回測、必要時 API／Dashboard／Docker。  
> **不使用** `tests/`、pytest、臨時 mock 腳本作為功能完成或「流程跑通」的依據（它們無法反映真實時機）。

---

## 目錄

0. [與現行方向對齊](#0-與現行方向對齊)
1. [判斷原則](#1-判斷原則)
2. [目前已有的主要使用手冊](#2-目前已有的主要使用手冊)
3. [目前缺少或應補強的手冊](#3-目前缺少或應補強的手冊)
4. [建議驗收順序](#4-建議驗收順序)
   - [Level 0](#level-0不用金鑰不用-docker)
   - [Level 1](#level-1本地-api-dashboard)
   - [Level 2](#level-2需要外部網路或新聞-api)
   - [Level 2.5 預設 AI 自主 paper（本階段核心）](#level-25預設-ai-自主-paper-流程本階段核心)
   - [Level 3 Paper-live 與 Testnet](#level-3paper-live-與-testnet主線-a)
   - [Level 4 Live 前](#level-4live-前驗收)
5. [目前已完成的手冊式實際印證紀錄](#5-目前已完成的手冊式實際印證紀錄)
6. [下一步](#6-下一步)

---

## 0. 與現行方向對齊

| 議題 | 本計畫立場（2026-07-11） |
|------|--------------------------|
| 本階段主目標 | **工程自主**：預設流程跑通 + 記帳正確 |
| 預設 AI 自主入口 | `python main.py autonomous`（paper + cycles） |
| 日常驗證 | 幣安虛擬帳戶／本機 Paper，真實時序 |
| 長期驗證 | **先下載歷史**，再 backtest／readiness-gate |
| 單元測試 | **非正式驗收** |
| 未訓練模型 | 可驗流程；不可用 PnL 證明智能 |
| 多帳戶／API 認證 | **不列入**本階段通過條件 |
| 訓練改善 | 流程通且記帳穩後；終局邊跑邊學 |

完整論述：[`CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)、[`TESTING_AND_VALIDATION_GUIDE.md`](../TESTING_AND_VALIDATION_GUIDE.md)。

---

## 1. 判斷原則

一項功能只有在同時滿足以下條件時，才視為「手冊可用」：

1. 有對應手冊或章節。  
2. 手冊列出的命令、URL、環境變數與目前程式碼一致。  
3. 使用者可以照手冊從啟動到完成操作。  
4. 操作完成後有可觀察輸出：CLI 結果、API JSON、Dashboard、runtime、ledger、帳戶狀態或報告檔。  
5. 若需要 API key、Docker、GPU 或實盤資金，手冊必須標示前置與安全限制。  
6. **不建立或執行 `tests/` 測試檔作為驗收**；只使用 CLI／API／Dashboard／Docker／真實回測的直接操作結果。  
7. 區分 **工程自主**（會跑、帳對）與 **智能自主**（模型品質）；後者不得用 untrained 短線盈虧蒙混。  
8. 抽查「正確證據」：決策→進場→出場是否對得上（見 CURRENT_DIRECTION §3.3）。

---

## 2. 目前已有的主要使用手冊

| 類別 | 文件 | 目前用途 | 初步狀態 |
|---|---|---|---|
| 總入口 | `docs/manuals/00_MASTER_MANUAL.md` | 專案總覽與閱讀順序 | 可用，但偏導覽 |
| 開機開始 | `docs/manuals/02_STARTUP_AND_SHUTDOWN.md` | 本地 CLI、API + Dashboard、Docker 的開機與關機流程 | 新增，可用 |
| 快速開始 | `docs/manuals/03_QUICKSTART.md` | 安裝、`.env`、status、news、plan、pretrade、trade、chat | 可用，與 02 有少量重疊 |
| 日常操作 | `docs/manuals/04_CLI_OPERATION.md` | CLI 指令與標準 SOP | 可用，但部分操作需再用真實入口逐條核對 |
| API | `docs/manuals/05_API_USER_MANUAL.md` | FastAPI 端點、PowerShell 範例 | 初步與 route 清單一致，需逐端點實測 |
| 前端 | `docs/manuals/06_FRONTEND_DASHBOARD.md` | Operations Dashboard 面板操作 | 已補 Operations / Validation / Config / Dev Tools 分區與本地 5173-5180 差異 |
| Docker | `docs/manuals/07_DOCKER_DEPLOYMENT.md` | Compose 服務、volume、healthcheck | 可用，需完整 docker compose 實測 |
| 回測 | `docs/manuals/08_BACKTEST_SYSTEM.md` | backtest / simulate / BacktestEngine | 可用，需補可快速完成的短區間驗收指令 |
| Backtest 子系統 | `backtest/docs/USER_MANUAL.md` | Backtest 子系統操作 | 需與根目錄回測手冊合併或交叉索引 |
| 分析 | `docs/manuals/09_ANALYSIS_MODULE.md` | news / plan / pretrade | 可用，需核對 API request schema 是否完全一致 |
| 策略 | `docs/manuals/10_STRATEGY_MODULE.md` | strategy-backtest / strategy-run | 可用，需實測短區間 strategy-backtest |
| 風控 | `docs/manuals/11_RISK_MANAGEMENT.md` | 風險等級、倉位計算、pretrade 整合 | 可用，但偏概念，缺少可執行驗收步驟 |
| RAG | `docs/RAG_TECHNICAL_MANUAL.md` | RAG 技術架構 | 技術手冊，不是使用者操作手冊 |
| NLP 訓練 | `docs/manuals/12_NLP_TRAINING.md` | TinyLLM / unified trainer | 可用，但屬訓練手冊，不是日常操作 |
| 雲端訓練 | `docs/manuals/13_CLOUD_TRAINING_RUNBOOK.md` | GPU 訓練真實資料短流程、resume、artifact 回收 | 可用，需與目前 signal tensor 狀態同步 |
| 架構 | `docs/ARCHITECTURE_OVERVIEW.md` | 模組與資料流 | 可用，非操作手冊 |
| 交接 | `docs/PROJECT_HANDOVER_MAP.md` | 接手開發路徑 | 可用，非一般使用者手冊 |

---

## 3. 目前缺少或應補強的手冊

| 優先級 | 建議新增/補強文件 | 原因 |
|---|---|---|
| P0 | `docs/manuals/14_TESTNET_AND_LIVE_TRADING.md` | 已建立；需持續同步 API / UI 的 `monitor_only`、`testnet_auto`、`live_auto` 與 live guard。 |
| P0 | `docs/manuals/20_UI_END_TO_END_OPERATION.md` | 已建立；下一步需以 Playwright 或人工點擊完成 UI 端到端驗收。 |
| P1 | `docs/manuals/15_DATA_ACQUISITION.md` | 已建立；需持續同步 catalog / inspect / backtest-data 的實際欄位。 |
| P1 | `docs/manuals/16_RUNTIME_ARTIFACTS.md` | 已建立；需持續同步 runtime、logs、output、rl_models 的產物位置。 |
| P1 | `docs/manuals/17_ENVIRONMENT_VARIABLES.md` | 已建立；已補 `ALLOW_LIVE_TRADING`，仍需和 `.env.example` 定期核對。 |
| P2 | `docs/manuals/18_OPERATION_TROUBLESHOOTING.md` | 已建立；需持續補 API、交易卡住、外部服務降級的處理流程。 |
| P2 | 待編號：Meta Learner 使用手冊 | 尚未建立；v2.2 已有 `meta_learner` 初版與模型權重，目前主要記在開發日誌與 roadmap，不夠像使用手冊。 |
| P2 | 待建立：Release readiness checklist | 每次要標記版本前，按手冊驗收結果確認是否可發布。 |

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
| API | `GET /api/v1/status` | `ready=true`、`blocking=[]` |
| API | `GET /api/v1/backtest/catalog` | 可列出 dataset |
| Frontend | `npm run dev` | Dashboard 可開啟並打到 API；Docker frontend 留到最後重建 |
| Frontend | Status / Backtest / API Playground | 前端操作能得到後端回應 |
| UI End-to-End | `20_UI_END_TO_END_OPERATION.md` | 使用者可從 UI 完成 status、catalog、backtest、news、pretrade、chat、testnet start/stop、history 檢查 |

### Level 2：需要外部網路或新聞 API

| 手冊 | 實際入口 | 成功標準 |
|---|---|---|
| Analysis | `python main.py news --symbol BTCUSDT` | 能完成新聞分析或明確降級 |
| Analysis | `python main.py plan --symbol BTCUSDT` | 能產出計畫或明確列出外部資料失敗原因 |
| Analysis | `python main.py pretrade --symbol BTCUSDT --action long` | 能產出 PROCEED / CAUTION / REJECT 與理由 |
| CLI / 04 | `python main.py autonomous --mode advisor --symbol BTCUSDT` | 終端有 `final_action`；`decision_ledger.jsonl` 追加一筆 |

### Level 2.5：預設 AI 自主 paper 流程（本階段核心）

> **這是 2026-07-11 方向下的主驗收層。** 通過本層 = 工程自主大致成立；**不要求**模型已訓練或績效漂亮。

| 手冊 | 實際入口 | 成功標準 |
|---|---|---|
| 04 / 14 / CURRENT_DIRECTION | `python main.py autonomous --mode paper_auto --execute-paper --cycles 3 --symbol BTCUSDT --paper-balance 10000` | 多輪可完成或合理 STOP；ledger 有多輪 record |
| 04 / 16 | 同上 | 若允許執行：有 paper_execution 或明確 `skipped=existing_position` |
| 16 | 抽查 ledger + 虛擬帳戶狀態 | 決策／進場／（若有）出場結果可對帳；餘額變化說得通 |
| 04 | 可選 `--max-position-hold-cycles` | 卡單行為可觀察或文件化未觸發原因 |
| CURRENT_DIRECTION | 觀察模型狀態 | `trained: false` 時不將盈虧解釋為 AI 智能達標 |
| — | **禁止** | 用 `pytest tests` 代替本表任何一列 |

補充：

- Paper 執行應走 **共用 TradingEngine**（非「永遠獨立第二帳戶」的舊描述）。  
- 平倉後應能觀察引擎學習鏈與／或 ledger outcome（shared callback）。  
- 學習寫入可先「只記錄」再開滿；見 TESTING_AND_VALIDATION_GUIDE §7。

### Level 3：Paper-live 與 Testnet（主線 A）

| 手冊 | 實際入口 | 成功標準 |
|---|---|---|
| Testnet / Live | `python main.py trade --symbol BTCUSDT --paper-live --paper-balance 10000` | paper log 目錄、可 Ctrl+C 停止；平倉後可查 `memory/`（選驗） |
| Testnet / Live | `python main.py trade --symbol BTCUSDT --testnet` | 能啟動監控、讀取價格、可用 Ctrl+C 停止 |
| API | `POST /api/v1/trade/start` / `GET /api/v1/trade/status` / `POST /api/v1/trade/stop` | API 可啟停交易 task，可觀察 `running`、`mode`、`engine.auto_trade`，不殘留背景程序 |
| Dashboard | TradeControlPanel | UI 可選 `Monitor only` / `Testnet auto`，可啟停並看到狀態 |

### Level 4：Live 前驗收

| 手冊 | 實際入口 | 成功標準 |
|---|---|---|
| Live Trading | `trade --live` 或 API / UI `live_auto` 前檢查 | CLI 必須人工二次確認；API / UI 必須 `ALLOW_LIVE_TRADING=1` + `confirm_live=I_UNDERSTAND_LIVE_RISK`；金鑰、餘額、槓桿、最大倉位限制需人工確認 |
| Backtest / Strategy | 長區間 OOS / walk-forward | 有固定資料區間、命令、結果檔與績效摘要 |
| Risk | pretrade + risk settings | 最大單筆風險、每日風險、最大回撤限制都可查證 |

---

## 5. 目前已完成的手冊式實際印證紀錄

以下是 2026-05-02 已用實際入口完成的操作，不屬於臨時測試腳本：

| 操作 | 結果 |
|---|---|
| `python main.py --help` | 成功列出 CLI 命令 |
| `python main.py status` | 成功，核心模組顯示 OK，版本 v2.1 |
| `python main.py backtest-data --symbol BTCUSDT --interval 1h` | 成功，找到 BTCUSDT 1h，2020-01-01 到 2023-12-31，共 1461 個 zip |
| 短區間 `simulate` | 成功，產生 runtime |
| 短區間 `backtest` | 成功，實際產生開平倉與回測統計 |
| `frontend/devops-d npm run build` | 成功，Vite production build 完成 |
| 本地 API 啟動 + `GET /api/v1/status` | 成功，`ready=true`、`blocking=[]` |
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
| 本地 API | 啟動 uvicorn 後 `GET /api/v1/status` | 通過，`ready=true`、`blocking=[]` |
| 本地 API | `GET /api/v1/backtest/catalog` | 通過，`success=true`，dataset_count=1 |
| 本地 Dashboard | `npm run dev -- --host 127.0.0.1 --port 5173` | 通過，HTTP 200 |
| Docker | `docker compose config --services` | 通過，列出 status/api/backtest/frontend/news/plan/pretrade/simulate |
| Docker | `docker compose ps` | 通過，`bioneuron-api` 與 `bioneuron-frontend` 已 running 且 healthy |
| Docker API | `GET http://127.0.0.1:8000/api/v1/status` | 2026-05-14 曾通過；本輪 Docker 留到最後重建 |
| Docker Frontend | `GET http://127.0.0.1:3000` | 通過，HTTP 200 |
| 關機檢查 | 查詢本地 uvicorn / Vite / trade 殘留程序 | 通過，未發現本輪啟動的殘留程序 |

### 2026-05-04 AI 自動交易與 UI 文件清理紀錄

本次清理目的：移除手冊中舊的 `symbol/testnet` 啟動範例與「測試網監控等同自動交易」的錯誤語意，將文件同步到目前 API / UI 的三種交易模式。

| 文件 | 修改重點 |
|---|---|
| `02_STARTUP_AND_SHUTDOWN.md` | API 啟動 body 改為包含 `mode`、`auto_trade`、`load_ai_model`、`model_name`、`warmup_model`，並補 `trade/status` 查詢 |
| `03_QUICKSTART.md` | 將 CLI `trade --testnet` 說明改為測試網監控；自動交易改指向 UI / API 的 `testnet_auto` |
| `04_CLI_OPERATION.md` | 將 `trade` 語意改為監控 / 交易入口，避免把 CLI testnet 監控寫成已啟用自動送單 |
| `05_API_USER_MANUAL.md` | 更新快速範例，加入 `/api/v1/trade/status` 與新交易啟動欄位 |
| `06_FRONTEND_DASHBOARD.md` | Daily SOP 改為 `Monitor only` / `Testnet auto`，並要求 Refresh Status 後再停止 |
| `14_TESTNET_AND_LIVE_TRADING.md` | 已同步 API / UI live guard：`ALLOW_LIVE_TRADING=1` + `confirm_live=I_UNDERSTAND_LIVE_RISK` |
| `17_ENVIRONMENT_VARIABLES.md` | 新增 `ALLOW_LIVE_TRADING` 說明，並補 live 前確認條件 |
| `20_UI_END_TO_END_OPERATION.md` | 已把 Trade Control 流程改為 mode/status/stop 的端到端驗收 |

文件層完成狀態：AI 自動交易的操作文件已對齊目前第一階段功能；第一輪雲端訓練產物已接回 runtime，但仍未把模型成效寫成已驗證，因為權重品質還需要固定資料區間回測、OOS / walk-forward、paper-live 與 testnet 觀察支撐。

### 2026-05-04 實際入口操作優先驗證紀錄

本輪原則：不使用 `tests/` 測試檔；改用使用者會真正操作的 CLI / API / Dashboard 入口驗證。

| 實際入口 | 驗證內容 | 結果 |
|---|---|---|
| CLI | `python main.py status` | 通過；TradingEngine / BinanceFutures / NewsAnalyzer / SOPSystem / PlanController / PreTradeCheck / BacktestEngine 均為 `[OK]` |
| API | `GET /api/v1/status` | 通過；`ready=true`、`blocking=[]`、version `2.1` |
| API | `GET /api/v1/trade/status` | 通過；未啟動時 `running=false`、`mode=stopped` |
| API | `POST /api/v1/trade/start`，`mode=monitor_only`、`testnet=true` | 通過；回傳「交易監控已啟動 [測試網] BTCUSDT」，`running=true`、`auto_trade=false` |
| API | `POST /api/v1/trade/stop` | 通過；停止後 `running=false`、`mode=stopped` |
| Dashboard | `GET http://127.0.0.1:5173` | 通過；HTTP 200，代表本地 Dashboard dev server 可開啟 |
| Frontend | `npm run build` / `npm run lint` | 通過；build 成功；lint exit code 0，保留 7 個既有 Fast Refresh warnings |
---

## 6. 下一步

### 2026-05-02 後續使用者操作手冊實際驗證

以下操作均使用正式入口執行，未使用 `tests/`、未執行臨時測試腳本、未建立測試檔。

| 手冊 | 實際入口 | 結果 |
|---|---|---|
| `03_QUICKSTART.md` | `status`、`news`、`plan`、`pretrade`、`chat` | 通過；`pretrade` 正常回傳 `REJECT` 風控結果，屬有效操作結果 |
| `04_CLI_OPERATION.md` | CLI help / status / data / simulate / backtest / news / plan / pretrade / chat | 通過；均可由目前 CLI 入口執行 |
| `05_API_USER_MANUAL.md` | 本地 API 臨時測試埠 `127.0.0.1:8001` 逐端點呼叫 | 通過；REST 端點與三個 WebSocket 端點均可連線並取得回應。正式手冊仍以 `127.0.0.1:8000` / `localhost:8000` 為預設 |
| `06_FRONTEND_DASHBOARD.md` | `npm run build`、本地 Vite HTTP 200、Docker frontend HTTP 200 | 通過；production build 成功 |
| `07_DOCKER_DEPLOYMENT.md` | `docker compose config --quiet`、`docker compose run --rm status`、`docker compose run --rm backtest` | 部分通過；source compose 已修正並通過 config，舊 image 的 `backtest` 可執行；`simulate` 需等 image 重建後重跑 |
| `08_BACKTEST_SYSTEM.md` | 短區間 `simulate` / `backtest`、API run、runtime 查詢 | 通過；產生實際 runtime |
| `09_ANALYSIS_MODULE.md` | `news`、`plan`、`pretrade`、API `news` / `pretrade` | 通過；外部新聞可正常降級或回傳分析結果 |
| `10_STRATEGY_MODULE.md` | `strategy-backtest` 短區間、API `/api/v1/backtest/strategy-run` | 通過；10 個策略模板均可執行並產生 runtime |
| `11_RISK_MANAGEMENT.md` | `pretrade` 風控檢查與 Dashboard risk snapshot | 通過；風控結果可觀察，未繞過 REJECT |
| `14_TESTNET_AND_LIVE_TRADING.md` | API `trade/start` + `trade/status` + `trade/stop`，`mode=monitor_only` / `testnet=true` | 通過；可啟動、查詢並停止測試網監控。Live 未執行，依手冊安全限制保留人工確認 |
| `15_DATA_ACQUISITION.md` | `backtest-data`、API catalog / inspect | 通過；BTCUSDT 1h 本地資料可列出並載入 |
| `16_RUNTIME_ARTIFACTS.md` | `backtest-runs`、runtime 目錄檢查 | 通過；可列出最新 runs，runtime 內含 summary/status/account/result/orders |
| `17_ENVIRONMENT_VARIABLES.md` | `.env` 存在、`.env` 被 ignore、key 名稱檢查、`.env.example` 對齊 compose | 通過；未輸出任何 secret 值 |
| `18_OPERATION_TROUBLESHOOTING.md` | CLI/API/Docker 狀態與殘留程序檢查 | 通過；本輪啟動的本地 API/Vite/trade 未殘留 |
| `19_DASHBOARD_TROUBLESHOOTING.md` | API status、frontend HTTP、WebSocket 實際連線 | 通過；REST 與 WebSocket 入口可用 |
| `20_UI_END_TO_END_OPERATION.md` | 文件已建立；API/HTTP/build 實際入口已驗證 | 部分通過；仍需 Playwright 或人工完成瀏覽器點擊驗收 |

### 2026-05-14 Docker image 重建與複驗

| 檢查項目 | 結果 |
|---|---|
| Docker image 重建 | 通過；`api` / `frontend` image 已重建 |
| Docker API / CLI image 一致性 | 通過；`status/backtest/simulate` 共用 `bioneuronai-api:latest` runtime image |
| 歷史 K 線掛載 | 通過；Compose 以 `./backtest:/app/backtest` 掛載本機資料，Docker API catalog 可讀 |
| Python 語法解析 | 歷史紀錄：Docker Python 3.11 runtime 曾可執行 CLI。本輪已改以本機 Python 3.13 + PyTorch CPU 2.8.0 作為主要 runtime，Docker 最後重建 |
| Docker command 對 CLI parser | 通過；`status/news/pretrade/plan/backtest/simulate/trade` command 均符合目前 CLI |
| 前端 API 呼叫對後端 route | 通過；Operations Dashboard 使用的 API path 均有後端 route |
| 環境變數一致性 | 通過；新聞正式來源不再需要 CryptoPanic token |
| Docker compose 結構 | 通過；`docker compose config --quiet` 無錯誤 |
| 前端 production build | 通過；`frontend/devops-d npm run build` 成功 |

### 已完成的 image 層驗證

已完成並通過：

1. `docker compose build api frontend`
2. `docker compose up -d api frontend`
3. `docker compose run --rm status`
4. `docker compose run --rm backtest`

### 2026-05-19 本機 Python 3.13 runtime 與 paper-live 複驗

本輪依使用者決策，先不處理 Docker；改以本機全域 Python 3.13 + PyTorch CPU 2.8.0 作為主要 runtime，Docker image 等自然語言、交易判斷與 API/UI 流程收斂後最後重建。

| 實際入口 | 驗證內容 | 結果 |
|---|---|---|
| API | `GET /api/v1/status` | 通過；`ready=true`、`blocking=[]`，Python 3.13.9、PyTorch 2.8.0+cpu、現役交易模型與 TinyLLM 權重均可讀 |
| Frontend | `frontend/devops-d npm run build` | 通過；Vite production build 成功 |
| Frontend | 本機 Vite `http://127.0.0.1:5176` | 通過；HTTP 200，CORS preflight 允許 `http://127.0.0.1:5176` |
| Chat API | `POST /api/v1/chat` 詢問交易狀態 | 通過；觸發 `trade_status` tool，回傳實際交易 task 狀態 |
| Chat API | `POST /api/v1/chat` 分析 BTCUSDT | 通過；觸發 `analyze_market` tool，使用即時價格、24h 漲跌、RSI、EMA 與 K 線數 |
| Chat API | 以中文要求啟動 BTCUSDT `paper_live` | 通過；觸發 `start_paper_live` tool，啟動後 `ai_model_loaded=true`、`paper_trading=true`，隨後已停止 |
| Trade API | `POST /api/v1/trade/start`，`mode=paper_live` | 通過；啟動虛擬實盤，`engine.ai_model_loaded=true`、`engine.paper_trading=true` |
| Trade API | `POST /api/v1/trade/stop` | 通過；停止後 `running=false`、`mode=stopped` |

本輪同時修復 `TradingEngine.__init__` 中 `InferenceEngine` 的區域變數遮蔽問題；該問題會讓 paper-live / AI model 啟動路徑在建立 inference engine 前失敗。
5. `docker compose run --rm simulate`
6. Docker API `/api/v1/status`、`/api/v1/backtest/catalog`
7. Docker frontend `http://127.0.0.1:3000`
8. Docker container 內 AI model load：`loaded=True`

Live trading 仍不納入自動驗證；只保留 testnet 啟停與人工二次確認流程。

### 2026-06-09 測試目錄移除後正式入口驗證

本輪已移除 `tests/` 目錄與測試工具設定；驗收改用正式 CLI 入口直接操作。

| 實際入口 | 結果 |
|---|---|
| `python main.py status` | 通過；TradingEngine / BinanceFutures / NewsAnalyzer / SOPSystem / PlanController / PreTradeCheck / BacktestEngine 均為 `[OK]` |
| `python main.py pretrade --symbol BTCUSDT --action long --output output/manual_pretrade_after_test_cleanup.json` | 通過；產生正式 pretrade 報告，因技術信號不足、新聞偏空與高風險而回傳 `REJECT` |
| `python main.py autonomous --mode advisor --symbol BTCUSDT --action BUY --max-pairs 1 --output output/manual_autonomous_after_test_cleanup.json` | 通過；產生 advisor 決策，最終 `advise_only`，不執行訂單 |

觀察到的外部條件：

- 未建立正式 `.env` 時，Binance account / leverage bracket 簽名端點回傳 401；系統降級使用本機虛擬餘額。
- 新聞輪次必須同時取得 CoinDesk RSS 與 Google News RSS；任一來源無法取得或解析時，該輪明確失敗，不使用部分結果降級。
- 交易結果為拒絕/建議觀望，符合無正式密鑰與風險偏高時的安全行為。
