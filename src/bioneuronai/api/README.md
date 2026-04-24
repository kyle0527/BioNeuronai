# API 模組 (API)

> 路徑：`src/bioneuronai/api/`
> 更新日期：2026-04-23
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

1. 建立 `FastAPI` app
2. 管理 `TradeManager` 的啟停與背景 task
3. 提供 `/api/v1/status`、`/api/v1/chat`、`/api/v1/news`、`/api/v1/pretrade`、`/api/v1/backtest/*` 等入口
4. `backtest` 相關 route 現在包含策略模組 UI/CLI 共用的 `POST /api/v1/backtest/strategy-run`
4. 處理 CORS、lifespan 與 `/docs` Swagger 暴露

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
