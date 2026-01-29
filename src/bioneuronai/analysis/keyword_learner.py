"""
關鍵字學習器 - 負責權重更新與學習
=======================================

職責分離：
- KeywordManager: 載入、匹配、查詢（唯讀為主）
- KeywordLearner: 學習、更新權重、儲存（寫入為主）

這樣設計的好處：
1. 單一職責原則
2. 查詢操作不會意外修改數據
3. 學習過程可獨立控制（批量學習、定時學習等）
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import asdict

from .keywords import KeywordManager, Keyword

logger = logging.getLogger(__name__)


class KeywordLearner:
    """
    關鍵字學習器
    
    負責：
    1. 記錄預測結果
    2. 驗證預測準確性
    3. 更新關鍵字權重（強化學習）
    4. 儲存更新後的數據
    
    使用方式：
    ```python
    from bioneuronai.analysis.keyword_learner import KeywordLearner
    
    learner = KeywordLearner()
    
    # 記錄預測
    learner.log_prediction(
        keywords=['fed', 'rate cut'],
        predicted_direction='bullish',
        symbol='BTCUSDT',
        price_at_prediction=88000
    )
    
    # 驗證並學習
    learner.validate_and_learn()
    ```
    """
    
    # 學習參數
    WEIGHT_INCREASE_FACTOR = 1.08  # 預測正確：權重 +8%
    WEIGHT_DECREASE_FACTOR = 0.92  # 預測錯誤：權重 -8%
    MAX_DYNAMIC_WEIGHT = 2.0       # 權重上限
    MIN_DYNAMIC_WEIGHT = 0.3       # 權重下限
    
    # 預測驗證參數
    DEFAULT_CHECK_HOURS = 4        # 預設驗證時間（小時）
    PRICE_THRESHOLD = 0.01         # 價格變動門檻 1%
    
    def __init__(
        self,
        keyword_manager: Optional[KeywordManager] = None,
        db_path: str = "config/keyword_learning.db"
    ):
        """
        初始化學習器
        
        Args:
            keyword_manager: 關鍵字管理器實例，若不提供則自動建立
            db_path: 學習記錄資料庫路徑
        """
        self.keyword_manager = keyword_manager or KeywordManager()
        self.db_path = db_path
        
        # 初始化學習記錄資料庫
        self._init_learning_db()
        
        logger.info("🎓 KeywordLearner 初始化完成")
    
    def _init_learning_db(self):
        """初始化學習記錄資料庫"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 預測記錄表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                prediction_id TEXT UNIQUE,
                keywords TEXT,
                predicted_direction TEXT,
                symbol TEXT,
                price_at_prediction REAL,
                timestamp TEXT,
                check_after_hours INTEGER,
                status TEXT DEFAULT 'pending',
                actual_direction TEXT,
                price_at_check REAL,
                price_change_pct REAL,
                checked_at TEXT,
                is_correct INTEGER
            )
        ''')
        
        # 學習歷史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS learning_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT,
                old_weight REAL,
                new_weight REAL,
                prediction_id TEXT,
                is_correct INTEGER,
                learned_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_prediction(
        self,
        keywords: List[str],
        predicted_direction: str,
        symbol: str,
        price_at_prediction: float,
        check_after_hours: int = 4,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        記錄一次預測
        
        Args:
            keywords: 觸發此預測的關鍵字列表
            predicted_direction: 預測方向 ('bullish', 'bearish', 'neutral')
            symbol: 交易對
            price_at_prediction: 預測時價格
            check_after_hours: 幾小時後驗證
            metadata: 額外資訊
            
        Returns:
            prediction_id: 預測ID
        """
        prediction_id = f"PRED_{datetime.now().strftime('%Y%m%d%H%M%S')}_{symbol}"
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO predictions 
            (prediction_id, keywords, predicted_direction, symbol, 
             price_at_prediction, timestamp, check_after_hours, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (
            prediction_id,
            json.dumps(keywords),
            predicted_direction,
            symbol,
            price_at_prediction,
            datetime.now().isoformat(),
            check_after_hours
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📝 記錄預測: {prediction_id} - {predicted_direction} ({len(keywords)} 關鍵字)")
        return prediction_id
    
    def validate_and_learn(
        self,
        get_current_price: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        驗證待驗證的預測並進行學習
        
        Args:
            get_current_price: 獲取當前價格的函數 (symbol) -> float
            
        Returns:
            學習統計
        """
        if get_current_price is None:
            # 使用預設的價格獲取方式
            from ..data.binance_futures import BinanceFuturesConnector
            connector = BinanceFuturesConnector(testnet=True)
            def get_current_price(symbol):
                data = connector.get_ticker_price(symbol)
                return data.price if data else None
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 找出需要驗證的預測
        cursor.execute('''
            SELECT * FROM predictions 
            WHERE status = 'pending'
            AND datetime(timestamp, '+' || check_after_hours || ' hours') <= datetime('now')
        ''')
        
        pending = cursor.fetchall()
        
        stats = {
            'validated': 0,
            'correct': 0,
            'wrong': 0,
            'keywords_updated': 0
        }
        
        for row in pending:
            pred_id = row[1]
            keywords = json.loads(row[2])
            predicted_direction = row[3]
            symbol = row[4]
            price_at_prediction = row[5]
            
            # 獲取當前價格
            current_price = get_current_price(symbol)
            if current_price is None:
                continue
            
            # 計算價格變動
            price_change_pct = (current_price - price_at_prediction) / price_at_prediction
            
            # 判斷實際方向
            if price_change_pct > self.PRICE_THRESHOLD:
                actual_direction = 'bullish'
            elif price_change_pct < -self.PRICE_THRESHOLD:
                actual_direction = 'bearish'
            else:
                actual_direction = 'neutral'
            
            # 判斷預測是否正確
            is_correct = (predicted_direction == actual_direction) or \
                         (predicted_direction == 'neutral' and abs(price_change_pct) < self.PRICE_THRESHOLD)
            
            # 更新預測記錄
            cursor.execute('''
                UPDATE predictions 
                SET status = 'validated',
                    actual_direction = ?,
                    price_at_check = ?,
                    price_change_pct = ?,
                    checked_at = ?,
                    is_correct = ?
                WHERE prediction_id = ?
            ''', (
                actual_direction,
                current_price,
                price_change_pct * 100,
                datetime.now().isoformat(),
                1 if is_correct else 0,
                pred_id
            ))
            
            # 更新關鍵字權重
            for kw in keywords:
                updated = self._update_keyword_weight(kw, is_correct, pred_id, cursor)
                if updated:
                    stats['keywords_updated'] += 1
            
            stats['validated'] += 1
            if is_correct:
                stats['correct'] += 1
                logger.info(f"✅ 預測正確: {pred_id} ({predicted_direction} == {actual_direction})")
            else:
                stats['wrong'] += 1
                logger.info(f"❌ 預測錯誤: {pred_id} ({predicted_direction} != {actual_direction})")
        
        conn.commit()
        conn.close()
        
        # 儲存更新後的關鍵字
        if stats['keywords_updated'] > 0:
            self._save_keywords()
        
        logger.info(f"🎓 學習完成: 驗證 {stats['validated']} 筆, "
                   f"正確 {stats['correct']}, 錯誤 {stats['wrong']}")
        
        return stats
    
    def _update_keyword_weight(
        self,
        keyword: str,
        is_correct: bool,
        prediction_id: str,
        cursor: sqlite3.Cursor
    ) -> bool:
        """
        更新單一關鍵字的權重
        
        Args:
            keyword: 關鍵字
            is_correct: 預測是否正確
            prediction_id: 預測ID
            cursor: 資料庫游標
            
        Returns:
            是否成功更新
        """
        kw_lower = keyword.lower()
        
        if kw_lower not in self.keyword_manager.keywords:
            logger.warning(f"關鍵字 '{keyword}' 不存在，跳過")
            return False
        
        kw_obj = self.keyword_manager.keywords[kw_lower]
        old_weight = kw_obj.dynamic_weight
        
        # 計算新權重
        if is_correct:
            new_weight = min(old_weight * self.WEIGHT_INCREASE_FACTOR, self.MAX_DYNAMIC_WEIGHT)
            kw_obj.correct_count += 1
        else:
            new_weight = max(old_weight * self.WEIGHT_DECREASE_FACTOR, self.MIN_DYNAMIC_WEIGHT)
        
        kw_obj.dynamic_weight = new_weight
        kw_obj.prediction_count += 1
        kw_obj.last_updated = datetime.now().strftime("%Y-%m-%d")
        
        # 記錄學習歷史
        cursor.execute('''
            INSERT INTO learning_history 
            (keyword, old_weight, new_weight, prediction_id, is_correct, learned_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            kw_lower,
            old_weight,
            new_weight,
            prediction_id,
            1 if is_correct else 0,
            datetime.now().isoformat()
        ))
        
        logger.debug(f"  📊 {keyword}: {old_weight:.2f} -> {new_weight:.2f} "
                    f"({'↑' if is_correct else '↓'})")
        
        return True
    
    def _save_keywords(self):
        """儲存更新後的關鍵字到分類檔案"""
        keywords_dir = Path("config/keywords")
        
        if not keywords_dir.exists():
            # 如果分類目錄不存在，使用舊的單檔儲存
            self.keyword_manager._save_keywords()
            return
        
        # 按類別分組
        by_category: Dict[str, List[Keyword]] = {}
        for kw in self.keyword_manager.keywords.values():
            cat = kw.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(kw)
        
        # 儲存各類別檔案
        for cat, keywords in by_category.items():
            cat_file = keywords_dir / f"{cat}.json"
            
            # 讀取現有檔案以保留元數據
            if cat_file.exists():
                with open(cat_file, 'r', encoding='utf-8') as f:
                    cat_data = json.load(f)
            else:
                cat_data = {"category": cat, "description": ""}
            
            cat_data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cat_data['count'] = len(keywords)
            cat_data['keywords'] = [asdict(kw) for kw in keywords]
            
            with open(cat_file, 'w', encoding='utf-8') as f:
                json.dump(cat_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 已儲存 {len(by_category)} 個類別檔案")
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """獲取學習統計"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 總體統計
        cursor.execute('SELECT COUNT(*) FROM predictions')
        total_predictions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM predictions WHERE status = "validated"')
        validated = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM predictions WHERE is_correct = 1')
        correct = cursor.fetchone()[0]
        
        # 各關鍵字統計
        cursor.execute('''
            SELECT keyword, 
                   COUNT(*) as total,
                   SUM(is_correct) as correct,
                   AVG(CASE WHEN is_correct = 1 THEN new_weight - old_weight ELSE old_weight - new_weight END) as avg_change
            FROM learning_history
            GROUP BY keyword
            ORDER BY total DESC
            LIMIT 20
        ''')
        keyword_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_predictions': total_predictions,
            'validated': validated,
            'correct': correct,
            'accuracy': correct / validated if validated > 0 else 0,
            'top_keywords': [
                {'keyword': row[0], 'total': row[1], 'correct': row[2], 'accuracy': row[2]/row[1] if row[1] > 0 else 0}
                for row in keyword_stats
            ]
        }
    
    def get_pending_count(self) -> int:
        """獲取待驗證的預測數量"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM predictions WHERE status = "pending"')
        count = cursor.fetchone()[0]
        conn.close()
        return count


# 便利函數
def get_keyword_learner() -> KeywordLearner:
    """獲取全局 KeywordLearner 實例"""
    if not hasattr(get_keyword_learner, '_instance'):
        get_keyword_learner._instance = KeywordLearner()
    return get_keyword_learner._instance
