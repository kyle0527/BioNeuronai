# BioNeuronAI UI 端到端操作手冊

> 版本：v2.1 正式主線 / v2.2 訓練後驗證期
> 更新日期：2026-05-19
> 主要入口：`frontend/devops-d/`  
> Dashboard：`http://localhost:3000`  
> API：`http://localhost:8000`

---

## 📑 目錄

- [1. 手冊定位](#1-手冊定位)
- [2. UI 與資料契約確認](#2-ui-與資料契約確認)
- [3. 啟動前檢查](#3-啟動前檢查)
- [4. 第一輪 UI 驗收流程](#4-第一輪-ui-驗收流程)
- [5. 每日 UI 操作 SOP](#5-每日-ui-操作-sop)
- [6. UI 直接操作的完善目標](#6-ui-直接操作的完善目標)
- [7. 關機流程](#7-關機流程)
- [8. 相關文件](#8-相關文件)

---

## 1. 手冊定位

本手冊只回答一件事：使用者如何從開啟系統開始，透過 UI 完成一輪可觀察、可停止、可追蹤的操作。

`06_FRONTEND_DASHBOARD.md` 是面板功能參考；本文件是端到端操作流程。若兩份文件有重疊，以本文件作為「從開始到結束怎麼操作」的入口，以 `06` 作為欄位與面板細節參考。

目前正式 UI 主線是 `frontend/devops-d/`。`frontend/trading/` 與 `frontend/admin-da/` 原始碼保留，但不是第一階段操作主線。

---

## 2. UI 與資料契約確認

UI / API 相關資料定義不是缺少 `src/schemas` 內容。現況是：

| 類別 | 定義位置 | 說明 |
|---|---|---|
| REST request / response | `src/schemas/api.py` | `NewsRequest`、`PreTradeRequest`、`BacktestRequest`、`TradeStartRequest`、`ChatRequest` 等 |
| 訓練與模型操作 | `src/schemas/api.py` | `TrainingStartRequest`、`ModelPromoteRequest` |
| Dashboard / WebSocket 資料 | `src/schemas/api.py` | `DashboardDataResponse`、`WsRiskData`、`WsPosition`、`WsTradeExecution` 等 |
| 訂單與持倉 | `src/schemas/orders.py`、`src/schemas/positions.py` | Binance order / position 契約 |
| 風控 | `src/schemas/risk.py`、`src/schemas/portfolio.py` | 風險參數、倉位、投資組合風險 |
| RAG / pretrade | `src/schemas/rag.py` | RAG 風險與交易前檢查契約 |

因此目前的主要缺口不是「沒有 schema」，而是 UI 操作文件需要把 schema 對應到實際畫面、按鈕與完成標準。

---

## 3. 啟動前檢查

### Docker 路線

在專案根目錄執行：

```powershell
docker compose up api frontend
```

等待兩個服務健康：

```powershell
docker compose ps
```

成功標準：

| 服務 | 成功狀態 |
|---|---|
| `bioneuron-api` | `healthy` |
| `bioneuron-frontend` | `healthy` |

開啟：

```text
http://localhost:3000
```

### 本地開發路線

先啟動 API：

```powershell
$env:PYTHONPATH="src"
python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
```

另一個終端機啟動 UI：

```powershell
cd frontend/devops-d
npm install
npm run dev
```

開啟 Vite 顯示的網址，通常是 `5173`；若該 port 已被占用，可能是 `5176` 等下一個可用 port：

```text
http://localhost:5173
http://127.0.0.1:5176
```

---

## 4. 第一輪 UI 驗收流程

這一輪不需要實盤資金，目標是確認 UI 能直接操作後端。

### 步驟 1：確認 API 連線

1. 開啟 Dashboard。
2. 看右上角 API badge，應顯示目前 API URL。
3. 進入 `Operations` tab。
4. 確認 `Live Market Chart` 載入 BTCUSDT 最新 K 線。
5. 等待 `Operations Overview` 載入，或按刷新。

成功標準：

| 項目 | 成功狀態 |
|---|---|
| API badge | 指向正確 API URL |
| Live Market Chart | 顯示最新 K 線；最後一根 candle 若未收盤，標示為 updating |
| Operations Overview | 顯示 API OK、runtime mode、execution target、model state |
| Status response | `ready=true`、`blocking=[]` |
| 模組狀態 | 主要模組顯示 available |

若顯示 `Failed to fetch`，先處理 API 未啟動、CORS 或 API URL 設定問題。排查見 [19_DASHBOARD_TROUBLESHOOTING.md](19_DASHBOARD_TROUBLESHOOTING.md)。

2026-05-19 本機 UI 複驗：`http://127.0.0.1:5176/` 回應 200，`/api/v1/status` 回傳 `ready=true`、`blocking=[]`；`Operations`、`Validation`、`Config`、`Dev Tools`、`Chat` 五個 tab 均未出現卡片重疊或水平撐版。`Trade Control` 的 JSON raw response、`News` response、`Request History` 大量紀錄與 `Chat` 長文字都已限制在各自容器內。

### 步驟 2：確認資料目錄

1. 切到 `Validation` tab，找到 `Data Catalog` 或 `Backtest` 的 catalog 功能。
2. Symbol 可填 `BTCUSDT`，Interval 可填 `1h`。
3. 執行掃描。

成功標準：

| 項目 | 成功狀態 |
|---|---|
| dataset | 至少看到 `BTCUSDT 1h` 或 `ETHUSDT 1h` |
| 日期範圍 | 能看到本地資料起訖日期 |
| ZIP 數量 | 大於 0 |

若無資料，先回 CLI 執行資料確認：

```powershell
python main.py backtest-data --json
```

目前 UI 不負責下載歷史資料；UI 只使用已存在於 `backtest/data/` 的資料。

### 步驟 3：執行短回測

1. 在 `Backtest` 面板填入：

| 欄位 | 建議值 |
|---|---|
| Symbol | `BTCUSDT` |
| Interval | `1h` |
| Start Date | `2020-01-01` |
| End Date | `2020-01-01` |
| Balance | `10000` |
| Warmup Bars | `1` |

2. 先執行 inspect 或 catalog 類操作，確認資料可讀。
3. 執行 backtest run。

成功標準：

| 項目 | 成功狀態 |
|---|---|
| status | `completed` |
| run_id | 有值 |
| run_dir | 指向 `backtest/runtime/<run_id>` |
| stats | 顯示 total_return / max_drawdown / trade_count 等欄位 |

短區間可能沒有交易，`trade_count=0` 不代表 UI 操作失敗。判斷重點是 `status=completed` 與 runtime 已產生。

### 步驟 4：執行新聞分析

1. 在 `News` 面板填入 `BTCUSDT`。
2. Max items 建議使用 `5` 到 `10`。
3. 執行分析。

成功標準：

| 項目 | 成功狀態 |
|---|---|
| API response | `success=true` 或明確降級訊息 |
| 結果區 | 顯示 sentiment / headline / count 類資訊 |
| Request History | 在 `Dev Tools` tab 出現 `/api/v1/news` 記錄 |

若新聞來源受免費額度限制，可能出現 0 篇或降級結果；只要 API 明確回傳狀態，不視為 UI 失敗。

### 步驟 5：執行 PreTrade

1. 在 `PreTrade` 面板填入：

| 欄位 | 建議值 |
|---|---|
| Symbol | `BTCUSDT` |
| Action | `long` 或 `short` |

2. 執行檢查。
3. 查看 overall status 與風險理由。

成功標準：

| 狀態 | 解讀 |
|---|---|
| `PROCEED` | 通過，仍需人工判斷 |
| `CAUTION` | 有警告，縮小倉位或觀望 |
| `REJECT` | 風控拒絕，不應進場 |

`REJECT` 是有效結果，不是錯誤。UI 必須把拒絕理由顯示清楚，使用者不可把 REJECT 當成需要繞過的障礙。

### 步驟 6：使用 Chat

1. 切到 `Chat` tab。
2. Symbol 可填 `BTCUSDT`。
3. Language 選 `zh` 或 `auto`。
4. 輸入問題，例如：

```text
請用風控角度解釋目前 BTCUSDT 是否適合追多
```

成功標準：

| 項目 | 成功狀態 |
|---|---|
| response | 有文字回應 |
| conversation_id | 有值 |
| confidence | 有值或明確為 null |
| Request History | 在 `Dev Tools` tab 出現 `/api/v1/chat` 記錄 |

若模型低信心而保守回答，屬安全行為。

### 步驟 7：Paper-live / 測試網交易監控啟停

> 本步驟優先做 paper-live 或 testnet。不要在本流程中啟用 live_auto。

1. 回到 `Operations` tab。
2. 在 `Trade Control` 面板將 `Mode` 選為 `Paper live` 或 `Monitor only`。
3. 若選 `Paper live`，確認 `Environment` 顯示 `Mainnet` 且面板說明為 virtual execution；若選 `Monitor only`，可維持 testnet。
4. Symbol 填 `BTCUSDT`。
5. 執行 `Start Trading`。
6. 執行 `Refresh Status`，確認回應中 `running=true` 或 `engine.is_monitoring=true`。
7. 執行 `Stop Trading`。
8. 再次執行 `Refresh Status`，確認 `running=false`。

若要測試 AI 自動交易流程但不使用真實資金，優先使用 `Paper live`。它使用主網行情但不送出 Binance 訂單；所有成交/持倉只寫入本地 paper ledger。`Load AI Model` 預設開啟，Model 使用 `my_100m_model`；目前權重品質不作為本輪 UI 驗收標準，重點是啟動流程可被 UI 操作且可停止。

成功標準：

| 項目 | 成功狀態 |
|---|---|
| start | API 回傳交易監控已啟動 |
| stop | API 回傳交易監控已停止 |
| 後端 | 不殘留交易 task |
| Request History | 在 `Dev Tools` tab 出現 `/api/v1/trade/start`、`/api/v1/trade/status` 與 `/api/v1/trade/stop` |

2026-05-19 已用本機 API 完成 `paper_live` 短流程複驗：啟動後 `running=true`、`engine.ai_model_loaded=true`、`engine.paper_trading=true`，停止後 `running=false`。同日也用中文 Chat 指令觸發 `start_paper_live` tool，確認自然語言可進入同一條交易控制路徑。此紀錄只證明 UI/API/Chat 所依賴的交易控制入口可用；長時間觀察與績效驗證仍需另跑 paper ledger 週期。

若要做 live 操作，必須改走 [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) 的人工確認流程。

### 步驟 8：訓練與模型交接

本步驟只確認 UI 能登記遠端訓練與查詢模型狀態，不要求本機啟動訓練。

1. 切到 `Validation` tab。
2. 在 `Training / Model` 面板將 Mode 選為 `External`。
3. Job 填入 `cloud-training`。
4. Cloud Job ID 可填遠端 job id；若只是登記後續再訓練規劃，可留空。
5. Signal Train / Signal Val 可填 `gs://` 路徑或本機 `data/processed/*.pt`。
6. Cloud Output 填入訓練 artifacts 目標。
7. 執行 `Start / Register`。
8. 執行 `Job Status`，確認 response 有 `job_id` 與 `status`。
9. 執行 `Model Status`，確認目前 active model / env 狀態可讀。

第一輪雲端訓練產物已接回 runtime。若後續再訓練產生新的 `.pth`，可在 Model Path 填入產物位置並執行 `Promote`。模型品質與交易成效不在本步驟判定；這裡只驗證 UI 能完成訓練產物交接操作。

成功標準：

| 項目 | 成功狀態 |
|---|---|
| register | API 回傳 `success=true` 與 `job_id` |
| status | 可用 `job_id` 查回作業狀態；遠端登記模式為 `registered` |
| model status | 回傳 active model / env / trade engine 狀態 |
| promote | 有實際模型檔時可登記到 `config/active_model.json` |

### 步驟 9：檢查 Request History

1. 切到 `Dev Tools` tab。
2. 在 `Request History` 面板檢查本輪請求。
3. 確認本輪操作至少出現：

| Endpoint | 來源 |
|---|---|
| `/api/v1/status` | Status |
| `/api/v1/market/klines` | Live Market Chart |
| `/api/v1/data/catalog` 或 `/api/v1/backtest/catalog` | Data / Backtest |
| `/api/v1/backtest/run` | Backtest |
| `/api/v1/news` | News |
| `/api/v1/pretrade` | PreTrade |
| `/api/v1/chat` | Chat |
| `/api/v1/trade/start` | Trade Control |
| `/api/v1/trade/status` | Trade Control |
| `/api/v1/trade/stop` | Trade Control |
| `/api/v1/training/start` | Training / Model |
| `/api/v1/model/status` | Training / Model |

成功標準是每筆操作都有時間、方法、endpoint、狀態與 duration。這是 UI 操作可追蹤性的最低要求。

2026-05-19 已修正 `Request History` 在累積大量紀錄時把卡片撐到異常高度的問題；左側紀錄列表與右側細節區會在 Dev Tools 面板內部捲動。

---

## 5. 每日 UI 操作 SOP

日常使用建議順序：

```text
1. 開啟 Dashboard
2. Operations：確認 Live Market Chart 正在更新、API OK、execution target、model loaded
3. Validation / Data Catalog：確認資料可讀
4. News：讀取市場事件與情緒
5. PreTrade：執行 long / short 檢查
6. Backtest：必要時跑短區間或指定區間驗證
7. Chat：詢問風控或策略解釋
8. Trade Control：優先用 paper-live 或 testnet；live_auto 只走專門 live 流程
9. Training / Model：後續再訓練作業登記或模型狀態確認
10. Dev Tools / Request History：確認本輪操作都有記錄
11. 停止交易監控並關閉服務
```

完成標準：

| 階段 | 可接受結果 |
|---|---|
| 系統狀態 | `ready=true`、`blocking=[]`；若失敗，依 `blocking` 修正必要項目 |
| 新聞 | 有結果或明確降級 |
| PreTrade | 得到 `PROCEED` / `CAUTION` / `REJECT` |
| 回測 | 產生 run_id 與 runtime |
| 交易監控 | testnet 可 start/stop |
| 訓練交接 | 可登記遠端 job，模型狀態可讀 |
| 歷史追蹤 | Request History 可追蹤完整流程 |

---

## 6. UI 直接操作的完善目標

接下來 UI 方向應優先補齊以下項目：

| 優先級 | 目標 | 原因 |
|---|---|---|
| P0 | 讓 Dashboard 每個核心操作都有明確 loading / success / error 狀態 | 已具備基礎狀態；後續仍可針對個別操作加強成功摘要 |
| P0 | Backtest 結果直接連到 runtime run detail | 使用者不應回終端機找 run_id |
| P0 | Trade Control 加強 live guard | 已補：UI 需要 `Live auto` + confirm 字串，後端還需 `ALLOW_LIVE_TRADING=1` |
| P0 | Training / Model 補齊遠端訓練登記、狀態查詢與 promote | 已補第一版；仍需雲端平台 job 狀態自動同步 |
| P1 | Data Catalog 顯示「如何取得資料」與目前可用日期 | 避免使用者用不存在的日期回測 |
| P1 | PreTrade 顯示 REJECT 的硬性原因與下一步 | 讓風控拒絕變成可理解結果 |
| P1 | Request History 支援匯出或複製本輪操作摘要 | JSON/CSV 匯出已可用；大量紀錄容器高度已修正，後續可補「本輪摘要」格式 |
| P2 | 把 API Playground 常用操作做成預設模板 | 降低手動填 JSON 的錯誤率 |

---

## 7. 關機流程

若使用 Docker：

```powershell
docker compose down
```

若使用本地開發：

1. 在 UI 先停止 Trade Control。
2. 停止 Vite 終端機。
3. 停止 uvicorn 終端機。

關機後可檢查：

```powershell
docker compose ps
```

成功標準是沒有仍在運行的交易監控服務。若懷疑仍有背景程序，先看 [18_OPERATION_TROUBLESHOOTING.md](18_OPERATION_TROUBLESHOOTING.md)。

---

## 8. 相關文件

| 文件 | 用途 |
|---|---|
| [06_FRONTEND_DASHBOARD.md](06_FRONTEND_DASHBOARD.md) | Dashboard 面板功能參考 |
| [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md) | REST API / WebSocket 參考 |
| [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) | testnet / live 安全操作 |
| [19_DASHBOARD_TROUBLESHOOTING.md](19_DASHBOARD_TROUBLESHOOTING.md) | Dashboard 連線與 UI 排查 |
| [17_ENVIRONMENT_VARIABLES.md](17_ENVIRONMENT_VARIABLES.md) | API URL、CORS、交易金鑰與環境變數 |
