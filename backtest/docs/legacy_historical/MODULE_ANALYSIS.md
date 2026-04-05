# data_downloads 模塊分析報告
更新時間: 2026-01-23

## 📁 模塊結構

```
data_downloads/
├── ai_trade_nexttick.py        # ✨ 核心：AI 實際交易執行
├── data_feeder.py              # 歷史數據餵送器
├── mock_api.py                 # 模擬 API 連接
├── run_backtest.py             # 回測系統
├── test_simple.py              # 簡單測試
├── README.md                   # 模塊說明文檔
├── QUICKSTART.md              # 快速開始指南
├── scripts/                    # 數據下載腳本
│   ├── download-kline.py      # K線下載
│   ├── download-trade.py      # 交易數據下載
│   ├── download-aggTrade.py   # 聚合交易下載
│   ├── download-futures-*.py  # 期貨數據下載
│   ├── enums.py               # 常量定義
│   ├── utility.py             # 工具函數
│   └── requirements.txt       # 依賴清單
└── binance_historical/         # 歷史數據存儲
    ├── spot/                  # 現貨數據
    └── futures/               # 期貨數據 (USD-M)
```

## 🎯 核心腳本功能

### 1. ai_trade_nexttick.py ⭐ (已修正)
**功能**: 核心 AI 交易執行腳本
- **AI 讀取歷史**: 每根 K 線讀取前 100 根歷史數據
- **AI 推論決策**: 111.2M 參數神經網路，輸出 long/short/neutral
- **執行交易**: 虛擬帳戶模擬（10000 USDT），真實手續費
- **防偷看機制**: 只能訪問當前時間之前的數據

**修正內容**:
- 修復持倉檢查時的類型轉換錯誤
- 避免 `abs(float(pos["positionAmt"]))` 導致的字符串錯誤
- 分離變量提取和計算邏輯

**測試結果** (2026-01-10~15):
- 575 根 K 線，執行 1 筆交易
- Bar 186: weak_short @ $3114.37 (51.7%)
- 收益: -0.10%

### 2. data_feeder.py
**功能**: 歷史數據餵送器
- 按時間順序逐條餵送數據
- 可調速度（speed_multiplier）
- 支持暫停、繼續、跳過
- 回調函數處理每條數據

**關鍵特性**:
```python
HistoricalDataFeeder(
    symbol="ETHUSDT",
    interval="1m",
    start_date="2025-12-22",
    end_date="2026-01-21",
    speed_multiplier=1.0  # 1=實時, 0=無延遲
)
```

**用途**: 模擬實時數據流，用於策略回測

### 3. mock_api.py
**功能**: 模擬 Binance API 連接
- 假裝連接真實 API
- 按順序餵送 K 線數據
- 測試模式：只載入指定日期

**配置**:
```python
SYMBOL = "ETHUSDT"
INTERVAL = "1m"
SPEED = 100        # 100倍速
TEST_DATE = "2025-12-22"
```

**用途**: 離線測試 API 交互邏輯

### 4. run_backtest.py
**功能**: 歷史數據回測系統
- 連接 AI 推論引擎
- 載入 100M 參數模型
- 統計交易信號（buy/sell/hold）

**集成**:
- 使用 `InferenceEngine`
- 載入 `HundredMillionModel`
- 最小信心度 0.6

**用途**: 驗證 AI 策略表現

### 5. test_simple.py
**功能**: 簡單測試腳本
- 快速驗證數據載入
- 測試基本功能

## 📥 數據下載腳本 (scripts/)

### 下載工具
| 腳本 | 功能 | 支持市場 |
|------|------|---------|
| `download-kline.py` | K線數據 | spot, um, cm |
| `download-trade.py` | 交易數據 | spot, um, cm |
| `download-aggTrade.py` | 聚合交易 | spot, um, cm |
| `download-futures-indexPriceKlines.py` | 指數價格 K線 | um, cm |
| `download-futures-markPriceKlines.py` | 標記價格 K線 | um, cm |
| `download-futures-premiumIndexKlines.py` | 溢價指數 K線 | um, cm |

### 數據來源
- **Binance Public Data**: https://data.binance.vision/
- 提供免費的歷史市場數據
- 包含現貨、期貨、幣本位期貨

### 支持的時間間隔
```
1s, 1m, 3m, 5m, 15m, 30m,
1h, 2h, 4h, 6h, 8h, 12h,
1d, 3d, 1w, 1mo
```

### 使用示例
```bash
# 下載 ETHUSDT 15分鐘 K線
cd data_downloads/scripts
python download-kline.py -t um -s ETHUSDT -i 15m

# 下載多個交易對
python download-kline.py -t um -s ETHUSDT BTCUSDT -i 15m 1h

# 指定日期範圍
python download-kline.py -t um -s ETHUSDT -i 15m \
    -startDate 2025-12-01 -endDate 2026-01-21
```

## 📊 已下載數據

### ETHUSDT 15分鐘 K線
- **路徑**: `binance_historical/data/futures/um/daily/klines/ETHUSDT/15m/`
- **時間範圍**: 2025-12-22 ~ 2026-01-21 (30 天)
- **完整度**: 100% (96 根/天)
- **格式**: CSV (壓縮成 ZIP)

**數據欄位**:
```
open_time, open, high, low, close, volume,
close_time, quote_volume, count,
taker_buy_volume, taker_buy_quote_volume, ignore
```

## 🔄 工作流程

### 1. 數據下載流程
```
scripts/download-kline.py
    ↓
binance_historical/data/futures/um/daily/klines/
    ↓
ETHUSDT/15m/2025-12-22_2026-01-21/*.zip
```

### 2. AI 交易流程
```
ai_trade_nexttick.py
    ↓
MockBinanceConnector (讀取 ZIP 數據)
    ↓
next_tick() 推進時間
    ↓
AI 推論 (111.2M 參數)
    ↓
執行交易決策
```

### 3. 回測流程
```
run_backtest.py
    ↓
HistoricalDataFeeder (餵送數據)
    ↓
InferenceEngine (AI 分析)
    ↓
統計信號 (buy/sell/hold)
```

## 🔧 依賴關係

### scripts/requirements.txt
```
requests
pandas
```

### 模塊依賴
```python
# ai_trade_nexttick.py
from bioneuronai.backtest import MockBinanceConnector
from bioneuronai.core.trading_engine import TradingEngine

# run_backtest.py
from bioneuronai.core import InferenceEngine
from bioneuronai.data_models import MarketData

# data_feeder.py
import pandas, zipfile, logging
```

## 💡 使用建議

### 開發測試
```bash
# 1. 下載數據 (如果還沒有)
cd data_downloads/scripts
python download-kline.py -t um -s ETHUSDT -i 15m

# 2. 運行 AI 交易測試
cd ..
python ai_trade_nexttick.py
```

### 數據更新
```bash
# 更新最新數據
cd scripts
python download-kline.py -t um -s ETHUSDT -i 15m \
    -startDate 2026-01-21
```

### 回測策略
```bash
# 運行完整回測
python run_backtest.py
```

## ⚠️ 注意事項

1. **數據存儲**: ZIP 文件需要解壓讀取，注意磁盤空間
2. **時間校準**: 確保系統時區正確（數據是 UTC+8）
3. **依賴版本**: 確保 pandas 版本兼容
4. **API 限制**: Binance Public Data 無需 API Key，但有下載速率限制

## 🚀 下一步優化

### 高優先級
1. 整合 `data_feeder.py` 到 `MockBinanceConnector`
2. 統一數據讀取接口
3. 添加數據緩存機制

### 中優先級
4. 支持更多交易對
5. 添加數據完整性檢查
6. 自動化數據更新腳本

### 低優先級
7. 數據壓縮優化
8. 多線程下載支持
9. Web 界面管理

---
*模塊分析: 基於實際代碼審查和測試結果*
