# 測試網、Paper-live、Autonomous 與實盤交易操作手冊

> **套件版本**：v2.1  
> **範圍**：如何啟動、停止、檢查與排查 `trade` 與 `autonomous`。  
> **更新日期**：2026-07-11  
> **方向權威**：[`../CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)  
> **現況權威**：[`../PROJECT_STATUS.md`](../PROJECT_STATUS.md)  
> **本階段原則**：先把 **虛擬帳戶／Paper 上的預設自主流程** 跑通並記帳正確；再 testnet；最後才 live。  
> **進 live 前**：readiness-gate、固定區間歷史回測、pretrade、風控與長時間觀察。  
> **驗收**：真實 CLI 與產物；**不用** pytest。多帳戶等商用周邊**非本手冊本階段重點**。

---

## 目錄

1. [現行方向與單一自主決策線（必讀）](#1-現行方向與單一自主決策線必讀)
   - [1.1 本階段要證明什麼](#11-本階段要證明什麼)
   - [1.2 入口責任](#12-入口責任)
2. [前置檢查](#2-前置檢查)
3. [Testnet 啟動](#3-testnet-啟動)
4. [Paper-live 行情觀測](#4-paper-live-行情觀測)
5. [Autonomous 自主流程（唯一決策線）](#5-autonomous-自主流程唯一決策線)
   - [5.1 Advisor](#51-advisor-模式預設不送單)
   - [5.2 Paper-auto](#52-paper-auto-模式工程自主主路徑)
   - [5.3 Ledger 與 outcome](#53-ledger-與-outcome)
   - [5.4 不建議的操作](#54-不建議的操作)
6. [API 啟停交易](#6-api-啟停交易)
7. [Live 前必做檢查](#7-live-前必做檢查)
8. [Live 啟動](#8-live-啟動)
9. [緊急停止](#9-緊急停止)
10. [常見問題](#10-常見問題)

---

## 1. 現行方向與單一自主決策線（必讀）

### 1.1 本階段要證明什麼

| 要 | 不要 |
|----|------|
| 工程自主：會自己跑、真下平、帳對 | 用未訓練模型盈虧證明「AI 很強」 |
| 日常：Paper／虛擬帳戶真實時序 | 用單元測試檔充當時機驗收 |
| 長期：先下載歷史再回測 | 把多帳戶／API 認證當本階段阻塞 |

優先順序：工程自主 → 穩定 → 訓練改善 → 終局邊跑邊學。見 [`CURRENT_DIRECTION.md`](../CURRENT_DIRECTION.md)。

### 1.2 入口責任

自動決策與下單只有 `autonomous` 一條線。`trade`／API trade manager 僅保留行情觀測與 VirtualAccount 價格同步。

| 維度 | `trade`（觀測） | `autonomous`（**唯一 AI 自主**） |
|------|-----------------|------------------------------------------|
| CLI | `python main.py trade ...` | `python main.py autonomous ...` |
| 執行核心 | TradingEngine `start_market_observer()` + WebSocket | AutonomousOperator 規劃 + **共用** TradingEngine paper |
| 長時間 | tick 長駐 | `--cycles N`（N>1）`run_forever` |
| LoRA / Memory | 不產生交易樣本 | ✅ **經 shared 平倉回調**進引擎鏈 |
| Decision Ledger | ❌ | ✅ |
| Paper 下單 | 不下單 | `--mode paper_auto` + `--execute-paper` |

**唯一自主執行層（勿寫成「永遠獨立帳戶、無學習」）**：

- quantity 優先 pretrade；無效 fallback notional fraction  
- 已有持倉：`skipped=existing_position`  
- 平倉：shared callback → 引擎學習鏈 + ledger + calibrator  
- 卡單／反思參數見 04 手冊  
- `testnet_auto`／`live_guarded`：依實作可能**不直接送單**，以 CLI 說明與 ledger 為準  

完整參數：[04_CLI_OPERATION.md](04_CLI_OPERATION.md)。

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

## 4. Paper-live 行情觀測

Paper-live 是即時 tick 觀測入口：行情使用 Binance mainnet public data，僅同步本地 `VirtualAccount` 的價格，**不產生訊號、不下單、不寫入學習樣本**。

**預設 AI 自主長跑**請優先看第 5 節 `autonomous`。
CLI：

```powershell
python main.py trade --symbol BTCUSDT --paper-live --paper-balance 10000
```

成功標準：

- 看到 paper-live / 虛擬實盤模式啟動。
- 可用 `Ctrl+C` 停止；不會出現本入口產生的訂單紀錄。

2026-05-19 本機 API 已完成短流程驗證：`mode=paper_live` 可啟動，狀態顯示 `running=true`、`engine.ai_model_loaded=true`、`engine.paper_trading=true`、paper account balance `10000`；隨後呼叫 `/api/v1/trade/stop` 可停止並回到 `running=false`。這只代表啟停與本地虛擬執行層可用，不代表已完成長時間績效驗證。

API：

```powershell
$body = @{
  symbol = "BTCUSDT"
  testnet = $false
  mode = "paper_live"
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

---

## 5. Autonomous 自主流程（唯一決策線）

`autonomous` 是唯一 AI 自主入口：規劃 → pretrade → adaptation →（可選）paper 執行 → ledger。
Paper **不是**另一套永久隔離的交易島，而是透過 **共用 TradingEngine** 下單與平倉回調（學習鏈 + ledger）。

> **目前驗收範圍（2026-07-19）**：僅執行本章 CLI／Paper 流程與產物對帳；前端與 Docker 暫停至核心流程收尾。

建議順序：

1. advisor 單輪確認規劃鏈  
2. `paper_auto --execute-paper --cycles N` 驗工程自主與記帳  
3. 需要 tick 級觀測才另開 `trade --paper-live`；它不參與決策
4. 流程穩後再開滿在線改善／基線訓練  

### 5.1 Advisor 模式（預設，不送單）

```powershell
python main.py autonomous --mode advisor --market-source live --symbol BTCUSDT --output output\autonomous_advisor.json
```

終端常見欄位：

- `candidates`  
- `plan_status`、`plan_execution_ready`  
- `final_action`、`can_execute`、`risk_multiplier`、`confidence_floor`  
- `next_interval_minutes`、`reasons`（在 `adaptation` 內）  
- Pretrade 區塊（`pretrade_summary`）  

若 `final_action` 為 `advise_only`／`observe`，或 pretrade 為 WAIT／REJECT，本輪應停在觀察。
AI signal 為 `neutral`／HOLD 時，`pretrade_summary` 可為空，因為系統不應以預設 BUY／SELL 繞過 AI 決策；這同樣是正確的安全結果。

### 5.2 Paper-auto 模式（工程自主主路徑）

```powershell
# 只決策、不送單
python main.py autonomous --mode paper_auto --symbol BTCUSDT --output output\autonomous_paper_auto.json

# 條件通過且 adaptation 允許時，送本機 paper 單
python main.py autonomous --mode paper_auto --market-source live --symbol BTCUSDT --execute-paper --paper-balance 10000

# 持續 N 輪（本階段核心驗收；輪間隔依 next_interval_minutes）
python main.py autonomous --mode paper_auto --symbol BTCUSDT --execute-paper --cycles 24 --paper-balance 10000

# AI 自主常駐（直到安全 STOP 或 Ctrl+C；不會設定 Windows 開機自啟）
python main.py autonomous --mode paper_auto --market-source live --execute-paper --forever --paper-balance 10000
```

成功時關注：

- 多輪是否跑完或合理 STOP  
- `paper_execution`：symbol、side、qty、`quantity_source`、order status  
- `quantity_source=pretrade_quantity` 為優先；`notional_fraction` 表示 fallback  
- `skipped=existing_position` 為已有持倉的預期行為  
- **正確證據**：ledger 決策與帳戶變化可對（見 CURRENT_DIRECTION）  
- `trained: false` 時不把盈虧當智能達標  

可選：`--max-position-hold-cycles`、`--reflect-every`（以 `-h` 為準）。

### 5.3 Ledger 與 outcome

預設路徑：

```text
data\bioneuronai\planning\autonomous\decision_ledger.jsonl
```

```powershell
Get-Content data\bioneuronai\planning\autonomous\decision_ledger.jsonl -Tail 5
```

- 每輪 append 決策紀錄（如 `autonomous_cycle`）  
- 平倉後可有 `trade_outcome`（供 AdaptationController 連敗／回撤規則）  
- 平倉同時走 shared callback → 引擎側 memory／LoRA／Hub（是否寫入持久狀態依執行設定；流程未穩時可先以記帳為準）  

自訂：`--ledger-path <path>`。

### 5.4 不建議的操作

- 將 `trade --paper-live` 誤認為可下單入口；下單只由 `autonomous` 產生
- 假設 `testnet_auto`／`live_guarded` 一定會自動下單（以實作與 ledger 為準，常為需人工確認）  
- 用 pytest 代替本節真實操作  
- 在記帳未對前，把 LoRA／Hub 狀態變化當成「已改善成功」的唯一證據  

---

## 6. API 啟停交易

API 的 `testnet_auto`、`live_auto` 與 `auto_trade=true` 已被明確拒絕；此入口只啟動行情觀測。自主 paper 執行請使用第 5 節的 CLI。

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

`trade --live` 與 API `live_auto` 不再是自動下單入口。正式網執行尚未開放；須先完成 paper 長跑、重啟對帳與模型治理 gate。本節的舊 live 範例僅保留作環境設定參考，不能用於送單。

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

API 目前只能啟動觀測；paper 自動執行必須從 CLI `autonomous` 進入。

---

## 9. 緊急停止與應急（從舊 SOP 併入）

下列清單取自舊 `CRYPTO_TRADING_SOP` 應急章，已改寫為**實際操作**（CLI／交易所畫面），不依賴測試檔。

### 9.1 停止本系統

CLI 模式：

```text
Ctrl+C
```

API 模式：

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/trade/stop" -Method POST
```

確認是否仍有交易程序：

```powershell
Get-CimInstance Win32_Process -Filter "name = 'python.exe'" |
  Where-Object { $_.CommandLine -like '*main.py trade*' -or $_.CommandLine -like '*uvicorn*bioneuronai.api.app*' -or $_.CommandLine -like '*main.py autonomous*' } |
  Select-Object ProcessId, CommandLine
```

### 9.2 API／連線中斷（持倉保護）

1. **立即評估**：網路、Binance 狀態頁、是否僅本機程式斷線。  
2. **保護持倉**：用 Binance Web／App 確認持倉與 SL/TP 是否仍在；必要時手動補保護單。  
3. **應急**：無法恢復且風險升高 → App 手動減倉／平倉；記錄時間與原因。  
4. **事後**：對帳 ledger／virtual account／交易所；再重啟 paper 或 testnet，**不要**在未對帳時開滿 LoRA。

### 9.3 市場極端行情（瀑布／閃崩）

| 現象 | 立即動作 |
|------|----------|
| 短時間單邊暴漲跌、成交量暴增 | **暫停新開倉**（停 `autonomous --execute-paper`） |
| 止損可能被穿透 | 交易所端檢查並手動平倉或收緊保護 |
| 長影線閃崩後快速恢復 | 勿立刻報復性重進；先等穩定再決定 |
| 資金費率極端 | 評估是否在收費前減倉；**不以費率本身當交易理由** |

### 9.4 帳戶安全

收到可疑登入通知時（分鐘級）：

1. 改密碼／撤銷 API key、檢查持倉與提現紀錄。  
2. 必要時先手動平倉，再重發新 key 寫入 `.env`。  
3. 本系統重啟前執行 `python main.py status` 與 `pretrade`。

考古原文：`docs/archive/recovered_from_git/docs_v3/CRYPTO_TRADING_SOP.md` §應急。

---

## 10. 常見問題

| 問題 | 可能原因 | 處理 |
|---|---|---|
| 無法讀取帳戶 | API key 錯誤、權限不足、testnet/mainnet 不一致 | 重新確認 `.env` 與 Binance 權限 |
| `pretrade` 一直 REJECT | 餘額不足、風控條件不通過、新聞/RAG 風險 | 依 reject 理由處理，不要繞過 |
| `autonomous` 有結果但沒有真的開始監控 | 正常；單輪 advisor 只做一輪決策 | 長時間自主使用 `--market-source live --cycles N` |
| autonomous paper 倉位與 pretrade 不符 | pretrade quantity 無效，fallback `notional_fraction` | 檢查 pretrade 輸出；確認 `quantity_source` |
| 同 symbol 重複進場 | 2026-06-15 已跳過（`skipped=existing_position`） | 檢查 autonomous ledger 與 VirtualAccount 狀態 |
| `reflect` 樣本不足 | EpisodicMemory 空 | 先跑能真正平倉的 autonomous paper 累積記錄 |
| start 後無法再次 start | API 交易 task 已在運行 | 先呼叫 `/api/v1/trade/stop` |
| trade paper-live 沒有訂單 | 正常；它只同步價格 | 用 autonomous paper 的 ledger 與 paper log 驗證成交 |
| testnet 可用但 live 不可用 | 正式期貨帳戶未開通或未入金 | 到 Binance 檢查 Futures 狀態 |
