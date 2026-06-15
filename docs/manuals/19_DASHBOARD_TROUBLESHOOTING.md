# Dashboard 操作排查手冊

> **套件版本**：v2.1
> **範圍**：`frontend/devops-d` 前端、API、CORS、WebSocket 排查
> **更新日期**：2026-06-15
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)

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
- `ready=true` 且 `blocking=[]`；若有 blocking，先依回應中的必要項目修正。

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
| Response 顯示大量 JSON | API raw response 正常顯示，不是亂碼 | 只要被限制在框內可捲動，即為正常 |
| JSON 蓋住下一個面板 | 前端仍在跑舊版或 JSONViewer 高度未生效 | 重新整理頁面；確認 `frontend/devops-d/src/components/JSONViewer.tsx` 已固定高度並重新跑 Vite |
| Request History 變成超長頁面 | 請求紀錄太多且容器未限制高度 | 2026-05-19 已修正為內部捲動；若仍發生，清除 history 或重新載入新版前端 |
| 想從 UI 跑 autonomous | Dashboard 無 B 線面板 | 用 CLI：`python main.py autonomous ...`；驗收 ledger |
| Paper live 與 autonomous paper 混淆 | 兩者不同連接器生命週期 | Trade Control = 主線 A；autonomous 僅 CLI |

### 版面檢查

若懷疑面板有覆蓋或撐版，先做以下確認：

1. 切換 `Operations`、`Validation`、`Config`、`Dev Tools`、`Chat`。
2. 觀察是否有卡片互相覆蓋，或頁面出現水平捲軸。
3. 在 `Dev Tools > Request History` 保留大量紀錄時，左右兩張卡片應固定高度，內容在面板內部捲動。

2026-05-19 已用本機瀏覽器檢查上述五個 tab：無卡片重疊、無水平撐版；`Request History` 大量紀錄時最大卡片高度維持在正常範圍。

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
