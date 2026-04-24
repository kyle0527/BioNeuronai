# Backtest

`backtest/` 是專案的正式 replay / backtest 子系統。這一層只說明模組責任、主要檔案與子文件入口；更細的資料目錄規則放在下一層 README。

## 模組定位

`backtest/` 的責任有三類：

1. 載入歷史市場資料。
2. 接收訂單意圖並模擬執行。
3. 保存每次 replay / backtest 的 runtime 輸出。

它不負責決定是否交易。交易決策仍屬於策略、分析與交易引擎層。

## 目錄結構

- `__init__.py`
  統一匯出 replay domain 主要類別、路徑、服務函式與 UI 載入函式。
- `contracts.py`
  `OrderIntent`、`ExecutionReceipt`、`ReplayRuntimeState` 與協定介面。
- `paths.py`
  `DATA_ROOT`、`BACKTEST_DATA_DIR`、`RUNTIME_ROOT`、`UI_ROOT`、`VENDOR_ROOT`、`ensure_backtest_dirs()`，以及舊路徑 fallback 規則。
- `data_stream.py`
  `KlineBar`、`HistoricalDataStream`、`resolve_data_dir()`、`create_stream()`。
- `catalog.py`
  掃描歷史資料集並輸出 catalog。
- `mock_connector.py`
  `MockBinanceConnector`，模擬市場資料、帳戶與下單行為。
- `backtest_engine.py`
  `BacktestConfig`、`BacktestResult`、`BacktestEngine`、`quick_backtest()`、`create_mock_connector()`。
- `runtime_store.py`
  `ReplayRunRecorder`、`list_runs()`、`load_run()`。
- `service.py`
  對 API / CLI 友善的高階入口：
  `run_simulation_summary()`、`run_backtest_summary()`、`collect_signal_training_data()`、`list_runtime_runs()`、`get_runtime_run()`。
- `web.py`
  載入 `backtest/ui/index.html`。
- `data/`
  正式歷史資料根目錄。
  文件：[data/README.md](data/README.md)
- `runtime/`
  replay / backtest 執行輸出。
  文件：[runtime/README.md](runtime/README.md)
- `vendor/`
  第三方材料整合區。
  文件：[vendor/README.md](vendor/README.md)
- `docs/legacy_historical/`
  舊資料方案補充文件。
  文件：[docs/legacy_historical/README.md](docs/legacy_historical/README.md)
- `ui/`
  回測頁面靜態資產，目前可見 `index.html`。

## 頂層匯出

`backtest.__init__` 目前會匯出：

- domain 類型：
  `OrderIntent`、`ExecutionReceipt`、`ReplayRuntimeState`
- replay 核心：
  `MockBinanceConnector`、`HistoricalDataStream`、`KlineBar`、`BacktestEngine`、`BacktestConfig`
- 快捷函式：
  `quick_backtest()`、`create_mock_connector()`、`resolve_data_dir()`、`get_catalog()`、`list_runs()`、`load_run()`
- 高階服務：
  `run_backtest_summary()`、`run_simulation_summary()`、`collect_signal_training_data()`、`list_runtime_runs()`、`get_runtime_run()`
- 路徑與資源：
  `BACKTEST_DATA_DIR`、`DATA_ROOT`、`DOCS_ROOT`、`UI_ROOT`、`RUNTIME_ROOT`、`VENDOR_ROOT`、`ensure_backtest_dirs()`、`load_backtest_ui_html()`

## 依賴方向

```text
data ───────────→ data_stream ─────→ mock_connector ─────→ backtest_engine
                      │                    │                     │
                      └────→ catalog       └────→ runtime_store  └────→ service

paths ────────────────────────────────────────────────────────────↑
ui/index.html ───────────────────────────────────────────────────→ web
```

另外：

- `mock_connector.py` 會使用 `bioneuronai.trading.VirtualAccount`。
- `service.py` 會在需要時載入 `TradingEngine` 與 `InferenceEngine`，用於完整回測主線或訊號訓練資料收集。

## 文件鏈

- 下一層文件：
  [data/README.md](data/README.md)
  [runtime/README.md](runtime/README.md)
  [vendor/README.md](vendor/README.md)
  [docs/legacy_historical/README.md](docs/legacy_historical/README.md)
- 相關補充文件：
  [docs/CURRENT_STATUS.md](docs/CURRENT_STATUS.md)
  [docs/DEPRECATIONS.md](docs/DEPRECATIONS.md)
  [docs/INTEGRATION_PLAN.md](docs/INTEGRATION_PLAN.md)
  [docs/USER_MANUAL.md](docs/USER_MANUAL.md)

## 使用入口

```python
from backtest import BacktestEngine, run_backtest_summary

engine = BacktestEngine(symbol="BTCUSDT", interval="1h")
summary = run_backtest_summary(symbol="BTCUSDT", interval="1h")
```
