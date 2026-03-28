"""
關鍵字管理器
============

KeywordManager - 核心關鍵字管理功能

功能：
- 關鍵字匹配
- 預測記錄
- 準確率追蹤
- 持久化存儲 (SQLite + JSON)

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import json
import os
import re
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, cast
from dataclasses import asdict

# 2. 本地模組
from ..._paths import resolve_project_path
from .models import Keyword, KeywordMatch, PredictionRecord
from .loader import KeywordLoader

logger = logging.getLogger(__name__)


class KeywordManager:
    """
    關鍵字管理器 v3.0
    
    功能：
    1. 從分類檔案載入關鍵字 (config/keywords/)
    2. 文本匹配與權重計算
    3. 預測記錄與準確率追蹤
    4. 持久化存儲 SQLite + JSON
    
    注意：不再包含硬編碼關鍵字，所有關鍵字來自 config/keywords/ 目錄
    """
    
    # 路徑設定
    DEFAULT_CONFIG_PATH = "config/market_keywords.json"
    DEFAULT_KEYWORDS_DIR = "config/keywords"
    DEFAULT_DB_PATH = "config/market_keywords.db"
    
    # 學習參數
    WEIGHT_INCREASE_FACTOR = 1.08  # 預測正確 +8%
    WEIGHT_DECREASE_FACTOR = 0.92  # 預測錯誤 -8%
    MAX_DYNAMIC_WEIGHT = 2.0       # 權重上限
    MIN_DYNAMIC_WEIGHT = 0.3       # 權重下限
    
    # 基礎權重調整參數（長期學習）
    BASE_WEIGHT_INCREASE = 0.05    # 長期表現好 +0.05
    BASE_WEIGHT_DECREASE = 0.05    # 長期表現差 -0.05
    MAX_BASE_WEIGHT = 3.5          # 基礎權重上限
    MIN_BASE_WEIGHT = 0.5          # 基礎權重下限
    MIN_PREDICTIONS_FOR_BASE = 20  # 至少20次預測才調整基礎權重
    
    def __init__(self, config_path: Optional[str] = None, db_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.keywords_dir = self.DEFAULT_KEYWORDS_DIR
        self.db_path = str(resolve_project_path(db_path or self.DEFAULT_DB_PATH))
        self.keywords: Dict[str, Keyword] = {}
        
        # 初始化 SQLite 資料庫
        self._init_database()
        
        # 載入關鍵字
        self._load_keywords()
        
        logger.info(f"✅ 關鍵字系統就緒: {len(self.keywords)} 個關鍵字")
    
    def _init_database(self):
        """初始化 SQLite 資料庫"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 關鍵字表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS keywords (
                keyword TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                base_weight REAL NOT NULL,
                dynamic_weight REAL DEFAULT 1.0,
                sentiment_bias TEXT NOT NULL,
                description TEXT,
                added_date TEXT NOT NULL,
                last_updated TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0,
                prediction_count INTEGER DEFAULT 0,
                correct_count INTEGER DEFAULT 0
            )
        ''')
        
        # 預測歷史表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prediction_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                news_title TEXT,
                predicted_direction TEXT NOT NULL,
                actual_direction TEXT,
                price_before REAL,
                price_after REAL,
                price_change_pct REAL,
                is_correct INTEGER,
                created_at TEXT NOT NULL,
                verified_at TEXT,
                FOREIGN KEY (keyword) REFERENCES keywords(keyword)
            )
        ''')
        
        # 索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pred_keyword ON prediction_history(keyword)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pred_created ON prediction_history(created_at)')
        
        conn.commit()
        conn.close()
        logger.debug(f"資料庫已初始化: {self.db_path}")
    
    def _load_keywords(self):
        """載入關鍵字 (優先順序: 分類目錄 > 單一 JSON > 資料庫)"""
        loader = KeywordLoader(self.keywords_dir, self.config_path)
        
        # 嘗試從分類目錄載入
        self.keywords = loader.load()
        
        if self.keywords:
            # 同步到資料庫
            self._save_to_database()
            return
        
        # 嘗試從資料庫載入
        if self._load_from_database():
            logger.info(f"從資料庫載入 {len(self.keywords)} 個關鍵字")
            return
        
        # 無關鍵字可載入
        logger.error("❌ 無法載入關鍵字！請確認 config/keywords/ 目錄包含關鍵字檔案")
    
    def _load_from_database(self) -> bool:
        """從資料庫載入關鍵字"""
        if not os.path.exists(self.db_path):
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM keywords")
            rows = cursor.fetchall()
            conn.close()
            
            if not rows:
                return False
            
            for row in rows:
                kw = Keyword(
                    word=row[0],
                    category=row[1],
                    base_weight=row[2],
                    dynamic_weight=row[3],
                    sentiment_bias=row[4],
                    description=row[5],
                    added_date=row[6],
                    last_updated=row[7],
                    hit_count=row[8],
                    prediction_count=row[9],
                    correct_count=row[10]
                )
                self.keywords[kw.word] = kw
            
            return True
        except Exception as e:
            logger.error(f"從資料庫載入失敗: {e}")
            return False
    
    def _save_to_database(self):
        """儲存關鍵字到資料庫"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for kw in self.keywords.values():
                cursor.execute('''
                    INSERT OR REPLACE INTO keywords 
                    (keyword, category, base_weight, dynamic_weight, sentiment_bias,
                     description, added_date, last_updated, hit_count, 
                     prediction_count, correct_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    kw.word, kw.category, kw.base_weight, kw.dynamic_weight,
                    kw.sentiment_bias, kw.description, kw.added_date, kw.last_updated,
                    kw.hit_count, kw.prediction_count, kw.correct_count
                ))
            
            conn.commit()
            conn.close()
            logger.debug("已同步到資料庫")
        except Exception as e:
            logger.error(f"儲存到資料庫失敗: {e}")
    
    # ========================================
    # 關鍵字匹配
    # ========================================
    
    def find_matches(self, text: str) -> List[KeywordMatch]:
        """在文本中尋找匹配的關鍵字"""
        text_lower = text.lower()
        matches = []
        
        for kw in self.keywords.values():
            # 判斷是否為中文
            is_chinese = any('\u4e00' <= c <= '\u9fff' for c in kw.word)
            
            if is_chinese:
                # 中文不需要 word boundary
                if kw.word in text_lower:
                    kw.hit_count += 1
                    matches.append(self._create_match(kw))
            else:
                # 英文使用 word boundary
                pattern = r'\b' + re.escape(kw.word) + r'\b'
                if re.search(pattern, text_lower, re.IGNORECASE):
                    kw.hit_count += 1
                    matches.append(self._create_match(kw))
        
        # 按權重排序
        matches.sort(key=lambda x: x.effective_weight, reverse=True)
        return matches
    
    def _create_match(self, kw: Keyword) -> KeywordMatch:
        """建立 KeywordMatch 物件"""
        return KeywordMatch(
            keyword=kw.word,
            category=kw.category,
            effective_weight=kw.effective_weight,
            sentiment_bias=kw.sentiment_bias,
            description=kw.description,
            accuracy=kw.accuracy,
            days_old=kw.days_since_added
        )
    
    # ========================================
    # 關鍵字管理
    # ========================================
    
    def add_keyword(
        self,
        keyword: str,
        category: str,
        base_weight: float,
        sentiment_bias: str,
        description: str = "",
        subcategory: str = "general"
    ) -> bool:
        """新增關鍵字"""
        kw_lower = keyword.lower()
        
        if kw_lower in self.keywords:
            logger.warning(f"關鍵字 '{keyword}' 已存在")
            return False
        
        today = datetime.now().strftime("%Y-%m-%d")
        new_kw = Keyword(
            word=kw_lower,
            category=category,
            base_weight=base_weight,
            dynamic_weight=1.0,
            sentiment_bias=sentiment_bias,
            description=description,
            added_date=today,
            last_updated=today,
            subcategory=subcategory
        )
        
        self.keywords[kw_lower] = new_kw
        self._save_keywords()
        self._save_to_database()
        
        logger.info(f"新增關鍵字: {keyword} [{category}/{subcategory}] 權重:{base_weight}")
        return True
    
    def remove_keyword(self, keyword: str):
        """移除關鍵字"""
        kw_lower = keyword.lower()
        if kw_lower in self.keywords:
            del self.keywords[kw_lower]
            self._save_keywords()
            logger.info(f"已移除關鍵字: {keyword}")
    
    def update_keywords_from_trending(self, trending_topics: List[Dict[str, Any]]) -> int:
        """從熱門話題更新關鍵字"""
        added_count = 0
        
        for topic in trending_topics:
            keyword = topic.get('keyword', '').lower()
            category = topic.get('category', 'event')
            weight = topic.get('weight', 1.5)
            sentiment = topic.get('sentiment', 'neutral')
            description = topic.get('description', '')
            
            if keyword and keyword not in self.keywords:
                if self.add_keyword(keyword, category, weight, sentiment, description):
                    added_count += 1
        
        if added_count > 0:
            logger.info(f"從熱門話題新增 {added_count} 個關鍵字")
        
        return added_count
    
    def refresh_stale_keywords(self) -> int:
        """重置過時關鍵字權重"""
        today = datetime.now().strftime("%Y-%m-%d")
        refreshed = []
        
        for kw in self.keywords.values():
            if kw.is_stale:
                old_weight = kw.dynamic_weight
                kw.dynamic_weight = 1.0
                kw.last_updated = today
                refreshed.append((kw.word, old_weight))
        
        if refreshed:
            self._save_keywords()
            self._save_to_database()
            logger.info(f"已重置 {len(refreshed)} 個過時關鍵字")
        
        return len(refreshed)
    
    # ========================================
    # 儲存功能
    # ========================================
    
    def _save_keywords(self):
        """保存關鍵字（優先儲存到分類目錄）"""
        keywords_path = resolve_project_path(self.keywords_dir)
        
        if keywords_path.exists():
            self._save_to_category_files()
        else:
            self._save_to_single_file()
    
    def _save_to_category_files(self):
        """儲存到分類檔案"""
        keywords_path = resolve_project_path(self.keywords_dir)
        keywords_path.mkdir(parents=True, exist_ok=True)
        
        # 按類別分組
        by_category: Dict[str, List[Keyword]] = {}
        for kw in self.keywords.values():
            cat = kw.category
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(kw)
        
        # 儲存各類別檔案
        for cat, keywords in by_category.items():
            cat_file = keywords_path / f"{cat}.json"
            
            # 讀取現有檔案以保留描述
            description = ""
            if cat_file.exists():
                try:
                    with open(cat_file, 'r', encoding='utf-8') as f:
                        existing = json.load(f)
                        description = existing.get('description', '')
                except Exception:
                    pass
            
            cat_data = {
                "category": cat,
                "description": description,
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "count": len(keywords),
                "keywords": [asdict(kw) for kw in keywords]
            }
            
            with open(cat_file, 'w', encoding='utf-8') as f:
                json.dump(cat_data, f, ensure_ascii=False, indent=2)
        
        # 更新索引檔
        self._update_index_file(by_category)
        logger.debug(f"已儲存 {len(by_category)} 個分類檔案")
    
    def _save_to_single_file(self):
        """儲存到單一 JSON 檔案"""
        config_path = resolve_project_path(self.config_path)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        category_stats = {}
        for kw in self.keywords.values():
            key = f"{kw.category}/{kw.subcategory}"
            category_stats[key] = category_stats.get(key, 0) + 1
        
        data = {
            'version': '3.0',
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_keywords': len(self.keywords),
            'category_stats': category_stats,
            'keywords': [asdict(kw) for kw in self.keywords.values()]
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f"已保存關鍵字到 {config_path}")
        except Exception as e:
            logger.error(f"保存關鍵字失敗: {e}")
    
    def _update_index_file(self, by_category: Dict[str, List[Keyword]]) -> None:
        """更新索引檔"""
        keywords_path = resolve_project_path(self.keywords_dir)
        index_file = keywords_path / "_index.json"
        
        index_data = {
            "version": "3.0",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_keywords": len(self.keywords),
            "categories": {
                cat: {"file": f"{cat}.json", "count": len(kws)}
                for cat, kws in by_category.items()
            }
        }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    # ========================================
    # 預測記錄
    # ========================================
    
    def record_prediction(
        self,
        keyword: str,
        predicted_direction: str,
        price_before: float = 0.0,
        news_title: str = ""
    ) -> int:
        """記錄預測"""
        kw_lower = keyword.lower()
        if kw_lower not in self.keywords:
            logger.warning(f"關鍵字 '{keyword}' 不存在")
            return -1
        
        kw = self.keywords[kw_lower]
        kw.prediction_count += 1
        kw.last_updated = datetime.now().strftime("%Y-%m-%d")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO prediction_history 
            (keyword, news_title, predicted_direction, price_before, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (kw_lower, news_title, predicted_direction, price_before, now))
        
        prediction_id = cursor.lastrowid
        
        cursor.execute('''
            UPDATE keywords SET prediction_count = ?, last_updated = ?
            WHERE keyword = ?
        ''', (kw.prediction_count, kw.last_updated, kw_lower))
        
        conn.commit()
        conn.close()
        
        logger.info(f"預測記錄 [ID:{prediction_id}] {keyword} -> {predicted_direction}")
        self._save_keywords()
        
        return prediction_id if prediction_id is not None else -1
    
    def verify_prediction(
        self,
        prediction_id: int,
        actual_direction: str,
        price_after: float = 0.0,
        adjustment_factor: Optional[float] = None
    ) -> bool:
        """驗證預測"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT keyword, predicted_direction, price_before 
            FROM prediction_history WHERE id = ?
        ''', (prediction_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            logger.warning(f"找不到預測 ID: {prediction_id}")
            return False
        
        keyword, predicted_direction, price_before = row
        
        # 判斷正確性
        is_correct: bool = predicted_direction == actual_direction
        
        # 計算價格變化
        price_change_pct = 0.0
        if price_before and price_after:
            price_change_pct = ((price_after - price_before) / price_before) * 100
            
            # 如果價格變化超過 2%，用實際方向重新判斷
            if abs(price_change_pct) > 2.0:
                if price_change_pct > 0 and actual_direction == 'positive':
                    is_correct = (predicted_direction == 'positive')
                elif price_change_pct < 0 and actual_direction == 'negative':
                    is_correct = (predicted_direction == 'negative')
        
        # 更新預測記錄
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            UPDATE prediction_history SET
                actual_direction = ?,
                price_after = ?,
                price_change_pct = ?,
                is_correct = ?,
                verified_at = ?
            WHERE id = ?
        ''', (actual_direction, price_after, price_change_pct,
              1 if is_correct else 0, now, prediction_id))
        
        # 更新關鍵字統計
        kw = self.keywords.get(keyword)
        if kw and is_correct:
            kw.correct_count += 1
        
        # 調整動態權重（自適應步長：預測次數越多步長越小，防止震盪）
        if kw:
            factor = adjustment_factor
            if factor is None:
                n = max(1, kw.prediction_count)
                scale = 1.0 / (1.0 + 0.05 * n)  # 隨預測次數衰減
                if is_correct:
                    factor = 1.0 + (self.WEIGHT_INCREASE_FACTOR - 1.0) * scale
                else:
                    factor = 1.0 - (1.0 - self.WEIGHT_DECREASE_FACTOR) * scale
            kw.dynamic_weight = min(
                max(kw.dynamic_weight * factor, self.MIN_DYNAMIC_WEIGHT),
                self.MAX_DYNAMIC_WEIGHT
            )
            
            cursor.execute('''
                UPDATE keywords SET 
                    correct_count = ?, dynamic_weight = ?, last_updated = ?
                WHERE keyword = ?
            ''', (kw.correct_count, kw.dynamic_weight,
                  datetime.now().strftime("%Y-%m-%d"), keyword))
        
        conn.commit()
        conn.close()
        
        result_emoji = "✅" if is_correct else "❌"
        logger.info(f"{result_emoji} 驗證 [ID:{prediction_id}] {keyword}: "
                   f"預測={predicted_direction}, 實際={actual_direction}, "
                   f"變化={price_change_pct:+.2f}%")
        
        # 🆕 自動學習：長期表現 → 調整基礎權重
        if kw and kw.prediction_count >= self.MIN_PREDICTIONS_FOR_BASE:
            self._update_base_weight(keyword)
        
        self._save_keywords()
        return is_correct
    
    def _update_base_weight(self, keyword: str):
        """根據長期表現更新基礎權重"""
        kw = self.keywords.get(keyword.lower())
        if not kw or kw.prediction_count < self.MIN_PREDICTIONS_FOR_BASE:
            return
        
        old_base = kw.base_weight
        
        # 根據準確率調整基礎權重
        if kw.accuracy > 0.7:  # 70% 以上準確率
            kw.base_weight = min(
                kw.base_weight + self.BASE_WEIGHT_INCREASE,
                self.MAX_BASE_WEIGHT
            )
        elif kw.accuracy < 0.4:  # 40% 以下準確率
            kw.base_weight = max(
                kw.base_weight - self.BASE_WEIGHT_DECREASE,
                self.MIN_BASE_WEIGHT
            )
        
        if abs(kw.base_weight - old_base) > 0.01:
            logger.info(
                f"📊 {keyword} 基礎權重調整: {old_base:.2f} → {kw.base_weight:.2f} "
                f"(準確率 {kw.accuracy:.1%}, {kw.prediction_count}次預測)"
            )
            
            # 更新資料庫
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE keywords SET base_weight = ?, last_updated = ?
                WHERE keyword = ?
            ''', (kw.base_weight, datetime.now().strftime("%Y-%m-%d"), keyword.lower()))
            conn.commit()
            conn.close()
    
    def update_sentiment_bias_from_results(self, keyword: str, price_changes: list):
        """根據實際價格變化更新情緒偏向
        
        Args:
            keyword: 關鍵字
            price_changes: 價格變化列表 [(predicted_dir, actual_change_pct), ...]
        """
        kw = self.keywords.get(keyword.lower())
        if not kw or len(price_changes) < 10:
            return
        
        # 統計實際影響
        positive_count = sum(1 for _, change in price_changes if change > 1.0)
        negative_count = sum(1 for _, change in price_changes if change < -1.0)
        
        total = len(price_changes)
        positive_ratio = positive_count / total
        negative_ratio = negative_count / total
        
        old_bias = kw.sentiment_bias
        
        # 自動判斷情緒偏向
        if positive_ratio > 0.6:
            kw.sentiment_bias = 'positive'
        elif negative_ratio > 0.6:
            kw.sentiment_bias = 'negative'
        elif positive_ratio > 0.4 or negative_ratio > 0.4:
            kw.sentiment_bias = 'uncertain'
        else:
            kw.sentiment_bias = 'neutral'
        
        if kw.sentiment_bias != old_bias:
            logger.info(
                f"🎭 {keyword} 情緒偏向更新: {old_bias} → {kw.sentiment_bias} "
                f"(正:{positive_ratio:.1%} 負:{negative_ratio:.1%})"
            )
            
            # 更新資料庫
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE keywords SET sentiment_bias = ?, last_updated = ?
                WHERE keyword = ?
            ''', (kw.sentiment_bias, datetime.now().strftime("%Y-%m-%d"), keyword.lower()))
            conn.commit()
            conn.close()
    
    def record_and_verify_prediction(
        self,
        keyword: str,
        predicted_direction: str,
        actual_direction: str,
        price_before: float = 1000.0,
        price_after: Optional[float] = None,
        adjustment_factor: Optional[float] = None,
        news_title: str = ""
    ) -> None:
        """快速記錄並驗證預測"""
        if price_after is None:
            price_after = price_before

        pred_id = self.record_prediction(keyword, predicted_direction, price_before, news_title)
        if pred_id > 0:
            self.verify_prediction(
                pred_id,
                actual_direction,
                price_after,
                adjustment_factor=adjustment_factor,
            )
    
    # ========================================
    # 查詢與統計
    # ========================================
    
    def get_stale_keywords(self) -> List[Keyword]:
        """獲取過時關鍵字"""
        return [kw for kw in self.keywords.values() if kw.is_stale]
    
    def get_top_keywords(self, n: int = 20) -> List[Keyword]:
        """獲取權重最高的 N 個關鍵字"""
        sorted_kw = sorted(
            self.keywords.values(),
            key=lambda x: x.effective_weight,
            reverse=True
        )
        return sorted_kw[:n]
    
    def get_statistics(self) -> Dict[str, Any]:
        """獲取統計資料"""
        total = len(self.keywords)
        by_category: Dict[str, int] = {}
        stale_count = 0
        high_accuracy = 0
        low_accuracy = 0
        
        for kw in self.keywords.values():
            cat = kw.category
            by_category[cat] = by_category.get(cat, 0) + 1
            
            if kw.is_stale:
                stale_count += 1
            if kw.accuracy > 0.7:
                high_accuracy += 1
            elif kw.accuracy < 0.3 and kw.prediction_count > 5:
                low_accuracy += 1
        
        return {
            'total': total,
            'by_category': by_category,
            'stale_count': stale_count,
            'high_accuracy_count': high_accuracy,
            'low_accuracy_count': low_accuracy
        }
    
    def get_prediction_history(
        self,
        keyword: Optional[str] = None,
        limit: int = 50,
        only_verified: bool = False
    ) -> List[PredictionRecord]:
        """獲取預測歷史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM prediction_history"
        params: list = []
        
        conditions = []
        if keyword:
            conditions.append("keyword = ?")
            params.append(keyword.lower())
        if only_verified:
            conditions.append("verified_at IS NOT NULL")
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            records.append(PredictionRecord(
                id=row[0],
                keyword=row[1],
                news_title=row[2],
                predicted_direction=row[3],
                actual_direction=row[4],
                price_before=row[5],
                price_after=row[6],
                price_change_pct=row[7],
                is_correct=bool(row[8]) if row[8] is not None else None,
                created_at=row[9],
                verified_at=row[10]
            ))
        
        return records
    
    def get_pending_predictions(self) -> List[PredictionRecord]:
        """獲取待驗證的預測"""
        return self.get_prediction_history(only_verified=False)
    
    def get_overall_accuracy(self) -> Tuple[float, int, int]:
        """獲取整體準確率"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*), SUM(is_correct) 
            FROM prediction_history 
            WHERE verified_at IS NOT NULL
        ''')
        row = cursor.fetchone()
        conn.close()
        
        total = row[0] or 0
        correct = int(row[1] or 0)
        
        accuracy = correct / total if total > 0 else 0.0
        return accuracy, correct, total
    
    def get_keyword_performance(self, min_predictions: int = 5) -> List[Dict[str, Any]]:
        """獲取關鍵字表現排名"""
        performance: List[Dict[str, Any]] = []
        
        for kw in self.keywords.values():
            if kw.prediction_count >= min_predictions:
                performance.append({
                    'keyword': kw.word,
                    'category': kw.category,
                    'accuracy': kw.accuracy,
                    'predictions': kw.prediction_count,
                    'correct': kw.correct_count,
                    'effective_weight': kw.effective_weight,
                    'days_old': kw.days_since_added,
                    'is_stale': kw.is_stale
                })
        
        performance.sort(key=lambda x: cast(float, x["accuracy"]), reverse=True)
        return performance
    
    # ========================================
    # 分析功能
    # ========================================
    
    def get_importance_score(self, text: str) -> Tuple[float, List[str]]:
        """計算重要性評分"""
        matches = self.find_matches(text)
        
        if not matches:
            return 0.0, []
        
        top_matches = matches[:3]
        total_weight = sum(m.effective_weight for m in top_matches)
        accuracy_bonus = sum(m.accuracy * 0.5 for m in top_matches)
        
        score = min((total_weight + accuracy_bonus) * 1.2, 10.0)
        keywords = [m.keyword for m in matches]
        
        return round(score, 2), keywords
    
    def get_sentiment_bias(self, text: str) -> Tuple[str, float]:
        """分析情緒傾向"""
        matches = self.find_matches(text)
        
        if not matches:
            return 'neutral', 0.0
        
        positive_score = 0.0
        negative_score = 0.0
        
        for match in matches:
            weight = match.effective_weight * (0.5 + match.accuracy * 0.5)
            
            if match.sentiment_bias == 'positive':
                positive_score += weight
            elif match.sentiment_bias == 'negative':
                negative_score += weight
        
        total = positive_score + negative_score
        if total == 0:
            return 'neutral', 0.0
        
        if positive_score > negative_score:
            return 'positive', (positive_score - negative_score) / total
        elif negative_score > positive_score:
            return 'negative', (negative_score - positive_score) / total
        else:
            return 'neutral', 0.0
    
    def is_high_impact_news(self, text: str, threshold: float = 2.5) -> Tuple[bool, List[str]]:
        """判斷是否為高影響力新聞"""
        matches = self.find_matches(text)
        high_impact = [m for m in matches if m.effective_weight >= threshold]
        return len(high_impact) > 0, [m.keyword for m in high_impact]
    
    def print_report(self):
        """印出統計報告"""
        stats = self.get_statistics()
        stale = self.get_stale_keywords()
        top = self.get_top_keywords(10)
        
        print("=" * 60)
        print("📊 關鍵字系統報告")
        print("=" * 60)
        print(f"\n總關鍵字數: {stats['total']}")
        print("\n分類統計:")
        for cat, count in stats['by_category'].items():
            print(f"   {cat}: {count}")
        
        print("\n準確率統計:")
        print(f"   高準確率 (>70%): {stats['high_accuracy_count']}")
        print(f"   低準確率 (<30%): {stats['low_accuracy_count']}")
        
        print("\n權重最高關鍵字:")
        for kw in top:
            print(f"   • {kw.word}: {kw.effective_weight:.2f} "
                  f"(基礎:{kw.base_weight}, 動態:{kw.dynamic_weight:.2f}, "
                  f"準確率:{kw.accuracy:.0%})")
        
        if stale:
            print("\n⚠️ 過時關鍵字 (需要更新):")
            for kw in stale[:5]:
                print(f"   • {kw.word}: {kw.days_since_updated} 天, "
                      f"準確率:{kw.accuracy:.0%}")
        
        print("\n" + "=" * 60)


# ========================================
# 單例管理
# ========================================

_keyword_manager: Optional[KeywordManager] = None


def get_keyword_manager() -> KeywordManager:
    """獲取關鍵字管理器單例"""
    global _keyword_manager
    if _keyword_manager is None:
        _keyword_manager = KeywordManager()
    return _keyword_manager
