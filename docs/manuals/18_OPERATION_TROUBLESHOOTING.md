# 使用者操作排查手冊

> **套件版本**：v2.1
> **更新日期**：2026-06-15
> **範圍**：CLI、API、回測、交易主線操作排查
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)

---

## 目錄

1. [最小檢查](#1-最小檢查)
2. [CLI 問題](#2-cli-問題)
3. [雙主線混淆](#3-雙主線混淆)
4. [Backtest 問題](#4-backtest-問題)
5. [API 問題](#5-api-問題)
6. [News / Plan / Pretrade](#6-news--plan--pretrade)
7. [程序殘留](#7-程序殘留)
8. [何時不要繼續](#8-何時不要繼續)

---

## 1. 最小檢查

```powershell
python main.py --help
python main.py status
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

三者成功代表 CLI、核心模組與本地 replay 資料基本可用。

---

## 2. CLI 問題

| 現象 | 可能原因 | 處理 |
|------|----------|------|
| `python` 找不到 | PATH | 安裝 Python 3.13 並加入 PATH |
| `ModuleNotFoundError: bioneuronai` | 未在 repo 根或未安裝 | `pip install -e .`；用 `python main.py` |
| `pip install -e ".[rl]"` 失敗 | 無 `[rl]` extra | 改為 `pip install -e .` |
| 參數錯誤 | 格式不符 | `python main.py <cmd> --help` |
| 指令卡住 | 監控/外部 API | 看輸出；`Ctrl+C` |

---

## 3. 雙主線混淆

| 現象 | 解讀 | 處理 |
|------|------|------|
| `autonomous` 跑完但沒監控 | 正常；單輪 advisor 不啟動引擎 | 長時間用 `trade --paper-live` |
| 有 ledger 但 LoRA 沒更新 | B 線無 LoRA | 用主線 A paper-live 驗證學習 |
| paper 倉位與 pretrade 不符 | pretrade quantity 無效，fallback `notional_fraction` | 檢查 `paper_execution.quantity_source` |
| UI 找不到 autonomous | API/UI 未覆蓋 B 線 | 用 CLI + ledger |
| 同 symbol 重複持倉 | 2026-06-15 已跳過（`skipped=existing_position`） | 避免 A/B 並行於不同 connector |
| `reflect` 樣本不足 | EpisodicMemory 空 | 先跑 `trade --paper-live` |

詳見 [04_CLI_OPERATION.md](04_CLI_OPERATION.md) §2、[14_TESTNET_AND_LIVE_TRADING.md](14_TESTNET_AND_LIVE_TRADING.md)。

---

## 4. Backtest 問題

| 現象 | 可能原因 | 處理 |
|------|----------|------|
| 找不到資料 | symbol/interval/日期 | `backtest-data`；見 [15_DATA_ACQUISITION.md](15_DATA_ACQUISITION.md) |
| `simulate` 交易次數 0 | 設計如此（只統計信號） | 改用 `backtest` 要 mock 成交 |
| `backtest` 交易次數 0 | 區間太短/無訊號 | 拉長區間；查 `ai_ready` |
| runtime 空 | run 失敗 | 查終端錯誤；`backtest-runs` |
| readiness-gate FAIL | 矩陣未過門檻 | 看 case detail；補資料 |

---

## 5. API 問題

| 現象 | 可能原因 | 處理 |
|------|----------|------|
| Connection refused | API 未啟動 | `uvicorn bioneuronai.api.app:app` |
| `ready: false` | blocking 項目 | 依 `/api/v1/status` 的 `blocking` 修正 |
| CORS | origin 未允許 | `ALLOWED_ORIGINS` 含實際 Vite URL |
| trade start 失敗 | 已在運行或 key 錯 | 先 `trade/stop`；查 `.env` |
| 想 API 跑 autonomous | 無端點 | 改 CLI |

---

## 6. News / Plan / Pretrade

| 現象 | 可能原因 | 處理 |
|------|----------|------|
| news 0 篇 | 免費 API/無新聞 | 設 `CRYPTOPANIC_API_TOKEN` 或稍後重試 |
| plan 外部失敗 | 第三方 API | 看 CLI 是否標 `DATA_UNAVAILABLE` |
| pretrade REJECT | 風控/餘額 | 依理由處理，勿繞過 |
| Futures 餘額 0 | mainnet 無入金 | testnet 或劃轉資金 |

pretrade 風控層見 [11_RISK_MANAGEMENT.md](11_RISK_MANAGEMENT.md) §8。

---

## 7. 程序殘留

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*uvicorn*bioneuronai*' -or $_.CommandLine -like '*main.py trade*' } |
  Select-Object ProcessId, CommandLine
```

必要時 `Stop-Process -Id <pid> -Force`。

---

## 8. 何時不要繼續

勿進 live 若：

- testnet / paper-live 無法穩定啟停
- `pretrade` 持續 REJECT
- readiness-gate 或長區間回測未完成
- 不確定是否有交易程序在跑
- 混淆 autonomous 結果與 TradingEngine 監控狀態