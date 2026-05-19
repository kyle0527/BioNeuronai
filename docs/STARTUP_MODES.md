# BioNeuronAI 啟動方式差異

> 更新日期：2026-05-19
> 目的：釐清 CLI、API、UI、Docker 四種入口在實際操作與功能上的差異。

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
