# BioNeuronAI 啟動方式差異

> 更新日期：2026-06-03
> 目的：釐清 CLI、API、UI、Docker 四種入口，以及 AI 自主運作模式（新增）在實際操作與功能上的差異。

## 1. CLI

CLI 是最直接的單次任務入口：

```powershell
python main.py <command>
```

適合健康檢查、資料盤點、pretrade、plan、news、backtest、simulate、readiness-gate、chat，以及 paper-live / testnet / live 交易入口。它不需要常駐服務，最容易確認單一功能是否真的跑完。執行結果會寫入 `backtest/runtime/` 或 `output/`，這些屬於 runtime artifact，不納入 Git。

目前正式驗證先以本機全域 Python 3.13 為準；PyTorch 使用已確認可 import 的官方 CPU 2.8.0 組合。Docker image 留到本機自然語言、交易判斷與 API/UI readiness 收斂後最後重建。

## 2. API

API 是 FastAPI 長時間服務入口：

```powershell
python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
```

它負責提供 UI、外部自動化、Swagger 操作與交易控制端點。若 API 未啟動、port 不一致或 CORS 設定錯誤，UI 會出現 `Failed to fetch`。

## 3. UI

UI 目前主線是 `frontend/devops-d`：

```powershell
cd frontend/devops-d
npm run dev
```

UI 是人工操作與監控介面，本身不直接執行 AI 或交易邏輯；所有狀態、聊天、回測、交易控制、資料目錄與風控設定都透過 API 取得。
Docker frontend 預設是 `http://localhost:3000`；本地 Vite 通常是 `http://localhost:5173`，若 port 被占用會落到 `5176` 等下一個可用 port。

## 4. Docker

Docker 是容器化入口：

```powershell
docker compose up api frontend
docker compose run --rm status
docker compose run --rm pretrade
docker compose run --rm simulate
docker compose run --rm backtest
```

它適合部署、重現環境與隔離依賴。修改後端、前端或依賴後通常需要 `docker compose build`。本輪 Docker 不作主要驗證入口；待本機流程穩定後再重建 image，並重新確認 `model/` 權重、`backtest/` 掛載與 API/frontend 狀態。

## 建議使用順序

| 情境 | 建議入口 |
|---|---|
| 確認某個功能能不能跑 | CLI |
| 確認 UI / 自動化整合 | API + UI |
| 日常本機操作與觀察 | API + UI |
| 部署或重現乾淨環境 | Docker |
| 正式交易前完整檢查 | CLI `readiness-gate` + API/UI paper-live |

目前專案尚未完成「依原始設計目的完整跑過一次正式長週期自動運作」的驗收，因此舊 training / output / runtime 記錄只作為本機歸檔，不再視為正式進度證據。

---

## 5. AI 自主模式

這裡有兩條不同的自主路徑，不能混為一談。

### 5.1 `autonomous` 單輪決策

CLI：

```powershell
python main.py autonomous --mode advisor --symbol BTCUSDT
python main.py autonomous --mode paper_auto --symbol BTCUSDT
```

這條路徑的作用是：

- 做一輪 observe-plan-pretrade-adapt 判斷
- 輸出 `advise_only`、`observe` 或更進一步動作
- 寫入 decision ledger

它會結束，不會自己長時間監控。

### 5.2 `trade` 長時間監控主線

> 2026-06-03 驗證確認；這是 BioNeuronAI 真正持續運作的主線。

AI 自主模式透過 WebSocket 訂閱即時 Ticker，每次 Tick 到達即觸發完整的「市場資料 → AI 推論 → 策略融合 → 新聞 RAG 護欄 → 下單」管線，無需人工介入。

### 啟動方式（Python / API）

**方式 A — 直接呼叫（測試、開發）**

```python
from bioneuronai.core.trading_engine import TradingEngine

engine = TradingEngine(
    testnet=True,         # True = Binance Testnet; False = mainnet
    paper_trading=True,   # True = 虛擬成交，不送真實訂單
    enable_ai_model=True
)
engine.load_ai_model('my_100m_model')  # 載入 config/active_model.json 指定的 checkpoint
engine.enable_auto_trading()           # 設定 auto_trade = True
engine.start_monitoring('BTCUSDT')     # 訂閱 WebSocket；阻塞直到 stop_monitoring() 被呼叫
```

**方式 B — 透過 API**

```http
POST /api/v1/trade/start
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "mode": "paper_live",
  "auto_trade": true
}
```

> 當 `mode` 為 `paper_live`、`testnet_auto` 或 `live_auto` 時，`_auto_trade_requested()` 返回 True，系統自動呼叫 `enable_auto_trading()`。

### 自主決策管線（Tick → 訂單）

```
Binance WebSocket Tick
    ↓
on_ticker_update()
    ↓
_process_market_data()  →  抓取 K 線（BinanceFuturesConnector._get_klines）
    ↓
generate_trading_signal()
    ├── InferenceEngine.get_ai_prediction()         # TinyLLM 111.6M, ~165ms/次
    ├── StrategySelector.get_actionable_signal()    # 6 策略融合
    └── NewsAdapter.get_event_context()             # RAG FAISS 情緒分數
    ↓
_handle_trading_signal()
    └── if auto_trade: execute_trade()
            ├── _check_news_risk()                  # 新聞護欄（阻擋 has_major_negative）
            ├── _get_account_balance()
            ├── _get_current_price()
            ├── _calculate_position_size()
            ├── _is_cost_effective()
            └── connector.place_order()             # FILLED
```

### 各模式對照表

| 模式 | testnet= | paper_trading= | auto_trade= | 說明 |
|---|---|---|---|---|
| `monitor_only` | True | True | False | 只觀察訊號，不下單 |
| `paper_live` | False | True | True（可選） | 主網行情 + 虛擬成交 |
| `testnet_auto` | True | False | True | Testnet 真實下單（虛擬資金） |
| `live_auto` | False | False | True | **主網真實下單**（需謹慎） |

### 信心度門檻說明

`TradingEngine.ai_min_confidence`（預設 `0.5`）是下單前的最低 AI 信心度要求。
現役模型在當前市況下信心度約 0.33，低於門檻時輸出 `HOLD`。
Testnet 觀察期間可暫時降至 0.25（`engine.ai_min_confidence = 0.25`）以觀察更多訊號行為。

### 注意事項

- **新聞護欄是硬性阻擋**：`_check_news_risk()` 返回 False 時，即使 AI 訊號強、信心度高，也不會下單。此為設計行為，不是 bug。
- **4/6 策略目前有問題**：`mean_reversion`、`breakout` 等因 K 線週期不足回傳 None/Error；短期只有 `swing_trading` 和 `trend_following` 有效。
- **停止自主模式**：呼叫 `engine.stop_monitoring()` 或 `POST /api/v1/trade/stop`。
