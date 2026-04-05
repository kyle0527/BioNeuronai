# Backtest Replay System

`backtest/` 是目前專案正式的 replay 主路徑。

它的職責只有三類：

1. 提供歷史市場資料
2. 接收專案送出的訂單請求並模擬執行
3. 保存 replay runtime 結果

它**不負責**決定是否交易。  
是否下單仍由專案的策略模組、分析模組、交易流程決定。

## 目前狀態

- 正式歷史資料根目錄：`backtest/data/binance_historical/`
- 正式 runtime 輸出目錄：`backtest/runtime/`
- 正式 UI 資產目錄：`backtest/ui/`
- 正式 API 入口：
  - `/api/v1/backtest/catalog`
  - `/api/v1/backtest/inspect`
  - `/api/v1/backtest/simulate`
  - `/api/v1/backtest/run`
  - `/api/v1/backtest/runs`
  - `/api/v1/backtest/runs/{run_id}`
  - `/backtest/ui`
- 正式 CLI 命令：
  - `python main.py backtest`
  - `python main.py simulate`
  - `python main.py backtest-data`
  - `python main.py backtest-runs`

## 責任邊界

### `backtest/` 負責

- 載入 Binance 歷史資料
- 以時間順序重放歷史 K 線
- 維護模擬帳戶、模擬成交、模擬持倉
- 接收策略送出的訂單請求
- 產生 replay run artifacts

### `backtest/` 不負責

- 決定是否要交易
- 評估策略本身是否正確
- 取代專案主體的風控、策略、分析邏輯
- 修改原始歷史資料

## 目錄結構

```text
backtest/
├── __init__.py
├── backtest_engine.py
├── catalog.py
├── contracts.py
├── data_stream.py
├── mock_connector.py
├── paths.py
├── runtime_store.py
├── service.py
├── virtual_account.py
├── web.py
├── data/
│   ├── README.md
│   └── binance_historical/
├── docs/
│   ├── CURRENT_STATUS.md
│   ├── DEPRECATIONS.md
│   ├── INTEGRATION_PLAN.md
│   └── legacy_historical/
├── runtime/
│   └── README.md
├── ui/
│   └── index.html
└── vendor/
    └── README.md
```

## 資料路徑

目前正式主路徑已經是：

- `backtest/data/binance_historical/`

系統仍保留舊路徑 fallback，但那只是相容，不是正式規格。

## Runtime 輸出

每次 `simulate` 或 `backtest` 都會建立：

- `backtest/runtime/<run_id>/`

目錄內目前可能出現：

- `status.json`
- `summary.json`
- `account.json`
- `runtime_state.json`
- `result.json`
- `orders.jsonl`

其中：

- `result.json` 主要出現在 backtest run
- `orders.jsonl` 只有真的收到訂單請求時才會出現

## 實際運作流程

1. `data_stream.py` 讀取歷史資料
2. `MockBinanceConnector` 將目前 bar 與模擬帳戶狀態提供給上層
3. 上層策略 / 交易流程自行決定是否送出訂單
4. replay 層接收訂單後模擬執行
5. `runtime_store.py` 保存整次 run 的結果

## 現況提醒

- 目前正式資料集中可辨識的是 `ETHUSDT` 的多個 interval
- `backtest/` 現在除了評估正式 `TradingEngine` 主線，也可被高階策略競爭層拿來評估單一策略實例
- `StrategyArena` 與 `StrategyPortfolioOptimizer` 已改成使用正式 replay，而不是隨機假績效
- 目前固定策略層仍有真實限制：
  - `TrendFollowing` / `SwingTrading` / `MeanReversion` 已可產生 setup，但存在共同的 setup 驗證順序問題
  - `PairTrading` 需要次資產歷史資料，現有正式資料根目錄尚未補齊
  - `BreakoutTrading` / `DirectionChange` 在目前 ETH 歷史資料窗口上尚未驗證出穩定觸發
- 如果某次 backtest 沒有交易，不代表 replay 壞掉；代表那次測試裡上層策略沒有送出下單請求，或固定策略本身仍待調整
- 短資料區間時，請注意 `warmup_bars`

## 相關文件

- [USER_MANUAL.md](/c:/D/E/BioNeuronai/backtest/docs/USER_MANUAL.md)
- [CURRENT_STATUS.md](/c:/D/E/BioNeuronai/backtest/docs/CURRENT_STATUS.md)
- [DEPRECATIONS.md](/c:/D/E/BioNeuronai/backtest/docs/DEPRECATIONS.md)
- [INTEGRATION_PLAN.md](/c:/D/E/BioNeuronai/backtest/docs/INTEGRATION_PLAN.md)
- [data/README.md](/c:/D/E/BioNeuronai/backtest/data/README.md)
- [runtime/README.md](/c:/D/E/BioNeuronai/backtest/runtime/README.md)
- [vendor/README.md](/c:/D/E/BioNeuronai/backtest/vendor/README.md)
