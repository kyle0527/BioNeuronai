# Services 服務模組

數據庫服務和外部匯率服務。

## 📋 模組概述

Services 模組提供數據持久化和外部服務集成，是系統的基礎服務層。

## 🎯 主要組件

### 1. TradingDatabase (交易數據庫)

基於 SQLite 的本地數據庫服務，用於存儲交易記錄、信號和配置。

**主要功能：**
- 交易記錄管理
- 信號記錄存儲
- 交易對配置
- 匯率信息緩存
- 性能統計查詢

**數據表結構：**

**trading_pairs（交易對配置）**
```sql
CREATE TABLE trading_pairs (
    symbol TEXT PRIMARY KEY,
    base_currency TEXT,
    quote_currency TEXT,
    min_order_size REAL,
    max_order_size REAL,
    price_precision INTEGER,
    quantity_precision INTEGER,
    is_active INTEGER,
    created_at TEXT,
    updated_at TEXT
)
```

**trade_records（交易記錄）**
```sql
CREATE TABLE trade_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    side TEXT,              -- BUY/SELL
    entry_price REAL,
    exit_price REAL,
    quantity REAL,
    leverage INTEGER,
    pnl_usdt REAL,
    pnl_percent REAL,
    entry_time TEXT,
    exit_time TEXT,
    strategy TEXT,
    notes TEXT
)
```

**signal_records（信號記錄）**
```sql
CREATE TABLE signal_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    signal_type TEXT,       -- BUY/SELL
    source TEXT,            -- RSI/MACD/AI_FUSION...
    strength REAL,
    price REAL,
    timestamp TEXT,
    executed INTEGER,       -- 0=未執行, 1=已執行
    notes TEXT
)
```

**exchange_rates（匯率信息）**
```sql
CREATE TABLE exchange_rates (
    from_currency TEXT,
    to_currency TEXT,
    rate REAL,
    source TEXT,
    timestamp TEXT,
    PRIMARY KEY (from_currency, to_currency)
)
```

**使用示例：**
```python
from bioneuronai.services import TradingDatabase

# 初始化數據庫
db = TradingDatabase()

# 記錄交易
trade_id = db.record_trade(
    symbol="BTCUSDT",
    side="BUY",
    entry_price=45000.0,
    quantity=0.1,
    leverage=2,
    strategy="AI_FUSION"
)

# 更新交易結果
db.update_trade_exit(
    trade_id=trade_id,
    exit_price=46000.0,
    pnl_usdt=100.0,
    pnl_percent=2.22
)

# 記錄信號
signal_id = db.record_signal(
    symbol="ETHUSDT",
    signal_type="BUY",
    source="RSI_DIVERGENCE",
    strength=0.85,
    price=2500.0
)

# 查詢交易歷史
recent_trades = db.get_recent_trades(limit=10)
for trade in recent_trades:
    print(f"{trade.symbol}: PnL = {trade.pnl_usdt} USDT")

# 統計性能
stats = db.get_trading_statistics(days=30)
print(f"勝率: {stats['win_rate']:.2%}")
print(f"總盈虧: {stats['total_pnl']} USDT")
```

**常用查詢方法：**
```python
# 獲取特定幣種的交易
btc_trades = db.get_trades_by_symbol("BTCUSDT", days=7)

# 獲取特定策略的表現
fusion_trades = db.get_trades_by_strategy("AI_FUSION")

# 獲取盈利交易
profitable_trades = db.get_profitable_trades(days=30)

# 獲取虧損交易
losing_trades = db.get_losing_trades(days=30)

# 獲取未執行的信號
pending_signals = db.get_pending_signals()
```

### 2. ExchangeRateService (匯率服務)

提供實時匯率查詢和緩存服務。

**主要功能：**
- 實時匯率查詢
- 匯率緩存（避免頻繁請求）
- 多幣種轉換
- 歷史匯率記錄

**支持的貨幣對：**
- USD ↔ TWD（美元 ↔ 台幣）
- USD ↔ CNY（美元 ↔ 人民幣）
- USD ↔ EUR（美元 ↔ 歐元）
- 等其他主要貨幣對

**使用示例：**
```python
from bioneuronai.services import ExchangeRateService, get_exchange_rate_service

# 方式 1：直接初始化
rate_service = ExchangeRateService()

# 方式 2：使用單例（推薦）
rate_service = get_exchange_rate_service()

# 獲取匯率
usd_to_twd = await rate_service.get_rate("USD", "TWD")
print(f"1 USD = {usd_to_twd} TWD")

# 轉換金額
amount_usd = 1000
amount_twd = await rate_service.convert(amount_usd, "USD", "TWD")
print(f"{amount_usd} USD = {amount_twd} TWD")

# 獲取多個匯率
rates = await rate_service.get_multiple_rates([
    ("USD", "TWD"),
    ("USD", "CNY"),
    ("USD", "EUR"),
])
```

**匯率數據模型：**
```python
@dataclass
class ExchangeRateInfo:
    from_currency: str      # 源貨幣
    to_currency: str        # 目標貨幣
    rate: float            # 匯率
    source: str            # 數據來源
    timestamp: datetime    # 更新時間
    is_cached: bool        # 是否來自緩存
```

### 3. 數據導出功能

導出交易數據為 CSV 或 JSON 格式。

```python
# 導出為 CSV
db.export_trades_to_csv("trades_2024.csv", days=30)

# 導出為 JSON
db.export_trades_to_json("trades_2024.json", days=30)

# 導出統計報告
db.export_statistics_report("report_2024.json", days=90)
```

## 📦 導出 API

```python
from bioneuronai.services import (
    TradingDatabase,          # 交易數據庫
    Database,                 # 別名（向後兼容）
    ExchangeRateService,      # 匯率服務
    ExchangeRateInfo,         # 匯率信息數據類
    get_exchange_rate_service, # 單例獲取函數
)
```

## 🔗 依賴關係

**內部依賴：**
- 無（獨立模組）

**外部依賴：**
- `sqlite3` - SQLite 數據庫
- `requests` - HTTP 請求（匯率查詢）
- `pandas` - 數據處理（可選）

## 🎨 架構設計

```
services/
├── database.py             # 數據庫服務
├── exchange_rate_service.py # 匯率服務
└── __init__.py            # 模組導出
```

## 🔧 配置說明

```python
# 數據庫配置
DATABASE_CONFIG = {
    "db_path": "data/trading.db",     # 數據庫路徑
    "auto_backup": True,               # 自動備份
    "backup_interval_hours": 24,       # 備份間隔
}

# 匯率服務配置
EXCHANGE_RATE_CONFIG = {
    "api_url": "https://api.exchangerate-api.com/v4/latest/",
    "cache_duration_minutes": 60,      # 緩存時長
    "timeout_seconds": 10,             # 請求超時
}
```

## 📝 使用場景

### 場景 1：記錄完整交易流程

```python
async def complete_trade_workflow():
    db = TradingDatabase()
    
    # 1. 記錄信號
    signal_id = db.record_signal(
        symbol="BTCUSDT",
        signal_type="BUY",
        source="AI_FUSION",
        strength=0.92,
        price=45000.0
    )
    
    # 2. 執行交易
    trade_id = db.record_trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=45050.0,
        quantity=0.1,
        leverage=2,
        strategy="AI_FUSION"
    )
    
    # 3. 標記信號已執行
    db.mark_signal_executed(signal_id)
    
    # 4. 交易結束後更新
    db.update_trade_exit(
        trade_id=trade_id,
        exit_price=46000.0,
        pnl_usdt=95.0,
        pnl_percent=2.11
    )
```

### 場景 2：性能分析和報告

```python
def generate_performance_report(days=30):
    db = TradingDatabase()
    
    # 獲取統計數據
    stats = db.get_trading_statistics(days=days)
    
    print(f"📊 {days} 天交易報告")
    print(f"總交易次數: {stats['total_trades']}")
    print(f"勝率: {stats['win_rate']:.2%}")
    print(f"總盈虧: {stats['total_pnl']:.2f} USDT")
    print(f"平均盈利: {stats['avg_profit']:.2f} USDT")
    print(f"最大盈利: {stats['max_profit']:.2f} USDT")
    print(f"最大虧損: {stats['max_loss']:.2f} USDT")
    
    # 按策略分析
    strategies = db.get_strategy_performance()
    print("\n策略表現:")
    for strategy, perf in strategies.items():
        print(f"  {strategy}: {perf['win_rate']:.2%} ({perf['total_trades']} 筆)")
```

### 場景 3：匯率轉換和顯示

```python
async def display_pnl_in_multiple_currencies(pnl_usdt):
    rate_service = get_exchange_rate_service()
    
    # 轉換為多種貨幣
    currencies = ["TWD", "CNY", "EUR", "JPY"]
    
    print(f"盈虧: {pnl_usdt} USD")
    for currency in currencies:
        amount = await rate_service.convert(pnl_usdt, "USD", currency)
        print(f"     = {amount:.2f} {currency}")
```

## ⚠️ 注意事項

1. **數據備份**：定期備份數據庫文件
2. **並發訪問**：SQLite 支持有限的並發寫入
3. **匯率緩存**：注意緩存時效性
4. **磁盤空間**：定期清理舊數據

## 🚀 快速開始

```python
import asyncio
from bioneuronai.services import TradingDatabase, get_exchange_rate_service

async def main():
    # 數據庫操作
    db = TradingDatabase()
    
    # 記錄交易
    trade_id = db.record_trade(
        symbol="BTCUSDT",
        side="BUY",
        entry_price=45000.0,
        quantity=0.1,
        leverage=2,
        strategy="TEST"
    )
    
    # 查詢統計
    stats = db.get_trading_statistics(days=7)
    print(f"7天勝率: {stats['win_rate']:.2%}")
    
    # 匯率查詢
    rate_service = get_exchange_rate_service()
    usd_to_twd = await rate_service.get_rate("USD", "TWD")
    print(f"匯率: 1 USD = {usd_to_twd} TWD")

if __name__ == "__main__":
    asyncio.run(main())
```

## 📈 性能指標

- 數據庫查詢：< 10ms（本地 SQLite）
- 記錄寫入：< 5ms
- 匯率查詢：< 500ms（含網絡請求）
- 緩存命中率：> 90%

## 🔄 版本歷史

- v2.1.0 - 模組化重構，改進數據模型
- v2.0.0 - 新增匯率服務
- v1.5.0 - 優化數據庫查詢
- v1.0.0 - 初始版本
