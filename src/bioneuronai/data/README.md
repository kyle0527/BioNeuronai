# 數據基礎設施模組 (Data Infrastructure)

**路徑**: `src/bioneuronai/data/`  
**版本**: v2.1
**更新日期**: 2026-04-20
**架構層級**: Layer 0 — 基礎設施層

---

## 目錄

1. [模組概述](#模組概述)
2. [架構總覽](#架構總覽)
3. [核心文件](#核心文件)
4. [數據庫系統](#數據庫系統)
5. [API 連接器](#api-連接器)
6. [使用示例](#使用示例)
7. [性能與設計](#性能與設計)
8. [相關文檔](#相關文檔)

---

## 模組概述

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
    NewsDataFetcher,           # 同步新聞資料抓取器
    SyncExternalDataFetcher,   # 同步外部市場資料抓取器
)
```

---

## 架構總覽

```text
src/bioneuronai/data/
├── __init__.py                 # 模組入口
├── binance_futures.py          # Binance Futures API 連接器
├── database_manager.py         # 統一數據庫管理器
├── database.py                 # 舊版數據庫接口（保留中）
├── exchange_rate_service.py    # 即時匯率服務
├── web_data_fetcher.py         # 非同步外部市場數據抓取器
├── news_data_fetcher.py        # 同步新聞資料抓取器
└── sync_external_fetcher.py    # 同步外部市場資料抓取器
```

補充檔案：
1. [USAGE_GUIDE.md](USAGE_GUIDE.md)
2. `image/` 目前是輔助素材資料夾，不是下一層 README 文件鏈

檔案對照：
1. [__init__.py](__init__.py)
2. [binance_futures.py](binance_futures.py)
3. [database_manager.py](database_manager.py)
4. [database.py](database.py)
5. [exchange_rate_service.py](exchange_rate_service.py)
6. [web_data_fetcher.py](web_data_fetcher.py)
7. [news_data_fetcher.py](news_data_fetcher.py)
8. [sync_external_fetcher.py](sync_external_fetcher.py)
9. [USAGE_GUIDE.md](USAGE_GUIDE.md)

這個資料夾目前沒有更深一層的 README 子文件，因此本文件直接維護到檔案與公開服務層級。

注意：
1. `web_data_fetcher.py` 存在於資料夾內，但目前不在 `bioneuronai.data.__all__` 的主匯出列表
2. `database.py` 也不在主匯出列表；新開發應優先使用 `database_manager.py`

---

## 核心文件

### `binance_futures.py` — Binance Futures API 連接器

全功能 Binance 期貨 API 連接器，涵蓋 REST 查詢、WebSocket 實時推送、認證簽名與自動重連。

**主要類**:
- `BinanceFuturesConnector` — 主連接器
- `OrderResult` — 訂單結果 dataclass

**核心功能**:
```python
# REST API — 市場數據
connector.get_ticker_price(symbol)        # 獲取實時價格
connector.get_ticker_24hr(symbol)         # 24hr 價格統計
connector.get_klines(symbol, interval, limit)   # K 線數據
connector.get_order_book(symbol, limit)   # 訂單簿深度
connector.get_funding_rate(symbol, limit) # 資金費率
connector.get_open_interest(symbol)       # 未平倉合約數

# REST API — 帳戶與交易
connector.get_account_info()             # 帳戶信息（需簽名）
connector.get_exchange_info(symbol)      # 交易對規則
connector.place_order(symbol, side, order_type, quantity, ...)  # 下單

# WebSocket 實時推送
connector.subscribe_ticker_stream(symbol, callback, auto_reconnect)  # 訂閱價格流
connector.close_all_connections()        # 關閉所有 WebSocket 連接
```

**安全特性**: HMAC-SHA256 請求簽名 · 速率限制 · 斷線自動重連（最多 10 次）

---

### `database_manager.py` — 統一數據庫管理器

主要數據持久化核心，管理 11 張資料表，取代已廢棄的 `database.py`。

**主要類**:
- `DatabaseManager` — 統一管理器（線程安全）
- `get_database_manager()` — 全局單例工廠函式

**11 張資料表與對應方法**:

| 資料表 | 用途 | 保存方法 | 查詢方法 |
|--------|------|----------|----------|
| `trades` | 交易記錄 | `save_trade()` | `get_trades()` / `get_trade_statistics()` |
| `signals` | 交易信號 | `save_signal()` | `get_signals()` / `mark_signal_executed()` |
| `risk_stats` | 風險統計快照 | `save_risk_stats()` | `get_latest_risk_stats()` / `get_risk_stats_history()` |
| `pretrade_checks` | 交易前檢查 | `save_pretrade_check()` | `get_pretrade_checks()` |
| `news_analysis` | 新聞分析 | `save_news_analysis()` | `get_recent_news()` / `estimate_news_duration()` / `count_related_news()` |
| `performance_metrics` | 性能指標 | `save_performance_metric()` | `get_performance_metrics()` |
| `news_predictions` | 新聞預測 | `save_news_prediction()` | `get_pending_predictions()` / `get_prediction_accuracy()` |
| `strategy_genes` | 策略基因 | `save_strategy_gene()` | `get_best_genes()` / `update_gene_fitness()` / `deactivate_genes()` |
| `evolution_history` | 演化歷史 | `save_evolution_record()` | `get_evolution_history()` |
| `rl_training_history` | RL 訓練歷程 | `save_rl_training_step()` | `get_rl_training_progress()` |
| `event_memory` | 市場事件記憶 | `save_event()` | `get_active_events()` / `resolve_event()` / `calculate_total_event_score()` |

> **2026-03-29 更新**：`calculate_total_event_score()` 實作線性時間衰減。公式：`decay_factor = max(0.1, 1.0 - (age_hours / decay_hours) * 0.5)`，`decay_hours` 從各事件的 `metadata` 欄位中讀取（預設 72 小時）。最終分數以 `score × confidence × decay_factor` 累加後限制在 [-1.0, 1.0]，並回傳 `Tuple[float, List[Dict]]`。

**維護功能**: `export_to_json()` · `cleanup_old_data()` · `get_database_stats()` · `close()`

---

### `database.py` — 舊版數據庫接口

> ⚠️ **已廢棄 (Deprecated)**：本檔案不再主動維護，**新開發請一律使用 `DatabaseManager`**。  
> 保留原因：管理 3 張尚未遷移至 `database_manager.py` 的獨立資料表（`trading_pairs`、`strategy_weights`、`account_snapshots`），且未匯出至 `__init__.py`。

**資料模型**: `TradingPair` · `TradeRecord` (dataclasses)

---

### `exchange_rate_service.py` — 即時匯率服務

不落庫的即時匯率查詢與轉換服務，具備三級數據源自動回退。

**主要類**:
- `ExchangeRateService` — 匯率服務
- `ExchangeRateInfo` — 匯率結果 dataclass（`from_currency`, `to_currency`, `rate`, `source`, `updated_at`, `is_realtime`）

**三級數據源回退**:
1. **ExchangeRate-API** — 主要來源（免費 API）
2. **Binance USDT 穩定幣匯率** — 備用來源
3. **固定匯率表** — 離線回退（支援 USD/TWD/EUR/JPY/GBP/KRW/AUD/SGD/HKD）

**快取策略**: TTL = 300 秒 (5 分鐘)，線程安全（`threading.Lock`）

**API 方法**: `get_rate()` · `convert()` · `get_all_rates()` · `clear_cache()` · `format_conversion()`

---

### `web_data_fetcher.py` — 外部市場數據抓取器

基於 `asyncio` + `aiohttp` 的非同步批量外部數據抓取器，為上層分析模組提供市場情緒與宏觀指標。  
**必須在 `async with` 上下文中使用。**

**數據源與指標**:

| 數據源 | 提供指標 | 數據模型 |
|--------|----------|----------|
| Alternative.me | 恐慌貪婪指數 (0-100) | `FearGreedIndex` |
| CoinGecko | 全球市場總覽（總市值、BTC 佔比、24hr 交易量） | `GlobalMarketData` |
| CoinGecko | 穩定幣供應量（USDT/USDC/DAI/FDUSD） | `StablecoinMetrics` |
| DefiLlama | DeFi TVL（各鏈分布） | `DeFiMetrics` |

**已知限制**（設計性邊界，非 Bug）：
- `tvl_change_24h`、`supply_change_24h/7d` — 硬編碼 `0.0`，需歷史快照 API 才能計算
- `economic_events` — 空 list，需接入 Forex Factory 等授權 API
- `market_sentiment` — 保留 `None`，由呼叫方在抓取後自行合成

**配置**: `APIConfig` dataclass 管理端點、超時與重試次數

---

### `news_data_fetcher.py` — 同步新聞資料抓取器

同步封裝 CryptoPanic API 與 RSS feed 讀取，供 `analysis.news.CryptoNewsAnalyzer` 注入使用。這個檔案的重點是把外部 HTTP 呼叫留在 data 層，避免 analysis 模組直接散落 `requests.get()`。

**主要類**:
- `NewsDataFetcher`

---

### `sync_external_fetcher.py` — 同步外部市場資料抓取器

同步封裝 Fear & Greed、Yahoo Finance、Binance Spot 等外部資料來源，供 daily report / market data 流程注入使用。

**主要類**:
- `SyncExternalDataFetcher`

---

## 數據庫系統

### 數據庫表結構

```
trading.db
├── trades                # 交易記錄表
│   ├── id (PRIMARY KEY), order_id, symbol, side
│   ├── quantity, price, confidence, strategy
│   └── timestamp, pnl, fee
│
├── signals               # 信號歷史表
│   ├── id (PRIMARY KEY), symbol, action, confidence
│   └── strategy_name, reason, target_price, stop_loss, take_profit, timestamp, executed
│
├── risk_stats            # 風險統計快照表
│   ├── id (PRIMARY KEY), total_trades, win_rate
│   └── sharpe_ratio, max_drawdown, total_pnl, timestamp
│
├── pretrade_checks       # 交易前檢查表
├── news_analysis         # 新聞分析表
├── performance_metrics   # 性能指標表
├── news_predictions      # 新聞預測 & 驗證表
├── strategy_genes        # 策略基因表（策略演化）
├── evolution_history     # 演化歷史記錄表
├── rl_training_history   # RL 訓練歷程表
└── event_memory          # 市場事件記憶表
```

### 數據分層策略

| 層級 | 存儲位置 | 數據範圍 | 存取速度 |
|------|---------|---------|---------|
| 熱數據 | 記憶體 + SQLite | 當日信號、持倉 | < 1ms |
| 溫數據 | SQLite | 近期交易 (90 天) | < 5ms |
| 冷數據 | 壓縮歸檔 | 歷史備份 | > 100ms |

---

## API 連接器

### Binance Futures REST API

| 類別 | 端點 | 對應方法 |
|------|------|----------|
| 市場數據 | `/fapi/v1/ticker/price` | `get_ticker_price()` |
| 24hr 統計 | `/fapi/v1/ticker/24hr` | `get_ticker_24hr()` |
| K 線數據 | `/fapi/v1/klines` | `get_klines()` |
| 訂單簿 | `/fapi/v1/depth` | `get_order_book()` |
| 資金費率 | `/fapi/v1/fundingRate` | `get_funding_rate()` |
| 未平倉量 | `/fapi/v1/openInterest` | `get_open_interest()` |
| 帳戶 | `/fapi/v2/account` | `get_account_info()` |
| 交易對規則 | `/fapi/v1/exchangeInfo` | `get_exchange_info()` |
| 下單 | `/fapi/v1/order` | `place_order()` |

### WebSocket 即時頻道

| 頻道 | 對應方法 | 說明 |
|------|----------|------|
| `<symbol>@miniTicker` | `subscribe_ticker_stream()` | 實時價格推送 |
| 所有連接 | `close_all_connections()` | 關閉所有 WebSocket |

---

## 使用示例

### 1. API 連接
```python
from bioneuronai.data import BinanceFuturesConnector

connector = BinanceFuturesConnector(
    api_key="your_key",
    api_secret="your_secret",
    testnet=True  # Demo Trading 環境
)

# 獲取即時價格
price = connector.get_ticker_price("BTCUSDT")

# 獲取 K 線（最新 100 根 1h）
klines = connector.get_klines(symbol="BTCUSDT", interval="1h", limit=100)

# 查詢資金費率（最新一筆）
funding = connector.get_funding_rate("BTCUSDT", limit=1)

# WebSocket 訂閱實時價格
def on_tick(msg):
    print(f"最新價: {msg['c']}")

connector.subscribe_ticker_stream("BTCUSDT", on_tick, auto_reconnect=True)

# 程式結束時關閉所有連接
connector.close_all_connections()
```

### 2. 數據庫操作
```python
from bioneuronai.data import get_database_manager

db = get_database_manager()  # 全局單例

# 保存交易記錄
trade_id = db.save_trade({
    'order_id': '12345', 'symbol': 'BTCUSDT',
    'side': 'BUY', 'quantity': 0.1,
    'price': 45000.0, 'strategy': 'RSI_MACD',
    'timestamp': '2026-03-16T10:00:00'
})

# 查詢交易
trades = db.get_trades(start_date='2026-03-01', symbol='BTCUSDT', limit=100)

# 保存風險快照
db.save_risk_stats({
    'total_trades': 20, 'win_rate': 0.6,
    'sharpe_ratio': 1.5, 'max_drawdown': -0.08
})

# 查詢最新風險統計
stats = db.get_latest_risk_stats()

# 保存市場事件（用於 Event Memory）
db.save_event({
    'event_id': 'war_2026_03_16',
    'event_type': 'WAR',
    'headline': 'Middle East conflict escalates',
    'score': -0.8,
    'source_confidence': 0.9
})

# 取得所有 ACTIVE 事件的加權總分
total_score, events = db.calculate_total_event_score(symbol='BTCUSDT')
```

### 3. 匯率服務
```python
from bioneuronai.data import ExchangeRateService

rate_service = ExchangeRateService()

# 查詢 USDT → TWD 匯率
rate_info = rate_service.get_rate("USD", "TWD")
print(f"USD/TWD = {rate_info.rate:.2f}  (來源: {rate_info.source})")

# 金額換算
twd_amount = rate_service.convert(1000.0, "USD", "TWD")

# 一次取得所有支援幣別
all_rates = rate_service.get_all_rates("USD")  # → Dict[str, float]

# 格式化輸出
print(rate_service.format_conversion(100.0, "USD", "TWD"))  # "100.00 USD = 3,250.00 TWD"

# 清除快取（強迫下次重新抓取）
rate_service.clear_cache()
```

### 4. 外部數據抓取
```python
import asyncio
from bioneuronai.data.web_data_fetcher import WebDataFetcher

async def main():
    # 必須在 async with 上下文中使用
    async with WebDataFetcher() as fetcher:
        # 並行抓取所有外部指標（回傳 ExternalDataSnapshot）
        snapshot = await fetcher.fetch_all()
        
        if snapshot.fear_greed:
            print(f"恐慌貪婪指數: {snapshot.fear_greed.value} ({snapshot.fear_greed.classification})")
        
        if snapshot.global_market:
            print(f"加密市場總市值: ${snapshot.global_market.total_market_cap/1e9:.0f}B")
            print(f"BTC 佔比: {snapshot.global_market.btc_dominance:.1f}%")
        
        if snapshot.defi_metrics:
            print(f"DeFi TVL: ${snapshot.defi_metrics.total_tvl/1e9:.1f}B")
        
        # 也可以單獨抓取
        fear_greed = await fetcher.fetch_fear_greed_index()
        stablecoins = await fetcher.fetch_stablecoin_metrics()

asyncio.run(main())
```

---

## 性能與設計

| 特性 | 說明 |
|------|------|
| 線程安全 | `threading.local()` + `contextmanager` 管理獨立 SQLite 連線 |
| 自動重連 | WebSocket 斷線自動重建，最多 10 次，指數退避延遲 |
| 快取機制 | 匯率 5 分鐘 TTL，`threading.Lock` 保護 |
| 批量處理 | `asyncio.gather()` 並行抓取 4 個外部數據源 |
| 雙重備份 | SQLite + JSONL 並行存儲（可透過 `backup_enabled` 開關） |
| 非同步 | 外部數據使用 `asyncio` + `aiohttp`，支持重試與超時 |
| 依賴保護 | 外部 HTTP 失敗時以明確錯誤或空結果回報，由上層決定是否中止 |

---

## 相關文檔

1. [USAGE_GUIDE.md](USAGE_GUIDE.md)

- **使用手冊**: [USAGE_GUIDE.md](./USAGE_GUIDE.md)
- **數據庫升級指南**: [DATABASE_UPGRADE_GUIDE.md](../../../docs/DATABASE_UPGRADE_GUIDE.md)
- **數據存儲策略**: [DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md](../../../docs/DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md)
- **數據來源指南**: [DATA_SOURCES_GUIDE.md](../../../archived/docs_v2_1_legacy/DATA_SOURCES_GUIDE.legacy_20260406.md)
- **父模組**: [BioNeuronai 主模組](../README.md)

---

**最後更新**: 2026 年 4 月 19 日

> 📖 上層目錄：[src/bioneuronai/README.md](../README.md)
