# API 模組 (API)

> 路徑：`src/bioneuronai/api/`
> 更新日期：2026-05-13
> 定位：FastAPI 對外入口與 API 相容轉發層

`api/` 是 `bioneuronai` 對外暴露 HTTP 介面的模組。它的責任是把既有 CLI / core / analysis / planning / backtest 功能包裝成 REST API，而不是重新實作業務邏輯。

---

## 目錄

1. [模組定位](#模組定位)
2. [實際結構](#實際結構)
3. [檔案分工](#檔案分工)
4. [對外匯出](#對外匯出)
5. [維護邊界](#維護邊界)

---

## 模組定位

`api/` 目前做 3 件事：

1. 建立 FastAPI app 與 lifespan
2. 定義 REST route 與 WebSocket route，逐步拆到 `routes/`
3. 維持舊 import 路徑對 `schemas.api` 的相容轉發

---

## 實際結構

```text
api/
├── __init__.py  # 匯出 app
├── app.py       # FastAPI app、CORS、lifespan、runtime managers、router mounting
├── models.py    # 對 schemas.api 的轉發層
├── serialization.py # API JSON-safe serialization helper
├── routes/
│   ├── __init__.py
│   ├── analysis.py # news analysis route
│   ├── backtest.py # backtest / replay / runtime run routes
│   ├── chat.py # ChatEngine routes
│   ├── dashboard.py # dashboard / risk / data / websocket routes
│   ├── system.py # root、status、Binance credential validate
│   ├── trading.py # pretrade / trade start-status-stop routes
│   └── training.py # training job / model promote routes
└── README.md
```

檔案對照：
1. [__init__.py](__init__.py)
2. [app.py](app.py)
3. [models.py](models.py)
4. [serialization.py](serialization.py)
5. [routes/system.py](routes/system.py)
6. [routes/backtest.py](routes/backtest.py)

這個資料夾目前沒有更深一層的 README 子文件，因此本文件直接維護到檔案與 route 入口層級。

---

## 檔案分工

### `app.py`

1. 建立 `FastAPI` app，處理 CORS、lifespan 與 `/docs` Swagger 暴露
2. 內部維護三個狀態管理器：`TradeManager` (交易)、`TrainingJobManager` (訓練)、`ModelPromotionManager` (模型切換)
3. 掛載 route module：
   - `routes/system.py`：`/`、`/api/v1/status`、`/api/v1/binance/validate`
   - `routes/analysis.py`：`/api/v1/news`
   - `routes/backtest.py`：`/api/v1/backtest/*`、`/backtest/ui`
   - `routes/trading.py`：`/api/v1/pretrade`、`/api/v1/trade/*`
   - `routes/training.py`：`/api/v1/training/*`、`/api/v1/model/*`
   - `routes/chat.py`：`/api/v1/chat`
   - `routes/dashboard.py`：`/api/v1/dashboard`、`/api/v1/orders`、`/api/v1/positions/*`、`/api/v1/risk/config`、`/api/v1/data/catalog`、`/ws/*`
4. 提供三個 runtime manager 給 router factory 使用：`TradeManager`、`TrainingJobManager`、`ModelPromotionManager`

### `routes/system.py`

1. `GET /`：API root metadata
2. `GET /api/v1/status`：系統健康檢查
3. `POST /api/v1/binance/validate`：Binance 憑證與 Futures 權限檢查

後續若繼續拆 route，應沿用 `routes/<domain>.py` + `app.include_router(...)` 的模式。

### `routes/backtest.py`

1. `GET /api/v1/backtest/catalog`：歷史資料清單
2. `GET /api/v1/backtest/inspect`：資料集載入檢查
3. `POST /api/v1/backtest/simulate`：paper replay 模擬
4. `POST /api/v1/backtest/run`：完整 backtest replay
5. `POST /api/v1/backtest/strategy-run`：策略模板競爭回測
6. `GET /api/v1/backtest/runs`、`GET /api/v1/backtest/runs/{run_id}`：runtime run 查詢
7. `GET /backtest/ui`：內建簡易 backtest HTML 工具

### 其他 `routes/*.py`

| 檔案 | 端點範圍 | 依賴狀態 |
|---|---|---|
| `analysis.py` | `/api/v1/news` | 無常駐狀態 |
| `trading.py` | `/api/v1/pretrade`、`/api/v1/trade/*` | `TradeManager` |
| `training.py` | `/api/v1/training/*`、`/api/v1/model/*` | `TrainingJobManager`、`ModelPromotionManager` |
| `chat.py` | `/api/v1/chat` | `TradeManager` 提供即時價格上下文 |
| `dashboard.py` | dashboard / risk / data / websocket | `TradeManager`、`PROJECT_ROOT` |

TradeManager 目前支援四種交易模式：

| mode | 行情來源 | 執行層 | AI 載入 |
|---|---|---|---|
| `monitor_only` | 依 `testnet` 選擇 connector | 不自動送單 | `load_ai_model` 預設 true |
| `paper_live` | Binance mainnet public market data | 本地 `VirtualAccount` 價格同步，不送單 | 可選 |
| `testnet_auto` | — | 已拒絕；請使用 autonomous 單一決策線 | — |
| `live_auto` | — | 已拒絕；請使用 autonomous 單一決策線 | — |

`auto_trade=true`、`testnet_auto` 與 `live_auto` 都會被拒絕。API trade manager 僅提供觀測；自動決策與 paper 下單統一由 CLI `autonomous` 處理。

### `models.py`

1. 不是主要 schema 定義位置
2. 主要責任是從 `schemas.api` 重新導出 API request / response model
3. 用途是維持 `api.app` 與既有 import 路徑穩定

---

## 對外匯出

```python
from bioneuronai.api import app
```

若需要 request / response schema，請以 `schemas.api` 為主，而不是在此模組新增第二份事實來源。

---

## 維護邊界

1. 本文件只描述 API 模組角色與檔案分工。
2. 業務規則應回到 `core/`、`analysis/`、`planning/`、`backtest/` 維護。
3. 若 API route 新增或刪除，應同步更新本文件與上層 `src/bioneuronai/README.md` 的子模組導覽。

---

> 上層目錄：[BioNeuronai README](../README.md)
