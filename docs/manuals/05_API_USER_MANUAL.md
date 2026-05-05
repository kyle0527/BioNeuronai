# BioNeuronai REST API 使用手冊

> **版本**：v2.1  
> **更新日期**：2026-05-05
> **伺服器預設**：`http://localhost:8000`  
> **互動文件（Swagger UI）**：`http://localhost:8000/docs`

---

## 📑 目錄

- [1. 概述](#1-概述)
- [2. 啟動方式](#2-啟動方式)
  - [Docker（推薦）](#docker推薦)
  - [本地直接啟動](#本地直接啟動)
  - [確認是否正常啟動](#確認是否正常啟動)
- [3. 通用規格](#3-通用規格)
- [4. 系統端點 (System)](#4-系統端點-system)
  - [GET /api/v1/status](#get-apiv1status)
  - [POST /api/v1/binance/validate](#post-apiv1binancevalidate)
- [5. 分析端點 (Analysis)](#5-分析端點-analysis)
  - [POST /api/v1/news](#post-apiv1news)
- [6. 回測端點 (Backtest)](#6-回測端點-backtest)
  - [GET /api/v1/backtest/catalog](#get-apiv1backtestcatalog)
  - [GET /api/v1/backtest/inspect](#get-apiv1backtestinspect)
  - [POST /api/v1/backtest/simulate](#post-apiv1backtestsimulate)
  - [POST /api/v1/backtest/run](#post-apiv1backtestrun)
  - [GET /api/v1/backtest/runs](#get-apiv1backtestruns)
  - [GET /api/v1/backtest/runs/{run_id}](#get-apiv1backtestrunsrunid)
  - [POST /api/v1/backtest/strategy-run](#post-apiv1backteststrategy-run)
  - [GET /backtest/ui](#get-backtestui)
- [7. 交易端點 (Trading)](#7-交易端點-trading)
  - [POST /api/v1/pretrade](#post-apiv1pretrade)
  - [POST /api/v1/trade/start](#post-apiv1tradestart)
  - [GET /api/v1/trade/status](#get-apiv1tradestatus)
  - [POST /api/v1/trade/stop](#post-apiv1tradestop)
  - [POST /api/v1/orders](#post-apiv1orders)
  - [DELETE /api/v1/positions/{position_id}](#delete-apiv1positionspositionid)
- [8. 對話端點 (Chat)](#8-對話端點-chat)
  - [POST /api/v1/chat](#post-apiv1chat)
  - [DELETE /api/v1/chat/{conversation_id}](#delete-apiv1chatconversationid)
- [9. Dashboard 端點 (Dashboard)](#9-dashboard-端點-dashboard)
  - [GET /api/v1/dashboard](#get-apiv1dashboard)
- [10. 風控與資料端點 (Risk & Data)](#10-風控與資料端點-risk--data)
  - [GET /api/v1/risk/config](#get-apiv1riskconfig)
  - [PUT /api/v1/risk/config](#put-apiv1riskconfig)
  - [GET /api/v1/data/catalog](#get-apiv1datacatalog)
- [11. WebSocket 端點](#11-websocket-端點)
  - [WS /ws/trade](#ws-wstrade)
  - [WS /ws/analytics](#ws-wsanalytics)
  - [WS /ws/dashboard](#ws-wsdashboard)
- [12. 通用回應格式](#12-通用回應格式)
- [13. 錯誤處理](#13-錯誤處理)
- [14. 實用 PowerShell 範例](#14-實用-powershell-範例)
- [相關文件](#相關文件)

---

## 1. 概述

BioNeuronai API 是以 **FastAPI + uvicorn** 建立的 REST 服務，將所有 CLI 功能封裝為 HTTP 端點，供：

- **DevOps Dashboard 前端** (`frontend/devops-d/`) 呼叫
- **外部程式** 或自動化腳本整合
- **Swagger UI** 互動測試（`/docs`）

API 伺服器本身不含業務邏輯，它只是把呼叫轉發給對應的模組（`analysis/`、`planning/`、`backtest/`、`core/`）。

---

## 2. 啟動方式

### Docker（推薦）
```bash
docker compose up api
```
API 容器啟動後，健康檢查會在 30 秒內確認服務可用。

### 本地直接啟動
```bash
# 安裝依賴後
uvicorn bioneuronai.api.app:app --host 0.0.0.0 --port 8000
# 或透過 main.py
python -m uvicorn bioneuronai.api.app:app --reload
```

### 確認是否正常啟動
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/" -Method GET
# 預期回應: { "service": "BioNeuronai API", "version": "2.1", ... }
```

---

## 3. 通用規格

| 項目 | 說明 |
|---|---|
| 基礎 URL | `http://localhost:8000` |
| 內容類型 | `Content-Type: application/json` |
| 認證 | 目前無認證（僅限本地 / 內部網路，勿對外暴露） |
| CORS | 預設允許 localhost:5173 / 3000 / 8080；生產環境請設定 `ALLOWED_ORIGINS` 環境變數 |
| API 版本 | `/api/v1/...` |
| 互動文件 | `GET /docs`（Swagger UI） |

---

## 4. 系統端點 (System)

### GET /api/v1/status

檢查所有核心模組是否可載入並初始化。

**請求：** 無請求體

**回應範例：**
```json
{
  "success": true,
  "modules": [
    { "name": "TradingEngine",   "available": true,  "error": null },
    { "name": "BinanceFutures",  "available": true,  "error": null },
    { "name": "NewsAnalyzer",    "available": true,  "error": null },
    { "name": "SOPSystem",       "available": true,  "error": null },
    { "name": "PreTradeCheck",   "available": true,  "error": null }
  ],
  "version": "2.1",
  "all_ok": true,
  "timestamp": "2026-04-28T13:24:19.794456"
}
```

**注意：** `all_ok: false` 通常是模組 import 失敗，請查看 `logs/` 下的日誌。

---

### POST /api/v1/binance/validate

驗證 Binance API 金鑰是否有效（讀取 + Futures 權限）。

**請求體：**
```json
{
  "api_key": "your_api_key",
  "api_secret": "your_api_secret",
  "testnet": false
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| `api_key` | string | 否 | 未填則使用環境變數 `BINANCE_API_KEY` |
| `api_secret` | string | 否 | 未填則使用環境變數 `BINANCE_API_SECRET` |
| `testnet` | boolean | 否 | `false`=主網（預設），`true`=測試網 |

**回應（成功）：**
```json
{
  "success": true,
  "message": "憑證驗證成功 [mainnet]",
  "data": {
    "total_wallet_balance": "1234.56",
    "environment": "mainnet"
  }
}
```

---

## 5. 分析端點 (Analysis)

### POST /api/v1/news

抓取並分析指定交易對的最新新聞，返回情緒評分與重要事件。

**請求體：**
```json
{
  "symbol": "BTCUSDT",
  "max_items": 10
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| `symbol` | string | 是 | 交易對，如 `BTCUSDT`、`ETHUSDT` |
| `max_items` | integer | 否 | 最多抓取幾篇文章（預設 10） |

**回應範例：**
```json
{
  "success": true,
  "message": "新聞分析完成",
  "data": {
    "symbol": "BTCUSDT",
    "total_articles": 3,
    "positive_count": 2,
    "negative_count": 0,
    "neutral_count": 1,
    "overall_sentiment": "positive",
    "sentiment_score": 0.681,
    "recommendation": "🟢 強烈看漲信號，可考慮做多",
    "signal_valid_hours": 9,
    "signal_expires_at": "2026-04-28T22:24:48.952658",
    "recent_headlines": ["..."],
    "top_keywords": [["bitcoin", 3], ["btc", 3]]
  },
  "timestamp": "2026-04-28T13:24:48.96296"
}
```

**sentiment_score 解讀：**

| 範圍 | 情緒 | 建議 |
|---|---|---|
| `>= 0.5` | 強烈正向 | 🟢 可考慮做多 |
| `0.1 ~ 0.5` | 正向 | 🟡 謹慎做多 |
| `-0.1 ~ 0.1` | 中性 | ⚪ 觀望 |
| `<= -0.5` | 負向 | 🔴 避免做多 |

---

## 6. 回測端點 (Backtest)

### GET /api/v1/backtest/catalog

列出本地所有可用的歷史資料。

**查詢參數（可選）：**
- `symbol=ETHUSDT` — 篩選特定交易對
- `interval=1h` — 篩選特定時間粒度

**範例：**
```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/backtest/catalog?symbol=ETHUSDT"
```

---

### GET /api/v1/backtest/inspect

確認特定資料集是否可被 replay 層正確載入。

**查詢參數：**
- `symbol` (預設 ETHUSDT)
- `interval` (預設 1h)
- `start_date` (可選，格式 `YYYY-MM-DD`)
- `end_date` (可選)

---

### POST /api/v1/backtest/simulate

執行 Replay Simulate（快速沙盒，不完整執行全策略管道）。

**請求體：**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "balance": 10000,
  "bars": 300,
  "start_date": null,
  "end_date": null
}
```

| 欄位 | 類型 | 必填 | 說明 |
|---|---|---|---|
| `symbol` | string | 是 | 交易對 |
| `interval` | string | 是 | K 線粒度：`1m`/`5m`/`15m`/`1h`/`4h`/`1d` |
| `balance` | float | 否 | 虛擬初始資金（預設 10000 USDT） |
| `bars` | integer | 否 | 使用最近幾根 K 線（`start_date`/`end_date` 未指定時使用） |
| `start_date` | string | 否 | 開始日期（格式 `YYYY-MM-DD`） |
| `end_date` | string | 否 | 結束日期 |

---

### POST /api/v1/backtest/run

執行完整回測（Full Backtest Replay），會跑完整策略管道（包含 StrategySelector、AIFusion）。

**請求體：**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "balance": 10000,
  "start_date": "2020-01-01",
  "end_date": "2020-01-03",
  "warmup_bars": 10
}
```

**注意：** 此端點依資料量不同可能需要 15 秒 ~ 10 分鐘。請不要設定過短的 HTTP timeout。

**回應範例（成功）：**
```json
{
  "success": true,
  "message": "backtest 完成",
  "data": {
    "symbol": "ETHUSDT",
    "interval": "1h",
    "stats": {
      "initial_balance": 10000.0,
      "current_balance": 10027.60,
      "total_return": 0.276,
      "total_trades": 327,
      "win_rate": 27.2,
      "sharpe_ratio": 7.46,
      "sortino_ratio": 9.59,
      "max_drawdown": 0.285,
      "profit_factor": 1.29
    },
    "trade_count": 327,
    "status": "completed",
    "run_id": "20260428_132540_50707287"
  }
}
```

---

### GET /api/v1/backtest/runs

列出最近的 replay runtime 執行記錄。

**查詢參數：** `limit=10`（預設 10，最多 100）

---

### GET /api/v1/backtest/runs/{run_id}

讀取指定 `run_id` 的完整執行紀錄（包含所有訂單、成交明細）。

```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/backtest/runs/20260428_132540_50707287"
```

---

### POST /api/v1/backtest/strategy-run

執行策略模組競爭回測（多策略模板同時回測），支援 walk-forward 驗證。

**請求體：**
```json
{
  "symbol": "BTCUSDT",
  "interval": "1h",
  "balance": 10000,
  "start_date": "2020-01-01",
  "end_date": "2020-01-03",
  "warmup_bars": 100,
  "execution_mode": "template_rules",
  "commission_bps": 5.5,
  "slippage_bps": 1.0,
  "walk_forward": false,
  "close_open_positions_on_end": true,
  "parameter_overrides": null
}
```

| 欄位 | 類型 | 必填 | 說明 |
|------|------|:----:|------|
| `symbol` | string | 否 | 交易對，預設 `BTCUSDT` |
| `interval` | string | 否 | K 線週期，預設 `1h` |
| `balance` | float | 否 | 初始資金，預設 10000 |
| `start_date` | string | 否 | 起始日期 YYYY-MM-DD |
| `end_date` | string | 否 | 結束日期 YYYY-MM-DD |
| `execution_mode` | string | 否 | `template_rules`（全模板）或 `hybrid` |
| `commission_bps` | float | 否 | Taker 手續費（基點），預設 5.5（Binance Futures VIP0 0.05% × 1.1 保守設定） |
| `slippage_bps` | float | 否 | 滑點（基點），預設 1.0 |
| `walk_forward` | bool | 否 | 是否執行 walk-forward 70/30 切分 |
| `close_open_positions_on_end` | bool | 否 | 結束時強制平倉，預設 true |

**PowerShell 範例：**
```powershell
$body = @{ symbol='BTCUSDT'; interval='1h'; balance=10000; start_date='2020-01-01'; end_date='2020-01-03' } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://localhost:8000/api/v1/backtest/strategy-run' -Method Post -Body $body -ContentType 'application/json'
```

---

### GET /backtest/ui

開啟 API 伺服器內建的簡易 Backtest HTML 工具頁。此路由不屬於 `/api/v1` JSON API，主要用於本地人工檢視與快速操作。

```text
http://127.0.0.1:8000/backtest/ui
```

---

## 7. 交易端點 (Trading)

### POST /api/v1/pretrade

執行進場前六點綜合驗核（技術面 + 基本面 + 資金管理）。

**請求體：**
```json
{
  "symbol": "BTCUSDT",
  "action": "long"
}
```

| 欄位 | 說明 | 可選值 |
|---|---|---|
| `symbol` | 目標交易對 | `BTCUSDT`、`ETHUSDT` 等 |
| `action` | 預計交易方向 | `long`、`short` |

**回應 overall_assessment.status 解讀：**

| 狀態 | 說明 |
|---|---|
| `PROCEED` | 全部通過，可以進場 |
| `CAUTION` | 部分警告，可謹慎進場 |
| `REJECT` | 有硬性條件未通過，不應進場 |

---

### POST /api/v1/trade/start

啟動交易監控（後台 task，接收 WebSocket 推送並依模式決定是否允許自動送單）。

**請求體：**
```json
{
  "symbol": "BTCUSDT",
  "testnet": true,
  "mode": "monitor_only",
  "auto_trade": false,
  "load_ai_model": false,
  "model_name": "my_100m_model",
  "warmup_model": false,
  "confirm_live": "",
  "api_key": "",
  "api_secret": ""
}
```

> **重要安全提醒**：  
> - `testnet: true` 時連接 Binance 測試網，不消耗真實資金  
> - `api_key`/`api_secret` 若留空，系統會自動讀取環境變數  
> - `testnet_auto` 會啟用 `auto_trade`，需提供 Binance testnet key
> - `live_auto` 必須 `testnet=false`、`confirm_live=I_UNDERSTAND_LIVE_RISK`，且後端環境變數 `ALLOW_LIVE_TRADING=1`
> - **正式網交易前，請務必先在測試網驗證策略**

---

### GET /api/v1/trade/status

查詢交易監控與自動交易狀態。

**回應重點：**
```json
{
  "running": false,
  "mode": "stopped",
  "engine": {
    "is_monitoring": false,
    "auto_trade": false,
    "ai_model_loaded": false
  }
}
```

---

### POST /api/v1/trade/stop

停止目前正在執行的交易監控。

**請求體：** 無

---

### POST /api/v1/orders

透過 API 直接提交一筆訂單（需先呼叫 `/trade/start` 啟動引擎）。

**請求體：**
```json
{
  "symbol": "BTCUSDT",
  "side": "buy",
  "quantity": 0.01,
  "order_type": "LIMIT",
  "price": 76000,
  "stop_loss": 74000,
  "take_profit": 80000
}
```

---

### DELETE /api/v1/positions/{position_id}

平倉指定 position_id（需引擎已啟動）。

```powershell
Invoke-RestMethod -Method DELETE "http://localhost:8000/api/v1/positions/pos_btcusdt_001"
```

---

## 8. 對話端點 (Chat)

### POST /api/v1/chat

與內建 TinyLLM 對話（雙語：繁體中文 / English）。

**請求體：**
```json
{
  "message": "BTC 目前市場狀況如何？",
  "symbol": "BTCUSDT",
  "language": "zh",
  "conversation_id": null
}
```

| 欄位 | 說明 |
|---|---|
| `message` | 使用者輸入的問題（中文或英文皆可） |
| `symbol` | 可選。填入後系統會自動注入即時市場資料 |
| `language` | `auto`（自動偵測）、`zh`（繁體中文）、`en`（英文） |
| `conversation_id` | 可選。相同 ID 可維持多輪對話記憶 |

**回應範例：**
```json
{
  "success": true,
  "text": "目前 BTC 市場處於恐懼情緒，建議謹慎觀望...",
  "language": "zh",
  "confidence": 0.72,
  "market_context_used": true,
  "stopped_reason": null,
  "latency_ms": 5957.5,
  "conversation_id": "d4f505c7-0bc2-44f9-ac02-c52cf4552984",
  "timestamp": "2026-04-28T13:26:43.934873"
}
```

**confidence 解讀：**

| 範圍 | 狀態 |
|---|---|
| `>= 0.5` | 高信心，回應可信 |
| `0.2 ~ 0.5` | 中等信心 |
| `< 0.2` | 低信心，系統回答「抱歉，我無法確定這個答案。」 |

> **說明**：TinyLLM 屬於 111.6M 參數小型模型，訓練資料有限，低信心時會主動回退而非給出錯誤答案。這是設計行為，非 Bug。若需提升準確度，請參考 [12_NLP_TRAINING.md](12_NLP_TRAINING.md)。

---

### DELETE /api/v1/chat/{conversation_id}

清除指定 conversation_id 的對話歷史（重置多輪記憶）。

```powershell
Invoke-RestMethod -Method DELETE "http://localhost:8000/api/v1/chat/d4f505c7-0bc2-44f9-ac02-c52cf4552984"
```

---

## 9. Dashboard 端點 (Dashboard)

### GET /api/v1/dashboard

取得系統即時 Dashboard 快照（供 `frontend/admin-da` 使用）。

**回應包含：**
- `risk`：當前風險等級與百分比
- `maxDrawdown`：最大回撤統計
- `pretradeChecklist`：進場前檢查項目完成狀態
- `auditLog`：最近系統事件日誌
- `positions`：持倉列表（若有）

---

## 10. 風控與資料端點 (Risk & Data)

> **備注**：本節端點主要供 Dashboard 中的 **備用面板**（RiskConfigPanel、DataCatalogPanel）呼叫，
> 日常使用請以 BacktestPanel（catalog tab）與直接編輯設定檔為主。

### GET /api/v1/risk/config

讀取目前的風險設定檔 `config/risk_config_optimized.json` 全部內容。

**回應範例：**

```json
{
  "success": true,
  "message": "風險設定讀取成功",
  "data": {
    "risk_level": "MODERATE",
    "custom_overrides": {
      "max_risk_per_trade": 0.015,
      "max_leverage": 2.5
    }
  }
}
```

---

### PUT /api/v1/risk/config

更新風險設定。僅允許修改 `risk_level` 與 `custom_overrides` 兩個欄位，不會覆蓋其他設定。

**允許的 `risk_level` 值：** `CONSERVATIVE` / `MODERATE` / `AGGRESSIVE` / `HIGH_RISK`

**請求範例：**

```json
{
  "risk_level": "CONSERVATIVE"
}
```

**請求範例（同時更新覆蓋值）：**

```json
{
  "risk_level": "AGGRESSIVE",
  "custom_overrides": {
    "max_risk_per_trade": 0.03,
    "max_leverage": 5.0
  }
}
```

**回應範例（成功）：**

```json
{
  "success": true,
  "message": "風險設定已更新",
  "data": { "risk_level": "AGGRESSIVE", "custom_overrides": { ... } }
}
```

**回應範例（無效等級）：**

```json
{
  "success": false,
  "message": "無效的 risk_level：ULTRA，允許值：['AGGRESSIVE', 'CONSERVATIVE', 'HIGH_RISK', 'MODERATE']"
}
```

---

### GET /api/v1/data/catalog

> **備注**：此端點與 `GET /api/v1/backtest/catalog` 功能等效，
> 為 DataCatalogPanel（備用面板）提供獨立路由。日常使用請直接透過 BacktestPanel → catalog tab。

掃描 `backtest/data/` 目錄，列出所有已下載的歷史資料集。支援 `symbol` / `interval` 查詢篩選。

**查詢參數（均可選）：**

| 參數 | 類型 | 說明 |
|---|---|---|
| `symbol` | string | 篩選幣對，如 `BTCUSDT` |
| `interval` | string | 篩選時間週期，如 `1h` |

**PowerShell 範例：**

```powershell
Invoke-RestMethod "http://localhost:8000/api/v1/data/catalog?symbol=BTCUSDT&interval=1h"
```

---

## 11. WebSocket 端點

WebSocket 連線提供即時資料推送，前端使用 `ws://localhost:8000/ws/...` 連線。

### WS /ws/trade

**功能：** 即時報價、成交推送  
**更新頻率：** 每 2 秒  
**訊息格式：**
```json
{
  "type": "price_update",
  "symbol": "BTCUSDT",
  "price": 76095.7
}
```

### WS /ws/analytics

**功能：** 投資組合、績效推送  
**更新頻率：** 每 5 秒  
**訊息格式：**
```json
{
  "type": "portfolio_update",
  "portfolio": [...]
}
```

### WS /ws/dashboard

**功能：** Dashboard 整體狀態推送（`admin-da` 使用）  
**更新頻率：** 每 3 秒

---

## 12. 通用回應格式

大部分端點回傳 `ApiResponse` 結構：

```json
{
  "success": true,
  "message": "操作說明",
  "data": { ... },
  "timestamp": "2026-04-28T13:24:19.794456"
}
```

| 欄位 | 說明 |
|---|---|
| `success` | `true` = 成功；`false` = 失敗 |
| `message` | 操作結果說明 |
| `data` | 回應主體（各端點格式不同） |
| `timestamp` | 伺服器處理時間（ISO 8601） |

---

## 13. 錯誤處理

| 情境 | `success` | `message` 範例 |
|---|---|---|
| 模組 import 失敗 | `false` | `新聞分析失敗: No module named 'xxx'` |
| 無效請求參數 | HTTP 422 | Pydantic validation error |
| 交易引擎未啟動 | `false` | `交易引擎未啟動，請先呼叫 POST /api/v1/trade/start` |
| API 金鑰無效 | `false` | `API Key 無效或缺乏 Futures 權限` |
| Backtest 資料不存在 | `false` | `資料載入失敗: 找不到 XXXX_1h.parquet` |

---

## 14. 實用 PowerShell 範例

```powershell
# 1. 系統健康檢查
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/status" | ConvertTo-Json -Depth 5

# 2. 新聞分析
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/news" `
  -Method POST -Body '{"symbol":"BTCUSDT"}' -ContentType "application/json"

# 3. 進場前驗核
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/pretrade" `
  -Method POST -Body '{"symbol":"BTCUSDT","action":"long"}' -ContentType "application/json"

# 4. 執行回測（BTCUSDT 短區間）
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/backtest/run" `
  -Method POST `
  -Body '{"symbol":"BTCUSDT","interval":"1h","balance":10000,"start_date":"2020-01-01","end_date":"2020-01-03","warmup_bars":10}' `
  -ContentType "application/json" `
  -TimeoutSec 600

# 5. AI 對話
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" `
  -Method POST -Body '{"message":"BTC市場如何？","symbol":"BTCUSDT","language":"zh"}' `
  -ContentType "application/json"

# 6. 啟動測試網交易
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/trade/start" `
  -Method POST `
  -Body '{"symbol":"BTCUSDT","testnet":true,"mode":"monitor_only","auto_trade":false,"load_ai_model":false,"model_name":"my_100m_model","warmup_model":false}' `
  -ContentType "application/json"

# 7. 查詢交易狀態
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/trade/status" -Method GET

# 8. 停止交易
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/trade/stop" -Method POST
```

---

## 相關文件

| 文件 | 說明 |
|---|---|
| [03_QUICKSTART.md](03_QUICKSTART.md) | 新手快速上手 |
| [06_FRONTEND_DASHBOARD.md](06_FRONTEND_DASHBOARD.md) | 前端 Dashboard 操作手冊 |
| [08_BACKTEST_SYSTEM.md](08_BACKTEST_SYSTEM.md) | 回測系統詳細說明 |
| [04_CLI_OPERATION.md](04_CLI_OPERATION.md) | CLI 操作手冊 |
| [07_DOCKER_DEPLOYMENT.md](07_DOCKER_DEPLOYMENT.md) | Docker 部署指南 |
