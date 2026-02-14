# 數據連接模組 (Data Connectors)

**路徑**: `src/bioneuronai/data/`  
**版本**: v4.0 (系統升級版)  
**更新日期**: 2026-02-14

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [核心文件](#核心文件)
3. [數據庫系統](#數據庫系統)
4. [API 連接器](#api-連接器)
5. [使用示例](#使用示例)
6. [相關文檔](#相關文檔)

---

## 🎯 模組概述

數據連接模組提供與外部交易所和內部數據庫的連接功能。

### 模組職責
- ✅ Binance Futures API 連接
- ✅ SQLite 數據庫管理
- ✅ 匯率服務
- ✅ 數據持久化
- ✅ 實時數據流

---

## 📁 核心文件

### `binance_futures.py` (API 連接器)
Binance Futures API 完整實現。

**主要類**:
- `BinanceFuturesConnector` - Binance API 連接器

**核心功能**:
```python
# REST API
- get_ticker_price()      # 獲取實時價格
- get_klines()            # 獲取 K 線數據
- get_order_book()        # 獲取訂單簿
- place_order()           # 下單
- get_account_balance()   # 獲取帳戶餘額

# WebSocket
- start_ticker_socket()   # 實時價格推送
- start_kline_socket()    # 實時 K 線推送
```

### `database_manager.py` (NEW - 數據庫管理器)
統一的 SQLite 數據庫管理接口。

**主要類**:
- `DatabaseManager` - 數據庫管理器

**核心功能**:
```python
# 數據保存
- save_trade()            # 保存交易記錄
- save_signal()           # 保存交易信號
- save_risk_stats()       # 保存風險統計

# 數據查詢
- get_trades()            # 查詢交易記錄
- get_signals()           # 查詢信號歷史
- get_latest_risk_stats() # 獲取最新風險統計

# 數據維護
- export_to_json()        # 導出為 JSON
- cleanup_old_data()      # 清理舊數據
- get_database_stats()    # 獲取數據庫統計
```

### `database.py` (舊版數據庫接口)
傳統數據庫接口（保留用於向後兼容）。

**主要功能**:
- JSON 文件存儲
- 數據導出/導入
- 舊版兼容接口

### `exchange_rate_service.py`
多幣種匯率轉換服務。

**主要類**:
- `ExchangeRateService` - 匯率服務

**核心功能**:
- 實時匯率查詢
- 貨幣轉換
- 匯率緩存

---

## 🗄️ 數據庫系統

### 數據庫表結構

```
trading.db
├── trades                # 交易記錄表
│   ├── id (PRIMARY KEY)
│   ├── order_id
│   ├── symbol
│   ├── side
│   ├── quantity
│   ├── price
│   ├── timestamp
│   └── pnl
│
├── signals               # 信號歷史表
│   ├── id (PRIMARY KEY)
│   ├── symbol
│   ├── action
│   ├── confidence
│   ├── strategy_name
│   ├── timestamp
│   └── executed
│
├── risk_stats            # 風險統計表
│   ├── id (PRIMARY KEY)
│   ├── total_trades
│   ├── win_rate
│   ├── sharpe_ratio
│   ├── max_drawdown
│   └── timestamp
│
├── pretrade_checks       # 交易前檢查表
├── news_analysis         # 新聞分析表
└── performance_metrics   # 性能指標表
```

### 數據分層策略
- **熱數據** (內存): 當前信號、持倉
- **溫數據** (SQLite): 近期交易 (90 天)
- **冷數據** (歸檔): 歷史備份

---

## 🔌 API 連接器

### Binance Futures API

**支持的端點**:
| 類別 | 端點 | 說明 |
|------|------|------|
| 市場數據 | `/fapi/v1/ticker/24hr` | 24小時價格變動 |
| K線數據 | `/fapi/v1/klines` | 歷史K線 |
| 訂單簿 | `/fapi/v1/depth` | 市場深度 |
| 賬戶 | `/fapi/v2/account` | 帳戶信息 |
| 訂單 | `/fapi/v1/order` | 下單/查詢 |

**WebSocket 頻道**:
- `ticker` - 實時價格
- `kline` - 實時K線
- `depth` - 實時訂單簿
- `aggTrade` - 歸集交易流

---

## 💡 使用示例

### 1. API 連接
```python
from src.bioneuronai.data import BinanceFuturesConnector

# 初始化連接器
connector = BinanceFuturesConnector(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)

# 獲取價格
price = connector.get_ticker_price("BTCUSDT")

# 獲取K線
klines = connector.get_klines(
    symbol="BTCUSDT",
    interval="1h",
    limit=100
)

# WebSocket 實時數據
def on_message(msg):
    print(f"Price: {msg['c']}")

connector.start_ticker_socket("BTCUSDT", on_message)
```

### 2. 數據庫操作
```python
from src.bioneuronai.data import get_database_manager

# 獲取數據庫管理器
db = get_database_manager()

# 保存交易
trade_id = db.save_trade({
    'order_id': '12345',
    'symbol': 'BTCUSDT',
    'side': 'BUY',
    'quantity': 0.1,
    'price': 45000,
    'timestamp': '2026-01-22T10:00:00'
})

# 查詢交易
trades = db.get_trades(
    start_date='2026-01-01',
    symbol='BTCUSDT',
    limit=100
)

# 獲取統計
stats = db.get_latest_risk_stats()
```

### 3. 數據遷移
```python
# 從根目錄運行
python migrate_to_database.py
```

---

## 📊 性能特點

- **連接池**: 線程安全的數據庫連接
- **自動重連**: API 連接斷開自動重連
- **數據緩存**: 減少 API 調用次數
- **批量處理**: 支持批量數據操作
- **備份機制**: 雙重存儲 (SQLite + JSONL)

---

## 📚 相關文檔

- **數據庫升級指南**: [DATABASE_UPGRADE_GUIDE.md](../../../docs/DATABASE_UPGRADE_GUIDE.md)
- **數據流分析**: [DATAFLOW_ANALYSIS.md](../../../docs/DATAFLOW_ANALYSIS.md)
- **數據存儲策略**: [DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md](../../../docs/DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026年1月22日
