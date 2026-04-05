# Training Data - AI 訓練與交易數據中心

本資料夾集中管理所有用於 AI 模型訓練和交易系統的數據。

---

## 目錄

- [資料夾結構](#-資料夾結構)
- [用途說明](#-用途說明)
- [快速開始](#-快速開始)
- [數據使用場景](#-數據使用場景)
- [數據維護](#-數據維護)
- [數據統計（參考）](#-數據統計參考)
- [相關文檔](#-相關文檔)
- [注意事項](#%EF%B8%8F-注意事項)
- [技術支援](#-技術支援)

---

## 📁 資料夾結構

```
training_data/
├── README.md                    # 本說明文件
├── data_downloads/              # Binance 歷史數據與下載工具
│   ├── ai_trade_nexttick.py    # AI 交易執行腳本
│   ├── data_feeder.py          # 歷史數據餵送器
│   ├── mock_api.py             # Mock API 連接器
│   ├── run_backtest.py         # 回測系統
│   ├── scripts/                # 數據下載腳本集合
│   │   ├── download-kline.py
│   │   ├── download-trade.py
│   │   ├── download-aggTrade.py
│   │   ├── download-futures-*.py
│   │   └── download_example.py
│   └── binance_historical/     # Binance 歷史數據存放
│       ├── spot/               # 現貨市場數據
│       ├── futures/            # USD-M 期貨數據
│       └── coin_futures/       # COIN-M 期貨數據
│
└── trading_data/               # 交易運行時數據
    ├── trading.db              # 主交易數據庫
    ├── test_trading.db         # 測試數據庫
    ├── risk_statistics.json    # 風險統計數據
    ├── signals_history.json    # 信號歷史記錄
    ├── strategy_weights.json   # 策略權重配置
    └── backups/                # 數據備份

```

## 🎯 用途說明

### 1. data_downloads/
**用於：AI 模型訓練、策略回測、市場分析**

- **歷史數據源**: Binance Public Data (https://data.binance.vision/)
- **數據類型**: 
  - K線數據 (OHLCV) - 多時間週期
  - 原始交易數據 (Trades)
  - 聚合交易數據 (AggTrades)
  - 期貨專用數據 (Premium Index, Mark Price, Funding Rate)
- **核心腳本**:
  - `ai_trade_nexttick.py` - AI 實盤交易執行
  - `run_backtest.py` - 策略回測系統
  - `data_feeder.py` - 歷史數據重放器

📖 詳細說明：參考 [data_downloads/README.md](data_downloads/README.md)

### 2. trading_data/
**用於：交易記錄、風險管理、性能追蹤**

- **數據庫文件**:
  - `trading.db` - 主交易數據庫（訂單、持倉、PnL）
  - `test_trading.db` - 測試環境數據庫
- **JSON 配置**:
  - `risk_statistics.json` - 風險指標統計
  - `signals_history.json` - 交易信號歷史
  - `strategy_weights.json` - 多策略權重配置
- **備份機制**: 自動備份到 `backups/` 資料夾

## 🚀 快速開始

### AI 訓練數據準備

```bash
# 1. 切換到下載腳本目錄
cd training_data/data_downloads/scripts

# 2. 下載主流幣種歷史數據（用於模型訓練）
python download-kline.py -t um -s BTCUSDT ETHUSDT BNBUSDT -i 1h 4h -startDate 2023-01-01

# 3. 下載近期分鐘線數據（用於策略回測）
python download-kline.py -t um -s ETHUSDT -i 15m -startDate 2025-12-01
```

### 執行 AI 交易回測

```bash
# 切換到 data_downloads 目錄
cd training_data/data_downloads

# 執行 AI 交易（使用 next_tick 模式）
python ai_trade_nexttick.py
```

## 📊 數據使用場景

| 場景 | 使用數據 | 腳本/模組 |
|------|---------|----------|
| **AI 模型訓練** | data_downloads/binance_historical/ | src/bioneuronai/ai/hundred_million_model.py |
| **策略回測** | data_downloads/binance_historical/ | data_downloads/run_backtest.py |
| **實盤交易模擬** | data_downloads/binance_historical/ | data_downloads/ai_trade_nexttick.py |
| **風險分析** | trading_data/risk_statistics.json | src/bioneuronai/risk/risk_manager.py |
| **性能追蹤** | trading_data/trading.db | src/bioneuronai/analysis/performance_metrics.py |
| **信號分析** | trading_data/signals_history.json | src/bioneuronai/trading_plan/signal_analyzer.py |

## 🔧 數據維護

### 定期更新歷史數據

```bash
# 每日更新（下載前一天的數據）
cd training_data/data_downloads/scripts
python download-kline.py -t um -s BTCUSDT ETHUSDT -i 15m -skip-monthly 1

# 每月更新（下載上個月的月度數據）
python download-kline.py -t um -s BTCUSDT ETHUSDT -i 1h -skip-daily 1
```

### 清理過期數據

```bash
# 備份舊數據
cd training_data/trading_data
Copy-Item trading.db backups/trading_$(Get-Date -Format 'yyyyMMdd').db

# 清理測試數據
Remove-Item test_trading.db -ErrorAction SilentlyContinue
```

## 📈 數據統計（參考）

- **歷史數據量**: 30+ 天完整 K線數據
- **覆蓋交易對**: ETHUSDT, BTCUSDT 等主流幣種
- **時間週期**: 15m（主要用於 AI 交易）
- **數據完整度**: 100%（96 bars/天）
- **更新頻率**: 每日同步最新數據

## 🔗 相關文檔

- **數據下載詳細指南**: [data_downloads/README.md](data_downloads/README.md)
- **模組分析文檔**: [data_downloads/MODULE_ANALYSIS.md](data_downloads/MODULE_ANALYSIS.md)
- **AI 交易執行**: 參考 `ai_trade_nexttick.py` 腳本
- **項目主文檔**: [../README.md](../README.md)

## ⚠️ 注意事項

1. **磁碟空間**: 歷史數據量較大，建議預留 10GB+ 空間
2. **數據備份**: 定期備份 trading_data/*.db 和 *.json 文件
3. **路徑依賴**: 所有腳本假設從各自目錄執行，注意相對路徑
4. **時間戳格式**: 
   - 現貨數據 (2025+): 微秒時間戳
   - 期貨數據: 毫秒時間戳
5. **數據一致性**: 下載數據前檢查網路連接和磁碟空間

## 📞 技術支援

如遇到數據問題：
1. 檢查 [data_downloads/README.md](data_downloads/README.md) 的故障排除章節
2. 驗證數據文件完整性（使用 .CHECKSUM 文件）
3. 查看相關日誌文件定位問題

---

**最後更新**: 2026-01-23  
**版本**: v2.1.0  
**維護者**: BioNeuronAI Team

> 📖 上層目錄：[data/bioneuronai/README.md](../README.md)
