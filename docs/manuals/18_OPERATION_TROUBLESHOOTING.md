# 使用者操作排查手冊

> 範圍：使用者照手冊操作時遇到的常見問題。

---

## 📑 目錄

- [1. 先做最小檢查](#1-先做最小檢查)
- [2. CLI 問題](#2-cli-問題)
- [3. Backtest 問題](#3-backtest-問題)
- [4. API 問題](#4-api-問題)
- [5. News / Plan / Pretrade 問題](#5-news-plan-pretrade-問題)
- [6. 程序殘留](#6-程序殘留)
- [7. 何時不要繼續](#7-何時不要繼續)

---

## 1. 先做最小檢查

```powershell
python main.py --help
python main.py status
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

這三個命令能成功，代表 CLI、核心模組與本地資料基本可用。

---

## 2. CLI 問題

| 現象 | 可能原因 | 處理 |
|---|---|---|
| `python` 找不到 | Python 未加入 PATH | 重新安裝或使用正確 Python |
| `ModuleNotFoundError` | 沒在專案根目錄或未安裝 | 回到專案根目錄，執行 `pip install -e .` |
| 指令參數錯誤 | 命令格式不符 | 先跑 `python main.py <command> --help` |
| 指令卡住 | 正在連外部 API 或監控交易 | 看輸出，必要時 `Ctrl+C` |

---

## 3. Backtest 問題

| 現象 | 可能原因 | 處理 |
|---|---|---|
| 找不到資料 | symbol/interval/date 不存在 | 先跑 `backtest-data` |
| 交易次數為 0 | 區間太短或策略沒有訊號 | 拉長區間或改用 `backtest` |
| 結果很差 | 策略在該區間表現差 | 不代表程式錯誤，需看長區間 |
| runtime 沒看到 | run 未完成或路徑看錯 | 查 `backtest/runtime/` |

---

## 4. API 問題

| 現象 | 可能原因 | 處理 |
|---|---|---|
| `Connection refused` | API 沒啟動 | 啟動 `uvicorn` |
| `/api/v1/status` 非 OK | 模組 import 失敗 | 看 API 終端輸出 |
| CORS 錯誤 | 前端 origin 未允許 | 設 `ALLOWED_ORIGINS` |
| trade start 失敗 | 已在運行或 key 不對 | 先 stop，再檢查 `.env` |

---

## 5. News / Plan / Pretrade 問題

| 現象 | 可能原因 | 處理 |
|---|---|---|
| news 文章數 0 | 免費 API 限制或近期無新聞 | 稍後重試或設定 token |
| plan 外部資料失敗 | 外部 API 暫時不可用 | 看是否有 graceful fallback |
| pretrade REJECT | 風控或帳戶條件未通過 | 按 reject 理由處理 |
| 餘額顯示 0 | API key 權限或帳戶無資金 | 檢查 Binance Futures |

---

## 6. 程序殘留

查看 uvicorn：

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*uvicorn*bioneuronai.api.app*' } |
  Select-Object ProcessId, CommandLine
```

停止 uvicorn：

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*uvicorn*bioneuronai.api.app*' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

---

## 7. 何時不要繼續

以下情況不要進 live：

- testnet 無法穩定啟停。
- `pretrade` 仍然 REJECT。
- 回測沒有完成。
- API key 權限不清楚。
- 不知道目前是否有交易程序在跑。
