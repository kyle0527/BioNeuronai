# Dashboard 操作排查手冊

> 範圍：使用者操作 `frontend/devops-d` 時遇到的前端、API、CORS、WebSocket 問題。
> 更新日期：2026-05-13

---

## 📑 目錄

- [1. 啟動順序](#1-啟動順序)
- [2. 確認 API 可用](#2-確認-api-可用)
- [3. 前端 build 檢查](#3-前端-build-檢查)
- [4. 常見問題](#4-常見問題)
- [5. Docker Dashboard](#5-docker-dashboard)
- [6. API URL 設定](#6-api-url-設定)

---

## 1. 啟動順序

先啟動 API：

```powershell
python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
```

再啟動前端：

```powershell
cd frontend/devops-d
npm run dev
```

瀏覽器開：

```text
http://localhost:5173
http://127.0.0.1:5176  # 若 Vite 自動改用下一個可用 port
```

---

## 2. 確認 API 可用

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/status"
```

成功標準：

- 回傳 JSON。
- `all_ok` 為 `true`。

---

## 3. 前端 build 檢查

```powershell
cd frontend/devops-d
npm run build
```

成功標準：

- Vite build 成功。
- 產生 `dist/`。

---

## 4. 常見問題

| 現象 | 可能原因 | 處理 |
|---|---|---|
| 頁面空白 | 前端 dev server 未啟動或 build 失敗 | 看 `npm run dev` 終端 |
| `Failed to fetch` | API 沒啟動、API URL 指錯、或 CORS 不允許目前前端 origin | 先打 `/api/v1/status`，再查 CORS |
| CORS 錯誤 | `ALLOWED_ORIGINS` 未包含前端網址 | 設定目前實際 origin，例如 `http://127.0.0.1:5176` |
| Operations Overview 失敗 | `/status`、`/trade/status`、`/model/status` 或 `/dashboard` 任一端點失敗 | 逐一用 PowerShell 打 API |
| Backtest 面板沒資料 | 本地歷史資料不存在 | 跑 `python main.py backtest-data` |
| WebSocket 連不上 | API 沒啟動或 ws endpoint 異常 | 先確認 REST API 正常 |

---

## 5. Docker Dashboard

啟動：

```powershell
docker compose up api frontend
```

瀏覽器：

```text
http://localhost:3000
```

確認服務：

```powershell
docker compose ps
```

查看 logs：

```powershell
docker compose logs --tail=100 api
docker compose logs --tail=100 frontend
```

---

## 6. API URL 設定

本地 dev 預設 API：

```text
http://localhost:8000
```

若需要覆蓋，在 `frontend/devops-d/.env` 設定：

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

修改後重新啟動：

```powershell
npm run dev
```

後端未設定 `ALLOWED_ORIGINS` 時，預設允許：

- `http://localhost:3000`
- `http://127.0.0.1:3000`
- `http://localhost:8080`
- `http://127.0.0.1:8080`
- `http://localhost:5173` 到 `http://localhost:5180`
- `http://127.0.0.1:5173` 到 `http://127.0.0.1:5180`

若要手動確認 preflight：

```powershell
$headers = @{
  Origin = "http://127.0.0.1:5176"
  "Access-Control-Request-Method" = "POST"
  "Access-Control-Request-Headers" = "content-type"
}
Invoke-WebRequest -Method Options -Headers $headers "http://127.0.0.1:8000/api/v1/chat"
```
