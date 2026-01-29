# Binance 歷史數據下載 - 快速開始指南

## 5 分鐘快速上手

### 步驟 1: 安裝依賴

```bash
cd C:\D\E\BioNeuronai\data_downloads\scripts
pip install -r requirements.txt
```

### 步驟 2: 使用互動式範例

```bash
python download_example.py
```

這會啟動互動式選單，讓你選擇不同的下載範例。

### 步驟 3: 或直接下載（推薦用於 BioNeuronai）

```bash
# Windows PowerShell
cd C:\D\E\BioNeuronai\data_downloads\scripts

# 下載 BTC 和 ETH 的小時線數據（適合訓練 AI 模型）
python download-kline.py -t um -s BTCUSDT ETHUSDT -i 1h 4h -startDate 2023-01-01 -folder ..\binance_historical -c 1
```

## 常用下載命令

### 1. 訓練數據（推薦）

用於訓練 BioNeuronai 的 111M 參數模型：

```bash
# 下載 2023 年至今的主流幣種小時線數據
python download-kline.py -t um -s BTCUSDT ETHUSDT BNBUSDT SOLUSDT ADAUSDT XRPUSDT -i 1h 4h -startDate 2023-01-01 -folder ..\binance_historical
```

### 2. 回測數據

用於策略回測和驗證：

```bash
# 下載最近 3 個月的 15 分鐘線數據
python download-kline.py -t um -s BTCUSDT ETHUSDT -i 15m -startDate 2024-10-01 -skip-monthly 1 -folder ..\binance_historical
```

### 3. 高頻數據

用於高頻交易策略測試：

```bash
# 下載最近 7 天的 1 分鐘線數據
python download-kline.py -t um -s BTCUSDT -i 1m -startDate 2026-01-14 -skip-monthly 1 -folder ..\binance_historical
```

### 4. 完整數據集

包含 K線 + 交易數據：

```bash
# K線數據
python download-kline.py -t um -s BTCUSDT -i 1h -startDate 2024-01-01 -folder ..\binance_historical

# 聚合交易數據
python download-aggTrade.py -t um -s BTCUSDT -startDate 2024-01-01 -folder ..\binance_historical
```

## 參數快速參考

### 市場類型 (-t)
- `spot`: 現貨市場
- `um`: USD-M 永續合約（推薦用於 BioNeuronai）
- `cm`: COIN-M 永續合約

### 時間間隔 (-i)
```
1s   - 1 秒（高頻）
1m   - 1 分鐘（高頻）
5m   - 5 分鐘（日內交易）
15m  - 15 分鐘（日內交易）
1h   - 1 小時（推薦用於訓練）
4h   - 4 小時（推薦用於訓練）
1d   - 1 天（長期趨勢）
1w   - 1 週（長期趨勢）
```

### 常用交易對
```
主流幣: BTCUSDT ETHUSDT BNBUSDT
DeFi: SOLUSDT ADAUSDT LINKUSDT
Layer1: AVAXUSDT ATOMUSDT NEARUSDT
Meme: DOGEUSDT SHIBUSDT PEPEUSDT
```

## 驗證下載的數據

```bash
cd ..\binance_historical

# 查看下載的文件
Get-ChildItem -Recurse *.zip | Select-Object Name, Length, LastWriteTime

# 驗證校驗和（如果下載了 .CHECKSUM 文件）
Get-FileHash -Algorithm SHA256 BTCUSDT-1h-2024-01.zip
```

## 解壓縮數據

```bash
# 解壓單個文件
Expand-Archive -Path "BTCUSDT-1h-2024-01.zip" -DestinationPath "BTCUSDT-1h-2024-01" -Force

# 批量解壓（PowerShell）
Get-ChildItem *.zip | ForEach-Object {
    $dest = $_.BaseName
    Expand-Archive -Path $_.FullName -DestinationPath $dest -Force
    Write-Host "解壓: $($_.Name) -> $dest"
}
```

## 讀取 CSV 數據

### Python 範例

```python
import pandas as pd
import zipfile

# 直接從 zip 文件讀取
with zipfile.ZipFile('BTCUSDT-1h-2024-01.zip') as z:
    with z.open('BTCUSDT-1h-2024-01.csv') as f:
        df = pd.read_csv(f, header=None, names=[
            'open_time', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 
            'taker_buy_base', 'taker_buy_quote', 'ignore'
        ])

# 轉換時間戳
df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')

# 顯示前幾行
print(df.head())

# 基本統計
print(df.describe())
```

## 整合到 BioNeuronai

### 1. 在特徵工程模組中使用

編輯 `src/bioneuronai/analysis/feature_engineering.py`:

```python
import pandas as pd
import zipfile
from pathlib import Path

def load_historical_klines(symbol, interval, year_month):
    """載入歷史 K線數據"""
    data_dir = Path("data_downloads/binance_historical")
    zip_file = data_dir / f"futures/monthly/klines/{symbol}/{interval}/{symbol}-{interval}-{year_month}.zip"
    
    if not zip_file.exists():
        raise FileNotFoundError(f"找不到文件: {zip_file}")
    
    with zipfile.ZipFile(zip_file) as z:
        csv_name = f"{symbol}-{interval}-{year_month}.csv"
        with z.open(csv_name) as f:
            df = pd.read_csv(f, header=None, names=[
                'open_time', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 
                'taker_buy_base', 'taker_buy_quote', 'ignore'
            ])
    
    return df
```

### 2. 在回測模組中使用

編輯 `src/bioneuronai/trading_plan/backtest_validator.py`:

```python
def load_backtest_data(symbol, interval, start_date, end_date):
    """載入回測數據"""
    # 從下載的歷史數據載入
    data_dir = Path("data_downloads/binance_historical")
    # ... 實作載入邏輯
    pass
```

## 常見問題

### Q: 下載速度很慢？
A: 這是正常的，數據從 Binance CDN 下載。可以使用 `-skip-monthly 1` 只下載日度數據來加快速度。

### Q: 如何只下載最新的數據？
A: 使用 `-startDate` 和 `-endDate` 參數指定日期範圍。

### Q: 磁碟空間不足？
A: 
- 只下載必要的交易對和時間間隔
- 下載後可以刪除 .zip 文件，保留解壓後的 .csv
- 使用 `-skip-monthly 1` 只下載日度數據（體積較小）

### Q: 如何更新數據？
A: 直接執行相同的下載命令，腳本會自動跳過已存在的文件。

### Q: 數據從什麼時候開始？
A: 大部分交易對從 2020-01-01 開始有數據，具體取決於交易對的上線時間。

## 下一步

1. ✅ 下載必要的歷史數據
2. 📊 使用 Python/Pandas 讀取和分析數據
3. 🔧 將數據載入邏輯整合到 BioNeuronai 模組
4. 🧪 使用歷史數據進行策略回測
5. 🤖 使用數據訓練或微調 AI 模型

## 參考文件

- [完整 README](../README.md) - 詳細文檔
- [Binance Data Collection](https://data.binance.vision/) - 官方網站
- [範例腳本](download_example.py) - 互動式下載範例
