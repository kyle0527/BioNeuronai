# data_downloads — 歷史數據目錄

此目錄存放回測所需的 Binance K 線歷史數據（CSV 格式）。

## 目錄結構

```
data_downloads/
└── binance_historical/
    ├── BTCUSDT_1h.csv      ← 由下載工具產生
    ├── ETHUSDT_1h.csv
    └── ...
```

## 如何取得數據

BacktestEngine 預設讀取 `binance_historical/` 下的 CSV，
格式為：`timestamp,open,high,low,close,volume`。

**方式 1：使用工具下載（若存在）**
```bash
python tools/download_historical_data.py --symbol BTCUSDT --interval 1h --days 365
```

**方式 2：使用 HistoricalBacktest 直接從 API 加載**
```bash
python backtesting/historical_backtest.py --symbol BTCUSDT
```

**方式 3：手動放置**
將你的 CSV 檔案放到 `binance_historical/` 子目錄，
確保欄位順序為 `timestamp,open,high,low,close,volume`。

## 注意事項

- 此目錄下的數據檔案**不應提交到 git**（`.gitignore` 已排除 `*.csv`）
- 沒有數據時，`backtest` 和 `simulate` 命令會因找不到數據而失敗
- 相關原始碼：`backtest/backtest_engine.py:DEFAULT_DATA_DIR`
