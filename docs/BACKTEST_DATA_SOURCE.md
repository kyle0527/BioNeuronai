# 回測系統數據來源說明

## 📑 目錄

<!-- toc -->

- [📊 數據來源概覽](#%F0%9F%93%8A-%E6%95%B8%E6%93%9A%E4%BE%86%E6%BA%90%E6%A6%82%E8%A6%BD)
  * [為什麼選擇 Binance？](#%E7%82%BA%E4%BB%80%E9%BA%BC%E9%81%B8%E6%93%87-binance)
- [🔌 API 端點](#%F0%9F%94%8C-api-%E7%AB%AF%E9%BB%9E)
  * [主網 (Mainnet)](#%E4%B8%BB%E7%B6%B2-mainnet)
  * [測試網 (Testnet)](#%E6%B8%AC%E8%A9%A6%E7%B6%B2-testnet)
- [📈 支持的數據類型](#%F0%9F%93%88-%E6%94%AF%E6%8C%81%E7%9A%84%E6%95%B8%E6%93%9A%E9%A1%9E%E5%9E%8B)
  * [K 線 (Candlestick) 數據](#k-%E7%B7%9A-candlestick-%E6%95%B8%E6%93%9A)
  * [支持的時間框架](#%E6%94%AF%E6%8C%81%E7%9A%84%E6%99%82%E9%96%93%E6%A1%86%E6%9E%B6)
- [🚀 數據載入流程](#%F0%9F%9A%80-%E6%95%B8%E6%93%9A%E8%BC%89%E5%85%A5%E6%B5%81%E7%A8%8B)
  * [1. 初始化數據串流](#1-%E5%88%9D%E5%A7%8B%E5%8C%96%E6%95%B8%E6%93%9A%E4%B8%B2%E6%B5%81)
  * [2. 載入歷史數據](#2-%E8%BC%89%E5%85%A5%E6%AD%B7%E5%8F%B2%E6%95%B8%E6%93%9A)
  * [3. 數據格式](#3-%E6%95%B8%E6%93%9A%E6%A0%BC%E5%BC%8F)
- [⚙️ API 限制與優化](#%E2%9A%99%EF%B8%8F-api-%E9%99%90%E5%88%B6%E8%88%87%E5%84%AA%E5%8C%96)
  * [Binance API 限制](#binance-api-%E9%99%90%E5%88%B6)
  * [我們的優化策略](#%E6%88%91%E5%80%91%E7%9A%84%E5%84%AA%E5%8C%96%E7%AD%96%E7%95%A5)
- [📊 數據質量](#%F0%9F%93%8A-%E6%95%B8%E6%93%9A%E8%B3%AA%E9%87%8F)
  * [數據準確性](#%E6%95%B8%E6%93%9A%E6%BA%96%E7%A2%BA%E6%80%A7)
  * [數據時區](#%E6%95%B8%E6%93%9A%E6%99%82%E5%8D%80)
  * [數據缺失處理](#%E6%95%B8%E6%93%9A%E7%BC%BA%E5%A4%B1%E8%99%95%E7%90%86)
- [🔍 數據驗證](#%F0%9F%94%8D-%E6%95%B8%E6%93%9A%E9%A9%97%E8%AD%89)
  * [自動驗證檢查](#%E8%87%AA%E5%8B%95%E9%A9%97%E8%AD%89%E6%AA%A2%E6%9F%A5)
  * [手動驗證示例](#%E6%89%8B%E5%8B%95%E9%A9%97%E8%AD%89%E7%A4%BA%E4%BE%8B)
- [💡 使用示例](#%F0%9F%92%A1-%E4%BD%BF%E7%94%A8%E7%A4%BA%E4%BE%8B)
  * [基礎用法](#%E5%9F%BA%E7%A4%8E%E7%94%A8%E6%B3%95)
  * [高級用法：多交易對](#%E9%AB%98%E7%B4%9A%E7%94%A8%E6%B3%95%E5%A4%9A%E4%BA%A4%E6%98%93%E5%B0%8D)
- [🛠️ 故障排除](#%F0%9F%9B%A0%EF%B8%8F-%E6%95%85%E9%9A%9C%E6%8E%92%E9%99%A4)
  * [常見問題](#%E5%B8%B8%E8%A6%8B%E5%95%8F%E9%A1%8C)
- [📚 參考資料](#%F0%9F%93%9A-%E5%8F%83%E8%80%83%E8%B3%87%E6%96%99)
  * [Binance API 文檔](#binance-api-%E6%96%87%E6%AA%94)
  * [相關檔案](#%E7%9B%B8%E9%97%9C%E6%AA%94%E6%A1%88)
- [✅ 總結](#%E2%9C%85-%E7%B8%BD%E7%B5%90)

<!-- tocstop -->

---

## 📊 數據來源概覽

BioNeuronai 回測系統使用 **Binance Futures API** 作為真實歷史數據來源。

### 為什麼選擇 Binance？

| 優勢 | 說明 |
|------|------|
| ✅ **免費** | 歷史 K 線數據完全免費，無需 API 密鑰 |
| ✅ **深度** | 支持多年歷史數據 |
| ✅ **高頻** | 最小 1 分鐘 K 線 |
| ✅ **可靠** | 全球最大交易所，數據準確性高 |
| ✅ **完整** | 提供 OHLCV + 輔助數據 |

---

## 🔌 API 端點

### 主網 (Mainnet)
```
基礎 URL: https://fapi.binance.com
K線端點: /fapi/v1/klines
```

### 測試網 (Testnet)
```
基礎 URL: https://testnet.binancefuture.com
K線端點: /fapi/v1/klines
```

---

## 📈 支持的數據類型

### K 線 (Candlestick) 數據

每根 K 線包含以下字段：

| 字段 | 類型 | 說明 |
|------|------|------|
| **open_time** | int64 | 開盤時間（毫秒時間戳） |
| **open** | string | 開盤價 |
| **high** | string | 最高價 |
| **low** | string | 最低價 |
| **close** | string | 收盤價 |
| **volume** | string | 成交量 |
| **close_time** | int64 | 收盤時間（毫秒時間戳） |
| **quote_volume** | string | 成交額 |
| **trades** | int | 成交筆數 |
| **taker_buy_base** | string | 主動買入成交量 |
| **taker_buy_quote** | string | 主動買入成交額 |

### 支持的時間框架

```
1m  - 1 分鐘
3m  - 3 分鐘
5m  - 5 分鐘
15m - 15 分鐘
30m - 30 分鐘
1h  - 1 小時
2h  - 2 小時
4h  - 4 小時
6h  - 6 小時
8h  - 8 小時
12h - 12 小時
1d  - 1 天
3d  - 3 天
1w  - 1 週
1M  - 1 個月
```

---

## 🚀 數據載入流程

### 1. 初始化數據串流
```python
from backtest.data_stream import HistoricalDataStream

stream = HistoricalDataStream(
    data_dir="backtest/data/binance_historical",
    symbol="BTCUSDT",
    interval="1h",
    start_date="2025-01-01",
    end_date="2025-12-31",
)
```

### 2. 載入歷史數據
```python
df = stream.load_data()
print(f"載入 {len(df)} 根 K 線")
print(df.head())
```

### 3. 數據格式
```python
# DataFrame 列名
['open_time', 'open', 'high', 'low', 'close', 'volume']

# 數據類型
open_time: datetime64[ns]
open:      float64
high:      float64
low:       float64
close:     float64
volume:    float64
```

---

## ⚙️ API 限制與優化

### Binance API 限制

| 限制類型 | 數值 | 說明 |
|----------|------|------|
| **單次請求** | 最多 1500 根 K 線 | 超過需分批請求 |
| **請求頻率** | 1200 次/分鐘 | 權重計算 |
| **IP 限制** | 2400 次/分鐘 | 多賬號共享 |

### 我們的優化策略

#### 1. 分批載入
```python
# 自動分批，每次 1500 根
while current_start < end_date:
    chunk_end = current_start + timedelta(seconds=interval_seconds * 1500)
    klines = client.get_klines(
        symbol=symbol,
        interval=interval,
        start_time=int(current_start.timestamp() * 1000),
        end_time=int(chunk_end.timestamp() * 1000),
        limit=1500
    )
    all_klines.extend(klines)
    current_start = chunk_end
```

#### 2. 速率控制
```python
# 請求間隔 200ms
await asyncio.sleep(0.2)
```

#### 3. 異步執行
```python
# 使用 asyncio.to_thread 避免阻塞
klines = await asyncio.to_thread(
    client.get_klines,
    symbol=symbol,
    interval=interval,
    ...
)
```

---

## 📊 數據質量

### 數據準確性

✅ **Binance 數據質量保證**:
- 毫秒級時間戳精度
- 實時更新（最新 K 線可能未完成）
- 歷史數據回填完整

### 數據時區

⚠️ **重要**: Binance API 返回 **UTC+0** 時區數據

```python
# 轉換為本地時區
data['open_time'] = pd.to_datetime(data['open_time'], unit='ms')
data['open_time'] = data['open_time'].dt.tz_localize('UTC').dt.tz_convert('Asia/Taipei')
```

### 數據缺失處理

```python
# 檢查缺失 K 線
expected_count = (end_date - start_date).total_seconds() / interval_seconds
actual_count = len(data)

if actual_count < expected_count * 0.95:
    logger.warning(f"數據缺失: {expected_count - actual_count} 根 K 線")
```

---

## 🔍 數據驗證

### 自動驗證檢查

載入器會自動執行以下檢查：

```python
# 1. 時間順序驗證
assert data['open_time'].is_monotonic_increasing

# 2. 價格範圍驗證
assert (data['high'] >= data['low']).all()
assert (data['high'] >= data['open']).all()
assert (data['high'] >= data['close']).all()
assert (data['low'] <= data['open']).all()
assert (data['low'] <= data['close']).all()

# 3. 數量完整性
assert len(data) > 0
```

### 手動驗證示例

```python
# 檢查數據統計
print(data.describe())

# 檢查異常值
volatility = (data['high'] - data['low']) / data['open']
outliers = volatility[volatility > 0.1]  # 波動 > 10%
print(f"異常波動 K 線: {len(outliers)}")

# 檢查成交量
zero_volume = data[data['volume'] == 0]
print(f"零成交量 K 線: {len(zero_volume)}")
```

---

## 💡 使用示例

### 基礎用法
```python
from backtest.data_stream import HistoricalDataStream

stream = HistoricalDataStream(
    data_dir="backtest/data/binance_historical",
    symbol="BTCUSDT",
    interval="1h",
    start_date="2025-01-01",
    end_date="2025-12-31",
)
data = stream.load_data()

print(f"✅ 成功載入 {len(data)} 根 K 線")
print(f"時間範圍: {data['open_time'].iloc[0]} 到 {data['open_time'].iloc[-1]}")
print(f"平均價格: ${data['close'].mean():,.2f}")
print(f"總成交量: {data['volume'].sum():,.0f}")
```

### 高級用法：多交易對
```python
from backtest.data_stream import HistoricalDataStream

def load_multiple_symbols():
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    all_data = {}

    for symbol in symbols:
        stream = HistoricalDataStream(
            data_dir="backtest/data/binance_historical",
            symbol=symbol,
            interval="1h",
            start_date="2025-01-01",
            end_date="2025-01-31",
        )
        data = stream.load_data()
        all_data[symbol] = data
        print(f"✅ {symbol}: {len(data)} 根 K 線")

    return all_data
```

---

## 🛠️ 故障排除

### 常見問題

#### 1. 請求失敗
```
錯誤: HTTPError 429 Too Many Requests
原因: 超過 API 速率限制
解決: 增加請求間隔時間 (await asyncio.sleep(0.5))
```

#### 2. 數據缺失
```
警告: 無數據 - YYYY-MM-DD 到 YYYY-MM-DD
原因: 
  - 交易對不存在
  - 時間範圍超出歷史深度
  - 網絡連接問題
解決: 檢查交易對名稱、縮短時間範圍、檢查網絡
```

#### 3. 時區問題
```
問題: K 線時間與本地時間不符
原因: Binance 使用 UTC+0
解決: 轉換時區（見上方"數據時區"章節）
```

---

## 📚 參考資料

### Binance API 文檔
- [Binance Futures API 文檔](https://binance-docs.github.io/apidocs/futures/en/)
- [Klines/Candlestick Data](https://binance-docs.github.io/apidocs/futures/en/#kline-candlestick-data)
- [API 速率限制](https://binance-docs.github.io/apidocs/futures/en/#limits)

### 相關檔案
- `backtest/data_stream.py` - 歷史數據載入與串流實現
- `backtest/backtest_engine.py` - 正式 replay backtest 主鏈
- `src/bioneuronai/data/binance_futures.py` - Binance API 客戶端
- `backtest/README.md` - 回測模組說明

---

## ✅ 總結

**數據來源**: Binance Futures API  
**免費使用**: ✅ 是  
**需要密鑰**: ❌ 否（僅查詢歷史數據）  
**數據質量**: ⭐⭐⭐⭐⭐ 優秀  
**更新頻率**: 實時  
**歷史深度**: 數年  

**最大優勢**: 
- 完全免費
- 數據準確
- API 穩定
- 全球可訪問

**注意事項**:
- API 速率限制 (1200 次/分鐘)
- 單次最多 1500 根 K 線
- UTC+0 時區

---

**最後更新**: 2026-04-25  
**維護者**: BioNeuronai 開發團隊
