# BioNeuronai 回測系統使用指南
**版本**: v2.1
**更新日期**: 2026-04-07

---

## 📑 目錄

1. 系統概覽
2. CLI 命令行回測
3. 自定義分析與腳本
4. 核心資料流

---

## 1. 系統概覽

BioNeuronai v2.1 的主回測系統位於 `backtest/` 目錄，透過 CLI 命令列統一入口調用。新版系統採用嚴格的 Pydantic 模型驗證，使用 `backtest/mock_connector.py` 取代真實的 `data/binance_futures.py` 連線，將真實歷史數據逐筆喂給 `core/trading_engine.py`。

### 核心原則
- **不重複發明輪子**：回測模式中，策略 (`strategies/`) 與 AI 推論 (`core/inference_engine.py`) **完全沿用實盤程式碼**；帳戶帳本由 `MockBinanceConnector` 內建，介面與實盤 `trading/virtual_account.py` 保持一致。
- **資料無未來性**：MockConnector 會攔截 `get_klines`，確保在 `T` 時刻絕對拿不到 `T+1` 的收盤價。

---

## 2. CLI 命令行回測

回測的主要方式是透過 `main.py backtest`。

### 基礎使用

請確保您的歷史資料已存於本地或準備好遠端接口：

```bash
python main.py backtest --symbol BTCUSDT --interval 1h --start-date 2025-01-01 --end-date 2025-04-01
```

### 紙交易模擬 (Simulate)

如果只是希望利用 `MockBinanceConnector` 即時觀測引擎在一段 K 線上的流轉狀態，可以使用 `simulate`：

```bash
python main.py simulate --symbol BTCUSDT --bars 300
```
這將會拉取近期的 300 根 K 線並跑一遍即時推進流程。

---

## 3. 自定義分析與腳本

若希望手寫 Jupyter Notebook 或是特定分析，請遵守以下流程：

### 第一步：定義並驅動 BacktestEngine

`BacktestEngine` 接受平坦參數（非 config 物件），`run()` 為同步方法，需傳入一個逐 bar 回呼函式：

```python
from backtest.backtest_engine import BacktestEngine

def my_strategy(bar, connector):
    """每根 K 線觸發一次；connector 為 MockBinanceConnector。"""
    klines = connector.data_stream.get_klines_until_now(50)
    if not klines or len(klines) < 20:
        return
    # 在此實作進出場邏輯
    # connector.place_order(bar.symbol, "BUY", "MARKET", 0.01)

engine = BacktestEngine(
    symbol="BTCUSDT",
    interval="1h",
    start_date="2025-01-01",
    end_date="2025-03-31",
    initial_balance=10000.0,
)
result = engine.run(my_strategy, print_summary=True)

print(f"交易次數: {len(result.trades)}")
print(f"總損益: {result.stats.get('total_pnl', 0):.2f} USDT")
```

### 方法 2：`run_with_trading_engine()` — 完整策略管道回測

若需要在回測中執行完整的 `TradingEngine` 管線（含 AI 推理、`StrategySelector`、特徵工程、事件上下文），使用此方法即可，無需手動接線：

```python
from backtest.backtest_engine import BacktestEngine
from bioneuronai.core.trading_engine import TradingEngine

trading_engine = TradingEngine(testnet=True, enable_ai_model=False)

engine = BacktestEngine(
    symbol="BTCUSDT",
    interval="1h",
    start_date="2025-01-01",
    end_date="2025-03-31",
    initial_balance=10000.0,
)

# 自動替換 connector → MockBinanceConnector，結束後還原
result = engine.run_with_trading_engine(
    trading_engine=trading_engine,
    auto_trade=True,       # False = 只觀察信號，不模擬下單
    print_summary=True,
)
```

`run_with_trading_engine()` 會在每根 K 線呼叫 `trading_engine.generate_trading_signal()`，
`auto_trade=True` 時再將信號送交 `execute_trade()` 記錄模擬成交。
InferenceEngine 的滾動特徵視窗也會在每次 `run()` 開始時自動 reset，避免跨 episode 污染。

---

## 4. 核心資料流與組件

1. **`backtest/mock_connector.py`**: 作為 `BinanceFuturesConnector` 的替身，接收歷史 K 線，開放供 `TradingEngine` 提取，並在內部維護帳戶餘額、持倉、未實現損益等狀態（帳戶邏輯已整合至此，不再依賴獨立的 `backtest/virtual_account.py`）。
2. **`trading/virtual_account.py`**: 供實盤交易使用的帳戶事實層，記錄訂單狀態與餘額。回測環境由 `MockBinanceConnector` 內建取代。
3. **`backtest/service.py`**: 提供 `run_backtest_summary()`、`run_simulation_summary()`、`collect_signal_training_data()` 等高階 API，供 CLI 與 Web API 呼叫。
4. **`data/database_manager.py`**: 無論是在實盤還是回測，所有訂單完成紀錄皆可寫入 `trades` 表格以便後續查詢。
