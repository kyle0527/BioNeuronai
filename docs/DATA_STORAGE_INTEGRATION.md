# BioNeuronai 數據存儲與整合方案
> **版本**: v2.1.0  
> **更新日期**: 2026-01-22


## 📑 目錄

1. �📊 Risk Manager 模組整合狀態
2. 💾 數據存儲方案
3. 🔄 數據備份與恢復
4. 📈 數據查詢與分析
5. 🔐 數據安全
6. 📊 數據庫 Schema (trading.db)
7. 🎯 完整整合範例
8. 📝 總結

---

## �📊 Risk Manager 模組整合狀態

### ✅ 已整合模組

#### 1. **TradingEngine** (核心交易引擎)
**文件**: `src/bioneuronai/core/trading_engine.py`

**整合點**:

```python
# 初始化
self.risk_manager = RiskManager()  # Line 111

# 使用場景
├── start_monitoring()          # 監控啟動時更新初始餘額
│   └── risk_manager.update_balance(initial_balance)  # Line 394
│
├── _handle_trading_signal()    # 信號處理前檢查
│   └── risk_manager.check_can_trade(confidence, balance)  # Line 627
│
├── execute_trade()             # 執行交易後記錄
│   └── risk_manager.record_trade(trade_info)  # Line 718
│
└── get_system_status()         # 系統狀態查詢
    └── risk_manager.get_risk_statistics()  # Line 940, 957, 1002
```

**數據流向**:
```
Account Balance (Binance API)
    ↓
risk_manager.update_balance()
    ↓
[峰值追蹤 + 回撤計算]
    ↓
Trading Signal
    ↓
risk_manager.check_can_trade()  ← 6項檢查
    ↓
[通過] → execute_trade()
    ↓
risk_manager.record_trade()
    ↓
[交易歷史 + 統計更新]
```

#### 2. **PlanController** (計劃控制器)
**文件**: `src/bioneuronai/trading/plan_controller.py`

**整合點**:

```python
# 初始化
self.risk_manager = RiskManager()  # Line 43

# 使用場景
├── calculate_position_size()    # 倉位計算
│   └── risk_manager.calculate_position_size(...)  # Line 428
│
└── get_risk_parameters()        # 獲取風險參數
    └── risk_manager.risk_parameters[risk_level]  # Line 391
```

---

## 💾 數據存儲方案

### 📁 目錄結構

```
BioNeuronai/
├── trading_data/                    # 【主要數據目錄】
│   ├── signals_history.json        # 信號歷史
│   ├── strategy_weights.json       # 策略權重
│   ├── risk_statistics.json        # ✅ 風險統計（建議新增）
│   ├── trade_history.json          # ✅ 交易歷史（建議新增）
│   ├── balance_history.json        # ✅ 餘額歷史（建議新增）
│   ├── trading.db                  # SQLite 數據庫
│   └── test_trading.db             # 測試數據庫
│
├── pretrade_check_data/            # 預交易檢查數據
├── sop_automation_data/            # SOP 自動化數據
├── data_downloads/                 # 歷史市場數據
│   └── binance_historical/         # Binance K線數據
└── trading_system.log              # 系統日誌
```

### 🗄️ 當前數據存儲實現

#### 已實現存儲

**1. 信號歷史** (`signals_history.json`)
```python
# trading_engine.py
self.signals_history: List[TradingSignal] = []
```

**2. 交易記錄** (文件存儲)
```python
# Line 719
self._save_trade_to_file(trade_info)
```

**3. 系統日誌** (`trading_system.log`)
```python
logging.FileHandler('trading_system.log', encoding='utf-8')
```

---

### ⚠️ 需要新增的存儲

#### 建議新增 1: 風險統計持久化

**文件**: `trading_data/risk_statistics.json`

**內容結構**:
```json
{
  "last_updated": "2026-01-22T12:30:00",
  "statistics": {
    "total_trades": 150,
    "win_rate": 0.6268,
    "profit_factor": 2.08,
    "max_drawdown": 0.1245,
    "sharpe_ratio": 1.87,
    "net_profit": 11610.57
  },
  "daily_stats": [
    {
      "date": "2026-01-22",
      "trades": 5,
      "pnl": 250.0,
      "win_rate": 0.8
    }
  ]
}
```

**實現方法**:
```python
# 在 RiskManager 中添加
def save_statistics(self, filepath: str = "trading_data/risk_statistics.json"):
    stats = self.get_risk_statistics()
    stats['last_updated'] = datetime.now().isoformat()

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

def load_statistics(self, filepath: str = "trading_data/risk_statistics.json"):
    if Path(filepath).exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 恢復歷史數據
            self.trade_history = data.get('trade_history', [])
```

#### 建議新增 2: 交易歷史持久化

**文件**: `trading_data/trade_history.json`

**內容結構**:
```json
{
  "trades": [
    {
      "id": 1,
      "timestamp": "2026-01-22T10:30:00",
      "symbol": "BTCUSDT",
      "side": "BUY",
      "entry_price": 50000.0,
      "exit_price": 52000.0,
      "size": 0.1,
      "pnl": 200.0,
      "strategy": "ai_strategy_fusion",
      "confidence": 0.85
    }
  ]
}
```

**實現方法**:
```python
# 在 RiskManager.record_trade() 中添加
def record_trade(self, trade_info: Dict):
    # ... 現有邏輯 ...

    # 自動保存到文件
    self._save_trade_history()

def _save_trade_history(self, filepath: str = "trading_data/trade_history.json"):
    data = {
        'trades': self.trade_history,
        'last_updated': datetime.now().isoformat()
    }

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
```

#### 建議新增 3: 餘額歷史持久化

**文件**: `trading_data/balance_history.json`

**內容結構**:
```json
{
  "balance_snapshots": [
    {
      "timestamp": "2026-01-22T10:00:00",
      "balance": 10000.0,
      "peak_balance": 10000.0,
      "drawdown": 0.0
    },
    {
      "timestamp": "2026-01-22T12:00:00",
      "balance": 10250.0,
      "peak_balance": 10250.0,
      "drawdown": 0.0
    }
  ]
}
```

**實現方法**:
```python
# 在 RiskManager.update_balance() 中添加
def update_balance(self, balance: float):
    # ... 現有邏輯 ...

    # 記錄快照
    self._save_balance_snapshot(balance)

def _save_balance_snapshot(self, balance: float):
    snapshot = {
        'timestamp': datetime.now().isoformat(),
        'balance': balance,
        'peak_balance': self.peak_balance,
        'drawdown': (self.peak_balance - balance) / self.peak_balance if self.peak_balance > 0 else 0
    }

    # 讀取現有數據
    filepath = "trading_data/balance_history.json"
    if Path(filepath).exists():
        with open(filepath, 'r') as f:
            data = json.load(f)
    else:
        data = {'balance_snapshots': []}

    # 添加新快照
    data['balance_snapshots'].append(snapshot)

    # 限制最多保存 10000 條
    if len(data['balance_snapshots']) > 10000:
        data['balance_snapshots'] = data['balance_snapshots'][-10000:]

    # 保存
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
```

---

## 🔄 數據備份與恢復

### 自動備份方案

**每日備份腳本**:

```python
# tools/backup_trading_data.py
import shutil
from pathlib import Path
from datetime import datetime

def backup_trading_data():
    """每日自動備份交易數據"""
    source_dir = Path("trading_data")
    backup_dir = Path("trading_data_backups")
    backup_dir.mkdir(exist_ok=True)

    # 創建日期命名的備份
    today = datetime.now().strftime("%Y%m%d")
    backup_path = backup_dir / f"backup_{today}"

    if not backup_path.exists():
        shutil.copytree(source_dir, backup_path)
        print(f"✅ 備份完成: {backup_path}")

    # 清理 30 天前的備份
    for old_backup in backup_dir.glob("backup_*"):
        if (datetime.now() - datetime.strptime(old_backup.name[-8:], "%Y%m%d")).days > 30:
            shutil.rmtree(old_backup)
            print(f"🗑️ 刪除舊備份: {old_backup}")

if __name__ == "__main__":
    backup_trading_data()
```

**定時任務設置** (Windows):
```powershell
# 每天凌晨 2 點執行
schtasks /create /tn "BioNeuronai_Backup" /tr "python C:\D\E\BioNeuronai\tools\backup_trading_data.py" /sc daily /st 02:00
```

### 數據恢復方案

```python
# tools/restore_trading_data.py
def restore_from_backup(backup_date: str):
    """從指定日期恢復數據"""
    backup_path = Path(f"trading_data_backups/backup_{backup_date}")
    target_dir = Path("trading_data")

    if backup_path.exists():
        # 備份當前數據
        shutil.move(target_dir, f"trading_data_old_{datetime.now():%Y%m%d%H%M%S}")

        # 恢復備份
        shutil.copytree(backup_path, target_dir)
        print(f"✅ 數據已從 {backup_date} 恢復")
    else:
        print(f"❌ 備份不存在: {backup_date}")

# 使用範例
restore_from_backup("20260122")
```

---

## 📈 數據查詢與分析

### 查詢 API

**1. 獲取最近 N 筆交易**:
```python
def get_recent_trades(n: int = 10) -> List[Dict]:
    filepath = "trading_data/trade_history.json"
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data['trades'][-n:]
```

**2. 按日期範圍查詢**:
```python
def get_trades_by_date_range(start_date: str, end_date: str) -> List[Dict]:
    filepath = "trading_data/trade_history.json"
    with open(filepath, 'r') as f:
        data = json.load(f)

    return [
        t for t in data['trades']
        if start_date <= t['timestamp'][:10] <= end_date
    ]

# 使用範例
trades = get_trades_by_date_range("2026-01-01", "2026-01-22")
```

**3. 按幣種篩選**:
```python
def get_trades_by_symbol(symbol: str) -> List[Dict]:
    filepath = "trading_data/trade_history.json"
    with open(filepath, 'r') as f:
        data = json.load(f)

    return [t for t in data['trades'] if t['symbol'] == symbol]

# 使用範例
btc_trades = get_trades_by_symbol("BTCUSDT")
```

**4. 生成績效報告**:
```python
def generate_performance_report(start_date: str, end_date: str) -> Dict:
    trades = get_trades_by_date_range(start_date, end_date)

    total_pnl = sum(t.get('pnl', 0) for t in trades if 'pnl' in t)
    winning_trades = [t for t in trades if t.get('pnl', 0) > 0]

    return {
        'period': f"{start_date} to {end_date}",
        'total_trades': len(trades),
        'winning_trades': len(winning_trades),
        'win_rate': len(winning_trades) / len(trades) if trades else 0,
        'total_pnl': total_pnl,
        'avg_pnl_per_trade': total_pnl / len(trades) if trades else 0
    }

# 使用範例
report = generate_performance_report("2026-01-01", "2026-01-22")
print(json.dumps(report, indent=2))
```

---

## 🔐 數據安全

> ⚠️ 補註：
> 本章節的「使用 `.env` 文件」方向本身可參考；
> 但若要作為目前專案的正式基準，仍需結合最新的使用者級 / 系統級憑證分層與 `src/schemas/` 單一事實來源原則一起理解。

### 敏感數據處理

**1. API Key 加密存儲**:
```python
# 使用 .env 文件 (已在 .gitignore)
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here
```

**2. 交易數據加密** (可選):
```python
from cryptography.fernet import Fernet

def encrypt_trade_data(data: Dict, key: bytes) -> bytes:
    f = Fernet(key)
    json_data = json.dumps(data).encode()
    return f.encrypt(json_data)

def decrypt_trade_data(encrypted_data: bytes, key: bytes) -> Dict:
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_data)
    return json.loads(decrypted)
```

### 訪問控制

**1. 文件權限設置** (Linux/Mac):
```bash
chmod 600 trading_data/*.json  # 僅所有者可讀寫
chmod 700 trading_data/        # 僅所有者可訪問
```

**2. 數據庫加密** (SQLite):
```python
import sqlcipher3

# 創建加密數據庫
conn = sqlcipher3.connect("trading_data/trading_encrypted.db")
conn.execute(f"PRAGMA key = '{encryption_key}'")
```

---

## 📊 數據庫 Schema (trading.db)

### 建議的表結構

```sql
-- 交易記錄表
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- BUY/SELL
    entry_price REAL NOT NULL,
    exit_price REAL,
    size REAL NOT NULL,
    pnl REAL,
    strategy VARCHAR(50),
    confidence REAL,
    order_id VARCHAR(50),
    status VARCHAR(20)  -- OPEN/CLOSED/CANCELLED
);

-- 餘額快照表
CREATE TABLE balance_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    balance REAL NOT NULL,
    peak_balance REAL NOT NULL,
    drawdown REAL NOT NULL
);

-- 風險警報表
CREATE TABLE risk_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    suggested_action TEXT
);

-- 每日統計表
CREATE TABLE daily_statistics (
    date DATE PRIMARY KEY,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    total_pnl REAL,
    max_drawdown REAL,
    sharpe_ratio REAL
);
```

### 數據庫操作範例

```python
import sqlite3
from datetime import datetime

class TradingDatabase:
    def __init__(self, db_path: str = "trading_data/trading.db"):
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol VARCHAR(20) NOT NULL,
                side VARCHAR(10) NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                size REAL NOT NULL,
                pnl REAL,
                strategy VARCHAR(50),
                confidence REAL
            )
        ''')
        self.conn.commit()

    def insert_trade(self, trade_info: Dict):
        self.conn.execute('''
            INSERT INTO trades (timestamp, symbol, side, entry_price, size, strategy, confidence)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now(),
            trade_info['symbol'],
            trade_info['side'],
            trade_info['entry_price'],
            trade_info['size'],
            trade_info.get('strategy', 'Unknown'),
            trade_info.get('confidence', 0)
        ))
        self.conn.commit()

    def get_recent_trades(self, n: int = 10):
        cursor = self.conn.execute(
            'SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?',
            (n,)
        )
        return cursor.fetchall()
```

---

## 🎯 完整整合範例

### 在 TradingEngine 中啟用完整數據持久化

```python
class TradingEngine:
    def __init__(self, ...):
        # ... 現有初始化 ...

        # 數據持久化
        self.db = TradingDatabase()
        self.enable_data_persistence = True

    def execute_trade(self, signal: TradingSignal):
        # ... 執行交易邏輯 ...

        if order_result and order_result.status != "ERROR":
            trade_info = {
                'symbol': signal.symbol,
                'side': signal.action,
                'entry_price': current_price,
                'size': position_size,
                'strategy': signal.strategy_name,
                'confidence': signal.confidence
            }

            # 1. Risk Manager 記錄
            self.risk_manager.record_trade(trade_info)

            # 2. 數據庫記錄
            if self.enable_data_persistence:
                self.db.insert_trade(trade_info)

            # 3. JSON 文件記錄 (舊方法)
            self._save_trade_to_file(trade_info)
```

---

## 📝 總結

### ✅ 已完成整合

1. **TradingEngine** - 4 個調用點
2. **PlanController** - 2 個調用點
3. **記憶體數據** - trade_history, balance, alerts

### 🔄 建議改進

1. **新增持久化存儲**:
   - ✅ `risk_statistics.json`
   - ✅ `trade_history.json`
   - ✅ `balance_history.json`

2. **數據庫整合**:
   - ✅ SQLite schema 設計
   - ✅ 雙寫機制 (JSON + DB)

3. **數據備份與恢復**:
   - ✅ 每日自動備份
   - ✅ 30 天保留策略

4. **查詢與分析 API**:
   - ✅ 按日期/幣種/策略篩選
   - ✅ 績效報告生成

### 📂 建議的文件位置

```
trading_data/
├── risk_statistics.json      # 風險統計 (RiskManager 輸出)
├── trade_history.json         # 交易歷史 (RiskManager 輸出)
├── balance_history.json       # 餘額歷史 (RiskManager 輸出)
├── trading.db                 # SQLite 數據庫 (雙寫)
└── signals_history.json       # 信號歷史 (TradingEngine 輸出)
```

需要我實現這些持久化功能嗎？
