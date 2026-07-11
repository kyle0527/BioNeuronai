# BioNeuronai Operations Dashboard 操作手冊

> **套件版本**：v2.1（`pyproject.toml`）
> **更新日期**：2026-06-15
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)
> **存取網址**：Docker `http://localhost:3000`；本地 Vite 依終端機輸出，常見 `http://localhost:5173` 或 `http://127.0.0.1:5176`
> **後端 API**：`http://localhost:8000`

---

## 📑 目錄

- [1. 概述](#1-概述)
- [2. 啟動 Dashboard](#2-啟動-dashboard)
  - [方式 A：Docker（後續重建）](#方式-adocker後續重建)
  - [方式 B：本地開發模式](#方式-b本地開發模式)
  - [驗證](#驗證)
- [3. 整體介面說明](#3-整體介面說明)
- [4. 各面板操作說明](#4-各面板操作說明)
  - [OperationsOverviewPanel — 操作總覽](#operationsoverviewpanel-操作總覽)
  - [MarketChartPanel — 即時 K 線](#marketchartpanel-即時-k-線)
  - [StatusPanel — 系統狀態](#statuspanel-系統狀態)
  - [NewsPanel — 新聞分析](#newspanel-新聞分析)
  - [PreTradePanel — 進場前驗核](#pretradepanel-進場前驗核)
  - [BacktestPanel — 回測](#backtestpanel-回測)
  - [ChatPanel — AI 對話助理](#chatpanel-ai-對話助理)
  - [TradeControlPanel — 交易控制](#tradecontrolpanel-交易控制)
  - [TrainingPanel — 訓練與模型](#trainingpanel-訓練與模型)
  - [APIPlayground — API 測試台](#apiplayground-api-測試台)
  - [RequestHistoryPanel — 請求歷史](#requesthistorypanel-請求歷史)
  - [DataCatalogPanel — 資料目錄（備用）](#datacatalogpanel-資料目錄備用)
  - [RiskConfigPanel — 風控設定（備用）](#riskconfigpanel-風控設定備用)
- [5. 典型操作流程](#5-典型操作流程)
  - [每日盤前 SOP（日常使用）](#每日盤前-sop日常使用)
  - [策略研究 SOP（回測分析）](#策略研究-sop回測分析)
- [6. 常見問題](#6-常見問題)
- [7. 相關文件](#7-相關文件)

---

## 1. 概述

BioNeuronai Operations Dashboard 是一個 **React 19 + Vite 7** 前端應用。Docker 模式由 nginx 服務於 `port 3000`；本地開發模式由 Vite 提供，port 會依可用性落在 `5173-5180`。它提供：

- **Operations Overview**：API 健康、runtime mode、執行目標、模型狀態、paper-live 帳戶
- **Live Market Chart**：Binance Futures public K 線圖，顯示當下正在更新的 candle
- **新聞情緒分析** 視覺化
- **進場前驗核** 操作
- **回測執行** 與結果查看
- **AI 交易對話** 介面
- **交易控制**（啟動/停止監控）
- **訓練與模型操作**（後續再訓練登記、查狀態、promote 模型；第一輪雲端訓練已接回 runtime）
- **API 測試台**（直接呼叫所有端點）
- **請求歷史紀錄**
- **資料目錄**（備用資料檢視）
- **風控設定**（備用設定入口）

所有操作都透過 API 伺服器（`localhost:8000`）執行，Dashboard 本身不直接呼叫 Binance 或任何交易所。

### 1.1 UI 與雙執行主線

| 功能 | Dashboard | 備註 |
|------|-----------|------|
| 主線 A：`trade` 監控 | ✅ Trade Control → `/api/v1/trade/*` | paper-live / testnet / live |
| 主線 B：`autonomous` | ❌ | 僅 CLI：`python main.py autonomous ...` |
| Replay 回測 | ✅ Backtest 面板 | 非即時交易主線 |
| `plan` | ❌ | 僅 CLI |

若目標是「從打開 UI 到完成一輪操作並關機」，請先看 [20_UI_END_TO_END_OPERATION.md](20_UI_END_TO_END_OPERATION.md)。本文件為各面板功能參考。

---

## 2. 啟動 Dashboard

### 方式 A：Docker（後續重建）

```bash
# 同時啟動 API + Dashboard
docker compose up api frontend
```

本輪先以本地 Vite + 本地 API 驗證。Docker frontend/API 會在本機功能收斂後最後重建；重建完成後再使用此路線。啟動後約 30 秒，兩個容器都 `healthy`，瀏覽器開啟：
- Dashboard：`http://localhost:3000`
- API 文件：`http://localhost:8000/docs`

### 方式 B：本地開發模式

```bash
cd frontend/devops-d
npm install
npm run dev
```

開發伺服器通常啟動於 `http://localhost:5173`；若該 port 被占用，Vite 會改用下一個可用 port，例如 `http://127.0.0.1:5176`。

### 驗證

進入前端網址後，頁面應顯示 `BioNeuronAI Operations`，第一個 tab 為 `Operations`，並在 `Operations Overview` 顯示 API 健康、runtime mode、執行目標與模型狀態。模組清單以 `GET /api/v1/status` 實際回應為準，常見項目包含 TradingEngine、BinanceFutures、NewsAnalyzer、SOPSystem、PreTradeCheck。

若看到 `Failed to fetch` 或網路錯誤，代表 API 伺服器（port 8000）尚未啟動。

2026-05-19 本機驗證狀態：`npm run build` 通過；`http://127.0.0.1:5176/` 回應 200；`GET /api/v1/status` 回報 `ready=true`、`blocking=[]`。同日已用瀏覽器檢查 `Operations`、`Validation`、`Config`、`Dev Tools`、`Chat` 五個 tab，未發現卡片重疊或水平撐版。

---

## 3. 整體介面說明

Dashboard 採用上方 tab + 分區面板佈局。

```
┌─────────────────────────────────────────────────────────┐
│  BioNeuronAI Operations                     API Badge   │
├──────────┬──────────────────────────────────────────────┤
│ Operations │ Validation │ Config │ Dev Tools │ Chat     │
├──────────┴──────────────────────────────────────────────┤
│  Operations：Overview / Trade / PreTrade / News          │
│  Validation：Backtest / Data Catalog / Training          │
│  Config：Status / Risk Config                            │
│  Dev Tools：API Playground / Request History             │
└──────────┴──────────────────────────────────────────────┘
```

點選上方 tab 可切換主區域；`Operations` 是日常監控和交易控制入口，`Dev Tools` 才是 API 調試與 request history。

---

## 4. 各面板操作說明

### OperationsOverviewPanel — 操作總覽

**功能：** 第一屏總覽目前 API、交易 runtime、執行層、模型與 paper-live 狀態。

**顯示重點：**

| 區塊 | 說明 |
|---|---|
| Runtime | `running`、`mode`、symbol、auto trade |
| Execution | 是否不下單、paper ledger、testnet 或 live mainnet |
| Model | active model、模型檔是否存在、目前 engine 是否已載入 |
| Health | API modules、blocking count、readiness issues、dashboard risk snapshot |
| Paper | `paper_live` 時顯示 balance、equity、positions、orders、log path |

此面板使用 `GET /api/v1/status`、`GET /api/v1/trade/status`、`GET /api/v1/model/status`、`GET /api/v1/dashboard`。若其中任一 API 失敗，先依 [19_DASHBOARD_TROUBLESHOOTING.md](19_DASHBOARD_TROUBLESHOOTING.md) 排查 API URL、CORS 與後端進程。

### MarketChartPanel — 即時 K 線

**功能：** 在 Operations 第一屏顯示 Binance Futures public K 線，用來確認目前行情是否持續更新，以及 AI / paper-live 操作時參考的是當下市場。

**資料來源：**

| 項目 | 說明 |
|---|---|
| API | `GET /api/v1/market/klines` |
| 預設 symbol | `BTCUSDT` |
| 預設週期 | `1m` |
| 更新方式 | 每 3 秒輪詢 |
| 最新 candle | 若 `closed=false`，代表這根 K 線仍在形成中，close / high / low / volume 會隨市場更新 |

**操作方式：**

1. 在 `Operations` tab 查看 `Live Market Chart`。
2. 可切換 symbol 與 interval。
3. `Refresh every 3s` 開啟時會自動更新最後一根 K 線。
4. 若想凍結畫面檢查，可關閉自動更新。

2026-05-19 實測：同一根 `1m` candle 在 4 秒內 `open_time` 不變、`closed=false`，volume 從 `12.321` 更新為 `14.961`，確認當下 K 線資料會刷新。

### StatusPanel — 系統狀態

**功能：** 顯示所有後端模組的可用狀態。

**操作步驟：**
1. 進入「系統狀態」面板
2. 點選「**刷新狀態**」按鈕，呼叫 `GET /api/v1/status`
3. 查看 5 個模組的狀態列表

**狀態指示燈說明：**

| 狀態 | 顏色 | 說明 |
|---|---|---|
| available: true | 🟢 綠色 | 模組正常 |
| available: false | 🔴 紅色 | 模組載入失敗，查看 error 訊息 |
| ready: true | ✅ | 必要 runtime、模型與設定都可用，系統可操作 |

**常見問題：**
- `TradingEngine` 或 readiness 不可用：優先依 `blocking` 顯示的項目處理；必要項目失敗時不應視為可操作。
- `BinanceFutures` 不可用：確認 `.env` 中 `BINANCE_API_KEY` 已設定且有效。

---

### NewsPanel — 新聞分析

**功能：** 抓取並分析加密貨幣新聞，輸出情緒評分與建議方向。

**操作步驟：**
1. 進入「新聞分析」面板
2. 在「交易對」欄位輸入目標（如 `BTCUSDT`）
3. 點選「**分析新聞**」按鈕
4. 等待 5~15 秒，查看結果

**結果說明：**

| 欄位 | 說明 |
|---|---|
| 情緒評分 (0~1) | 0 = 極度負向；1 = 極度正向 |
| 正面/負面/中性文章數 | 各情緒分類的文章計數 |
| 熱門關鍵字 | 本次新聞最常出現的詞彙 |
| 建議 | 🟢 看漲 / 🔴 看跌 / ⚪ 觀望 |
| 訊號有效期 | 此分析結果的建議有效時長（小時） |
| 最新標題 | 本次抓取的頭條列表 |

**注意：** CryptoPanic 免費方案每小時有請求限制，若顯示 `total_articles: 0`，請稍等片刻再試。

---

### PreTradePanel — 進場前驗核

**功能：** 在準備下單前，執行六點安全驗核。

**操作步驟：**
1. 進入「進場前驗核」面板
2. 選擇「交易對」（如 `BTCUSDT`）
3. 選擇「方向」：做多（long）或做空（short）
4. 點選「**執行驗核**」
5. 等待 10~30 秒，查看六項檢查結果

**驗核結果說明：**

| 項目 | 說明 |
|---|---|
| 技術訊號 | MACD、RSI、布林通道分析結果 |
| 基本面 | 新聞情緒 + RAG 知識庫檢索結果 |
| 風險計算 | 帳戶餘額、倉位大小、止損價格計算 |
| 訂單參數 | 建議進場價、止損、止盈設定 |
| 最終確認 | 綜合評分 |

**Overall Status 解讀：**

| 狀態 | 說明 | 建議行動 |
|---|---|---|
| `PROCEED` | 全部通過 ✅ | 可以進場 |
| `CAUTION` | 部分警告 ⚠️ | 謹慎進場，縮小倉位 |
| `REJECT` | 有硬性條件未通過 ❌ | **不應進場** |

**常見 REJECT 原因：**
- `account_balance: 0.0` — API 讀取不到帳戶餘額（read-only key 或未連接正式帳號）
- `RAG 檢索到重大負面事件` — 近期有黑天鵝事件觸發風險閥值

---

### BacktestPanel — 回測

**功能：** 使用歷史 K 線資料測試策略表現。

> **前置條件（重要）**：BacktestPanel 只能執行已下載至本地的歷史資料。若尚未下載，請先回到終端機執行：
> ```powershell
> python main.py backtest-data --symbol BTCUSDT --interval 1h
> ```
> 資料會存至 `backtest/data/`，之後 Dashboard 才能正常執行回測。

**操作步驟：**
1. 進入「回測」面板
2. 填入參數：
   - **交易對**：`BTCUSDT` / `ETHUSDT` / ...
   - **時間粒度**：`1h`（推薦）/ `15m` / `4h` / `1d`
   - **初始資金**：建議 10000 USDT
   - **開始日期 / 結束日期**：如 `2024-01-01` ~ `2024-03-31`
3. 點選「**執行回測**」
4. 等待（3 個月 1h 資料約需 15~30 秒）

**結果指標說明：**

| 指標 | 說明 | 參考標準 |
|---|---|---|
| `total_return` | 總報酬率 (%) | 正數為盈 |
| `win_rate` | 勝率 (%) | > 45% 為合理 |
| `sharpe_ratio` | 夏普比率 | > 1.0 較好；> 2.0 優秀 |
| `sortino_ratio` | 索提諾比率 | > 1.0 較好 |
| `max_drawdown` | 最大回撤 (%) | 越低越好，< 20% 可接受 |
| `profit_factor` | 獲利因子 | > 1.0 為盈利策略 |
| `total_trades` | 總交易次數 | 過少可能過度擬合 |

**查看歷史記錄：** 每次回測完成後，系統會自動儲存結果至 `backtest/runtime/`，可在面板底部查看最近 10 次執行記錄。

**Simulate vs Backtest 差異**（與 [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md) 一致）：

| 功能 | Simulate | Backtest |
|---|---|---|
| mock 下單 | 否（只統計信號） | 是（mock 撮合） |
| 策略管道 | `generate_trading_signal` 觀測 | 完整 AI 信號 + 模擬成交 |
| 用途 | 快速驗證資料與信號 | 正式策略績效評估 |

---

### ChatPanel — AI 對話助理

**功能：** 與內建 TinyLLM 模型以繁體中文或英文交流交易策略知識。

**操作步驟：**
1. 進入「AI 對話」面板
2. 在「交易對」欄位填入 `BTCUSDT`（可選，填入後會注入即時市場資料）
3. 選擇語言：`auto` / `zh` / `en`
4. 在輸入框輸入問題，按 Enter 送出
5. 等待 3~10 秒，查看回應

**有效問法範例：**
- "BTC 目前的市場體制是什麼？"
- "止損應該設在哪裡？"
- "RSI 超買怎麼操作？"
- "解釋一下 MACD 黃金交叉"

**信心度說明：**
- 模型信心度 < 0.2 時，系統會回答「抱歉，我無法確定這個答案。」
- 這是安全設計，避免模型給出低信心的錯誤建議
- 若需提升模型品質，請參考 [12_NLP_TRAINING.md](12_NLP_TRAINING.md) 進行訓練

**多輪對話：**
- Dashboard 自動維護 conversation_id
- 點選「**清除對話**」按鈕可重置對話歷史

---

### TradeControlPanel — 交易控制

**功能：** 啟動/停止 Binance 交易監控，並可選擇監控、paper-live、testnet auto 或 live auto。AI 模型預設載入；自動交易模式會由後端強制載入模型。

> **⚠️ 風險警示：此面板可觸發真實交易，請謹慎操作。**

**操作步驟（測試）：**
1. 進入「交易控制」面板
2. `Mode` 選擇 `Monitor only`、`Paper live` 或 `Testnet auto`
3. Symbol 輸入交易對（如 `BTCUSDT`）
4. 預設 `Load AI Model` 為開啟，Model 固定為 `unified_v2_100m`
5. 點選「**Start Trading**」
6. 點選「**Refresh Status**」確認 `running=true`，且 `engine.auto_trade` 符合模式
7. 點選「**Stop Trading**」結束

**操作步驟（正式網）：**

> 正式網需先完成：
> 1. 在 `StatusPanel` 確認 `BinanceFutures: available`
> 2. 在 `PreTradePanel` 執行驗核並通過
> 3. 確認已在 `.env` 設定有效的 Binance API 金鑰

1. 後端環境變數設定 `ALLOW_LIVE_TRADING=1`
2. `Mode` 選擇 `Live auto`
3. 在 `Live Confirm` 輸入 `I_UNDERSTAND_LIVE_RISK`
4. 點選「**Start Trading**」
5. **系統會開始監控市場，且在交易引擎產生非 HOLD 訊號時允許正式網送單**

**模式說明：**

| Mode | testnet | auto_trade | 用途 |
|---|---:|---:|---|
| `Monitor only` | 可選 | false | 只監控 WebSocket 與訊號，不自動送單 |
| `Paper live` | false | true | 使用 Binance mainnet 行情，但訂單只寫入本地虛擬帳戶 |
| `Testnet auto` | true | true | 測試網自動交易；需要 Binance testnet key |
| `Live auto` | false | true | 正式網自動交易；需要環境變數與確認字串 |

`Paper live` 的紀錄會寫入 `data/bioneuronai/trading/paper_live/`。平倉後會觸發主線 A 學習閉環（EpisodicMemory / LoRA）。**Autonomous 值班**（主線 B）不在此面板，請用 CLI 並檢查 `decision_ledger.jsonl`（見 [14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md) §5）。

---

### TrainingPanel — 訓練與模型

**功能：** 銜接後續訓練作業與 runtime 模型載入。第一輪雲端訓練產物已接回 runtime；此面板不取代雲端訓練平台，新的遠端訓練仍以 CLI / Docker / GCS 為主。

**遠端訓練登記：**
1. Mode 選 `External`
2. Job 填入作業名稱，例如 `cloud-training`
3. Cloud Job ID 填入 Vertex / GCE / 其他遠端 run id
4. Signal Train / Signal Val 填入本機或 `gs://` 訓練資料路徑
5. Cloud Output 填入 artifacts 目標，例如 `gs://YOUR_BUCKET/bioneuronai/training-runs/run-001`
6. 點選 `Start / Register`
7. 使用 `Job Status` 讀取目前 API 追蹤狀態

**模型 promote：**
1. Model 填入 `unified_v2_100m`
2. Model Path 填入訓練完成的 `.pth` 或模型目錄，可為 `gs://`
3. `Validate` 開啟時，後端會先確認模型檔可定位
4. 若交易引擎已運行且需要立即載入，開啟 `Reload Engine`
5. 點選 `Promote`
6. 點選 `Model Status` 確認 `active_model` 與 `MODEL_PATH` / `MODEL_DIR`

**限制：**
- `External` 模式只登記遠端 job，不會直接查 Vertex/GCE 狀態。
- `Local process` 會在 API 主機啟動本機訓練，會消耗本機 CPU/GPU；一般雲端訓練流程不需要使用。
- 模型 promote 不代表模型品質已驗證；目前第一輪雲端訓練產物已接回 runtime，但仍需固定區間回測、OOS / walk-forward、paper-live 與 testnet 結果支撐。

---

### APIPlayground — API 測試台

**功能：** 直接在 Dashboard 內呼叫任意 API 端點，方便開發與調試。

**操作步驟：**
1. 進入「API 測試台」面板
2. 選擇 HTTP 方法（GET / POST / DELETE）
3. 輸入端點路徑（如 `/api/v1/status`）
4. 若為 POST，在「請求體」欄填入 JSON
5. 點選「**送出**」
6. 在右側查看完整回應（含狀態碼、headers、body）

**常用測試組合：**

| 端點 | 方法 | 請求體 |
|---|---|---|
| `/api/v1/status` | GET | 無 |
| `/api/v1/news` | POST | `{"symbol":"BTCUSDT"}` |
| `/api/v1/pretrade` | POST | `{"symbol":"BTCUSDT","action":"long"}` |
| `/api/v1/backtest/catalog` | GET | 無 |
| `/api/v1/chat` | POST | `{"message":"BTC如何？","language":"zh"}` |

> **提示：** 亦可直接使用 Swagger UI（`http://localhost:8000/docs`）進行更詳細的互動測試。

---

### RequestHistoryPanel — 請求歷史

**功能：** 記錄本次 Dashboard 瀏覽期間所有 API 請求的歷史。

**顯示內容：**
- 時間戳
- 端點路徑
- HTTP 方法
- 回應狀態（success/failure）
- 回應時間（ms）

**用途：** 追蹤自己剛才執行了哪些操作；確認請求是否成功送達；比較不同參數的執行結果。

**版面狀態：** 2026-05-19 已修正大量請求紀錄造成面板高度失控的問題。`Request History` 左側列表與右側細節區會固定在 Dev Tools 面板內部捲動，不會把頁面撐到異常高度。

**Raw Response 顯示：** Dashboard 的 `Response` / `Raw Response` 區塊會以 JSON 顯示 API 原始回應。這不是亂碼；它是用來確認後端實際回傳內容。2026-05-19 已修正 JSON 區塊高度限制，長回應會在自己的框內捲動，不會覆蓋下一個面板。

---

### DataCatalogPanel — 資料目錄（備用）

> ⚠️ **此為備用面板**：相同功能已整合在 **BacktestPanel → catalog tab**，日常操作請以 BacktestPanel 為主。
> DataCatalogPanel 僅作為獨立視圖保留，當 BacktestPanel 不便使用時可切換至此。

**功能：** 呼叫 `GET /api/v1/data/catalog` 掃描 `backtest/data/` 目錄，顯示已下載的歷史資料集清單。

**面板狀態說明：**

| 狀態 | 說明 |
|---|---|
| 無資料（黃色警告） | `backtest/data/` 目錄無符合條件的資料集，顯示應執行的 CLI 下載指令 |
| 有資料 | 表格列出幣對、時間週期、日期範圍、ZIP 數量、K 線總數 |

**操作步驟（備用路徑）：**
1. 輸入 `Symbol`（選填）與 `Interval`（選填）篩選條件
2. 點「掃描」→ 顯示本地已有的資料集
3. 若顯示無資料，執行 CLI 指令下載後再重新掃描

---

### RiskConfigPanel — 風控設定（備用）

> ⚠️ **此為備用面板**：風險等級的首要修改方式是**直接編輯 `config/risk_config_optimized.json`**（詳見 [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md)），或使用 CLI / API 直接呼叫。
> RiskConfigPanel 僅提供 UI 快捷入口，適合不想手動編輯 JSON 時使用，所有變更會即時寫回設定檔。

**功能：** 呼叫 `GET /api/v1/risk/config` 與 `PUT /api/v1/risk/config` 讀取並切換風險等級。

**4 個風險等級：**

| 等級 | 顏色 | 適用場景 |
|---|---|---|
| `CONSERVATIVE` | 藍 | 低風險，保守配置 |
| `MODERATE` | 綠 | 預設，標準操作 |
| `AGGRESSIVE` | 橙 | 較高風險，擴大倉位 |
| `HIGH_RISK` | 紅 | 最高風險，需明確確認 |

**操作步驟（備用路徑）：**
1. 點「載入目前設定」→ 顯示當前等級（Badge 標示）
2. 點選目標等級按鈕
3. 點「套用 {LEVEL}」儲存 → 即時寫回 `risk_config_optimized.json`

---

## 5. 典型操作流程

### 每日盤前 SOP（日常使用）

```
1. 開啟 http://localhost:3000 或 Vite 顯示的本地網址
2. OperationsOverviewPanel → 確認 API OK、mode、execution target、model loaded
3. NewsPanel (BTCUSDT) → 查看新聞情緒與建議方向
4. PreTradePanel (BTCUSDT, long/short) → 執行驗核
   ├── PROCEED → 可考慮進場
   ├── CAUTION → 縮小倉位謹慎進場
   └── REJECT  → 今日不進場
5. 若決定觀察策略 → TradeControlPanel → `Paper live` 或 `Testnet auto`
6. Refresh Status → 確認 running / auto_trade / ai_model_loaded
7. 操作結束 → Stop Trading
```

### 策略研究 SOP（回測分析）

```
0. (首次) CLI 下載歷史資料（Dashboard 本身無此功能）：
   python main.py backtest-data --symbol BTCUSDT --interval 1h
1. BacktestPanel → 設定交易對/時間範圍/初始資金
2. 執行回測，記錄 Sharpe / MaxDrawdown / WinRate
3. 調整策略參數（config/strategy_weights_optimized.json）
4. 再次回測，比較結果
5. 反覆優化直到指標滿意
```

---

## 6. 常見問題

**Q: Dashboard 無法連接，顯示網路錯誤**
- 確認 `docker compose ps` 中 `bioneuron-api` 和 `bioneuron-frontend` 都是 `healthy`
- 確認沒有防火牆阻擋 port 3000 / 8000

**Q: 新聞分析返回 0 篇文章**
- CryptoPanic 免費方案有速率限制，等待 5 分鐘後重試
- 確認 `.env` 中 `CRYPTOPANIC_API_TOKEN` 若有設定則應有效

**Q: Backtest 面板執行後報錯或顯示「無歷史資料」**
- 本地尚未下載歷史 K 線資料，Dashboard 自身無下載功能
- 請先回到 CLI 執行：`python main.py backtest-data --symbol BTCUSDT --interval 1h`
- 資料下載完成後（存至 `backtest/data/`），重新在面板執行回測即可

**Q: 回測結果顯示許多「餘額不足」**
- 這是已知問題：固定倉位大小 (0.05 BTC) 在 BTC 高價時需要的保證金可能超過虛擬餘額
- 建議使用較小的初始資金參數或縮短回測時間範圍
- 不影響 `status: completed` 的結果有效性

**Q: ChatPanel 總是回答「抱歉，我無法確定」**
- TinyLLM 訓練資料有限，低信心的問題觸發安全回退
- 請嘗試更具體的問題（如「RSI 超買時怎麼設止損？」）
- 可進行模型訓練增強：參考 [12_NLP_TRAINING.md](12_NLP_TRAINING.md)

**Q: Response 區塊顯示一大段 JSON，看起來像亂碼**
- 這是 API raw response，屬於正常顯示。
- 若 JSON 溢出到下一個面板才是 UI 問題。2026-05-19 已修復 `JSONViewer` 高度限制；若再看到覆蓋，先重新整理前端並確認 Vite 使用的是最新程式碼。

**Q: PreTrade 總是 REJECT，account_balance 為 0**
- 系統使用 read-only Binance API，無法查詢真實帳戶餘額
- 這是正確的安全行為，要測試時請改用 testnet 模式

---

## 7. 相關文件

| 文件 | 說明 |
|---|---|
| [03_QUICKSTART.md](03_QUICKSTART.md) | 新手快速上手（含 Docker 設定） |
| [05_API_USER_MANUAL.md](05_API_USER_MANUAL.md) | REST API 完整端點手冊 |
| [20_UI_END_TO_END_OPERATION.md](20_UI_END_TO_END_OPERATION.md) | UI 從啟動到完成操作的端到端流程 |
| [07_DOCKER_DEPLOYMENT.md](07_DOCKER_DEPLOYMENT.md) | Docker 部署與環境設定 |
| [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md) | 回測系統詳細說明 |
| [12_NLP_TRAINING.md](12_NLP_TRAINING.md) | AI 模型訓練指南 |
