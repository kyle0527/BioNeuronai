# Data 模組使用指南

> 路徑：`src/bioneuronai/data/`
> 更新日期：2026-04-20
> 層級：Layer 0 — 外部資料、交易所 API、資料庫與匯率服務

本文件是 `bioneuronai.data` 的使用指南。模組總覽請看 [data README](README.md)；這裡保留可操作範例、匯入方式與常見使用邊界。

---

## 目錄

1. [公開匯出](#公開匯出)
2. [BinanceFuturesConnector](#binancefuturesconnector)
3. [DatabaseManager](#databasemanager)
4. [ExchangeRateService](#exchangerateservice)
5. [NewsDataFetcher](#newsdatafetcher)
6. [SyncExternalDataFetcher](#syncexternaldatafetcher)
7. [WebDataFetcher](#webdatafetcher)
8. [使用邊界](#使用邊界)
9. [快速驗證](#快速驗證)

---

## 公開匯出

`bioneuronai.data.__init__` 目前公開匯出：

```python
from bioneuronai.data import (
    BinanceFuturesConnector,
    ExchangeRateService,
    DatabaseManager,
    get_database_manager,
    NewsDataFetcher,
    SyncExternalDataFetcher,
)
```

未在 `__init__.py` 公開匯出的元件需直接從檔案匯入，例如：

```python
from bioneuronai.data.web_data_fetcher import WebDataFetcher, APIConfig
from bioneuronai.data.binance_futures import OrderResult
```

---

## BinanceFuturesConnector

`BinanceFuturesConnector` 封裝 Binance Futures REST / WebSocket。

```python
from bioneuronai.data import BinanceFuturesConnector

connector = BinanceFuturesConnector(
    api_key="",
    api_secret="",
    testnet=True,
)
```

公開市場資料不需要 API key：

```python
price = connector.get_ticker_price("BTCUSDT")
klines = connector.get_klines("BTCUSDT", interval="1h", limit=100)
order_book = connector.get_order_book("BTCUSDT", limit=20)
funding = connector.get_funding_rate("BTCUSDT", limit=1)
open_interest = connector.get_open_interest("BTCUSDT")
```

帳戶與下單需要有效 API key：

```python
account = connector.get_account_info()
exchange_info = connector.get_exchange_info("BTCUSDT")

result = connector.place_order(
    symbol="BTCUSDT",
    side="BUY",
    order_type="MARKET",
    quantity=0.001,
)
```

WebSocket ticker stream：

```python
def on_tick(message: dict):
    print(message.get("s"), message.get("c"))

connector.subscribe_ticker_stream("BTCUSDT", on_tick, auto_reconnect=True)
connector.close_all_connections()
```

---

## DatabaseManager

`DatabaseManager` 是目前主要資料庫入口。

```python
from bioneuronai.data import get_database_manager

db = get_database_manager()
```

預設 DB 路徑：

```text
data/bioneuronai/trading/runtime/trading.db
```

常用操作：

```python
trade_id = db.save_trade({
    "order_id": "ORD_001",
    "symbol": "BTCUSDT",
    "side": "BUY",
    "quantity": 0.001,
    "price": 45000.0,
    "strategy": "manual",
})

trades = db.get_trades(symbol="BTCUSDT", limit=50)
stats = db.get_trade_statistics(days=30)
```

信號與風險快照：

```python
signal_id = db.save_signal({
    "symbol": "ETHUSDT",
    "action": "LONG",
    "confidence": 0.82,
    "strategy_name": "TrendFollowing",
    "reason": "trend setup",
})

db.mark_signal_executed(signal_id)

db.save_risk_stats({
    "total_trades": 45,
    "win_rate": 0.62,
    "sharpe_ratio": 1.8,
    "max_drawdown": -0.073,
    "total_pnl": 1250.5,
})
```

事件記憶：

```python
db.save_event({
    "event_id": "macro_001",
    "event_type": "MACRO",
    "headline": "Fed guidance changes market expectations",
    "score": -0.4,
    "source_confidence": 0.8,
    "affected_symbols": "BTCUSDT,ETHUSDT",
})

total_score, active_events = db.calculate_total_event_score(symbol="BTCUSDT")
```

維護：

```python
db.export_to_json(output_dir="data/bioneuronai/trading/exports")
db.cleanup_old_data(keep_days=90)
db.close()
```

---

## ExchangeRateService

`ExchangeRateService` 提供即時匯率查詢、轉換與格式化。

```python
from bioneuronai.data import ExchangeRateService

rate_service = ExchangeRateService()
rate_info = rate_service.get_rate("USD", "TWD")

if rate_info:
    print(rate_info.rate, rate_info.source, rate_info.is_realtime)
```

換算與批量查詢：

```python
twd = rate_service.convert(1000.0, "USD", "TWD")
rates = rate_service.get_all_rates("USD")
text = rate_service.format_conversion(5000.0, "USD", "TWD")
rate_service.clear_cache()
```

---

## NewsDataFetcher

`NewsDataFetcher` 是同步新聞抓取器，供 `analysis.news.CryptoNewsAnalyzer` 注入使用。它把 CryptoPanic / RSS HTTP 呼叫集中在 data 層。

```python
from bioneuronai.data import NewsDataFetcher

fetcher = NewsDataFetcher()
cryptopanic_articles = fetcher.fetch_cryptopanic("BTC")
rss_articles = fetcher.fetch_all_rss("BTC")
```

單一 RSS：

```python
items = fetcher.fetch_rss_feed(
    "https://cointelegraph.com/rss",
    coin="BTC",
)
```

失敗時回傳空 list，不向上拋 HTTP exception。

---

## SyncExternalDataFetcher

`SyncExternalDataFetcher` 是同步外部市場資料抓取器，供 analysis / daily report 等同步流程使用。

```python
from bioneuronai.data import SyncExternalDataFetcher

fetcher = SyncExternalDataFetcher()

fear_greed = fetcher.fetch_fear_greed_index()
indices = fetcher.fetch_global_stock_indices()
spot_sentiment = fetcher.fetch_binance_spot_sentiment()
```

失敗時回傳 `None` 或空結果，由呼叫方決定是否中止流程。

---

## WebDataFetcher

`WebDataFetcher` 是非同步外部市場資料抓取器，適合已有 event loop 或需要並行抓取的流程。它目前未從 `bioneuronai.data` 頂層匯出，需直接匯入。

```python
import asyncio
from bioneuronai.data.web_data_fetcher import WebDataFetcher, APIConfig

async def main():
    async with WebDataFetcher() as fetcher:
        snapshot = await fetcher.fetch_all()
        return snapshot

snapshot = asyncio.run(main())
```

單獨抓取：

```python
async def fetch_parts():
    async with WebDataFetcher() as fetcher:
        fear_greed = await fetcher.fetch_fear_greed_index()
        global_market = await fetcher.fetch_global_market_data()
        defi = await fetcher.fetch_defi_metrics()
        stablecoins = await fetcher.fetch_stablecoin_metrics()
        return fear_greed, global_market, defi, stablecoins
```

自訂設定：

```python
config = APIConfig(
    timeout=20.0,
    max_retries=5,
    retry_delay=2.0,
    coingecko_api_key="",
)
```

---

## 使用邊界

1. `database.py` 仍保留在目錄中，但新開發應使用 `DatabaseManager`。
2. `WebDataFetcher` 是 async context manager，需用 `async with`。
3. `NewsDataFetcher` 與 `SyncExternalDataFetcher` 是同步版，適合同步 analysis 流程。
4. Binance 私有 API 與下單需要有效 API key；公開市場資料可無 key 使用。
5. 外部 HTTP 失敗時，不同 fetcher 的回傳策略不同：同步 fetcher 多回傳 `None` / 空 list；`WebDataFetcher.fetch_all()` 回傳 `ExternalDataSnapshot` 並在 `errors` 中記錄失敗。

---

## 快速驗證

```bash
python -c "from bioneuronai.data import BinanceFuturesConnector, ExchangeRateService, get_database_manager, NewsDataFetcher, SyncExternalDataFetcher; print('data imports ok')"
```

需要實際連網的驗證請分開執行，避免把網路失敗誤判成 import 或 schema 錯誤。

---

> 上層文件：[data README](README.md)
