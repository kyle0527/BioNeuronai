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
2. 定義 REST route 與 WebSocket route
3. 維持舊 import 路徑對 `schemas.api` 的相容轉發

---

## 實際結構

```text
api/
├── __init__.py  # 匯出 app
├── app.py       # FastAPI app、routes、TradeManager、CORS
├── models.py    # 對 schemas.api 的轉發層
└── README.md
```

檔案對照：
1. [__init__.py](__init__.py)
2. [app.py](app.py)
3. [models.py](models.py)

這個資料夾目前沒有更深一層的 README 子文件，因此本文件直接維護到檔案與 route 入口層級。

---

## 檔案分工

### `app.py`

1. 建立 `FastAPI` app，處理 CORS、lifespan 與 `/docs` Swagger 暴露
2. 內部維護三個狀態管理器：`TradeManager` (交易)、`TrainingJobManager` (訓練)、`ModelPromotionManager` (模型切換)
3. 暴露 REST API 入口：
   - 系統/狀態：`/api/v1/status`、`/api/v1/binance/validate`
   - 交易/風險：`/api/v1/trade/*`、`/api/v1/pretrade`、`/api/v1/risk/config`
   - 回測/數據：`/api/v1/backtest/*`、`/api/v1/data/catalog`
   - 模型訓練：`/api/v1/training/*`、`/api/v1/model/*`
   - 對話/新聞：`/api/v1/chat`、`/api/v1/news`
   - 儀表板：`/api/v1/dashboard`、`/api/v1/orders`、`/api/v1/positions/*`
4. 提供 WebSocket 即時推送入口：`/ws/trade`、`/ws/analytics`、`/ws/dashboard`

TradeManager 目前支援四種交易模式：

| mode | 行情來源 | 執行層 | AI 載入 |
|---|---|---|---|
| `monitor_only` | 依 `testnet` 選擇 connector | 不自動送單 | `load_ai_model` 預設 true |
| `paper_live` | Binance mainnet public market data | 本地 `VirtualAccount`，不送 Binance order | 強制載入 |
| `testnet_auto` | Binance testnet | Binance testnet order API | 強制載入 |
| `live_auto` | Binance mainnet | Binance mainnet order API | 強制載入 |

`live_auto` 另外需要 `ALLOW_LIVE_TRADING=1` 與 `confirm_live=I_UNDERSTAND_LIVE_RISK`。`paper_live` 不需要 live guard，因為它不送出真實訂單。

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
