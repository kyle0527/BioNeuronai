# 數據分層存儲與讀取策略

**版本**: v2.1  
**最後更新**: 2026年1月22日  
**狀態**: ✅ 已實現

---

## 📋 目錄

1. [數據分層原理](#數據分層原理)
2. [數據類型與存儲位置](#數據類型與存儲位置)
3. [讀取策略](#讀取策略)
4. [寫入策略](#寫入策略)
5. [數據遷移與歸檔](#數據遷移與歸檔)
6. [性能優化](#性能優化)
7. [故障恢復](#故障恢復)
8. [最佳實踐](#最佳實踐)

---

## 數據分層原理

本系統採用**三層數據架構**：熱數據（內存）+ 溫數據（SQLite）+ 冷數據（歸檔）

```
┌─────────────────────────────────────────────────────────┐
│                     應用層                               │
│  (TradingEngine, RiskManager, Strategies, etc.)         │
└───────────────┬─────────────────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────────────────┐
│              DatabaseManager (統一接口)                  │
│  - 自動分層路由                                          │
│  - 智能緩存管理                                          │
│  - 備份機制                                              │
└─────┬──────────────┬──────────────┬─────────────────────┘
      │              │              │
      ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌─────────────┐
│  熱數據   │  │  溫數據   │  │   冷數據     │
│ (內存)    │  │ (SQLite)  │  │  (歸檔)      │
│           │  │           │  │              │
│ 當日實時  │  │ 近期歷史  │  │  >90天歷史   │
│ 交易信號  │  │ 交易記錄  │  │  壓縮備份    │
│ 市場數據  │  │ 風險統計  │  │  JSON/Parquet│
└──────────┘  └──────────┘  └─────────────┘
```

---

## 數據類型與存儲位置

### 1. 熱數據（內存）

**存儲位置**: Python 對象、字典、列表  
**生命週期**: 進程運行期間  
**讀取方式**: 直接內存訪問  

**包含數據**:
- 當前交易信號（`signals_history: List[TradingSignal]`）
- 當前持倉（`positions: List[Position]`）
- 實時市場數據（`_klines_cache`）
- 風險配置（`risk_parameters`）

**特點**:
- ⚡ 極快讀寫速度
- 🔄 進程重啟後丟失
- 💾 定期持久化到溫數據層

**讀取示例**:
```python
# 直接訪問
current_signals = trading_engine.signals_history[-10:]  # 最近10個信號
current_positions = trading_engine.positions
```

---

### 2. 溫數據（SQLite）

**存儲位置**: `trading_data/trading.db`  
**生命週期**: 持久化，90天自動清理策略  
**讀取方式**: SQL查詢（通過 DatabaseManager）  

**包含數據**:
- 交易記錄（`trades` 表）
- 信號歷史（`signals` 表）
- 風險統計快照（`risk_stats` 表）
- 交易前檢查記錄（`pretrade_checks` 表）
- 新聞分析結果（`news_analysis` 表）
- 性能指標（`performance_metrics` 表）

**特點**:
- 💾 持久化存儲
- 📊 支持複雜查詢
- 🔍 索引優化（按時間、交易對）
- 🔒 事務保證數據一致性
- 📦 單文件，易於備份

**讀取示例**:
```python
from src.bioneuronai.data.database_manager import get_database_manager

db = get_database_manager()

# 查詢最近30天交易記錄
trades = db.get_trades(
    start_date=(datetime.now() - timedelta(days=30)).isoformat(),
    symbol="BTCUSDT",
    limit=100
)

# 獲取最新風險統計
risk_stats = db.get_latest_risk_stats()

# 查詢信號歷史
signals = db.get_signals(
    start_date="2026-01-01T00:00:00",
    strategy="TrendFollowing",
    limit=50
)

# 獲取近24小時新聞
news = db.get_recent_news(hours=24, sentiment="POSITIVE")
```

---

### 3. 冷數據（歸檔）

**存儲位置**: `trading_data/backups/` 和 `trading_data/legacy_backup/`  
**生命週期**: 長期保存（可選壓縮）  
**讀取方式**: 文件解析  

**包含數據**:
- JSONL 備份（`trades_backup.jsonl`, `signals_backup.jsonl`）
- 歷史數據導出（`exports/*.json`）
- 舊系統遷移數據（`legacy_backup/*.json`）

**特點**:
- 📦 長期歸檔
- 🔒 不可變性
- 💿 易於遷移/分析
- 📉 壓縮存儲（未來可用 gzip）

**讀取示例**:
```python
import json

# 讀取 JSONL 備份
with open("trading_data/backups/trades_backup.jsonl", 'r') as f:
    for line in f:
        trade = json.loads(line)
        print(trade)

# 讀取導出的 JSON
with open("trading_data/exports/trades.json", 'r') as f:
    all_trades = json.load(f)
```

---

## 數據讀取模式對比

### 模式 A: 全部讀入內存（小數據集）

**適用場景**: 
- 回測 <10000 筆交易
- 策略分析
- 報表生成

**優點**: 簡單直接  
**缺點**: 內存佔用大

```python
db = get_database_manager()
all_trades = db.get_trades(limit=10000)  # 全部讀入
```

---

### 模式 B: 分批讀取（大數據集）

**適用場景**: 
- 大規模歷史分析
- 數據匯總統計
- 長期回測

**優點**: 內存友好  
**缺點**: 需要分頁邏輯

```python
def process_all_trades():
    db = get_database_manager()
    offset = 0
    batch_size = 1000
    
    while True:
        # SQLite 不直接支持 offset，使用 timestamp 分頁
        batch = db.get_trades(
            start_date=last_timestamp,
            limit=batch_size
        )
        
        if not batch:
            break
        
        # 處理這批數據
        for trade in batch:
            analyze_trade(trade)
        
        last_timestamp = batch[-1]['timestamp']
```

---

### 模式 C: 流式讀取（實時數據）

**適用場景**: 
- 實時監控
- 風險預警
- 性能追蹤

**優點**: 最小延遲  
**缺點**: 複雜性高

```python
# 從內存讀取實時信號
def get_latest_signals(n=10):
    return trading_engine.signals_history[-n:]

# 從數據庫讀取近期數據
def get_recent_trades(hours=24):
    db = get_database_manager()
    start_date = (datetime.now() - timedelta(hours=hours)).isoformat()
    return db.get_trades(start_date=start_date)
```

---

## 數據寫入策略

### 實時寫入（關鍵數據）

```python
# TradingEngine 執行交易時
def execute_trade(self, signal):
    # ... 執行交易 ...
    
    # 立即寫入數據庫
    trade_info = {
        'order_id': order['orderId'],
        'symbol': signal.symbol,
        'side': signal.action,
        'quantity': quantity,
        'price': price,
        'timestamp': datetime.now().isoformat()
    }
    
    self.db_manager.save_trade(trade_info)  # 同步寫入
```

### 批量寫入（非關鍵數據）

```python
# 性能指標批量保存
metrics_buffer = []

def buffer_metric(name, value):
    metrics_buffer.append({'name': name, 'value': value})
    
    # 達到閾值時批量寫入
    if len(metrics_buffer) >= 100:
        flush_metrics()

def flush_metrics():
    db = get_database_manager()
    for metric in metrics_buffer:
        db.save_performance_metric(
            metric_name=metric['name'],
            value=metric['value']
        )
    metrics_buffer.clear()
```

---

## 數據一致性保證

### 雙寫機制（數據庫 + JSONL）

```python
def _save_trade_to_file(self, trade_info):
    # 1. 主存儲：數據庫
    trade_id = self.db_manager.save_trade(trade_info)
    
    # 2. 備份：JSONL（異步，容錯）
    try:
        with open("trading_data/trades_history.jsonl", 'a') as f:
            json.dump(trade_info, f, ensure_ascii=False)
            f.write('\n')
    except Exception as e:
        logger.warning(f"JSONL 備份失敗: {e}")
```

### 事務保證

```python
# DatabaseManager 內部使用事務
@contextmanager
def _get_connection(self):
    try:
        yield self._local.conn
    except Exception as e:
        self._local.conn.rollback()  # 回滾失敗操作
        raise
    else:
        self._local.conn.commit()  # 提交成功操作
```

---

## 數據查詢優化

### 使用索引

```sql
-- trading.db 已建立的索引
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_signals_symbol ON signals(symbol);
```

### 時間範圍查詢

```python
# ✅ 好：使用索引的時間範圍查詢
trades = db.get_trades(
    start_date="2026-01-01T00:00:00",
    end_date="2026-01-31T23:59:59",
    symbol="BTCUSDT"
)

# ❌ 差：全表掃描
all_trades = db.get_trades(limit=999999)
filtered = [t for t in all_trades if t['symbol'] == 'BTCUSDT']
```

---

## 數據備份與恢復

### 自動備份

```python
# 每日執行
def daily_backup():
    db = get_database_manager()
    
    # 導出到 JSON
    db.export_to_json(output_dir="trading_data/exports")
    
    # 壓縮數據庫文件
    import shutil
    shutil.copy(
        "trading_data/trading.db",
        f"trading_data/backups/trading_{datetime.now():%Y%m%d}.db"
    )
```

### 數據恢復

```python
# 從備份恢復
def restore_from_backup(backup_date):
    import shutil
    
    backup_file = f"trading_data/backups/trading_{backup_date}.db"
    if Path(backup_file).exists():
        shutil.copy(backup_file, "trading_data/trading.db")
        logger.info(f"✅ 已從 {backup_date} 恢復數據")
    else:
        logger.error(f"❌ 備份文件不存在: {backup_file}")
```

---

## 數據清理策略

### 定期清理

```python
# 每週執行
def weekly_cleanup():
    db = get_database_manager()
    
    # 清理90天前的未執行信號
    db.cleanup_old_data(keep_days=90)
    
    logger.info("🗑️ 數據清理完成")
```

### 手動歸檔

```python
# 歸檔舊數據到冷存儲
def archive_old_data(before_date):
    db = get_database_manager()
    
    # 查詢舊數據
    old_trades = db.get_trades(end_date=before_date)
    
    # 保存到歸檔文件
    archive_file = f"trading_data/archives/trades_{before_date}.json.gz"
    import gzip
    with gzip.open(archive_file, 'wt', encoding='utf-8') as f:
        json.dump(old_trades, f)
    
    # 從數據庫刪除（可選）
    # DELETE FROM trades WHERE timestamp < ?
```

---

## 總結

### 數據讀取決策樹

```
需要讀取數據？
│
├─ 實時數據（<5秒） → 內存
│   └─ trading_engine.signals_history
│
├─ 近期數據（<90天） → SQLite
│   └─ db.get_trades(start_date, end_date)
│
└─ 歷史數據（>90天） → 歸檔文件
    └─ json.load(open("archives/..."))
```

### 關鍵原則

1. **寫入**: 實時寫入關鍵數據，批量寫入非關鍵數據
2. **讀取**: 優先內存，其次數據庫，最後文件
3. **備份**: 雙寫保證（數據庫 + JSONL）
4. **查詢**: 使用索引，限制時間範圍
5. **清理**: 定期歸檔，避免數據膨脹
6. **恢復**: 多層備份，快速恢復

### 存儲容量預估

| 時間跨度 | 交易筆數 | 數據量 | 存儲位置 |
|---------|---------|--------|---------|
| 1 天    | 100     | ~3 MB  | 內存+DB |
| 1 個月  | 3000    | ~90 MB | SQLite  |
| 1 年    | 36000   | ~1 GB  | SQLite  |
| >1 年   | >36000  | >1 GB  | 歸檔    |

**建議**:
- 小規模交易系統: SQLite 即可滿足
- 中等規模交易系統: SQLite + 定期歸檔
- 大規模交易系統: PostgreSQL/InfluxDB + 分布式存儲
