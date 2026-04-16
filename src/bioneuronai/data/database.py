"""
交易資料庫模組
================
管理交易對配置、交易記錄、信號歷史、策略權重等

注意：
- 匯率使用 exchange_rate_service.py 即時獲取，不存資料庫
- 即時價格從交易所 API 獲取，不存資料庫

使用 SQLite，無需額外安裝資料庫服務器
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingPair:
    """交易對資訊"""
    symbol: str              # 例如 BTCUSDT
    base_asset: str          # 基礎資產，例如 BTC
    quote_asset: str         # 報價資產，例如 USDT
    category: str            # 分類：major, altcoin, stablecoin, meme
    min_qty: float           # 最小交易數量
    min_notional: float      # 最小名義價值（美元）
    price_precision: int     # 價格小數位數
    qty_precision: int       # 數量小數位數
    is_active: bool = True   # 是否啟用
    description: str = ""    # 描述


@dataclass
class ExchangeRate:
    """匯率資訊"""
    from_currency: str       # 來源貨幣
    to_currency: str         # 目標貨幣
    rate: float              # 匯率
    updated_at: str          # 更新時間


@dataclass
class TradeRecord:
    """交易記錄"""
    id: Optional[int]
    symbol: str
    side: str                # BUY / SELL
    quantity: float
    entry_price: float
    exit_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    profit_loss: Optional[float]
    profit_loss_pct: Optional[float]
    strategy_name: str
    confidence: float
    status: str              # OPEN / CLOSED / CANCELLED
    opened_at: str
    closed_at: Optional[str]
    notes: str = ""


@dataclass
class SignalRecord:
    """信號記錄"""
    id: Optional[int]
    symbol: str
    action: str              # BUY / SELL / HOLD
    confidence: float
    strategy_name: str
    price_at_signal: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    suggested_qty: Optional[float]
    suggested_value: Optional[float]
    reasons: str
    created_at: str
    executed: bool = False


class TradingDatabase:
    """交易資料庫管理器
    
    .. deprecated::
        此類別在 v4.0 後已被 DatabaseManager (database_manager.py) 取代。
        請改用 DatabaseManager / get_database_manager() 來存取交易記錄。
        
        TradingDatabase 保留同所管理的獨特表：
            - trading_pairs  (交易對清單，含傳詳協議參數)
            - strategy_weights  (策略權重歷史)
            - account_snapshots (帳戶快照)
        上述表尚未合併進 DatabaseManager，未來將一併移入。
    """
    
    def __init__(self, db_path: str = "data/bioneuronai/trading/runtime/trading_pairs.db"):
        """初始化資料庫
        
        警告：預設路徑已更改為 trading_pairs.db 以避免與 DatabaseManager
        使用的 trading.db 產生表結構衝突。若要讀寫重要交易記錄請改用 DatabaseManager。
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        self._create_tables()
        self._init_default_data()
        
        logger.info(f"📦 資料庫初始化完成: {self.db_path}")
    
    def _create_tables(self):
        """創建資料表"""
        cursor = self.conn.cursor()
        
        # 1. 交易對表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trading_pairs (
                symbol TEXT PRIMARY KEY,
                base_asset TEXT NOT NULL,
                quote_asset TEXT NOT NULL,
                category TEXT DEFAULT 'altcoin',
                min_qty REAL DEFAULT 0.001,
                min_notional REAL DEFAULT 5.0,
                price_precision INTEGER DEFAULT 2,
                qty_precision INTEGER DEFAULT 3,
                is_active INTEGER DEFAULT 1,
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 注意：匯率不存資料庫！使用 exchange_rate_service.py 即時獲取
        
        # 2. 交易記錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                quantity REAL NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL,
                stop_loss REAL,
                take_profit REAL,
                profit_loss REAL,
                profit_loss_pct REAL,
                strategy_name TEXT,
                confidence REAL,
                status TEXT DEFAULT 'OPEN',
                opened_at TEXT DEFAULT CURRENT_TIMESTAMP,
                closed_at TEXT,
                notes TEXT DEFAULT '',
                FOREIGN KEY (symbol) REFERENCES trading_pairs(symbol)
            )
        """)
        
        # 4. 信號記錄表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                action TEXT NOT NULL,
                confidence REAL NOT NULL,
                strategy_name TEXT,
                price_at_signal REAL NOT NULL,
                stop_loss REAL,
                take_profit REAL,
                suggested_qty REAL,
                suggested_value REAL,
                reasons TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                executed INTEGER DEFAULT 0,
                FOREIGN KEY (symbol) REFERENCES trading_pairs(symbol)
            )
        """)
        
        # 5. 策略權重歷史表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_weights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                weight REAL NOT NULL,
                win_rate REAL,
                avg_return REAL,
                total_trades INTEGER DEFAULT 0,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 6. 帳戶快照表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                balance REAL NOT NULL,
                equity REAL NOT NULL,
                unrealized_pnl REAL DEFAULT 0,
                realized_pnl REAL DEFAULT 0,
                total_trades INTEGER DEFAULT 0,
                win_trades INTEGER DEFAULT 0,
                currency TEXT DEFAULT 'USDT',
                snapshot_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 創建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_created ON signals(created_at)")
        
        self.conn.commit()
        logger.info("✅ 資料表創建完成")
    
    def _init_default_data(self):
        """初始化預設數據"""
        # 檢查是否已有數據
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trading_pairs")
        if cursor.fetchone()[0] > 0:
            return
        
        # === 預設交易對 ===
        default_pairs = [
            # 主流幣 (Major)
            TradingPair("BTCUSDT", "BTC", "USDT", "major", 0.001, 5.0, 2, 3, True, "比特幣 - 加密貨幣之王"),
            TradingPair("ETHUSDT", "ETH", "USDT", "major", 0.001, 5.0, 2, 3, True, "以太坊 - 智能合約平台"),
            TradingPair("BNBUSDT", "BNB", "USDT", "major", 0.01, 5.0, 2, 2, True, "幣安幣 - 交易所代幣"),
            TradingPair("SOLUSDT", "SOL", "USDT", "major", 0.01, 5.0, 2, 2, True, "Solana - 高性能公鏈"),
            TradingPair("XRPUSDT", "XRP", "USDT", "major", 1.0, 5.0, 4, 1, True, "瑞波幣 - 跨境支付"),
            
            # 山寨幣 (Altcoin)
            TradingPair("ADAUSDT", "ADA", "USDT", "altcoin", 1.0, 5.0, 4, 1, True, "卡爾達諾 - 學術型公鏈"),
            TradingPair("DOGEUSDT", "DOGE", "USDT", "altcoin", 1.0, 5.0, 5, 0, True, "狗狗幣 - 迷因幣始祖"),
            TradingPair("DOTUSDT", "DOT", "USDT", "altcoin", 0.1, 5.0, 3, 2, True, "波卡 - 跨鏈協議"),
            TradingPair("AVAXUSDT", "AVAX", "USDT", "altcoin", 0.1, 5.0, 2, 2, True, "雪崩協議"),
            TradingPair("MATICUSDT", "MATIC", "USDT", "altcoin", 1.0, 5.0, 4, 1, True, "Polygon - L2 擴容"),
            TradingPair("LINKUSDT", "LINK", "USDT", "altcoin", 0.1, 5.0, 3, 2, True, "Chainlink - 預言機"),
            TradingPair("LTCUSDT", "LTC", "USDT", "altcoin", 0.01, 5.0, 2, 2, True, "萊特幣 - 數字白銀"),
            TradingPair("ATOMUSDT", "ATOM", "USDT", "altcoin", 0.1, 5.0, 3, 2, True, "Cosmos - 區塊鏈互聯網"),
            TradingPair("UNIUSDT", "UNI", "USDT", "altcoin", 0.1, 5.0, 3, 2, True, "Uniswap - DEX"),
            TradingPair("NEARUSDT", "NEAR", "USDT", "altcoin", 0.1, 5.0, 3, 2, True, "Near Protocol"),
            
            # 迷因幣 (Meme)
            TradingPair("SHIBUSDT", "SHIB", "USDT", "meme", 1000.0, 5.0, 8, 0, True, "柴犬幣"),
            TradingPair("PEPEUSDT", "PEPE", "USDT", "meme", 100000.0, 5.0, 10, 0, True, "青蛙佩佩"),
            TradingPair("FLOKIUSDT", "FLOKI", "USDT", "meme", 1000.0, 5.0, 8, 0, True, "Floki"),
            TradingPair("BONKUSDT", "BONK", "USDT", "meme", 10000.0, 5.0, 9, 0, True, "Bonk"),
            
            # DeFi 代幣
            TradingPair("AAVEUSDT", "AAVE", "USDT", "defi", 0.01, 5.0, 2, 2, True, "Aave - 借貸協議"),
            TradingPair("MKRUSDT", "MKR", "USDT", "defi", 0.001, 5.0, 1, 3, True, "MakerDAO"),
            TradingPair("CRVUSDT", "CRV", "USDT", "defi", 1.0, 5.0, 4, 1, True, "Curve Finance"),
            
            # Layer 2
            TradingPair("ARBUSDT", "ARB", "USDT", "layer2", 1.0, 5.0, 4, 1, True, "Arbitrum"),
            TradingPair("OPUSDT", "OP", "USDT", "layer2", 1.0, 5.0, 4, 1, True, "Optimism"),
            
            # AI 相關
            TradingPair("FETUSDT", "FET", "USDT", "ai", 1.0, 5.0, 4, 1, True, "Fetch.ai - AI 代幣"),
            TradingPair("AGIXUSDT", "AGIX", "USDT", "ai", 1.0, 5.0, 4, 1, True, "SingularityNET"),
            TradingPair("RENDERUSDT", "RENDER", "USDT", "ai", 0.1, 5.0, 3, 2, True, "Render Network"),
        ]
        
        for pair in default_pairs:
            self.add_trading_pair(pair)
        
        # 注意：匯率不存資料庫！使用 exchange_rate_service.py 即時獲取
        
        logger.info(f"✅ 預設數據初始化完成: {len(default_pairs)} 交易對")
    
    # ==================== 交易對操作 ====================
    
    def add_trading_pair(self, pair: TradingPair) -> bool:
        """新增交易對"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO trading_pairs 
                (symbol, base_asset, quote_asset, category, min_qty, min_notional, 
                 price_precision, qty_precision, is_active, description, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                pair.symbol, pair.base_asset, pair.quote_asset, pair.category,
                pair.min_qty, pair.min_notional, pair.price_precision, pair.qty_precision,
                1 if pair.is_active else 0, pair.description,
                datetime.now().isoformat()
            ))
            self.conn.commit()
            return True
        except Exception as e:
            logger.error(f"新增交易對失敗: {e}")
            return False
    
    def get_trading_pair(self, symbol: str) -> Optional[TradingPair]:
        """獲取交易對資訊"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM trading_pairs WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        if row:
            return TradingPair(
                symbol=row['symbol'],
                base_asset=row['base_asset'],
                quote_asset=row['quote_asset'],
                category=row['category'],
                min_qty=row['min_qty'],
                min_notional=row['min_notional'],
                price_precision=row['price_precision'],
                qty_precision=row['qty_precision'],
                is_active=bool(row['is_active']),
                description=row['description']
            )
        return None
    
    def get_all_trading_pairs(self, category: Optional[str] = None, active_only: bool = True) -> List[TradingPair]:
        """獲取所有交易對"""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM trading_pairs WHERE 1=1"
        params = []
        
        if active_only:
            query += " AND is_active = 1"
        if category:
            query += " AND category = ?"
            params.append(category)
        
        query += " ORDER BY category, symbol"
        
        cursor.execute(query, params)
        
        pairs = []
        for row in cursor.fetchall():
            pairs.append(TradingPair(
                symbol=row['symbol'],
                base_asset=row['base_asset'],
                quote_asset=row['quote_asset'],
                category=row['category'],
                min_qty=row['min_qty'],
                min_notional=row['min_notional'],
                price_precision=row['price_precision'],
                qty_precision=row['qty_precision'],
                is_active=bool(row['is_active']),
                description=row['description']
            ))
        return pairs
    
    def get_pairs_by_category(self) -> Dict[str, List[TradingPair]]:
        """按分類獲取交易對"""
        all_pairs = self.get_all_trading_pairs()
        categories: Dict[str, List[TradingPair]] = {}
        for pair in all_pairs:
            if pair.category not in categories:
                categories[pair.category] = []
            categories[pair.category].append(pair)
        return categories
    
    # ==================== 匯率操作（使用即時服務）====================
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Optional[float]:
        """
        獲取匯率（從即時服務）
        
        注意：匯率不存資料庫，使用 exchange_rate_service 即時獲取
        """
        try:
            from config.trading_config import resolve_binance_testnet
            from .binance_futures import BinanceFuturesConnector
            from .exchange_rate_service import get_exchange_rate_service

            testnet = resolve_binance_testnet(default=True)
            connector = BinanceFuturesConnector(testnet=testnet)
            service = get_exchange_rate_service(connector=connector)
            rate_info = service.get_rate(from_currency, to_currency)
            if rate_info:
                return rate_info.rate
            return None
        except ImportError:
            logger.warning("匯率服務不可用，請確保 exchange_rate_service.py 存在")
            return None
    
    def convert_currency(self, amount: float, from_currency: str, to_currency: str) -> Optional[float]:
        """貨幣轉換（使用即時匯率）"""
        rate = self.get_exchange_rate(from_currency, to_currency)
        if rate:
            return amount * rate
        return None
    
    # ==================== 交易記錄操作 ====================
    
    def record_trade(self, trade: TradeRecord) -> int:
        """記錄交易"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO trades 
            (symbol, side, quantity, entry_price, exit_price, stop_loss, take_profit,
             profit_loss, profit_loss_pct, strategy_name, confidence, status, opened_at, closed_at, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade.symbol, trade.side, trade.quantity, trade.entry_price, trade.exit_price,
            trade.stop_loss, trade.take_profit, trade.profit_loss, trade.profit_loss_pct,
            trade.strategy_name, trade.confidence, trade.status, trade.opened_at, trade.closed_at, trade.notes
        ))
        self.conn.commit()
        return cursor.lastrowid or 0
    
    def update_trade(self, trade_id: int, **kwargs) -> bool:
        """更新交易記錄"""
        if not kwargs:
            return False
        
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [trade_id]
        
        cursor = self.conn.cursor()
        cursor.execute(f"UPDATE trades SET {set_clause} WHERE id = ?", values)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def close_trade(self, trade_id: int, exit_price: float, notes: str = "") -> bool:
        """平倉交易"""
        cursor = self.conn.cursor()
        
        # 獲取原始交易
        cursor.execute("SELECT * FROM trades WHERE id = ?", (trade_id,))
        row = cursor.fetchone()
        if not row:
            return False
        
        # 計算盈虧
        entry_price = row['entry_price']
        quantity = row['quantity']
        side = row['side']
        
        if side == "BUY":
            profit_loss = (exit_price - entry_price) * quantity
            profit_loss_pct = (exit_price - entry_price) / entry_price * 100
        else:  # SELL
            profit_loss = (entry_price - exit_price) * quantity
            profit_loss_pct = (entry_price - exit_price) / entry_price * 100
        
        # 更新交易
        cursor.execute("""
            UPDATE trades SET 
                exit_price = ?, profit_loss = ?, profit_loss_pct = ?,
                status = 'CLOSED', closed_at = ?, notes = ?
            WHERE id = ?
        """, (exit_price, profit_loss, profit_loss_pct, datetime.now().isoformat(), notes, trade_id))
        self.conn.commit()
        return True
    
    def get_open_trades(self, symbol: Optional[str] = None) -> List[TradeRecord]:
        """獲取未平倉交易"""
        cursor = self.conn.cursor()
        
        if symbol:
            cursor.execute("SELECT * FROM trades WHERE status = 'OPEN' AND symbol = ?", (symbol,))
        else:
            cursor.execute("SELECT * FROM trades WHERE status = 'OPEN'")
        
        return [self._row_to_trade(row) for row in cursor.fetchall()]
    
    def get_trade_history(self, symbol: Optional[str] = None, limit: int = 100) -> List[TradeRecord]:
        """獲取交易歷史"""
        cursor = self.conn.cursor()
        
        if symbol:
            cursor.execute("""
                SELECT * FROM trades WHERE symbol = ?
                ORDER BY opened_at DESC LIMIT ?
            """, (symbol, limit))
        else:
            cursor.execute("""
                SELECT * FROM trades ORDER BY opened_at DESC LIMIT ?
            """, (limit,))
        
        return [self._row_to_trade(row) for row in cursor.fetchall()]
    
    def _row_to_trade(self, row) -> TradeRecord:
        """將資料庫行轉換為 TradeRecord"""
        return TradeRecord(
            id=row['id'],
            symbol=row['symbol'],
            side=row['side'],
            quantity=row['quantity'],
            entry_price=row['entry_price'],
            exit_price=row['exit_price'],
            stop_loss=row['stop_loss'],
            take_profit=row['take_profit'],
            profit_loss=row['profit_loss'],
            profit_loss_pct=row['profit_loss_pct'],
            strategy_name=row['strategy_name'],
            confidence=row['confidence'],
            status=row['status'],
            opened_at=row['opened_at'],
            closed_at=row['closed_at'],
            notes=row['notes'] or ""
        )
    
    # ==================== 信號記錄操作 ====================
    
    def record_signal(self, signal: SignalRecord) -> int:
        """記錄信號"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO signals 
            (symbol, action, confidence, strategy_name, price_at_signal, 
             stop_loss, take_profit, suggested_qty, suggested_value, reasons, created_at, executed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            signal.symbol, signal.action, signal.confidence, signal.strategy_name,
            signal.price_at_signal, signal.stop_loss, signal.take_profit,
            signal.suggested_qty, signal.suggested_value, signal.reasons,
            signal.created_at, 1 if signal.executed else 0
        ))
        self.conn.commit()
        return cursor.lastrowid or 0
    
    def get_recent_signals(self, symbol: Optional[str] = None, limit: int = 50) -> List[SignalRecord]:
        """獲取最近的信號"""
        cursor = self.conn.cursor()
        
        if symbol:
            cursor.execute("""
                SELECT * FROM signals WHERE symbol = ?
                ORDER BY created_at DESC LIMIT ?
            """, (symbol, limit))
        else:
            cursor.execute("""
                SELECT * FROM signals ORDER BY created_at DESC LIMIT ?
            """, (limit,))
        
        signals = []
        for row in cursor.fetchall():
            signals.append(SignalRecord(
                id=row['id'],
                symbol=row['symbol'],
                action=row['action'],
                confidence=row['confidence'],
                strategy_name=row['strategy_name'],
                price_at_signal=row['price_at_signal'],
                stop_loss=row['stop_loss'],
                take_profit=row['take_profit'],
                suggested_qty=row['suggested_qty'],
                suggested_value=row['suggested_value'],
                reasons=row['reasons'],
                created_at=row['created_at'],
                executed=bool(row['executed'])
            ))
        return signals
    
    # ==================== 策略權重操作 ====================
    
    def record_strategy_weights(self, weights: Dict[str, float], stats: Optional[Dict[str, Dict]] = None):
        """記錄策略權重"""
        cursor = self.conn.cursor()
        now = datetime.now().isoformat()
        
        for strategy_name, weight in weights.items():
            win_rate = None
            avg_return = None
            total_trades = 0
            
            if stats and strategy_name in stats:
                s = stats[strategy_name]
                win_rate = s.get('win_rate')
                avg_return = s.get('avg_return')
                total_trades = s.get('total_trades', 0)
            
            cursor.execute("""
                INSERT INTO strategy_weights 
                (strategy_name, weight, win_rate, avg_return, total_trades, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (strategy_name, weight, win_rate, avg_return, total_trades, now))
        
        self.conn.commit()
    
    def get_latest_weights(self) -> Dict[str, float]:
        """獲取最新的策略權重"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT strategy_name, weight FROM strategy_weights
            WHERE recorded_at = (SELECT MAX(recorded_at) FROM strategy_weights)
        """)
        
        weights = {}
        for row in cursor.fetchall():
            weights[row['strategy_name']] = row['weight']
        return weights
    
    # ==================== 帳戶快照 ====================
    
    def record_account_snapshot(self, balance: float, equity: float, 
                                 unrealized_pnl: float = 0, realized_pnl: float = 0,
                                 total_trades: int = 0, win_trades: int = 0,
                                 currency: str = "USDT"):
        """記錄帳戶快照"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO account_snapshots 
            (balance, equity, unrealized_pnl, realized_pnl, total_trades, win_trades, currency, snapshot_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (balance, equity, unrealized_pnl, realized_pnl, total_trades, win_trades, 
              currency, datetime.now().isoformat()))
        self.conn.commit()
    
    def get_account_history(self, days: int = 30) -> List[Dict]:
        """獲取帳戶歷史"""
        cursor = self.conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        cursor.execute("""
            SELECT * FROM account_snapshots 
            WHERE snapshot_at >= ?
            ORDER BY snapshot_at ASC
        """, (since,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    # ==================== 統計查詢 ====================
    
    def get_trading_statistics(self, days: int = 30) -> Dict:
        """獲取交易統計"""
        cursor = self.conn.cursor()
        since = (datetime.now() - timedelta(days=days)).isoformat()
        
        # 總體統計
        cursor.execute("""
            SELECT 
                COUNT(*) as total_trades,
                SUM(CASE WHEN profit_loss > 0 THEN 1 ELSE 0 END) as winning_trades,
                SUM(CASE WHEN profit_loss < 0 THEN 1 ELSE 0 END) as losing_trades,
                SUM(profit_loss) as total_pnl,
                AVG(profit_loss) as avg_pnl,
                MAX(profit_loss) as max_win,
                MIN(profit_loss) as max_loss
            FROM trades
            WHERE status = 'CLOSED' AND closed_at >= ?
        """, (since,))
        row = cursor.fetchone()
        
        total_trades = row['total_trades'] or 0
        winning_trades = row['winning_trades'] or 0
        
        stats = {
            'period_days': days,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': row['losing_trades'] or 0,
            'win_rate': winning_trades / total_trades if total_trades > 0 else 0,
            'total_pnl': row['total_pnl'] or 0,
            'avg_pnl': row['avg_pnl'] or 0,
            'max_win': row['max_win'] or 0,
            'max_loss': row['max_loss'] or 0,
        }
        
        # 按交易對統計
        cursor.execute("""
            SELECT symbol, 
                COUNT(*) as trades,
                SUM(profit_loss) as pnl
            FROM trades
            WHERE status = 'CLOSED' AND closed_at >= ?
            GROUP BY symbol
            ORDER BY pnl DESC
        """, (since,))
        
        stats['by_symbol'] = {row['symbol']: {'trades': row['trades'], 'pnl': row['pnl']} 
                              for row in cursor.fetchall()}
        
        return stats
    
    # ==================== 工具方法 ====================
    
    def format_price(self, symbol: str, price: float) -> str:
        """格式化價格"""
        pair = self.get_trading_pair(symbol)
        if pair:
            return f"{price:.{pair.price_precision}f}"
        return f"{price:.2f}"
    
    def format_quantity(self, symbol: str, quantity: float) -> float:
        """格式化數量（符合交易所精度要求）"""
        pair = self.get_trading_pair(symbol)
        if pair:
            return round(quantity, pair.qty_precision)
        return round(quantity, 3)
    
    def validate_order(self, symbol: str, quantity: float, price: float) -> Dict:
        """驗證訂單是否符合要求"""
        pair = self.get_trading_pair(symbol)
        if not pair:
            return {'valid': False, 'error': f'交易對 {symbol} 不存在'}
        
        if not pair.is_active:
            return {'valid': False, 'error': f'交易對 {symbol} 已停用'}
        
        if quantity < pair.min_qty:
            return {'valid': False, 'error': f'數量 {quantity} 小於最小值 {pair.min_qty}'}
        
        notional = quantity * price
        if notional < pair.min_notional:
            return {'valid': False, 'error': f'名義價值 {notional:.2f} 小於最小值 {pair.min_notional}'}
        
        return {'valid': True, 'formatted_qty': self.format_quantity(symbol, quantity)}
    
    def close(self):
        """關閉資料庫連接"""
        self.conn.close()
        logger.info("📦 資料庫連接已關閉")


# 全局資料庫實例
_db_instance: Optional[TradingDatabase] = None


def get_database() -> TradingDatabase:
    """獲取全局資料庫實例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = TradingDatabase()
    return _db_instance


if __name__ == "__main__":
    # 測試資料庫
    print("🧪 測試交易資料庫...\n")
    print("=" * 60)
    
    db = TradingDatabase("data/bioneuronai/trading/runtime/test_trading.db")
    
    # 測試交易對
    print("\n📊 交易對列表（按分類）：")
    categories = db.get_pairs_by_category()
    for cat, pairs in categories.items():
        print(f"\n  【{cat.upper()}】({len(pairs)} 個)")
        for p in pairs[:3]:  # 每類只顯示前3個
            print(f"    • {p.symbol}: {p.description}")
        if len(pairs) > 3:
            print(f"    ... 還有 {len(pairs) - 3} 個")
    
    # 測試即時匯率（從 exchange_rate_service）
    print("\n\n" + "=" * 60)
    print("💱 即時匯率轉換測試（從 API 獲取）：")
    test_amount = 1000  # USDT
    currencies = ["USD", "TWD", "EUR", "JPY", "CNY"]
    for curr in currencies:
        converted = db.convert_currency(test_amount, "USDT", curr)
        if converted:
            print(f"  {test_amount} USDT = {converted:,.2f} {curr}")
        else:
            print(f"  {test_amount} USDT → {curr}: 無法獲取匯率")
    
    # 測試訂單驗證
    print("\n\n" + "=" * 60)
    print("✅ 訂單驗證測試：")
    test_orders = [
        ("BTCUSDT", 0.01, 93000),
        ("BTCUSDT", 0.0001, 93000),  # 太小
        ("SHIBUSDT", 100000, 0.00001),
    ]
    for symbol, qty, price in test_orders:
        result = db.validate_order(symbol, qty, price)
        status = "✅" if result['valid'] else "❌"
        print(f"  {status} {symbol} {qty} @ {price}: {result}")
    
    print("\n" + "=" * 60)
    print("✅ 資料庫測試完成！")
    print("\n📦 資料庫存放的內容：")
    print("  ✅ 交易對配置（symbol, 最小數量, 精度等）")
    print("  ✅ 交易記錄（你做過的每筆交易）")
    print("  ✅ 信號記錄（AI 產生的信號歷史）")
    print("  ✅ 策略權重歷史（AI 學習過程）")
    print("  ✅ 帳戶快照（定期記錄餘額變化）")
    print("\n❌ 不存在資料庫的內容：")
    print("  ❌ 匯率 → 使用 exchange_rate_service.py 即時獲取")
    print("  ❌ 即時價格 → 從交易所 WebSocket 獲取")
    
    db.close()

