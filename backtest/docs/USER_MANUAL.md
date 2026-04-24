# Backtest Replay 使用者手冊

這份手冊是給使用者操作 `backtest/` 時看的。

重點只有三件事：

1. 怎麼啟動
2. 怎麼操作
3. 跑完之後去哪裡看結果

## 這個系統是做什麼的

`backtest/` 會用歷史市場資料來重放市場情境，讓專案在不連接即時市場的情況下也能運作。

它可以：

- 提供歷史 K 線資料
- 執行 simulate
- 執行 backtest
- 保存每次執行的結果
- 讓你從 CLI、API、UI 三種方式操作

它不會自己決定要不要交易。  
是否送出訂單，仍然由專案本身的策略流程決定。

補充：

- 目前 replay 也會被高階策略競爭層拿來做正式評估
- 但 replay 本身仍只是資料重放與模擬執行層，不是策略評分邏輯本身
- 如果你要的是策略模組操作，請改看 [策略模組操作手冊](C:/D/E/BioNeuronai/docs/STRATEGY_MODULE_USER_MANUAL.md)

## 資料放哪裡

目前正式歷史資料目錄是：

- `backtest/data/binance_historical/`

目前 replay 結果會寫到：

- `backtest/runtime/`

## 最常用的 4 個 CLI 指令

### 1. 查看目前可用的歷史資料

```powershell
python main.py backtest-data
```

如果想用 JSON 看：

```powershell
python main.py backtest-data --json
```

如果只看特定資料：

```powershell
python main.py backtest-data --symbol ETHUSDT --interval 1h
```

### 2. 執行 simulate

```powershell
python main.py simulate --symbol ETHUSDT --interval 1h --bars 50
```

常用參數：

- `--symbol`
- `--interval`
- `--bars`
- `--balance`
- `--start-date`
- `--end-date`

範例：

```powershell
python main.py simulate --symbol ETHUSDT --interval 15m --bars 200 --balance 50000
```

### 3. 執行 backtest

```powershell
python main.py backtest --symbol ETHUSDT --interval 1h
```

常用參數：

- `--symbol`
- `--interval`
- `--balance`
- `--start-date`
- `--end-date`
- `--warmup-bars`

範例：

```powershell
python main.py backtest --symbol ETHUSDT --interval 1h --start-date 2025-12-22 --end-date 2025-12-23 --balance 10000 --warmup-bars 10
```

### 4. 查看已經跑過的 replay 結果

列出最近幾次：

```powershell
python main.py backtest-runs --limit 10
```

查看指定 run：

```powershell
python main.py backtest-runs --run-id 20260404_212636_b152c139
```

如果想直接看 JSON：

```powershell
python main.py backtest-runs --run-id 20260404_212636_b152c139 --json
```

## UI 使用方式

### 啟動 API 服務

```powershell
uvicorn bioneuronai.api.app:app --host 0.0.0.0 --port 8000
```

如果你是在專案根目錄執行，並且 `src/` 已在目前環境可匯入，這條就可以用。

### 打開 UI

瀏覽器開：

- `http://127.0.0.1:8000/backtest/ui`

### UI 可以做什麼

- 看目前有哪些可用 dataset
- Inspect 某個 dataset 能不能被 replay 載入
- 直接執行 simulate
- 直接執行 backtest
- 看 recent runs
- 點某一筆 run 查看詳細結果

### UI 主要欄位

- `Dataset`
- `Symbol`
- `Interval`
- `Start Date`
- `End Date`
- `Balance`
- `Warmup Bars`
- `Bars`

## API 使用方式

### 1. 查看資料 catalog

`GET /api/v1/backtest/catalog`

### 2. 檢查某個 dataset 能不能載入

`GET /api/v1/backtest/inspect`

常用查詢參數：

- `symbol`
- `interval`
- `start_date`
- `end_date`

### 3. 執行 simulate

`POST /api/v1/backtest/simulate`

### 4. 執行 backtest

`POST /api/v1/backtest/run`

### 5. 查看 replay runs

`GET /api/v1/backtest/runs`

### 6. 查看指定 replay run

`GET /api/v1/backtest/runs/{run_id}`

## 跑完之後去哪裡看結果

每次執行都會建立一個 run 目錄：

- `backtest/runtime/<run_id>/`

常見檔案：

- `status.json`
  - 這次 run 的狀態
- `summary.json`
  - 這次 run 的摘要
- `account.json`
  - 模擬帳戶資料
- `runtime_state.json`
  - replay 執行狀態
- `result.json`
  - backtest 詳細結果
- `orders.jsonl`
  - 有接到訂單時才會出現

## 一般操作建議

### 第一次使用

建議順序：

1. 先跑 `python main.py backtest-data`
2. 確認有資料可用
3. 先跑一個小的 `simulate`
4. 再跑 `backtest`
5. 最後用 `backtest-runs` 查結果

### 如果資料區間很短

請留意 `--warmup-bars`。

如果 `warmup_bars` 太大，而資料區間太短，可能會導致：

- 有載入資料
- 但有效 bar 很少
- 或根本沒有有效交易區段

這不一定是錯誤，通常是參數不適合當前資料長度。

### 如果這次沒有任何交易

先不要直接判定 replay 壞掉。

請先檢查：

- 策略這次有沒有送出下單請求
- 資料區間是否太短
- `warmup_bars` 是否太大
- 固定策略本身是否仍在調整中

## 常見問題

### Q1. 為什麼 `simulate` 或 `backtest` 跑完沒有交易？

因為 replay 系統不決定是否交易。  
沒有交易通常表示這次上層策略沒有送出訂單。

目前還要額外注意：

- 某些固定策略雖然能正常跑，但可能因資料依賴不足或進場條件尚未完全打通而暫時沒有交易
- `PairTradingStrategy` 必須有次資產歷史資料

### Q2. 為什麼會有 `orders.jsonl`，但不是每次都有？

只有這次 run 真的收到訂單請求時，才會產生 `orders.jsonl`。

### Q3. 原始歷史資料會不會被改掉？

不會。  
原始歷史資料是只讀的。  
所有 replay 結果都應該寫到 `backtest/runtime/`。

### Q4. UI 和 CLI 的結果是不是同一套？

是。  
現在 CLI、API、UI 都走同一套 replay service 和 runtime 輸出。

### Q5. 現在策略競爭是不是也用同一套 replay？

是。  
目前 `StrategyArena` 和 `StrategyPortfolioOptimizer` 已改成使用正式 replay 結果，不再使用隨機假績效。

但這不代表所有固定策略都已經完全可用。  
如果某些策略長時間沒有交易，應優先檢查策略本身的觸發能力、資料依賴與 setup 驗證流程。

## 建議搭配閱讀

- [README.md](/c:/D/E/BioNeuronai/backtest/README.md)
- [CURRENT_STATUS.md](/c:/D/E/BioNeuronai/backtest/docs/CURRENT_STATUS.md)
- [DEPRECATIONS.md](/c:/D/E/BioNeuronai/backtest/docs/DEPRECATIONS.md)
