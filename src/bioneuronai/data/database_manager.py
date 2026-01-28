"""
數據庫管理器 (Database Manager)
================================

統一管理所有交易系統數據的持久化存儲。

數據分層策略：
- 熱數據（當日）：內存 + SQLite 實時寫入
- 溫數據（近期）：SQLite 查詢
- 冷數據（歷史）：定期壓縮歸檔

支持的數據類型：
1. 交易記錄 (trades)
2. 信號歷史 (signals)
3. 風險統計 (risk_stats)
4. 交易前檢查 (pretrade_checks)
5. 新聞分析 (news_analysis)
6. 性能指標 (performance_metrics)
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """交易系統數據庫管理器"""
    
    def __init__(self, db_path: str = "trading_data/trading.db", backup_enabled: bool = True):
        """
        初始化數據庫管理器
        
        Args:
            db_path: 數據庫文件路徑
            backup_enabled: 是否啟用 JSONL 備份
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(exist_ok=True, parents=True)
        
        self.backup_enabled = backup_enabled
        self.backup_dir = self.db_path.parent / "backups"
        if backup_enabled:
            self.backup_dir.mkdir(exist_ok=True)
        
        # 線程本地存儲，每個線程有自己的連接
        self._local = threading.local()
        
        # 初始化數據庫表
        self._create_tables()
        
        logger.info(f"✅ DatabaseManager 初始化完成: {self.db_path}")
    
    @contextmanager
    def _get_connection(self):
        """獲取線程安全的數據庫連接"""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            self._local.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            self._local.conn.row_factory = sqlite3.Row
        
        try:
            yield self._local.conn
        except Exception as e:
            self._local.conn.rollback()
            raise
        else:
            self._local.conn.commit()
    
    def _create_tables(self):
        """創建所有必要的數據表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 1. 交易記錄表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id TEXT UNIQUE,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    quantity REAL NOT NULL,
                    price REAL NOT NULL,
                    confidence REAL,
                    strategy TEXT,
                    timestamp TEXT NOT NULL,
                    pnl REAL,
                    fee REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)")
            
            # 2. 信號歷史表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    strategy_name TEXT,
                    reason TEXT,
                    target_price REAL,
                    stop_loss REAL,
                    take_profit REAL,
                    timestamp TEXT NOT NULL,
                    executed BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_signals_symbol ON signals(symbol)")
            
            # 3. 風險統計表 (時序數據)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS risk_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_trades INTEGER,
                    winning_trades INTEGER,
                    losing_trades INTEGER,
                    win_rate REAL,
                    total_profit REAL,
                    total_loss REAL,
                    net_profit REAL,
                    profit_factor REAL,
                    average_win REAL,
                    average_loss REAL,
                    sharpe_ratio REAL,
                    max_drawdown REAL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_risk_timestamp ON risk_stats(timestamp)")
            
            # 7. 新聞預測表 (News Predictions)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prediction_id TEXT UNIQUE NOT NULL,
                    news_id TEXT,
                    news_title TEXT,
                    news_source TEXT,
                    target_symbol TEXT NOT NULL,
                    predicted_direction TEXT NOT NULL,
                    predicted_magnitude REAL,
                    confidence REAL NOT NULL,
                    prediction_time TEXT NOT NULL,
                    check_after_hours INTEGER DEFAULT 4,
                    validation_time TEXT,
                    price_at_prediction REAL NOT NULL,
                    price_at_validation REAL,
                    actual_change_pct REAL,
                    status TEXT DEFAULT 'pending',
                    is_correct BOOLEAN,
                    accuracy_score REAL,
                    keywords_used TEXT,
                    sentiment_score REAL,
                    human_feedback TEXT,
                    human_rating INTEGER,
                    needs_human_review BOOLEAN DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_pred_symbol ON news_predictions(target_symbol)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_pred_status ON news_predictions(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_pred_time ON news_predictions(prediction_time)")
            
            # 8. 策略基因表 (Strategy Genes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_genes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gene_id TEXT UNIQUE NOT NULL,
                    strategy_type TEXT NOT NULL,
                    ma_fast INTEGER,
                    ma_slow INTEGER,
                    rsi_period INTEGER,
                    rsi_overbought REAL,
                    rsi_oversold REAL,
                    atr_period INTEGER,
                    bb_period INTEGER,
                    bb_std REAL,
                    stop_loss_atr_multiplier REAL,
                    take_profit_atr_multiplier REAL,
                    position_size_pct REAL,
                    min_confirmations INTEGER,
                    confirmation_threshold REAL,
                    fitness_score REAL DEFAULT 0.0,
                    total_trades INTEGER DEFAULT 0,
                    win_rate REAL DEFAULT 0.5,
                    profit_factor REAL DEFAULT 1.0,
                    sharpe_ratio REAL DEFAULT 0.0,
                    max_drawdown REAL DEFAULT 0.0,
                    total_return REAL DEFAULT 0.0,
                    generation INTEGER DEFAULT 0,
                    parent_ids TEXT,
                    birth_time TEXT NOT NULL,
                    is_mutant BOOLEAN DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_genes_fitness ON strategy_genes(fitness_score DESC)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_genes_generation ON strategy_genes(generation)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_genes_type ON strategy_genes(strategy_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_genes_active ON strategy_genes(is_active)")
            
            # 9. 演化歷史表 (Evolution History)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evolution_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    generation INTEGER NOT NULL,
                    best_fitness REAL NOT NULL,
                    avg_fitness REAL NOT NULL,
                    best_gene_id TEXT NOT NULL,
                    best_strategy_type TEXT,
                    survivors INTEGER,
                    eliminated INTEGER,
                    offspring INTEGER,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_evo_generation ON evolution_history(generation)")
            
            # 10. RL 訓練記錄表 (RL Training History)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rl_training_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    episode INTEGER NOT NULL,
                    timestep INTEGER NOT NULL,
                    mean_reward REAL,
                    std_reward REAL,
                    episode_length INTEGER,
                    loss REAL,
                    entropy REAL,
                    value_loss REAL,
                    policy_loss REAL,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rl_model ON rl_training_history(model_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_rl_timestep ON rl_training_history(timestep)")
            
            conn.commit()
            logger.info("✅ 數據表創建完成（包含新增的演化和預測表）")
            
            # 4. 交易前檢查表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pretrade_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    check_type TEXT NOT NULL,
                    result TEXT NOT NULL,
                    details TEXT,
                    passed BOOLEAN,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pretrade_timestamp ON pretrade_checks(timestamp)")
            
            # 5. 新聞分析表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS news_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    source TEXT,
                    url TEXT,
                    published_at TEXT,
                    sentiment TEXT,
                    score REAL,
                    keywords TEXT,
                    impact TEXT,
                    analyzed_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_news_published ON news_analysis(published_at)")
            
            # 6. 性能指標表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    period TEXT,
                    timestamp TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_name ON performance_metrics(metric_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON performance_metrics(timestamp)")
            
            # 11. 事件記憶表 (Event Memory) - 追蹤外部市場事件
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS event_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    headline TEXT NOT NULL,
                    score REAL NOT NULL,
                    status TEXT DEFAULT 'ACTIVE',
                    termination_condition TEXT,
                    embedding_id TEXT,
                    source TEXT,
                    source_confidence REAL DEFAULT 0.5,
                    affected_symbols TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TEXT,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 創建索引 - 優化查詢 ACTIVE 事件
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_status ON event_memory(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_type ON event_memory(event_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_event_created ON event_memory(created_at)")
            
            conn.commit()
            logger.info("✅ 數據表創建完成")
    
    # ==================== 交易記錄 ====================
    
    def save_trade(self, trade_info: Dict) -> Optional[int]:
        """
        保存交易記錄
        
        Args:
            trade_info: 交易信息字典
            
        Returns:
            插入的記錄 ID
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trades (
                    order_id, symbol, side, quantity, price, 
                    confidence, strategy, timestamp, pnl, fee
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade_info.get('order_id'),
                trade_info.get('symbol'),
                trade_info.get('side'),
                trade_info.get('quantity'),
                trade_info.get('price'),
                trade_info.get('confidence'),
                trade_info.get('strategy'),
                trade_info.get('timestamp', datetime.now().isoformat()),
                trade_info.get('pnl'),
                trade_info.get('fee')
            ))
            
            trade_id = cursor.lastrowid
            
            # 備份到 JSONL
            if self.backup_enabled:
                self._backup_to_jsonl('trades', trade_info)
            
            logger.debug(f"💾 交易記錄已保存: ID={trade_id}, Symbol={trade_info.get('symbol')}")
            return trade_id
    
    def get_trades(
        self, 
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        查詢交易記錄
        
        Args:
            start_date: 開始日期 (ISO格式)
            end_date: 結束日期 (ISO格式)
            symbol: 交易對過濾
            limit: 返回記錄數限制
            
        Returns:
            交易記錄列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM trades WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if end_date:
                query += " AND timestamp <= ?"
                params.append(end_date)
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def get_trade_statistics(self, days: int = 30) -> Dict:
        """
        獲取交易統計數據
        
        Args:
            days: 統計天數
            
        Returns:
            統計數據字典
        """
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 總交易次數
            cursor.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END) as winning,
                       SUM(CASE WHEN pnl < 0 THEN 1 ELSE 0 END) as losing,
                       SUM(pnl) as total_pnl,
                       AVG(pnl) as avg_pnl
                FROM trades
                WHERE timestamp >= ?
            """, (start_date,))
            
            row = cursor.fetchone()
            
            return {
                'total_trades': row['total'],
                'winning_trades': row['winning'],
                'losing_trades': row['losing'],
                'win_rate': row['winning'] / row['total'] if row['total'] > 0 else 0,
                'total_pnl': row['total_pnl'] or 0,
                'average_pnl': row['avg_pnl'] or 0,
                'period_days': days
            }
    
    # ==================== 信號歷史 ====================
    
    def save_signal(self, signal_info: Dict) -> Optional[int]:
        """保存交易信號"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO signals (
                    symbol, action, confidence, strategy_name, reason,
                    target_price, stop_loss, take_profit, timestamp, executed
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                signal_info.get('symbol'),
                signal_info.get('action'),
                signal_info.get('confidence'),
                signal_info.get('strategy_name'),
                signal_info.get('reason'),
                signal_info.get('target_price'),
                signal_info.get('stop_loss'),
                signal_info.get('take_profit'),
                signal_info.get('timestamp', datetime.now().isoformat()),
                signal_info.get('executed', False)
            ))
            
            signal_id = cursor.lastrowid
            
            if self.backup_enabled:
                self._backup_to_jsonl('signals', signal_info)
            
            return signal_id
    
    def get_signals(
        self,
        start_date: Optional[str] = None,
        symbol: Optional[str] = None,
        strategy: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """查詢信號歷史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM signals WHERE 1=1"
            params = []
            
            if start_date:
                query += " AND timestamp >= ?"
                params.append(start_date)
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            if strategy:
                query += " AND strategy_name = ?"
                params.append(strategy)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
    
    def mark_signal_executed(self, signal_id: int):
        """標記信號為已執行"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE signals SET executed = 1 WHERE id = ?
            """, (signal_id,))
    
    # ==================== 風險統計 ====================
    
    def save_risk_stats(self, stats: Dict) -> Optional[int]:
        """保存風險統計快照"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO risk_stats (
                    total_trades, winning_trades, losing_trades, win_rate,
                    total_profit, total_loss, net_profit, profit_factor,
                    average_win, average_loss, sharpe_ratio, max_drawdown, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stats.get('total_trades'),
                stats.get('winning_trades'),
                stats.get('losing_trades'),
                stats.get('win_rate'),
                stats.get('total_profit'),
                stats.get('total_loss'),
                stats.get('net_profit'),
                stats.get('profit_factor'),
                stats.get('average_win'),
                stats.get('average_loss'),
                stats.get('sharpe_ratio'),
                stats.get('max_drawdown'),
                datetime.now().isoformat()
            ))
            
            return cursor.lastrowid
    
    def get_latest_risk_stats(self) -> Optional[Dict]:
        """獲取最新風險統計"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM risk_stats 
                ORDER BY timestamp DESC LIMIT 1
            """)
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_risk_stats_history(self, days: int = 30) -> List[Dict]:
        """獲取風險統計歷史"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM risk_stats 
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (start_date,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ==================== 交易前檢查 ====================
    
    def save_pretrade_check(self, check_info: Dict) -> Optional[int]:
        """保存交易前檢查記錄"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pretrade_checks (
                    symbol, check_type, result, details, passed, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                check_info.get('symbol'),
                check_info.get('check_type'),
                check_info.get('result'),
                json.dumps(check_info.get('details', {}), ensure_ascii=False),
                check_info.get('passed'),
                datetime.now().isoformat()
            ))
            
            return cursor.lastrowid
    
    def get_pretrade_checks(self, symbol: Optional[str] = None, days: int = 7) -> List[Dict]:
        """查詢交易前檢查記錄"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM pretrade_checks WHERE timestamp >= ?"
            params = [start_date]
            
            if symbol:
                query += " AND symbol = ?"
                params.append(symbol)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                data = dict(row)
                if data.get('details'):
                    data['details'] = json.loads(data['details'])
                results.append(data)
            
            return results
    
    # ==================== 新聞分析 ====================
    
    def save_news_analysis(self, news_info: Dict) -> Optional[int]:
        """保存新聞分析結果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO news_analysis (
                    title, source, url, published_at, sentiment, 
                    score, keywords, impact
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                news_info.get('title'),
                news_info.get('source'),
                news_info.get('url'),
                news_info.get('published_at'),
                news_info.get('sentiment'),
                news_info.get('score'),
                json.dumps(news_info.get('keywords', []), ensure_ascii=False),
                news_info.get('impact')
            ))
            
            return cursor.lastrowid
    
    def get_recent_news(self, hours: int = 24, sentiment: Optional[str] = None) -> List[Dict]:
        """獲取近期新聞"""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM news_analysis WHERE published_at >= ?"
            params = [start_time]
            
            if sentiment:
                query += " AND sentiment = ?"
                params.append(sentiment)
            
            query += " ORDER BY published_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                data = dict(row)
                if data.get('keywords'):
                    data['keywords'] = json.loads(data['keywords'])
                results.append(data)
            
            return results
    
    # ==================== 性能指標 ====================
    
    def save_performance_metric(self, metric_name: str, value: float, period: str = "daily"):
        """保存性能指標"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO performance_metrics (
                    metric_name, metric_value, period, timestamp
                ) VALUES (?, ?, ?, ?)
            """, (metric_name, value, period, datetime.now().isoformat()))
    
    def get_performance_metrics(self, metric_name: str, days: int = 30) -> List[Dict]:
        """獲取性能指標歷史"""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM performance_metrics
                WHERE metric_name = ? AND timestamp >= ?
                ORDER BY timestamp ASC
            """, (metric_name, start_date))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ==================== 新聞預測 CRUD ====================
    
    def save_news_prediction(self, prediction: Dict) -> Optional[int]:
        """保存新聞預測"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO news_predictions (
                    prediction_id, news_id, news_title, news_source,
                    target_symbol, predicted_direction, predicted_magnitude,
                    confidence, prediction_time, check_after_hours,
                    price_at_prediction, keywords_used, sentiment_score,
                    needs_human_review, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                prediction.get('prediction_id'),
                prediction.get('news_id'),
                prediction.get('news_title'),
                prediction.get('news_source'),
                prediction.get('target_symbol'),
                prediction.get('predicted_direction'),
                prediction.get('predicted_magnitude'),
                prediction.get('confidence'),
                prediction.get('prediction_time'),
                prediction.get('check_after_hours', 4),
                prediction.get('price_at_prediction'),
                json.dumps(prediction.get('keywords_used', [])),
                prediction.get('sentiment_score'),
                prediction.get('needs_human_review', 0),
                prediction.get('status', 'pending')
            ))
            return cursor.lastrowid
    
    def update_prediction_validation(self, prediction_id: str, validation_data: Dict):
        """更新預測驗證結果"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE news_predictions SET
                    validation_time = ?,
                    price_at_validation = ?,
                    actual_change_pct = ?,
                    status = ?,
                    is_correct = ?,
                    accuracy_score = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE prediction_id = ?
            """, (
                validation_data.get('validation_time'),
                validation_data.get('price_at_validation'),
                validation_data.get('actual_change_pct'),
                validation_data.get('status'),
                validation_data.get('is_correct'),
                validation_data.get('accuracy_score'),
                prediction_id
            ))
    
    def get_pending_predictions(self) -> List[Dict]:
        """獲取待驗證的預測"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM news_predictions
                WHERE status = 'pending'
                ORDER BY prediction_time ASC
            """)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_prediction_accuracy(self, symbol: Optional[str] = None) -> Dict:
        """獲取預測準確率統計"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if symbol:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                        AVG(accuracy_score) as avg_accuracy,
                        AVG(confidence) as avg_confidence
                    FROM news_predictions
                    WHERE target_symbol = ? AND is_correct IS NOT NULL
                """, (symbol,))
            else:
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                        AVG(accuracy_score) as avg_accuracy,
                        AVG(confidence) as avg_confidence
                    FROM news_predictions
                    WHERE is_correct IS NOT NULL
                """)
            
            row = cursor.fetchone()
            if row and row['total'] > 0:
                return {
                    'total': row['total'],
                    'correct': row['correct'],
                    'accuracy_rate': row['correct'] / row['total'],
                    'avg_accuracy_score': row['avg_accuracy'] or 0,
                    'avg_confidence': row['avg_confidence'] or 0,
                }
            
            return {'total': 0, 'correct': 0, 'accuracy_rate': 0, 
                    'avg_accuracy_score': 0, 'avg_confidence': 0}
    
    # ==================== 策略基因 CRUD ====================
    
    def save_strategy_gene(self, gene: Dict) -> Optional[int]:
        """保存策略基因"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO strategy_genes (
                    gene_id, strategy_type, ma_fast, ma_slow,
                    rsi_period, rsi_overbought, rsi_oversold,
                    atr_period, bb_period, bb_std,
                    stop_loss_atr_multiplier, take_profit_atr_multiplier,
                    position_size_pct, min_confirmations, confirmation_threshold,
                    fitness_score, total_trades, win_rate, profit_factor,
                    sharpe_ratio, max_drawdown, total_return,
                    generation, parent_ids, birth_time, is_mutant, is_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                gene.get('gene_id'),
                gene.get('strategy_type'),
                gene.get('ma_fast'),
                gene.get('ma_slow'),
                gene.get('rsi_period'),
                gene.get('rsi_overbought'),
                gene.get('rsi_oversold'),
                gene.get('atr_period'),
                gene.get('bb_period'),
                gene.get('bb_std'),
                gene.get('stop_loss_atr_multiplier'),
                gene.get('take_profit_atr_multiplier'),
                gene.get('position_size_pct'),
                gene.get('min_confirmations'),
                gene.get('confirmation_threshold'),
                gene.get('fitness_score', 0.0),
                gene.get('total_trades', 0),
                gene.get('win_rate', 0.5),
                gene.get('profit_factor', 1.0),
                gene.get('sharpe_ratio', 0.0),
                gene.get('max_drawdown', 0.0),
                gene.get('total_return', 0.0),
                gene.get('generation', 0),
                json.dumps(gene.get('parent_ids', [])),
                gene.get('birth_time'),
                gene.get('is_mutant', 0),
                gene.get('is_active', 1)
            ))
            return cursor.lastrowid
    
    def update_gene_fitness(self, gene_id: str, fitness_data: Dict):
        """更新基因適應度"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE strategy_genes SET
                    fitness_score = ?,
                    total_trades = ?,
                    win_rate = ?,
                    profit_factor = ?,
                    sharpe_ratio = ?,
                    max_drawdown = ?,
                    total_return = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE gene_id = ?
            """, (
                fitness_data.get('fitness_score'),
                fitness_data.get('total_trades'),
                fitness_data.get('win_rate'),
                fitness_data.get('profit_factor'),
                fitness_data.get('sharpe_ratio'),
                fitness_data.get('max_drawdown'),
                fitness_data.get('total_return'),
                gene_id
            ))
    
    def get_best_genes(self, top_n: int = 10, strategy_type: Optional[str] = None) -> List[Dict]:
        """獲取最佳基因"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if strategy_type:
                cursor.execute("""
                    SELECT * FROM strategy_genes
                    WHERE is_active = 1 AND strategy_type = ?
                    ORDER BY fitness_score DESC
                    LIMIT ?
                """, (strategy_type, top_n))
            else:
                cursor.execute("""
                    SELECT * FROM strategy_genes
                    WHERE is_active = 1
                    ORDER BY fitness_score DESC
                    LIMIT ?
                """, (top_n,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def deactivate_genes(self, gene_ids: List[str]):
        """停用基因（淘汰）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            placeholders = ','.join(['?'] * len(gene_ids))
            cursor.execute(f"""
                UPDATE strategy_genes SET
                    is_active = 0,
                    updated_at = CURRENT_TIMESTAMP
                WHERE gene_id IN ({placeholders})
            """, gene_ids)
    
    # ==================== 演化歷史 CRUD ====================
    
    def save_evolution_record(self, evolution_data: Dict) -> Optional[int]:
        """保存演化記錄"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO evolution_history (
                    generation, best_fitness, avg_fitness, best_gene_id,
                    best_strategy_type, survivors, eliminated, offspring, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evolution_data.get('generation'),
                evolution_data.get('best_fitness'),
                evolution_data.get('avg_fitness'),
                evolution_data.get('best_gene_id'),
                evolution_data.get('best_strategy_type'),
                evolution_data.get('survivors'),
                evolution_data.get('eliminated'),
                evolution_data.get('offspring'),
                evolution_data.get('timestamp')
            ))
            return cursor.lastrowid
    
    def get_evolution_history(self, last_n: int = 100) -> List[Dict]:
        """獲取演化歷史"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM evolution_history
                ORDER BY generation DESC
                LIMIT ?
            """, (last_n,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ==================== RL 訓練記錄 CRUD ====================
    
    def save_rl_training_step(self, training_data: Dict) -> Optional[int]:
        """保存 RL 訓練步驟"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rl_training_history (
                    model_name, episode, timestep, mean_reward, std_reward,
                    episode_length, loss, entropy, value_loss, policy_loss, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                training_data.get('model_name'),
                training_data.get('episode'),
                training_data.get('timestep'),
                training_data.get('mean_reward'),
                training_data.get('std_reward'),
                training_data.get('episode_length'),
                training_data.get('loss'),
                training_data.get('entropy'),
                training_data.get('value_loss'),
                training_data.get('policy_loss'),
                training_data.get('timestamp')
            ))
            return cursor.lastrowid
    
    def get_rl_training_progress(self, model_name: str, last_n: int = 1000) -> List[Dict]:
        """獲取 RL 訓練進度"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM rl_training_history
                WHERE model_name = ?
                ORDER BY timestep DESC
                LIMIT ?
            """, (model_name, last_n))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    # ==================== 工具方法 ====================
    
    def _backup_to_jsonl(self, data_type: str, data: Dict):
        """備份數據到 JSONL 文件"""
        backup_file = self.backup_dir / f"{data_type}_backup.jsonl"
        
        try:
            with open(backup_file, 'a', encoding='utf-8') as f:
                json.dump({
                    **data,
                    'backup_time': datetime.now().isoformat()
                }, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            logger.error(f"備份失敗: {e}")
    
    def export_to_json(self, output_dir: str = "trading_data/exports"):
        """導出所有數據到 JSON 文件（用於遷移或分析）"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True, parents=True)
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 導出所有表
            tables = ['trades', 'signals', 'risk_stats', 'pretrade_checks', 'news_analysis']
            
            for table in tables:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                data = [dict(row) for row in rows]
                
                output_file = output_path / f"{table}.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                logger.info(f"✅ 導出 {table}: {len(data)} 條記錄 -> {output_file}")
    
    def cleanup_old_data(self, keep_days: int = 90):
        """清理舊數據（保留最近 N 天）"""
        cutoff_date = (datetime.now() - timedelta(days=keep_days)).isoformat()
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # 只清理信號歷史（交易記錄保留）
            cursor.execute("""
                DELETE FROM signals WHERE timestamp < ? AND executed = 0
            """, (cutoff_date,))
            
            deleted = cursor.rowcount
            logger.info(f"🗑️ 清理舊信號: {deleted} 條")
    
    # ==================== 事件記憶 (Event Memory) ====================
    
    def save_event(self, event_info: Dict) -> Optional[str]:
        """
        保存市場事件到事件記憶
        
        Args:
            event_info: 事件信息字典
                - event_id: 事件唯一ID (必填)
                - event_type: 事件類型 WAR/HACK/REGULATION/MACRO/etc (必填)
                - headline: 事件標題 (必填)
                - score: 事件影響評分 -1.0 到 1.0 (必填)
                - termination_condition: 結束條件描述 (選填)
                - embedding_id: 向量嵌入ID，預留給NLP (選填)
                - source: 來源 (選填)
                - source_confidence: 來源可信度 0-1 (選填)
                - affected_symbols: 影響的交易對，逗號分隔 (選填)
                - metadata: 額外元數據 JSON字串 (選填)
                
        Returns:
            event_id if successful, None otherwise
        """
        required_fields = ['event_id', 'event_type', 'headline', 'score']
        for field in required_fields:
            if field not in event_info:
                logger.error(f"❌ 缺少必填欄位: {field}")
                return None
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO event_memory 
                    (event_id, event_type, headline, score, status, 
                     termination_condition, embedding_id, source, source_confidence,
                     affected_symbols, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event_info['event_id'],
                    event_info['event_type'],
                    event_info['headline'],
                    event_info['score'],
                    event_info.get('status', 'ACTIVE'),
                    event_info.get('termination_condition'),
                    event_info.get('embedding_id'),
                    event_info.get('source'),
                    event_info.get('source_confidence', 0.5),
                    event_info.get('affected_symbols'),
                    event_info.get('metadata'),
                    datetime.now().isoformat()
                ))
                
                logger.info(f"✅ 事件已保存: {event_info['event_type']} - {event_info['headline'][:30]}...")
                return event_info['event_id']
                
            except Exception as e:
                logger.error(f"❌ 保存事件失敗: {e}")
                return None
    
    def get_active_events(self, event_type: Optional[str] = None, 
                          symbol: Optional[str] = None) -> List[Dict]:
        """
        獲取所有 ACTIVE 狀態的事件
        
        Args:
            event_type: 過濾特定事件類型 (選填)
            symbol: 過濾影響特定交易對的事件 (選填)
            
        Returns:
            事件列表
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM event_memory WHERE status = 'ACTIVE'"
            params: List[Any] = []
            
            if event_type:
                query += " AND event_type = ?"
                params.append(event_type)
            
            if symbol:
                # affected_symbols 是逗號分隔的字串
                query += " AND (affected_symbols LIKE ? OR affected_symbols IS NULL)"
                params.append(f"%{symbol}%")
            
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def resolve_event(self, event_id: str, resolution_note: Optional[str] = None) -> bool:
        """
        解析（關閉）一個事件
        
        Args:
            event_id: 事件ID
            resolution_note: 解析備註 (選填)
            
        Returns:
            是否成功
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                # 更新元數據以包含解析備註
                if resolution_note:
                    cursor.execute("""
                        UPDATE event_memory 
                        SET status = 'RESOLVED',
                            resolved_at = ?,
                            updated_at = ?,
                            metadata = COALESCE(metadata || '; ', '') || ?
                        WHERE event_id = ?
                    """, (
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        f"resolution: {resolution_note}",
                        event_id
                    ))
                else:
                    cursor.execute("""
                        UPDATE event_memory 
                        SET status = 'RESOLVED',
                            resolved_at = ?,
                            updated_at = ?
                        WHERE event_id = ?
                    """, (
                        datetime.now().isoformat(),
                        datetime.now().isoformat(),
                        event_id
                    ))
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ 事件已解析: {event_id}")
                    return True
                else:
                    logger.warning(f"⚠️ 找不到事件: {event_id}")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ 解析事件失敗: {e}")
                return False
    
    def calculate_total_event_score(self, symbol: Optional[str] = None) -> Tuple[float, List[Dict]]:
        """
        計算所有 ACTIVE 事件的總分數
        
        Args:
            symbol: 過濾特定交易對 (選填)
            
        Returns:
            (total_score, active_events_list)
        """
        active_events = self.get_active_events(symbol=symbol)
        
        if not active_events:
            return 0.0, []
        
        # 加權計算總分
        total_score = 0.0
        for event in active_events:
            score = event.get('score', 0.0)
            confidence = event.get('source_confidence', 0.5)
            # 以信心度加權
            total_score += score * confidence
        
        # 限制在 [-1, 1] 範圍
        total_score = max(-1.0, min(1.0, total_score))
        
        logger.debug(f"📊 Event Score: {total_score:.3f} from {len(active_events)} active events")
        return total_score, active_events
    
    def get_database_stats(self) -> Dict:
        """獲取數據庫統計信息"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            tables = ['trades', 'signals', 'risk_stats', 'pretrade_checks', 'news_analysis']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                row = cursor.fetchone()
                stats[table] = row['count']
            
            # 數據庫文件大小
            stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
            
            return stats
    
    def close(self):
        """關閉數據庫連接"""
        if hasattr(self._local, 'conn') and self._local.conn:
            self._local.conn.close()
            self._local.conn = None
            logger.info("🔒 DatabaseManager 已關閉")


# 全局單例
_db_manager: Optional[DatabaseManager] = None
_db_path_cache: Optional[str] = None


def get_database_manager(db_path: str = "src/trading_data/trading.db") -> DatabaseManager:
    """獲取數據庫管理器單例"""
    global _db_manager, _db_path_cache
    
    # 如果路徑變了，重新創建
    if _db_manager is None or _db_path_cache != db_path:
        _db_manager = DatabaseManager(db_path)
        _db_path_cache = db_path
    
    return _db_manager
