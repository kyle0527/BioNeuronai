# 數據庫系統升級指南
> **版本**: v2.1  
> **更新日期**: 2026-01-22  
> **模組**: `src.bioneuronai.data.database_manager`


## 📑 目錄

1. 📋 概述
2. 🚀 快速開始
3. 📂 文件結構
4. 🔧 新功能
5. 📖 使用範例
6. ⚙️ 配置選項
7. 🔄 數據備份
8. 📊 數據查詢 API
9. 🛠️ 故障排除
10. 📈 性能優化
11. 🔐 數據安全
12. 📚 相關文檔
13. ❓ 常見問題
14. 🎯 下一步
15. 📞 支持

---

## 📋 概述

本次更新將 BioNeuronai 的數據存儲從 JSON/JSONL 文件升級到 **SQLite 數據庫**，提供：
- ✅ 統一的數據管理接口
- ✅ 高效的查詢和統計
- ✅ 數據一致性保證
- ✅ 自動備份機制
- ✅ 向後兼容（保留 JSON 備份）

---

## 🚀 快速開始

### 1. 數據遷移（首次使用）

如果你有舊的 JSON/JSONL 數據，運行遷移腳本：

```powershell
python migrate_to_database.py
```

這會：
- ✅ 創建 `trading_data/trading.db` 數據庫
- ✅ 遷移所有舊數據
- ✅ 備份舊文件到 `trading_data/legacy_backup/`
- ✅ 生成遷移報告

### 2. 使用新系統

**無需修改現有代碼！** TradingEngine 和 RiskManager 已自動使用數據庫。

```python
from src.bioneuronai.core import TradingEngine

# 自動使用數據庫
engine = TradingEngine(testnet=True)

# 正常使用，數據會自動保存到數據庫
engine.execute_trade(signal)
```

### 3. 查詢歷史數據

```python
from src.bioneuronai.data import get_database_manager
from datetime import datetime, timedelta

db = get_database_manager()

# 查詢最近30天交易
trades = db.get_trades(
    start_date=(datetime.now() - timedelta(days=30)).isoformat(),
    symbol="BTCUSDT",
    limit=100
)

# 獲取最新風險統計
risk_stats = db.get_latest_risk_stats()

# 查詢信號歷史
signals = db.get_signals(
    strategy="TrendFollowing",
    limit=50
)
```

---

## 📂 文件結構

```
trading_data/
├── trading.db                 # 主數據庫（SQLite）
├── backups/                   # 自動備份
│   ├── trades_backup.jsonl    # 交易記錄備份
│   └── signals_backup.jsonl   # 信號記錄備份
├── legacy_backup/             # 遷移前的舊文件
│   ├── trades_history.jsonl.20260122_123456
│   └── signals_history.json.20260122_123456
└── exports/                   # 數據導出
    ├── trades.json
    ├── signals.json
    └── risk_stats.json
```

---

## 🔧 新功能

### DatabaseManager 類

統一的數據管理接口：

```python
from src.bioneuronai.data.database_manager import get_database_manager

db = get_database_manager()

# 保存交易記錄
db.save_trade(trade_info)

# 保存信號
db.save_signal(signal_info)

# 保存風險統計
db.save_risk_stats(stats)

# 保存新聞分析
db.save_news_analysis(news_info)

# 保存性能指標
db.save_performance_metric('sharpe_ratio', 1.85)

# 獲取統計信息
stats = db.get_database_stats()

# 導出數據
db.export_to_json('trading_data/exports')

# 清理舊數據
db.cleanup_old_data(keep_days=90)
```

### 數據分層

系統自動管理三層數據：

1. **熱數據（內存）**: 當前交易信號、持倉
2. **溫數據（SQLite）**: 近期交易記錄、風險統計
3. **冷數據（歸檔）**: 長期備份、歷史數據

詳見: [docs/DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md](docs/DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md)

---

## 📖 使用範例

運行範例腳本查看所有功能：

```powershell
python examples_database_usage.py
```

包含範例：
- ✅ 保存交易記錄
- ✅ 查詢交易歷史
- ✅ 保存和查詢信號
- ✅ 風險統計追蹤
- ✅ 新聞分析存儲
- ✅ 性能指標追蹤
- ✅ 數據導出
- ✅ 統計分析

---

## ⚙️ 配置選項

### TradingEngine

```python
engine = TradingEngine(
    api_key="...",
    api_secret="...",
    testnet=True,
    # 數據庫會自動初始化
)
```

### RiskManager

```python
risk_manager = RiskManager(
    use_database=True  # 啟用數據庫（默認）
)
```

### DatabaseManager

```python
db = DatabaseManager(
    db_path="trading_data/trading.db",  # 數據庫路徑
    backup_enabled=True                 # 啟用 JSONL 備份
)
```

---

## 🔄 數據備份

### 自動備份

每次交易都會自動備份到：
- `trading_data/backups/trades_backup.jsonl`
- `trading_data/backups/signals_backup.jsonl`

### 手動備份

```python
db = get_database_manager()

# 導出所有數據到 JSON
db.export_to_json('trading_data/exports')

# 或直接複製數據庫文件
import shutil
shutil.copy('trading_data/trading.db', 'backup/trading_20260122.db')
```

### 定期清理

```python
# 清理90天前的未執行信號
db.cleanup_old_data(keep_days=90)
```

---

## 📊 數據查詢 API

### 交易記錄

```python
# 查詢交易
trades = db.get_trades(
    start_date="2026-01-01T00:00:00",  # 開始日期（可選）
    end_date="2026-01-31T23:59:59",    # 結束日期（可選）
    symbol="BTCUSDT",                  # 交易對（可選）
    limit=100                          # 返回數量
)

# 獲取交易統計
stats = db.get_trade_statistics(days=30)
```

### 信號歷史

```python
# 查詢信號
signals = db.get_signals(
    start_date="2026-01-01T00:00:00",  # 開始日期（可選）
    symbol="ETHUSDT",                  # 交易對（可選）
    strategy="TrendFollowing",         # 策略名稱（可選）
    limit=50
)

# 標記信號為已執行
db.mark_signal_executed(signal_id)
```

### 風險統計

```python
# 獲取最新統計
latest = db.get_latest_risk_stats()

# 獲取歷史統計
history = db.get_risk_stats_history(days=30)
```

### 新聞分析

```python
# 獲取近期新聞
news = db.get_recent_news(
    hours=24,              # 最近 N 小時
    sentiment="POSITIVE"   # 情感過濾（可選）
)
```

### 性能指標

```python
# 保存指標
db.save_performance_metric(
    metric_name='sharpe_ratio',
    value=1.85,
    period='daily'
)

# 查詢歷史
history = db.get_performance_metrics('sharpe_ratio', days=30)
```

---

## 🛠️ 故障排除

### 數據庫被鎖定

```python
# SQLite 默認超時 30 秒，如需增加：
db = DatabaseManager(db_path="trading_data/trading.db")
# 內部已設置 timeout=30.0
```

### 數據不一致

```python
# 從備份恢復
import shutil
shutil.copy(
    'trading_data/backups/trading_20260122.db',
    'trading_data/trading.db'
)
```

### 數據庫損壞

```python
# 從 JSONL 備份重建
python migrate_to_database.py
```

---

## 📈 性能優化

### 已建立的索引

```sql
CREATE INDEX idx_trades_timestamp ON trades(timestamp);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_signals_symbol ON signals(symbol);
```

### 查詢優化建議

```python
# ✅ 好：使用時間範圍和索引
trades = db.get_trades(
    start_date=start,
    end_date=end,
    symbol="BTCUSDT"
)

# ❌ 差：全表掃描
all_trades = db.get_trades(limit=999999)
```

---

## 🔐 數據安全

### 數據加密（可選）

如需加密敏感數據，使用 SQLCipher：

```python
# 安裝: pip install sqlcipher3
# 修改 DatabaseManager 連接字符串
```

### 訪問控制

數據庫文件權限：

```powershell
# 限制訪問權限（僅所有者）
icacls "trading_data\trading.db" /inheritance:r /grant:r "$env:USERNAME:(R,W)"
```

---

## 📚 相關文檔

- [數據存儲與讀取策略](docs/DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md)
- [DatabaseManager API 文檔](src/bioneuronai/data/database_manager.py)
- [使用範例](examples_database_usage.py)
- [遷移工具](migrate_to_database.py)

---

## ❓ 常見問題

### Q: 舊的 JSON 文件還會更新嗎？

A: 會！為了兼容性，系統會同時寫入數據庫和 JSONL 備份文件。

### Q: 可以不使用數據庫嗎？

A: 可以。如果數據庫初始化失敗，系統會自動降級到 JSON 文件模式。

### Q: 數據庫文件可以刪除嗎？

A: 可以。刪除 `trading.db` 後會自動重新創建空數據庫。但建議先備份。

### Q: 如何遷移到其他數據庫（如 PostgreSQL）？

A: 使用 `db.export_to_json()` 導出數據，然後導入到新數據庫。

### Q: 數據庫會自動清理嗎？

A: 不會。需要手動調用 `db.cleanup_old_data(keep_days=90)` 或設置定時任務。

---

## 🎯 下一步

1. ✅ 運行數據遷移: `python migrate_to_database.py`
2. ✅ 測試新功能: `python examples_database_usage.py`
3. ✅ 閱讀完整文檔: [docs/DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md](docs/DATA_STORAGE_AND_RETRIEVAL_STRATEGY.md)
4. ✅ 開始使用！

---

## 📞 支持

如有問題，請查看:
- 📖 [完整文檔](docs/)
- 🐛 [Issue Tracker](https://github.com/kyle0527/BioNeuronai/issues)
- 💬 [討論區](https://github.com/kyle0527/BioNeuronai/discussions)
