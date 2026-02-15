# 數據基礎設施模組 (Data Infrastructure)

**路徑**: `src/bioneuronai/data/`  
**版本**: v4.1  
**更新日期**: 2026-02-15  
**架構層級**: Layer 0 — 基礎設施層

---

## 📋 目錄

1. [模組概述](#模組概述)
2. [架構總覽](#架構總覽)
3. [核心文件](#核心文件)
4. [數據庫系統](#數據庫系統)
5. [API 連接器](#api-連接器)
6. [外部數據抓取](#外部數據抓取)
7. [匯率服務](#匯率服務)
8. [使用示例](#使用示例)
9. [性能與設計](#性能與設計)
10. [相關文檔](#相關文檔)

---

## 🎯 模組概述

數據基礎設施模組是 BioNeuronai 系統的最底層，負責所有外部數據的接入、內部數據的持久化與查詢。上層模組（core、trading、analysis、strategies）皆依賴本模組提供的數據服務。

### 模組職責
- ✅ Binance Futures REST / WebSocket API 全功能連接
- ✅ 統一數據庫管理（熱 / 溫 / 冷三層分級存儲）
- ✅ 即時匯率服務（三級數據源回退）
- ✅ 外部市場情緒 / 宏觀數據非同步抓取
- ✅ 線程安全連接池與自動重連

### 公開 API (`__init__.py` 匯出)
```python
from bioneuronai.data import (
    BinanceFuturesConnector,   # 交易所 API 連接器
    ExchangeRateService,       # 即時匯率服務
    DatabaseManager,           # 統一數據庫管理器
    get_database_manager,      # 數據庫管理器工廠函式
)
```

---

## 🏗️ 架構總覽

```
src/bioneuronai/data/
├── __init__.py                 # 模組入口 (24 行)
├── binance_futures.py          # Binance Futures API 連接器 (457 行)
├── database_manager.py         # 統一數據庫管理器 (1,356 行)
├── database.py                 # 舊版數據庫接口 - 向後兼容 (768 行)
├── exchange_rate_service.py    # 即時匯率服務 (309 行)
└── web_data_fetcher.py         # 外部市場數據抓取器 (453 行)
                                  ─────────
                                  合計 ~3,367 行
```

---

## 📁 核心文件

### `binance_futures.py` — Binance Futures API 連接器 (457 行)

全功能 Binance 期貨 API 連接器，涵蓋 REST 查詢、WebSocket 實時推送、認證簽名與自動重連。

**主要類**:
- `BinanceFuturesConnector` — 主連接器
- `OrderResult` — 訂單結果 dataclass

**核心功能**:
```python
# REST API
connector.get_ticker_price(symbol)    # 獲取實時價格
connector.get_klines(symbol, ...)     # 獲取 K 線數據
connector.get_order_book(symbol)      # 獲取訂單簿深度
connector.place_order(symbol, ...)    # 下單
connector.get_account_balance()       # 獲取帳戶餘額

# WebSocket 實時推送
connector.start_ticker_socket(symbol, callback)  # 價格推送
connector.start_kline_socket(symbol, callback)    # K 線推送
```

**安全特性**: HMAC-SHA256 請求簽名 · 速率限制 · 斷線自動重連

---

### `database_manager.py` — 統一數據庫管理器 (1,356 行)

新一代數據持久化核心，取代 `database.py`，支援六類數據的分層存儲。

**主要類**:
- `DatabaseManager` — 統一管理器
- `get_database_manager()` — 單例工廠函式

**支援的六類數據**:

| 數據類別 | 保存方法 | 查詢方法 |
|----------|----------|----------|
| 交易記錄 | `save_trade()` | `get_trades()` |
| 交易信號 | `save_signal()` | `get_signals()` |
| 風險統計 | `save_risk_stats()` | `get_latest_risk_stats()` |
| 交易前檢查 | `save_pretrade_check()` | `get_pretrade_checks()` |
| 新聞分析 | `save_news_analysis()` | `get_news_analysis()` |
| 性能指標 | `save_performance_metrics()` | `get_performance_metrics()` |

**維護功能**: `export_to_json()` · `cleanup_old_data()` · `get_database_stats()`

---

### `database.py` — 舊版數據庫接口 (768 行)

保留的向後兼容 SQLite 接口。管理交易對配置、交易記錄、信號歷史與策略權重。

**資料模型**: `TradingPair` · `ExchangeRate` · `TradeRecord` (dataclasses)

> ⚠️ 新開發請使用 `DatabaseManager`，本模組僅供舊程式碼兼容。

---

### `exchange_rate_service.py` — 即時匯率服務 (309 行)

不落庫的即時匯率查詢與轉換服務，具備三級數據源自動回退。

**主要類**:
- `ExchangeRateService` — 匯率服務
- `ExchangeRateInfo` — 匯率結果 dataclass

**三級數據源回退**:
1. **ExchangeRate-API** — 主要來源（免費 API）
2. **Binance USDT 穩定幣匯率** — 備用來源
3. **固定匯率表** — 離線回退

**快取策略**: TTL = 300 秒 (5 分鐘)，線程安全

---

### `web_data_fetcher.py` — 外部市場數據抓取器 (453 行)

基於 `asyncio` + `aiohttp` 的非同步批量外部數據抓取器，為上層分析模組提供市場情緒與宏觀指標。

**數據源與指標**:

| 數據源 | 提供指標 | 數據模型 |
|--------|----------|----------|
| Alternative.me | 恐慌貪婪指數 | `FearGreedIndex` |
| CoinGecko | 全球市場總覽 + 穩定幣供應 | `GlobalMarketData` |
| DefiLlama | DeFi TVL | `DeFiMetrics` |

**配置**: `APIConfig` dataclass 管理端點與超時設定

---

## 🗄️ 數據庫系統

### 數據庫表結構

```
trading.db
├── trades                # 交易記錄表
│   ├── id (PRIMARY KEY)
│   ├── order_id, symbol, side
│   ├── quantity, price
│   ├── timestamp, pnl
│
├── signals               # 信號歷史表
│   ├── id (PRIMARY KEY)
│   ├── symbol, action, confidence
│   ├── strategy_name, timestamp, executed
│
├── risk_stats            # 風險統計表
│   ├── id (PRIMARY KEY)
│   ├── total_trades, win_rate
│   ├── sharpe_ratio, max_drawdown, timestamp
│
├── pretrade_checks       # 交易前檢查表
├── news_analysis         # 新聞分析表
└── performance_metrics   # 性能指標表
```

### 數據分層策略

| 層級 | 存儲位置 | 數據範圍 | 存取速度 |
|------|---------|---------|---------|
| 熱數據 | 記憶體 + SQLite | 當日信號、持倉 | < 1ms |
| 溫數據 | SQLite | 近期交易 (90 天) | < 5ms |
| 冷數據 | 壓縮歸檔 | 歷史備份 | > 100ms |

---

## 🔌 API 連接器

### Binance Futures REST API

| 類別 | 端點 | 說明 |
|------|------|------|
| 市場數據 | `/fapi/v1/ticker/24hr` | 24 小時價格變動 |
| K 線數據 | `/fapi/v1/klines` | 歷史 K 線 |
| 訂單簿 | `/fapi/v1/depth` | 市場深度 |
| 賬戶 | `/fapi/v2/account` | 帳戶信息 |
| 訂單 | `/fapi/v1/order` | 下單 / 查詢 |

### WebSocket 即時頻道

| 頻道 | 用途 |
|------|------|
| `ticker` | 實時價格推送 |
| `kline` | 實時 K 線推送 |
| `depth` | 實時訂單簿更新 |
| `aggTrade` | 歸集交易流 |

---

## 💡 使用示例

### 1. API 連接
```python
from bioneuronai.data import BinanceFuturesConnector

connector = BinanceFuturesConnector(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True
)

# 獲取價格
price = connector.get_ticker_price("BTCUSDT")

# 獲取 K 線
klines = connector.get_klines(symbol="BTCUSDT", interval="1h", limit=100)

# WebSocket 實時數據
connector.start_ticker_socket("BTCUSDT", lambda msg: print(msg['c']))
```

### 2. 數據庫操作
```python
from bioneuronai.data import get_database_manager

db = get_database_manager()

# 保存交易
db.save_trade({
    'order_id': '12345', 'symbol': 'BTCUSDT',
    'side': 'BUY', 'quantity': 0.1,
    'price': 45000, 'timestamp': '2026-01-22T10:00:00'
})

# 查詢交易
trades = db.get_trades(start_date='2026-01-01', symbol='BTCUSDT', limit=100)
stats = db.get_latest_risk_stats()
```

### 3. 匯率服務
```python
from bioneuronai.data import ExchangeRateService

rate_service = ExchangeRateService()
rate_info = rate_service.get_rate("USD", "TWD")
print(f"USD/TWD = {rate_info.rate}")
```

### 4. 外部數據抓取
```python
from bioneuronai.data.web_data_fetcher import WebDataFetcher

fetcher = WebDataFetcher()
# 非同步抓取所有外部指標
snapshot = await fetcher.fetch_all()
print(f"恐慌貪婪指數: {snapshot.fear_greed.value}")
```

---

## 📊 性能與設計

| 特性 | 說明 |
|------|------|
| 線程安全 | `threading` + `contextmanager` 管理數據庫連線 |
| 自動重連 | WebSocket 斷線自動重建 |
| 快取機制 | 匯率 5 分鐘 TTL，減少 API 呼叫 |
| 批量處理 | 支持批量數據寫入與查詢 |
| 雙重備份 | SQLite + JSONL 並行存儲 |
| 非同步 | 外部數據使用 `asyncio` + `aiohttp` 高效抓取 |

---

## 📚 相關文檔

- **數據庫升級指南**: [DATABASE_UPGRADE_GUIDE.md](../../../docs/DATABASE_UPGRADE_GUIDE.md)
- **數據存儲策略**: [DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md](../../../docs/DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md)
- **數據來源指南**: [DATA_SOURCES_GUIDE.md](../../../docs/DATA_SOURCES_GUIDE.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026 年 2 月 15 日

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
