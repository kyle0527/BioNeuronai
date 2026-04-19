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
3. 帳戶 / 訂單 / 倉位狀態由 `MockBinanceConnector` 內部維護（回測環境不使用 `virtual_account.py`）
4. 上層策略 / 交易流程自行決定是否送出訂單
5. replay 層接收訂單後模擬執行
6. `runtime_store.py` 保存整次 run 的結果

### 整合 TradingEngine 完整管線

若需要在回測中執行 `TradingEngine` 的完整策略管線（含 AI 推理、`StrategySelector`、事件上下文），使用 `run_with_trading_engine()`：

```python
from backtest.backtest_engine import BacktestEngine
from bioneuronai.core.trading_engine import TradingEngine

engine = BacktestEngine(symbol="BTCUSDT", start_date="2025-01-01")
trading_engine = TradingEngine(testnet=True, enable_ai_model=False)

result = engine.run_with_trading_engine(
    trading_engine=trading_engine,
    auto_trade=True,
)
```

此方法自動替換 connector，回測結束後還原，不影響後續正式交易使用。

## 現況提醒

- 目前正式資料集中可辨識的是 `ETHUSDT` 的多個 interval
- `backtest/` 現在除了評估正式 `TradingEngine` 主線，也可被高階策略競爭層拿來評估單一策略實例
- `StrategyArena` 與 `StrategyPortfolioOptimizer` 已改成使用正式 replay，而不是隨機假績效
- 回測環境的訂單 / 帳戶狀態由 `MockBinanceConnector` 內部維護；`virtual_account.py` 僅用於實盤交易
- `backtest/` 透過 connector query API 讀取帳戶快照
- 目前固定策略層仍有真實限制：
  - `TrendFollowing` / `SwingTrading` 已可交易，但仍待進一步收斂 pending order 與策略狀態同步
  - `PairTrading` 次資產資料已補齊，目前可正式 replay
  - `BreakoutTrading` / `DirectionChange` 已可正式 replay，不再是純 0 trade
- 如果某次 backtest 沒有交易，不代表 replay 壞掉；代表那次測試裡上層策略沒有送出下單請求，或固定策略本身仍待調整
- 短資料區間時，請注意 `warmup_bars`

## 相關文件

- [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md)
- [docs/DEPRECATIONS.md](docs/DEPRECATIONS.md)
- [docs/INTEGRATION_PLAN.md](docs/INTEGRATION_PLAN.md)
- [data/README.md](data/README.md)
- [runtime/README.md](runtime/README.md)
- [vendor/README.md](vendor/README.md)
- [回測系統指南](../docs/BACKTEST_SYSTEM_GUIDE.md)
