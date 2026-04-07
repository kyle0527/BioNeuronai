# Data 模組使用手冊

**路徑**: `src/bioneuronai/data/`  
**版本**: v2.1  
**更新日期**: 2026-03-16

本手冊說明如何正確使用 `bioneuronai.data` 模組中的每一個元件。  
所有程式碼範例均為可直接執行的實際代碼，無任何虛構方法或不存在的 API。

---

## 📋 目錄

1. [快速起步](#快速起步)
2. [BinanceFuturesConnector 使用指南](#binancefuturesconnector-使用指南)
3. [DatabaseManager 使用指南](#databasemanager-使用指南)
4. [ExchangeRateService 使用指南](#exchangerateservice-使用指南)
5. [WebDataFetcher 使用指南](#webdatafetcher-使用指南)
6. [常見問題與錯誤處理](#常見問題與錯誤處理)
7. [環境依賴確認](#環境依賴確認)

---

## 快速起步

```python
# 一次匯入所有公開元件
from bioneuronai.data import (
    BinanceFuturesConnector,
    ExchangeRateService,
    DatabaseManager,
    get_database_manager,
)
```

> **注意**：`WebDataFetcher` 與已廢棄的 `TradingDatabase` 不在公開匯出中，  
> 需從 `bioneuronai.data.web_data_fetcher` 直接匯入。

---

## BinanceFuturesConnector 使用指南

### 初始化

```python
from bioneuronai.data import BinanceFuturesConnector

# Testnet（Demo Trading，預設）─ 不會動用真實資金
connector = BinanceFuturesConnector(
    api_key="your_testnet_api_key",
    api_secret="your_testnet_api_secret",
    testnet=True   # True = demo-fapi.binance.com
)

# 主網（真實交易）
connector_live = BinanceFuturesConnector(
    api_key="your_live_api_key",
    api_secret="your_live_api_secret",
    testnet=False  # False = fapi.binance.com
)

# 不設置 API Key 仍可讀取公開數據（無法下單）
connector_public = BinanceFuturesConnector()
```

---

### 市場數據查詢

```python
# 1. 即時價格
price: str | None = connector.get_ticker_price("BTCUSDT")
# 返回: "45000.00" 或 None（失敗時）
if price:
    print(f"BTC 即時價: {float(price):.2f} USDT")


# 2. 24 小時統計
ticker_24h: dict | None = connector.get_ticker_24hr("ETHUSDT")
# 返回: {"symbol": "ETHUSDT", "priceChange": "...", "priceChangePercent": "2.5", ...}
if ticker_24h:
    print(f"ETH 24hr 漲跌: {ticker_24h['priceChangePercent']}%")


# 3. K 線歷史數據
klines: list | None = connector.get_klines(
    symbol="BTCUSDT",
    interval="1h",   # 支援: 1m, 3m, 5m, 15m, 30m, 1h, 4h, 1d, 1w
    limit=100        # 最多 1500
)
# 返回: [[開盤時間, 開盤, 最高, 最低, 收盤, 成交量, ...], ...]
if klines:
    latest = klines[-1]
    print(f"最新 K 線開盤: {latest[1]}, 收盤: {latest[4]}")


# 4. 訂單簿深度
order_book: dict | None = connector.get_order_book("BTCUSDT", limit=20)
# 返回: {"lastUpdateId": ..., "bids": [["price", "qty"], ...], "asks": [...]}
if order_book:
    best_bid = order_book['bids'][0]
    best_ask = order_book['asks'][0]
    spread = float(best_ask[0]) - float(best_bid[0])
    print(f"買一: {best_bid[0]}, 賣一: {best_ask[0]}, 價差: {spread:.2f}")


# 5. 資金費率（永續合約）
funding: list | None = connector.get_funding_rate("BTCUSDT", limit=1)
# 返回: [{"symbol": "BTCUSDT", "fundingRate": "0.00010000", "fundingTime": 1577433600000}]
if funding:
    rate = float(funding[0]['fundingRate']) * 100
    print(f"最新資金費率: {rate:.6f}%")


# 6. 未平倉合約數
open_interest: dict | None = connector.get_open_interest("BTCUSDT")
# 返回: {"openInterest": "10659.509", "symbol": "BTCUSDT", "time": ...}
if open_interest:
    print(f"未平倉量: {open_interest['openInterest']} BTC")
```

---

### 帳戶查詢

```python
# 查詢帳戶信息（需要有效 API Key）
account: dict | None = connector.get_account_info()
if account:
    usdt_balance = next(
        (a for a in account.get('assets', []) if a['asset'] == 'USDT'), None
    )
    if usdt_balance:
        print(f"USDT 可用餘額: {usdt_balance['availableBalance']}")


# 查詢交易對規格（最小下單量、精度等）
exchange_info: dict | None = connector.get_exchange_info("BTCUSDT")
if exchange_info:
    print(f"BTC 合約類型: {exchange_info.get('contractType')}")
    for f in exchange_info.get('filters', []):
        if f['filterType'] == 'LOT_SIZE':
            print(f"最小下單量: {f['minQty']}, 步長: {f['stepSize']}")
```

---

### 下單

```python
from bioneuronai.data.binance_futures import OrderResult

# 市價單（需配置 API Key）
result: OrderResult | None = connector.place_order(
    symbol="BTCUSDT",
    side="BUY",           # "BUY" 或 "SELL"
    order_type="MARKET",  # "MARKET" 或 "LIMIT"
    quantity=0.001,
    stop_loss=44000.0,    # 可選：止損價格
    take_profit=47000.0   # 可選：止盈價格
)

if result and result.status != "ERROR":
    print(f"✅ 訂單成功: ID={result.order_id}, 狀態={result.status}")
else:
    print(f"❌ 訂單失敗: {result.error if result else '未知錯誤'}")


# 限價單（需指定 price）
limit_result: OrderResult | None = connector.place_order(
    symbol="ETHUSDT",
    side="BUY",
    order_type="LIMIT",
    quantity=0.01,
    price=2500.0   # LIMIT 單必填
)
```

---

### WebSocket 實時訂閱

```python
import time

def handle_price(msg: dict):
    """接收到價格推送時的回調函式"""
    symbol = msg.get('s', '')
    price = msg.get('c', '0')
    print(f"[{symbol}] 最新價: {price}")

# 訂閱價格流（後台線程運行，非阻塞）
ws = connector.subscribe_ticker_stream(
    symbol="BTCUSDT",
    callback=handle_price,
    auto_reconnect=True   # 自動重連（最多 10 次）
)

# 主程序繼續執行...
time.sleep(30)

# 程序結束前關閉所有連接
connector.close_all_connections()
```

---

## DatabaseManager 使用指南

### 初始化

```python
from bioneuronai.data import get_database_manager, DatabaseManager

# 方式一：全局單例（推薦）
db = get_database_manager()
# 預設路徑: data/bioneuronai/trading/runtime/trading.db

# 方式二：指定路徑
db = get_database_manager("data/bioneuronai/trading/runtime/custom.db")

# 方式三：直接實例化（較少用）
db = DatabaseManager(
    db_path="data/bioneuronai/trading/runtime/trading.db",
    backup_enabled=True  # 是否同時寫入 JSONL 備份
)
```

---

### 交易記錄

```python
# 保存交易
trade_id = db.save_trade({
    'order_id': 'ORD_20260316_001',
    'symbol': 'BTCUSDT',
    'side': 'BUY',          # "BUY" 或 "SELL"
    'quantity': 0.001,
    'price': 45000.0,
    'confidence': 0.78,     # 策略信心度 (0-1)
    'strategy': 'RSI_MACD', # 策略名稱
    'timestamp': '2026-03-16T10:00:00',
    'pnl': None,            # 平倉後才填
    'fee': 0.045            # 手續費 USDT
})
print(f"已保存，ID={trade_id}")


# 查詢交易記錄
trades = db.get_trades(
    start_date='2026-03-01',   # 可選：開始日期 (ISO格式)
    end_date='2026-03-16',     # 可選：結束日期
    symbol='BTCUSDT',          # 可選：篩選交易對
    limit=50                   # 最多返回筆數
)


# 交易統計（近 N 天）
stats = db.get_trade_statistics(days=30)
print(f"勝率: {stats['win_rate']:.1%}, 總 PnL: {stats['total_pnl']:.2f}")
```

---

### 信號歷史

```python
# 保存信號
signal_id = db.save_signal({
    'symbol': 'ETHUSDT',
    'action': 'LONG',          # "LONG" / "SHORT" / "CLOSE"
    'confidence': 0.82,
    'strategy_name': 'TrendFollowing',
    'reason': 'RSI 超買轉空，MACD 金叉',
    'target_price': 2600.0,
    'stop_loss': 2400.0,
    'take_profit': 2800.0,
    'timestamp': '2026-03-16T10:30:00'
})


# 查詢信號
signals = db.get_signals(
    start_date='2026-03-16',
    symbol='ETHUSDT',
    strategy='TrendFollowing',
    limit=20
)


# 標記信號已執行
db.mark_signal_executed(signal_id)
```

---

### 風險統計快照

```python
# 保存風險統計（每個交易週期結束後呼叫）
db.save_risk_stats({
    'total_trades': 45,
    'win_rate': 0.62,
    'sharpe_ratio': 1.8,
    'max_drawdown': -0.073,
    'total_pnl': 1250.5,
    'volatility': 0.02
})


# 查詢最新快照
latest = db.get_latest_risk_stats()
if latest:
    print(f"最新勝率: {latest['win_rate']:.1%}")


# 查詢歷史（近 30 天的快照序列）
history = db.get_risk_stats_history(days=30)
```

---

### 新聞分析

```python
# 保存新聞分析結果
news_id = db.save_news_analysis({
    'headline': 'Fed 宣布暫停升息',
    'category': 'MACRO',         # MACRO / REGULATION / HACK / WAR 等
    'sentiment': 'POSITIVE',     # POSITIVE / NEGATIVE / NEUTRAL
    'score': 0.65,               # -1.0 到 1.0
    'affected_symbols': 'BTCUSDT,ETHUSDT',
    'source': 'Reuters',
    'timestamp': '2026-03-16T14:00:00'
})


# 查詢最近新聞（24小時內正面新聞）
recent_news = db.get_recent_news(hours=24, sentiment='POSITIVE')


# 估算新聞持續影響時間（返回小時數）
duration = db.estimate_news_duration(keywords=['Fed', '升息', 'interest rate'])
print(f"預計影響 {duration:.1f} 小時")


# 統計相關新聞數量（最近 6 小時）
count = db.count_related_news(
    keywords=['Bitcoin', 'BTC'],
    hours=6
)
```

---

### 市場事件記憶 (Event Memory)

```python
# 保存市場事件（score: -1.0 極度看空 ~ +1.0 極度看多）
db.save_event({
    'event_id': 'hack_2026_03_16_001',
    'event_type': 'HACK',         # WAR / HACK / REGULATION / MACRO 等
    'headline': 'Major exchange hacked - $500M lost',
    'score': -0.95,               # 嚴重利空
    'source': 'CoinDesk',
    'source_confidence': 0.9,
    'affected_symbols': 'BTCUSDT,ETHUSDT',
    'termination_condition': '事件平息或資金追回後結束'
})


# 查詢所有 ACTIVE 事件
active_events = db.get_active_events()

# 過濾特定類型
war_events = db.get_active_events(event_type='WAR')

# 過濾特定交易對
btc_events = db.get_active_events(symbol='BTCUSDT')


# 計算總事件加權分數（用於交易決策）
total_score, events = db.calculate_total_event_score(symbol='BTCUSDT')
print(f"事件總分: {total_score:.3f}（共 {len(events)} 個活躍事件）")
# total_score 在 [-1.0, 1.0]，負值代表看空壓力


# 解析（關閉）事件
db.resolve_event(
    event_id='hack_2026_03_16_001',
    resolution_note='資金已全數追回，市場情緒恢復'
)
```

---

### 策略演化（Strategy Evolution）

```python
# 保存策略基因
gene_id = db.save_strategy_gene({
    'gene_id': 'gene_rsi_macd_v3',
    'strategy_type': 'RSI_MACD',
    'parameters': '{"rsi_period": 14, "macd_fast": 12, "macd_slow": 26}',
    'fitness': 1.85,              # 適應度評分
    'generation': 5,
    'parent_ids': 'gene_v1,gene_v2',
    'is_active': 1
})


# 查詢最佳基因（適應度前 N 名）
best_genes = db.get_best_genes(top_n=5, strategy_type='RSI_MACD')


# 更新基因適應度
db.update_gene_fitness('gene_rsi_macd_v3', {
    'fitness': 2.10,
    'total_trades': 30,
    'win_rate': 0.67
})


# 停用基因
db.deactivate_genes(['gene_old_v1', 'gene_old_v2'])


# 保存演化記錄
db.save_evolution_record({
    'generation': 5,
    'best_fitness': 2.10,
    'avg_fitness': 1.75,
    'best_gene_id': 'gene_rsi_macd_v3',
    'best_strategy_type': 'RSI_MACD',
    'survivors': 10,
    'eliminated': 5,
    'offspring': 8
})
```

---

### 維護操作

```python
# 取得數據庫統計
stats = db.get_database_stats()
print(f"交易記錄: {stats['trades']} 筆, DB 大小: {stats['db_size_mb']:.2f} MB")


# 匯出數據為 JSON（用於遷移或分析）
db.export_to_json(output_dir="data/bioneuronai/trading/exports")


# 清理舊數據（保留最近 90 天）
db.cleanup_old_data(keep_days=90)


# 明確關閉連接（通常不需要，單例會自動管理）
db.close()
```

---

## ExchangeRateService 使用指南

```python
from bioneuronai.data import ExchangeRateService
from bioneuronai.data.exchange_rate_service import ExchangeRateInfo

# 初始化（線程安全，可跨線程共用）
rate_service = ExchangeRateService()


# 查詢匯率
rate_info: ExchangeRateInfo | None = rate_service.get_rate("USD", "TWD")
if rate_info:
    print(f"USD/TWD = {rate_info.rate:.4f}")
    print(f"來源: {rate_info.source}")           # "exchangerate-api" / "fallback"
    print(f"即時匯率: {rate_info.is_realtime}")  # True / False
    print(f"更新時間: {rate_info.updated_at}")


# 金額換算
twd = rate_service.convert(1000.0, "USD", "TWD")  # 返回 float
print(f"1000 USDT ≈ {twd:.0f} TWD")


# 查詢所有支援幣別的匯率（以 USD 為基準）
all_rates = rate_service.get_all_rates("USD")
# 返回: {"TWD": 32.5, "EUR": 0.925, "JPY": 149.5, "GBP": 0.787, ...}
for currency, rate in all_rates.items():
    print(f"USD/{currency} = {rate}")


# 格式化顯示
result = rate_service.format_conversion(5000.0, "USD", "TWD")
print(result)  # "5,000.00 USD = 162,500.00 TWD"


# 強制重新抓取（清除快取）
rate_service.clear_cache()
fresh_rate = rate_service.get_rate("USD", "EUR")


# 支援的目標幣別
# USD, TWD, EUR, JPY, GBP, KRW, AUD, SGD, HKD
```

---

## WebDataFetcher 使用指南

> **重要**：`WebDataFetcher` 必須在 `async with` 上下文管理器中使用，  
> 以確保 `aiohttp.ClientSession` 正確建立與釋放。

### 基本用法

```python
import asyncio
from bioneuronai.data.web_data_fetcher import WebDataFetcher, APIConfig

async def fetch_market_data():
    # 使用預設配置（推薦）
    async with WebDataFetcher() as fetcher:
        # 並行抓取所有數據源（asyncio.gather）
        snapshot = await fetcher.fetch_all()
        return snapshot


# 執行
snapshot = asyncio.run(fetch_market_data())
```

---

### 自定義 API 配置

```python
from bioneuronai.data.web_data_fetcher import WebDataFetcher, APIConfig

config = APIConfig(
    timeout=20.0,                            # 請求超時（秒）
    max_retries=5,                           # 最大重試次數
    retry_delay=2.0,                         # 重試間隔（秒）
    coingecko_api_key="YOUR_CG_KEY_HERE"     # CoinGecko Pro Key（可選）
)

async def main():
    async with WebDataFetcher(config=config) as fetcher:
        snapshot = await fetcher.fetch_all()
```

---

### 解析抓取結果

```python
from schemas.external_data import ExternalDataSnapshot

async def analyze_snapshot():
    async with WebDataFetcher() as fetcher:
        snapshot: ExternalDataSnapshot = await fetcher.fetch_all()
    
    # 恐慌貪婪指數（0 = 極度恐慌, 100 = 極度貪婪）
    if snapshot.fear_greed:
        fg = snapshot.fear_greed
        print(f"恐慌貪婪指數: {fg.value} ({fg.classification})")
        # classification: "Extreme Fear" / "Fear" / "Neutral" / "Greed" / "Extreme Greed"
    
    # 全球加密市場
    if snapshot.global_market:
        gm = snapshot.global_market
        print(f"總市值: ${gm.total_market_cap/1e9:.0f}B")
        print(f"BTC 佔比: {gm.btc_dominance:.1f}%")
        print(f"ETH 佔比: {gm.eth_dominance:.1f}%")
        print(f"24hr 總交易量: ${gm.total_volume/1e9:.0f}B")
        print(f"市場情緒: {gm.market_sentiment_score}")
    
    # DeFi TVL
    if snapshot.defi_metrics:
        dm = snapshot.defi_metrics
        print(f"DeFi TVL: ${dm.total_tvl/1e9:.1f}B")
        print(f"前三大鏈: {list(dm.chains.keys())[:3]}")
        # 注意: dm.tvl_change_24h 目前固定為 0.0（需歷史數據）
    
    # 穩定幣供應
    if snapshot.stablecoin_metrics:
        sm = snapshot.stablecoin_metrics
        print(f"穩定幣總供應: ${sm.total_supply/1e9:.1f}B")
        for token, supply in sm.supply_by_token.items():
            print(f"  {token}: ${supply/1e9:.1f}B")
        # 注意: sm.supply_change_24h / supply_change_7d 目前固定為 0.0
    
    # 抓取資訊
    print(f"成功數據源: {[s.value for s in snapshot.data_sources]}")
    print(f"耗時: {snapshot.fetch_duration_ms}ms")
    if snapshot.errors:
        print(f"錯誤: {snapshot.errors}")


asyncio.run(analyze_snapshot())
```

---

### 單獨抓取特定數據

```python
async def fetch_single():
    async with WebDataFetcher() as fetcher:
        # 只抓恐慌貪婪指數
        fear_greed = await fetcher.fetch_fear_greed_index()
        
        # 只抓全球市場數據
        global_market = await fetcher.fetch_global_market_data()
        
        # 只抓 DeFi TVL
        defi = await fetcher.fetch_defi_metrics()
        
        # 只抓穩定幣供應量
        stablecoins = await fetcher.fetch_stablecoin_metrics()
        
        return fear_greed, global_market, defi, stablecoins
```

---

### 與交易引擎整合（同步呼叫 async）

```python
import asyncio
from bioneuronai.data.web_data_fetcher import WebDataFetcher

def get_market_snapshot_sync():
    """在同步程式碼中呼叫非同步抓取器"""
    async def _fetch():
        async with WebDataFetcher() as fetcher:
            return await fetcher.fetch_all()
    return asyncio.run(_fetch())

# 在同步程式中呼叫
snapshot = get_market_snapshot_sync()
```

---

## 常見問題與錯誤處理

### Q1：API Key 未配置時如何運作？

```python
connector = BinanceFuturesConnector()  # 無 API Key

# 公開市場數據可正常使用
price = connector.get_ticker_price("BTCUSDT")  # ✅ 正常

# 需要認證的 API 會返回 None 或失敗
account = connector.get_account_info()  # 返回 None
result = connector.place_order(...)     # 記錄警告並返回 None
```

### Q2：`requests` 未安裝時匯率服務如何處理？

```python
# exchange_rate_service.py 已處理 ImportError
# 若 requests 不可用，會直接使用內建固定匯率表（不崩潰）
rate_service = ExchangeRateService()
rate = rate_service.get_rate("USD", "TWD")  # 仍然返回結果（備用匯率）
```

### Q3：WebDataFetcher 網路失敗怎麼辦？

```python
async def robust_fetch():
    async with WebDataFetcher() as fetcher:
        snapshot = await fetcher.fetch_all()
    
    # fetch_all() 永遠返回 ExternalDataSnapshot，即使全部失敗
    # 失敗的數據源欄位為 None，錯誤訊息在 snapshot.errors
    
    if snapshot.fear_greed is None:
        print("恐慌貪婪指數抓取失敗，跳過")
    
    for error in snapshot.errors:
        print(f"數據源錯誤: {error}")
```

### Q4：如何確認數據庫正確建立？

```python
db = get_database_manager()
stats = db.get_database_stats()
print(stats)
# 預期輸出:
# {
#   'trades': 0, 'signals': 0, 'risk_stats': 0,
#   'pretrade_checks': 0, 'news_analysis': 0,
#   'performance_metrics': 0, 'db_size_mb': 0.05
# }
```

### Q5：如何在多線程中安全使用 DatabaseManager？

```python
import threading
from bioneuronai.data import get_database_manager

def worker_thread(thread_id: int):
    # 每個線程呼叫 get_database_manager() 都返回同一個實例
    # DatabaseManager 內部使用 threading.local() 確保每線程獨立連接
    db = get_database_manager()
    db.save_trade({'symbol': 'BTCUSDT', 'side': 'BUY', ...})

threads = [threading.Thread(target=worker_thread, args=(i,)) for i in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

---

## 環境依賴確認

```bash
# 檢查必要依賴
pip show requests aiohttp websocket-client pydantic

# 安裝（若缺少）
pip install requests aiohttp websocket-client pydantic
```

```python
# 程式內確認
def check_dependencies():
    results = {}
    
    try:
        import requests
        results['requests'] = requests.__version__
    except ImportError:
        results['requests'] = "❌ 未安裝（匯率服務將使用備用數據）"
    
    try:
        import aiohttp
        results['aiohttp'] = aiohttp.__version__
    except ImportError:
        results['aiohttp'] = "❌ 未安裝（WebDataFetcher 將無法使用）"
    
    try:
        import websocket
        results['websocket-client'] = websocket.__version__
    except ImportError:
        results['websocket-client'] = "❌ 未安裝（WebSocket 推送將無法使用）"
    
    for pkg, version in results.items():
        print(f"{pkg}: {version}")

check_dependencies()
```

---

## 驗證命令

```bash
# Ruff 代碼品質
python -m ruff check src/bioneuronai/data/

# mypy 型別檢查
python -m mypy src/bioneuronai/data/ --ignore-missing-imports

# 快速功能驗證（不需要 API Key）
python -c "
from bioneuronai.data import BinanceFuturesConnector, ExchangeRateService, get_database_manager
db = get_database_manager('data/test_verify.db')
stats = db.get_database_stats()
print('✅ DatabaseManager OK:', stats)
rs = ExchangeRateService()
r = rs.get_rate('USD', 'TWD')
print('✅ ExchangeRateService OK:', r.rate if r else 'fallback')
c = BinanceFuturesConnector()
print('✅ BinanceFuturesConnector OK')
import os; os.remove('data/test_verify.db')
"
```

---

*本手冊最後更新: 2026-03-16 | BioNeuronAI v2.1*
