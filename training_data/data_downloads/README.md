# BioNeuronai 歷史數據下載

本目錄用於存放從 Binance Public Data 下載的歷史市場數據。

## 目錄結構

```
training_data/data_downloads/
├── README.md                    # 本說明文件
├── MODULE_ANALYSIS.md           # 模組分析文檔
├── ai_trade_nexttick.py        # AI交易執行腳本
├── data_feeder.py              # 歷史數據餵送器
├── mock_api.py                 # Mock API連接器
├── run_backtest.py             # 回測系統
├── scripts/                    # 下載腳本
│   ├── download-kline.py       # K線數據下載
│   ├── download-trade.py       # 交易數據下載
│   ├── download-aggTrade.py    # 聚合交易數據下載
│   ├── download-futures-*.py   # 期貨專用下載腳本
│   ├── download_example.py     # 使用範例
│   ├── enums.py                # 常量定義
│   └── utility.py              # 工具函數
└── binance_historical/          # 下載的數據存放處
    ├── spot/                   # 現貨數據
    │   ├── monthly/            # 月度數據
    │   └── daily/              # 日度數據
    ├── futures/                # 期貨數據 (USD-M)
    │   ├── monthly/
    │   └── daily/
    └── coin_futures/           # 幣本位期貨數據 (COIN-M)
        ├── monthly/
        └── daily/
```

## 數據來源

**Binance Public Data**: https://data.binance.vision/

提供以下類型的歷史數據：
- **K線數據 (Klines)**: OHLCV 數據，支援多種時間間隔
- **交易數據 (Trades)**: 原始交易記錄
- **聚合交易 (AggTrades)**: 聚合的交易數據

### 支援的市場類型
- `spot`: 現貨市場
- `um`: USD-M 期貨 (USDT 本位永續合約)
- `cm`: COIN-M 期貨 (幣本位永續合約)

### 支援的時間間隔
- 秒級: `1s`
- 分鐘級: `1m`, `3m`, `5m`, `15m`, `30m`
- 小時級: `1h`, `2h`, `4h`, `6h`, `8h`, `12h`
- 日級: `1d`, `3d`
- 週級: `1w`
- 月級: `1mo`

## 快速開始

### 1. 安裝依賴

```bash
cd training_data/data_downloads/scripts
pip install -r requirements.txt
```

### 2. 設定環境變數（可選）

```bash
# Windows PowerShell
$env:STORE_DIRECTORY="C:\D\E\BioNeuronai\training_data\data_downloads\binance_historical"

# Linux/Mac
export STORE_DIRECTORY=/path/to/BioNeuronai/training_data/data_downloads/binance_historical
```

### 3. 下載數據

#### 下載 K線數據

```bash
# 下載 BTCUSDT 現貨 1小時 K線（所有可用數據）
python download_kline.py -t spot -s BTCUSDT -i 1h

# 下載多個交易對的 K線
python download_kline.py -t spot -s BTCUSDT ETHUSDT BNBUSDT -i 1h 4h

# 下載 USD-M 期貨數據（指定日期範圍）
python download_kline.py -t um -s BTCUSDT -i 1m -startDate 2024-01-01 -endDate 2024-12-31

# 下載所有交易對的日線數據（僅日度數據，跳過月度）
python download_kline.py -t spot -i 1d -skip-monthly 1

# 指定年份和月份
python download_kline.py -t spot -s BTCUSDT -i 1h -y 2024 -m 01 02 03

# 包含校驗和文件
python download_kline.py -t spot -s BTCUSDT -i 1h -c 1
```

#### 下載交易數據

```bash
# 下載 BTCUSDT 現貨交易數據
python download_trade.py -t spot -s BTCUSDT

# 下載 USD-M 期貨交易數據（指定日期）
python download_trade.py -t um -s BTCUSDT -startDate 2024-01-01 -endDate 2024-01-31
```

#### 下載聚合交易數據

```bash
# 下載 BTCUSDT 聚合交易數據
python download_aggTrade.py -t spot -s BTCUSDT

# 下載多個交易對的聚合交易數據
python download_aggTrade.py -t spot -s BTCUSDT ETHUSDT -startDate 2024-01-01
```

## 參數說明

### 通用參數

| 參數 | 說明 | 預設值 | 必填 |
|------|------|--------|------|
| `-t` | 市場類型: `spot`, `um`, `cm` | spot | 是 |
| `-s` | 交易對符號（可多個，空格分隔） | 所有交易對 | 否 |
| `-y` | 年份（可多個） | 2020至今 | 否 |
| `-m` | 月份（可多個） | 所有月份 | 否 |
| `-d` | 日期（可多個） | 所有日期 | 否 |
| `-startDate` | 開始日期 [YYYY-MM-DD] | 2020-01-01 | 否 |
| `-endDate` | 結束日期 [YYYY-MM-DD] | 當前日期 | 否 |
| `-skip-monthly` | 跳過月度數據 (1=跳過) | 0 | 否 |
| `-skip-daily` | 跳過日度數據 (1=跳過) | 0 | 否 |
| `-folder` | 數據存放目錄 | 當前目錄 | 否 |
| `-c` | 下載校驗和文件 (1=下載) | 0 | 否 |

### K線專用參數

| 參數 | 說明 | 預設值 | 必填 |
|------|------|--------|------|
| `-i` | 時間間隔（可多個） | 所有間隔 | 否 |

## 數據格式

### K線數據格式

#### 現貨 (SPOT)
從 2025-01-01 開始，時間戳為**微秒**級別。

| 欄位 | 說明 |
|------|------|
| Open time | 開盤時間（微秒） |
| Open | 開盤價 |
| High | 最高價 |
| Low | 最低價 |
| Close | 收盤價 |
| Volume | 交易量 |
| Close time | 收盤時間（微秒） |
| Quote asset volume | 計價資產交易量 |
| Number of trades | 交易筆數 |
| Taker buy base asset volume | 主動買入基礎資產交易量 |
| Taker buy quote asset volume | 主動買入計價資產交易量 |
| Ignore | 忽略欄位 |

#### USD-M 期貨
| 欄位 | 說明 |
|------|------|
| Open time | 開盤時間（毫秒） |
| Open | 開盤價 |
| High | 最高價 |
| Low | 最低價 |
| Close | 收盤價 |
| Volume | 交易量 |
| Close time | 收盤時間（毫秒） |
| Quote asset volume | 計價資產交易量 |
| Number of trades | 交易筆數 |
| Taker buy base asset volume | 主動買入基礎資產交易量 |
| Taker buy quote asset volume | 主動買入計價資產交易量 |
| Ignore | 忽略欄位 |

### 交易數據格式

#### 現貨交易
| 欄位 | 說明 |
|------|------|
| trade Id | 交易ID |
| price | 價格 |
| qty | 數量 |
| quoteQty | 計價資產數量 |
| time | 時間戳（微秒） |
| isBuyerMaker | 買方是否為掛單方 |
| isBestMatch | 是否為最佳匹配 |

#### USD-M 期貨交易
| 欄位 | 說明 |
|------|------|
| trade Id | 交易ID |
| price | 價格 |
| qty | 數量 |
| quoteQty | 計價資產數量 |
| time | 時間戳（毫秒） |
| isBuyerMaker | 買方是否為掛單方 |

### 聚合交易數據格式

| 欄位 | 說明 |
|------|------|
| Aggregate tradeId | 聚合交易ID |
| Price | 價格 |
| Quantity | 數量 |
| First tradeId | 第一筆交易ID |
| Last tradeId | 最後一筆交易ID |
| Timestamp | 時間戳 |
| Was the buyer the maker | 買方是否為掛單方 |

## 數據驗證

每個 zip 文件都有對應的 `.CHECKSUM` 文件用於驗證數據完整性：

```bash
# Windows PowerShell
Get-FileHash -Algorithm SHA256 BTCUSDT-1h-2024-01.zip | Format-List

# Linux
sha256sum -c BTCUSDT-1h-2024-01.zip.CHECKSUM

# MacOS
shasum -a 256 -c BTCUSDT-1h-2024-01.zip.CHECKSUM
```

## 使用建議

### 針對 BioNeuronai 系統

1. **訓練數據準備**
   - 下載多個交易對的歷史 K線數據（建議 1h 或 4h）
   - 時間範圍：至少 1-2 年的數據
   - 優先下載：BTCUSDT, ETHUSDT, BNBUSDT 等主流幣種

2. **回測數據**
   - 下載更精細的時間間隔（1m, 5m, 15m）用於策略回測
   - 包含交易數據以驗證流動性

3. **實時交易前驗證**
   - 下載最近 3-6 個月的數據進行模擬交易
   - 使用日度數據保持數據新鮮度

### 推薦下載命令

```bash
# 1. 下載主流交易對的小時線數據（用於模型訓練）
python download_kline.py -t um -s BTCUSDT ETHUSDT BNBUSDT SOLUSDT -i 1h 4h -startDate 2023-01-01 -folder ../binance_historical

# 2. 下載近期的分鐘線數據（用於回測）
python download_kline.py -t um -s BTCUSDT ETHUSDT -i 5m 15m -startDate 2024-01-01 -skip-monthly 1 -folder ../binance_historical

# 3. 下載交易數據（用於流動性分析）
python download_trade.py -t um -s BTCUSDT -startDate 2024-01-01 -skip-monthly 1 -folder ../binance_historical
```

## 注意事項

1. **磁碟空間**: 歷史數據量較大，確保有足夠的磁碟空間
2. **網路連線**: 下載大量數據需要穩定的網路連線
3. **時間戳格式**: 
   - 現貨數據從 2025-01-01 開始使用**微秒**時間戳
   - 期貨數據使用**毫秒**時間戳
4. **數據更新**: 
   - 每日數據次日可用
   - 月度數據於每月第一個週一可用

## 整合到 BioNeuronai

下載的數據可用於：
- 訓練 111M 參數的 AI 模型
- 策略回測和驗證
- 市場情境分析
- 特徵工程和數據預處理

相關模組：
- `src/bioneuronai/analysis/feature_engineering.py` - 特徵提取
- `src/bioneuronai/core/inference_engine.py` - 模型推論
- `src/bioneuronai/trading_plan/backtest_validator.py` - 回測驗證

## 參考資源

- Binance Data Collection: https://data.binance.vision/
- Binance API 文檔: https://binance-docs.github.io/apidocs/
- 原始專案: https://github.com/binance/binance-public-data
