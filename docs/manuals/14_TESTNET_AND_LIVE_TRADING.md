# 測試網、Paper-live 與實盤交易操作手冊

> 範圍：使用者如何啟動、停止、檢查與排查 `trade` 相關操作。  
> 更新日期：2026-05-13
> 原則：先 monitor/paper-live，再 testnet，最後才 live；未完成回測、pretrade 與風控確認前，不進 live。

---

## 📑 目錄

- [1. 前置檢查](#1-前置檢查)
- [2. Testnet 啟動](#2-testnet-啟動)
- [3. Paper-live 啟動](#3-paper-live-啟動)
- [4. API 啟停交易](#4-api-啟停交易)
- [5. Live 前必做檢查](#5-live-前必做檢查)
- [6. Live 啟動](#6-live-啟動)
- [7. 緊急停止](#7-緊急停止)
- [8. 常見問題](#8-常見問題)

---

## 1. 前置檢查

在專案根目錄：

```powershell
python main.py status
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

成功標準：

- `status` 顯示核心模組 OK。
- `backtest-data` 能列出本地歷史資料。

確認 `.env` 存在：

```powershell
Test-Path .env
```

不要把 API key 寫進文件或提交到 Git。

---

## 2. Testnet 啟動

`.env` 應設定：

```dotenv
BINANCE_TESTNET=true
BINANCE_API_KEY=your_testnet_key
BINANCE_API_SECRET=your_testnet_secret
```

啟動：

```powershell
python main.py trade --symbol BTCUSDT --testnet
```

成功標準：

- TradingEngine 初始化成功。
- 能讀取價格或進入監控流程。
- 可用 `Ctrl+C` 停止。

---

## 3. Paper-live 啟動

Paper-live 是目前建議的長時間觀察入口：行情使用 Binance mainnet public market data，但下單只進本地 `VirtualAccount`，不送出 Binance order API。

CLI：

```powershell
python main.py trade --symbol BTCUSDT --paper-live --paper-balance 10000
```

成功標準：

- 看到 paper-live / 虛擬實盤模式啟動。
- AI 模型預設載入，狀態可看到 `ai_model_loaded=true`。
- log 目錄位於 `data/bioneuronai/trading/paper_live/`。
- 任何訂單紀錄都寫入本地 JSONL，不會送到 Binance。

API：

```powershell
$body = @{
  symbol = "BTCUSDT"
  testnet = $false
  mode = "paper_live"
  paper_initial_balance = 10000
  auto_trade = $true
  load_ai_model = $true
  model_name = "my_100m_model"
  warmup_model = $false
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/trade/start" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

---

## 4. API 啟停交易

先啟動 API：

```powershell
python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
```

啟動交易：

```powershell
$body = @{
  symbol = "BTCUSDT"
  testnet = $true
  mode = "monitor_only"
  paper_initial_balance = 10000
  auto_trade = $false
  load_ai_model = $true
  model_name = "my_100m_model"
  warmup_model = $false
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/trade/start" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

查詢狀態：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/trade/status" `
  -Method GET
```

停止交易：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/trade/stop" `
  -Method POST
```

成功標準：

- start 回應成功或明確告知已在運行。
- status 可看到 `running`、`mode`、`engine.auto_trade`、`engine.ai_model_loaded`。
- stop 後交易 task 被清除。

---

## 5. Live 前必做檢查

Live 不是日常驗證入口。啟動前必須完成：

1. `02_STARTUP_AND_SHUTDOWN.md` Level 0 / Level 1 驗證。
2. `08_BACKTEST_SYSTEM.md` 指定區間回測。
3. `09_ANALYSIS_MODULE.md` 的 `pretrade` 檢查。
4. `11_RISK_MANAGEMENT.md` 的風險參數確認。
5. paper-live 已連續運行足夠時間，且本地 paper ledger 訂單/持倉符合預期。
6. testnet 可啟動、可停止，沒有殘留程序。
7. 人工確認最大槓桿、單筆最大風險、每日最大風險。

---

## 6. Live 啟動

`.env` 應設定：

```dotenv
BINANCE_TESTNET=false
BINANCE_API_KEY=your_live_key
BINANCE_API_SECRET=your_live_secret
ALLOW_LIVE_TRADING=1
```

API 啟動：

```powershell
$body = @{
  symbol = "BTCUSDT"
  testnet = $false
  mode = "live_auto"
  paper_initial_balance = 10000
  auto_trade = $true
  load_ai_model = $true
  model_name = "my_100m_model"
  warmup_model = $false
  confirm_live = "I_UNDERSTAND_LIVE_RISK"
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/trade/start" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

CLI live 啟動仍需依 `main.py trade --live` 的互動確認流程；API / UI 路線則由 `ALLOW_LIVE_TRADING=1` 與 `confirm_live=I_UNDERSTAND_LIVE_RISK` 雙重限制。

---

## 7. 緊急停止

CLI 模式：

```text
Ctrl+C
```

API 模式：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/trade/stop" -Method POST
```

Docker 模式：

```powershell
docker compose stop trade
```

確認是否仍有交易程序：

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*main.py trade*' -or $_.CommandLine -like '*uvicorn*bioneuronai.api.app*' } |
  Select-Object ProcessId, CommandLine
```

---

## 8. 常見問題

| 問題 | 可能原因 | 處理 |
|---|---|---|
| 無法讀取帳戶 | API key 錯誤、權限不足、testnet/mainnet 不一致 | 重新確認 `.env` 與 Binance 權限 |
| `pretrade` 一直 REJECT | 餘額不足、風控條件不通過、新聞/RAG 風險 | 依 reject 理由處理，不要繞過 |
| start 後無法再次 start | API 交易 task 已在運行 | 先呼叫 `/api/v1/trade/stop` |
| paper-live 有訂單但 Binance 沒成交 | 正常；paper-live 只寫本地虛擬帳戶 | 查看 `data/bioneuronai/trading/paper_live/` |
| testnet 可用但 live 不可用 | 正式期貨帳戶未開通或未入金 | 到 Binance 檢查 Futures 狀態 |
