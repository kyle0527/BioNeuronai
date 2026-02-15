# 回測系統數據來源說明

**創建日期**: 2026年2月15日  
**版本**: v4.0.0

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

### 1. 初始化數據載入器
```python
from bioneuronai.backtesting.historical_backtest import HistoricalDataLoader

# 主網數據
loader = HistoricalDataLoader(use_testnet=False)

# 測試網數據
loader_test = HistoricalDataLoader(use_testnet=True)
```

### 2. 載入歷史數據
```python
from datetime import datetime

data = await loader.load_data(
    symbol="BTCUSDT",           # 交易對
    start_date=datetime(2025, 1, 1),  # 開始日期
    end_date=datetime(2025, 12, 31),  # 結束日期
    interval="1h"               # 時間框架
)

# 返回 pandas DataFrame
print(f"載入 {len(data)} 根 K 線")
print(data.head())
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
from bioneuronai.backtesting.historical_backtest import HistoricalDataLoader
from datetime import datetime
import asyncio

async def main():
    loader = HistoricalDataLoader(use_testnet=False)
    
    # 載入 BTC 2025 年全年 1 小時 K 線
    data = await loader.load_data(
        symbol="BTCUSDT",
        start_date=datetime(2025, 1, 1),
        end_date=datetime(2025, 12, 31),
        interval="1h"
    )
    
    print(f"✅ 成功載入 {len(data)} 根 K 線")
    print(f"時間範圍: {data['open_time'].iloc[0]} 到 {data['open_time'].iloc[-1]}")
    print(f"平均價格: ${data['close'].mean():,.2f}")
    print(f"總成交量: {data['volume'].sum():,.0f}")

asyncio.run(main())
```

### 高級用法：多交易對
```python
async def load_multiple_symbols():
    loader = HistoricalDataLoader(use_testnet=False)
    
    symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]
    all_data = {}
    
    for symbol in symbols:
        data = await loader.load_data(
            symbol=symbol,
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 1, 31),
            interval="1h"
        )
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
- `src/bioneuronai/backtesting/historical_backtest.py` - 數據載入實現
- `src/bioneuronai/data/binance_futures.py` - Binance API 客戶端
- `test_backtest_system.py` - 測試腳本

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

**最後更新**: 2026年2月15日  
**維護者**: BioNeuronai 開發團隊
