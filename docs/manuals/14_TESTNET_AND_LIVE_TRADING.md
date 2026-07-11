# 測試網、Paper-live、Autonomous 與實盤交易操作手冊

> **套件版本**：v2.1
> **範圍**：使用者如何啟動、停止、檢查與排查 `trade` 與 `autonomous` 相關操作。
> **更新日期**：2026-06-15
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)
> **原則**：先 paper-live，再 testnet，最後才 live；未完成 readiness-gate、固定區間回測、pretrade、風控與長時間觀察前，不進 live。

---

## 目錄

1. [雙執行主線（必讀）](#1-雙執行主線必讀)
2. [前置檢查](#2-前置檢查)
3. [Testnet 啟動](#3-testnet-啟動)
4. [Paper-live 啟動](#4-paper-live-啟動)
5. [Autonomous 值班](#5-autonomous-值班)
6. [API 啟停交易](#6-api-啟停交易)
7. [Live 前必做檢查](#7-live-前必做檢查)
8. [Live 啟動](#8-live-啟動)
9. [緊急停止](#9-緊急停止)
10. [常見問題](#10-常見問題)

---

## 1. 雙執行主線（必讀）

本手冊涵蓋兩條**不同**的執行路徑，請勿混用驗收標準：

| 維度 | 主線 A：`trade` | 主線 B：`autonomous` |
|------|----------------|----------------------|
| CLI 入口 | `python main.py trade ...` | `python main.py autonomous ...` |
| 執行核心 | `TradingEngine` + WebSocket | `AutonomousOperator` 規劃迴圈 |
| 長時間監控 | ✅ 預設用途 | ❌ 除非 `--cycles N` 定時迴圈 |
| LoRA / EpisodicMemory | ✅（paper-live 平倉） | ❌ |
| Decision Ledger | ❌ | ✅ `decision_ledger.jsonl` |
| Paper 下單 | `--paper-live`（引擎內） | `--execute-paper`（獨立 paper 連接器） |

**主線 B 執行層（2026-06-15）**：
- `--execute-paper` **優先**採 pretrade `order_parameters.quantity`（× `risk_multiplier`）；無效時 fallback `--paper-notional-fraction`
- 已有持倉時跳過進場（`paper_execution.skipped=true`，`reason=existing_position`）
- 平倉回填 `confidence_calibrator.record_outcome_by_index()`
- 卡單平倉：`--max-position-hold-cycles`；反思：`--reflect-every`（需 `--cycles >1`）；獨立 `python main.py reflect`
- `testnet_auto` / `live_guarded` 模式 v1 **不直接送單**，僅標記需人工確認

完整參數表見 [04_CLI_OPERATION.md](04_CLI_OPERATION.md) §5。

---

## 2. 前置檢查

在專案根目錄：

```powershell
python main.py status
python main.py backtest-data --symbol BTCUSDT --interval 1h
```

成功標準：

- `status` 顯示核心模組 OK。
- `backtest-data` 能列出本地歷史資料。

日常不接交易所時只保留 `.env.example`。要進行 testnet 或 live 驗證時，才由範本建立 `.env`：

```powershell
Copy-Item .env.example .env
```

確認 `.env` 已建立：

```powershell
Test-Path .env
```

不要把 API key 寫進文件或提交到 Git。

---

## 3. Testnet 啟動

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

## 4. Paper-live 啟動

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

2026-05-19 本機 API 已完成短流程驗證：`mode=paper_live` 可啟動，狀態顯示 `running=true`、`engine.ai_model_loaded=true`、`engine.paper_trading=true`、paper account balance `10000`；隨後呼叫 `/api/v1/trade/stop` 可停止並回到 `running=false`。這只代表啟停與本地虛擬執行層可用，不代表已完成長時間績效驗證。

API：

```powershell
$body = @{
  symbol = "BTCUSDT"
  testnet = $false
  mode = "paper_live"
  paper_initial_balance = 10000
  auto_trade = $true
  load_ai_model = $true
  model_name = "unified_v2_100m"
  warmup_model = $false
} | ConvertTo-Json

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/trade/start" `
  -Method POST `
  -Body $body `
  -ContentType "application/json"
```

---

## 5. Autonomous 值班

`autonomous` 是**規劃與決策**入口，不是 `TradingEngine` 的替代品。日常建議：先跑 advisor 單輪，再依 `final_action` 決定是否進 `trade --paper-live` 或 `autonomous --execute-paper`。

### Advisor 模式（預設，不送單）

```powershell
python main.py autonomous --mode advisor --symbol BTCUSDT --output output\autonomous_advisor.json
```

終端機輸出欄位（JSON 對應欄位見括號）：

- `candidates`
- `plan_status`、`plan_execution_ready`
- `final_action`、`can_execute`、`risk_multiplier`、`confidence_floor`
- `next_interval_minutes`、`reasons`（在 `adaptation` 內）
- **Pretrade** 區塊（JSON：`pretrade_summary`，每 symbol 的 status / score）

若 `final_action` 為 `advise_only` / `observe`，或 pretrade 顯示 `WAIT` / `REJECT`，本輪應停在觀察。

### Paper-auto 模式

```powershell
# 只決策、不送單
python main.py autonomous --mode paper_auto --symbol BTCUSDT --output output\autonomous_paper_auto.json

# 條件通過且 adaptation 允許時，送本機 paper 單（需明確旗標）
python main.py autonomous --mode paper_auto --symbol BTCUSDT --execute-paper --paper-balance 10000

# 持續 N 輪（輪間隔由 next_interval_minutes 決定）
python main.py autonomous --mode paper_auto --symbol BTCUSDT --execute-paper --cycles 24
```

送單後若有成交，終端機會印 **Paper Execution**（`paper_execution`：symbol、side、qty、`quantity_source`、order status）。驗收時確認 `quantity_source=pretrade_quantity`；若為 `notional_fraction` 表示 pretrade quantity 無效而 fallback。

### Ledger 與 outcome

預設路徑：

```text
data\bioneuronai\planning\autonomous\decision_ledger.jsonl
```

```powershell
Get-Content data\bioneuronai\planning\autonomous\decision_ledger.jsonl -Tail 5
```

每輪會 append `autonomous_cycle`；平倉結算後會 append `trade_outcome`（供 AdaptationController 讀取連敗/回撤規則）。

自訂路徑：`--ledger-path <path>`。

### 不建議的操作

- 用 autonomous 結果驗證 LoRA 是否更新（LoRA 只走主線 A）
- 同 symbol 同時跑 `trade --paper-live` 與 `autonomous --execute-paper` 而不檢查持倉
- 假設 `testnet_auto` / `live_guarded` 會自動下單（v1 不送單）

---

## 6. API 啟停交易

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
  model_name = "unified_v2_100m"
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

## 7. Live 前必做檢查

Live 不是日常驗證入口。啟動前必須完成：

1. `02_STARTUP_AND_SHUTDOWN.md` Level 0 / Level 1 驗證。
2. `08_BACKTEST_SYSTEM.md` 指定區間回測。
3. `09_ANALYSIS_MODULE.md` 的 `pretrade` 檢查。
4. `11_RISK_MANAGEMENT.md` 的風險參數確認。
5. paper-live 已連續運行足夠時間，且本地 paper ledger 訂單/持倉符合預期。
6. testnet 可啟動、可停止，沒有殘留程序。
7. 人工確認最大槓桿、單筆最大風險、每日最大風險。

---

## 8. Live 啟動

Testnet 的 `.env` 應設定：

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
  model_name = "unified_v2_100m"
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

## 9. 緊急停止

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

## 10. 常見問題

| 問題 | 可能原因 | 處理 |
|---|---|---|
| 無法讀取帳戶 | API key 錯誤、權限不足、testnet/mainnet 不一致 | 重新確認 `.env` 與 Binance 權限 |
| `pretrade` 一直 REJECT | 餘額不足、風控條件不通過、新聞/RAG 風險 | 依 reject 理由處理，不要繞過 |
| `autonomous` 有結果但沒有真的開始監控 | 正常；單輪 advisor 不啟動 TradingEngine | 長時間監控用 `trade --paper-live`；定時規劃用 `--cycles N` |
| autonomous paper 倉位與 pretrade 不符 | pretrade quantity 無效，fallback `notional_fraction` | 檢查 pretrade 輸出；確認 `quantity_source` |
| 同 symbol 重複進場 | 2026-06-15 已跳過（`skipped=existing_position`） | 若仍發生，檢查是否雙主線並行於不同 connector |
| `reflect` 樣本不足 | EpisodicMemory 空 | 先跑 `trade --paper-live` 累積平倉記錄 |
| start 後無法再次 start | API 交易 task 已在運行 | 先呼叫 `/api/v1/trade/stop` |
| paper-live 有訂單但 Binance 沒成交 | 正常；paper-live 只寫本地虛擬帳戶 | 查看 `data/bioneuronai/trading/paper_live/` |
| testnet 可用但 live 不可用 | 正式期貨帳戶未開通或未入金 | 到 Binance 檢查 Futures 狀態 |
