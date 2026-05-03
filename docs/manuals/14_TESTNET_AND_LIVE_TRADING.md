# 測試網與實盤交易操作手冊

> 範圍：使用者如何啟動、停止、檢查與排查 `trade` 相關操作。  
> 原則：先 testnet，後 live；未完成回測、pretrade 與風控確認前，不進 live。

---

## 📑 目錄

- [1. 前置檢查](#1-前置檢查)
- [2. Testnet 啟動](#2-testnet-啟動)
- [3. API 啟停交易](#3-api-啟停交易)
- [4. Live 前必做檢查](#4-live-前必做檢查)
- [5. Live 啟動](#5-live-啟動)
- [6. 緊急停止](#6-緊急停止)
- [7. 常見問題](#7-常見問題)

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

## 3. API 啟停交易

先啟動 API：

```powershell
python -m uvicorn bioneuronai.api.app:app --host 127.0.0.1 --port 8000
```

啟動交易：

```powershell
$body = @{
  symbol = "BTCUSDT"
  testnet = $true
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/trade/start" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

停止交易：

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/trade/stop" `
  -Method POST
```

成功標準：

- start 回應成功或明確告知已在運行。
- stop 後交易 task 被清除。

---

## 4. Live 前必做檢查

Live 不是日常驗證入口。啟動前必須完成：

1. `02_STARTUP_AND_SHUTDOWN.md` Level 0 / Level 1 驗證。
2. `08_BACKTEST_SYSTEM.md` 指定區間回測。
3. `09_ANALYSIS_MODULE.md` 的 `pretrade` 檢查。
4. `11_RISK_MANAGEMENT.md` 的風險參數確認。
5. testnet 可啟動、可停止，沒有殘留程序。
6. 人工確認最大槓桿、單筆最大風險、每日最大風險。

---

## 5. Live 啟動

`.env` 應設定：

```dotenv
BINANCE_TESTNET=false
BINANCE_API_KEY=your_live_key
BINANCE_API_SECRET=your_live_secret
```

啟動：

```powershell
python main.py trade --symbol BTCUSDT --live
```

系統會要求輸入 `YES` 二次確認。未確認前不會進入 live。

---

## 6. 緊急停止

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

## 7. 常見問題

| 問題 | 可能原因 | 處理 |
|---|---|---|
| 無法讀取帳戶 | API key 錯誤、權限不足、testnet/mainnet 不一致 | 重新確認 `.env` 與 Binance 權限 |
| `pretrade` 一直 REJECT | 餘額不足、風控條件不通過、新聞/RAG 風險 | 依 reject 理由處理，不要繞過 |
| start 後無法再次 start | API 交易 task 已在運行 | 先呼叫 `/api/v1/trade/stop` |
| testnet 可用但 live 不可用 | 正式期貨帳戶未開通或未入金 | 到 Binance 檢查 Futures 狀態 |
