# 環境變數操作手冊

> **套件版本**：v2.1
> **範圍**：`.env.example` 與何時建立 `.env`（不記錄真實密鑰）
> **更新日期**：2026-06-15
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)

---

## 📑 目錄

- [1. 預設只保留 .env.example](#1-預設只保留-envexample)
- [2. 常用變數](#2-常用變數)
- [3. Testnet 建議設定](#3-testnet-建議設定)
- [4. Live 前確認](#4-live-前確認)
- [5. 安全檢查](#5-安全檢查)
- [6. 常見問題](#6-常見問題)

---

## 1. 預設只保留 `.env.example`

日常開發、閱讀手冊、執行不需要金鑰的 CLI 時，根目錄只保留 `.env.example`。

只有要使用 Binance、GCP Secret Manager、testnet 或 live 交易時，才由範本建立正式 `.env`：

```powershell
Copy-Item .env.example .env
```

確認 `.env` 已建立：

```powershell
Test-Path .env
```

---

## 2. 常用變數

| 變數 | 用途 | 是否敏感 |
|---|---|---|
| `BINANCE_API_KEY` | Binance API key | 是 |
| `BINANCE_API_SECRET` | Binance API secret | 是 |
| `BINANCE_TESTNET` | `true` 測試網，`false` 正式網 | 否 |
| `ALLOW_LIVE_TRADING` | API / UI 正式網自動交易開關；只有設為 `1` / `true` / `yes` 才允許 `live_auto` | 否 |
| `ALLOWED_ORIGINS` | API CORS allowlist | 否 |
| `API_PORT` | Docker API 對外 port | 否 |
| `FRONTEND_PORT` | Docker frontend 對外 port | 否 |
| `VITE_API_BASE_URL` | 前端 build 時寫入的 API URL | 否 |
| `MODEL_PATH` / `MODEL_DIR` | 模型權重位置；可為本機路徑或 `gs://` 路徑 | 否 |
| `TRAINING_OUTPUT_URI` | 雲端訓練完成後同步 artifacts 的 `gs://bucket/prefix` | 否 |
| `BIONEURONAI_DB_PATH` | SQLite runtime DB 路徑；雲端容器應指向持久掛載 | 否 |
| `GCP_SECRET_MANAGER_ENABLED` | 設為 `1` 時允許程式直接讀 GCP Secret Manager；預設建議用 secret injection | 否 |
| `BINANCE_API_KEY_SECRET_NAME` / `BINANCE_API_SECRET_NAME` | GCP Secret Manager secret 名稱 | 是 |
| `TRADE_SYMBOL` | Docker trade 預設交易對 | 否 |
| `TRADE_ACTION` | Docker pretrade 預設方向 | 否 |
| `BACKTEST_SYMBOL` | Docker backtest 預設交易對 | 否 |
| `BACKTEST_INTERVAL` | Docker backtest K 線週期 | 否 |
| `BACKTEST_START` / `BACKTEST_END` | Docker backtest 日期區間 | 否 |
| `BACKTEST_BALANCE` | Docker backtest 初始資金 | 否 |
| `BACKTEST_WARMUP_BARS` | Docker backtest 預熱 K 線數量 | 否 |
| `SIM_BALANCE` / `SIM_BARS` | Docker simulate 初始資金與 K 線數 | 否 |
| `SIM_START` / `SIM_END` | Docker simulate 日期區間 | 否 |

---

## 3. Testnet 建議設定

```dotenv
BINANCE_TESTNET=true
ALLOW_LIVE_TRADING=0
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://127.0.0.1:5176
```

Testnet key 與 live key 不要混用。

若 `ALLOWED_ORIGINS` 未設定，API 預設允許本地 `3000`、`8080`、`5173-5180`，且同時允許 `localhost` 與 `127.0.0.1`。

---

## 4. Live 前確認

Live 前人工確認：

```dotenv
BINANCE_TESTNET=false
ALLOW_LIVE_TRADING=1
```

並確認：

- API key 是正式網 key。
- Futures 權限已開通。
- 帳戶有可用餘額。
- 已完成 testnet 與 pretrade 驗證。
- 已完成 **主線 A** `trade --paper-live` 長時間觀察；paper-live 不需要 `ALLOW_LIVE_TRADING=1`（不送真實訂單）。
- **主線 B** `autonomous` 與 `ALLOW_LIVE_TRADING` 無關；B 線 v1 的 `testnet_auto`/`live_guarded` 不直接送單。
- API / UI live 自動交易請求必須另外提供 `confirm_live=I_UNDERSTAND_LIVE_RISK`。

---

## 5. 安全檢查

若已建立 `.env`，確認它不會被提交：

```powershell
git check-ignore .env
```

成功標準：輸出 `.env`。若尚未建立 `.env`，這一步可略過。

若已建立 `.env`，只查看 key 名稱，不印出值：

```powershell
Get-Content .env |
  Where-Object { $_ -match "^[A-Za-z_][A-Za-z0-9_]*=" } |
  ForEach-Object { ($_ -split "=", 2)[0] }
```

---

## 6. 常見問題

| 問題 | 原因 | 處理 |
|---|---|---|
| CORS 錯誤 | `ALLOWED_ORIGINS` 未包含前端網址 | 加入目前瀏覽器實際 origin，例如 `http://127.0.0.1:5176` |
| Binance 驗證失敗 | key/secret 錯、testnet/live 不一致 | 檢查 `.env` 與 Binance 後台 |
| news 執行失敗 | CoinDesk 或 Google News RSS 無法取得／解析 | 檢查網路與來源回應；本輪會明確失敗，不使用替代來源 |
| Docker port 衝突 | 8000 或 3000 被占用 | 調整 `API_PORT`、`FRONTEND_PORT` |
