"""
市場關鍵字配置模組（動態學習版 v2.0）
=====================================
定義會影響加密貨幣市場的重要關鍵字

特點：
1. 每個關鍵字都有新增日期和最後更新日期
2. 根據實際市場反應動態調整權重
3. 記錄命中次數和準確率
4. 自動標記過時關鍵字
5. 🆕 SQLite 持久化存儲
6. 🆕 詳細的預測歷史記錄
7. 🆕 支持導出/導入設定

使用方式：
    from market_keywords import KeywordManager
    
    km = KeywordManager()
    matches = km.find_matches("Fed raises interest rate")
    
    # 記錄預測（第一步：記錄預測）
    pred_id = km.record_prediction("fed", predicted_direction="negative", price_before=65000)
    
    # 驗證結果（第二步：3天後驗證）
    km.verify_prediction(pred_id, actual_direction="negative", price_after=64000)
"""

import json
import os
import sqlite3
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Keyword:
    """關鍵字資料結構"""
    keyword: str
    category: str           # person, institution, event, coin
    base_weight: float      # 基礎權重 1.0-3.0
    dynamic_weight: float   # 動態權重（根據表現調整）
    sentiment_bias: str     # positive, negative, neutral, uncertain
    description: str
    
    # 🆕 日期追蹤
    added_date: str         # 新增日期 (YYYY-MM-DD)
    last_updated: str       # 最後更新日期
    
    # 🆕 準確率追蹤
    hit_count: int = 0           # 命中次數（新聞中出現）
    prediction_count: int = 0    # 預測次數
    correct_count: int = 0       # 正確預測次數
    
    @property
    def accuracy(self) -> float:
        """計算準確率"""
        if self.prediction_count == 0:
            return 0.5  # 預設 50%
        return self.correct_count / self.prediction_count
    
    @property
    def effective_weight(self) -> float:
        """計算有效權重 = 基礎權重 × 動態權重"""
        return self.base_weight * self.dynamic_weight
    
    @property
    def days_since_added(self) -> int:
        """計算新增至今的天數"""
        added = datetime.strptime(self.added_date, "%Y-%m-%d")
        return (datetime.now() - added).days
    
    @property
    def days_since_updated(self) -> int:
        """計算最後更新至今的天數"""
        updated = datetime.strptime(self.last_updated, "%Y-%m-%d")
        return (datetime.now() - updated).days
    
    @property
    def is_stale(self) -> bool:
        """是否過時（超過 90 天未更新且命中率低）"""
        return self.days_since_updated > 90 and self.accuracy < 0.4


@dataclass
class PredictionRecord:
    """預測記錄"""
    id: int
    keyword: str
    news_title: str
    predicted_direction: str  # positive, negative, neutral
    actual_direction: Optional[str] = None
    price_before: float = 0.0
    price_after: Optional[float] = None
    price_change_pct: Optional[float] = None
    is_correct: Optional[bool] = None
    created_at: str = ""
    verified_at: Optional[str] = None


@dataclass
class KeywordMatch:
    """關鍵字匹配結果"""
    keyword: str
    category: str
    effective_weight: float
    sentiment_bias: str
    description: str
    accuracy: float
    days_old: int


class KeywordManager:
    """
    關鍵字管理器（動態學習版 v2.0）
    
    功能：
    1. 管理所有市場關鍵字
    2. 根據預測結果動態調整權重
    3. 追蹤關鍵字準確率
    4. 持久化存儲到 SQLite（主要）+ JSON（備份）
    5. 🆕 詳細的預測歷史記錄
    """
    
    # 預設設定檔路徑
    DEFAULT_CONFIG_PATH = "config/market_keywords.json"
    DEFAULT_DB_PATH = "config/market_keywords.db"
    
    # 權重調整參數
    WEIGHT_INCREASE_FACTOR = 1.08  # 正確預測時增加 8%
    WEIGHT_DECREASE_FACTOR = 0.92  # 錯誤預測時減少 8%
    MAX_DYNAMIC_WEIGHT = 2.0       # 最大動態權重
    MIN_DYNAMIC_WEIGHT = 0.3       # 最小動態權重
    
    def __init__(self, config_path: Optional[str] = None, db_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.keywords: Dict[str, Keyword] = {}
        
        # 初始化 SQLite 資料庫
        self._init_database()
        
        # 載入或初始化關鍵字
        if self._load_from_database():
            logger.info(f"📰 從資料庫載入 {len(self.keywords)} 個關鍵字")
        elif os.path.exists(self.config_path):
            self._load_keywords()
            self._save_to_database()  # 同步到資料庫
        else:
            self._initialize_default_keywords()
            self._save_keywords()
            self._save_to_database()
        
        logger.info(f"📰 關鍵字管理器已載入 {len(self.keywords)} 個關鍵字")
    
    def _init_database(self):
        """初始化 SQLite 資料庫"""
        # 確保目錄存在
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 創建關鍵字表
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
        
        # 🆕 創建預測歷史表
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
        
        # 創建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pred_keyword ON prediction_history(keyword)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pred_created ON prediction_history(created_at)')
        
        conn.commit()
        conn.close()
        logger.debug(f"資料庫初始化完成: {self.db_path}")
    
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
                    keyword=row[0],
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
                self.keywords[kw.keyword] = kw
            
            return True
        except Exception as e:
            logger.error(f"從資料庫載入失敗: {e}")
            return False
    
    def _save_to_database(self):
        """保存到資料庫"""
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
                    kw.keyword, kw.category, kw.base_weight, kw.dynamic_weight,
                    kw.sentiment_bias, kw.description, kw.added_date, kw.last_updated,
                    kw.hit_count, kw.prediction_count, kw.correct_count
                ))
            
            conn.commit()
            conn.close()
            logger.debug("關鍵字已保存到資料庫")
        except Exception as e:
            logger.error(f"保存到資料庫失敗: {e}")
    
    def _initialize_default_keywords(self):
        """初始化預設關鍵字"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # ========================================
        # 🧑 重要人物
        # ========================================
        persons = {
            'elon musk': ('person', 2.5, 'uncertain', '特斯拉CEO，推文常引發市場波動'),
            'musk': ('person', 2.5, 'uncertain', '馬斯克'),
            'vitalik': ('person', 2.0, 'neutral', '以太坊創辦人'),
            'vitalik buterin': ('person', 2.0, 'neutral', '以太坊創辦人'),
            'cz': ('person', 2.0, 'neutral', '幣安前CEO'),
            'changpeng zhao': ('person', 2.0, 'neutral', '幣安前CEO'),
            'michael saylor': ('person', 2.0, 'positive', 'MicroStrategy CEO，比特幣大多頭'),
            'saylor': ('person', 2.0, 'positive', 'MicroStrategy CEO'),
            'cathie wood': ('person', 1.8, 'positive', 'ARK Invest CEO'),
            'brian armstrong': ('person', 1.5, 'neutral', 'Coinbase CEO'),
            'sam bankman': ('person', 2.0, 'negative', 'FTX 前CEO'),
            'sbf': ('person', 2.0, 'negative', 'FTX 前CEO'),
            'powell': ('person', 3.0, 'uncertain', '美聯儲主席'),
            'jerome powell': ('person', 3.0, 'uncertain', '美聯儲主席'),
            'yellen': ('person', 2.8, 'uncertain', '美國財政部長'),
            'janet yellen': ('person', 2.8, 'uncertain', '美國財政部長'),
            'gensler': ('person', 2.5, 'negative', 'SEC 主席，對加密貨幣態度強硬'),
            'gary gensler': ('person', 2.5, 'negative', 'SEC 主席'),
            'lagarde': ('person', 2.5, 'uncertain', '歐洲央行行長'),
            'trump': ('person', 2.5, 'uncertain', '美國前/現任總統'),
            'biden': ('person', 2.3, 'uncertain', '美國總統'),
            'warren buffett': ('person', 2.0, 'negative', '投資大師，對加密貨幣持負面態度'),
            'buffett': ('person', 2.0, 'negative', '巴菲特'),
            'larry fink': ('person', 2.2, 'positive', 'BlackRock CEO，推動比特幣 ETF'),
        }
        
        for kw, (cat, weight, sentiment, desc) in persons.items():
            self.keywords[kw] = Keyword(
                keyword=kw, category=cat, base_weight=weight,
                dynamic_weight=1.0, sentiment_bias=sentiment, description=desc,
                added_date=today, last_updated=today
            )
        
        # ========================================
        # 🏛️ 重要機構
        # ========================================
        institutions = {
            'fed': ('institution', 3.0, 'uncertain', '美國聯邦儲備系統'),
            'federal reserve': ('institution', 3.0, 'uncertain', '美國聯邦儲備系統'),
            'fomc': ('institution', 3.0, 'uncertain', '聯邦公開市場委員會'),
            'sec': ('institution', 2.8, 'uncertain', '美國證券交易委員會'),
            'cftc': ('institution', 2.5, 'uncertain', '美國商品期貨交易委員會'),
            'treasury': ('institution', 2.5, 'uncertain', '美國財政部'),
            'doj': ('institution', 2.5, 'negative', '美國司法部'),
            'ecb': ('institution', 2.5, 'uncertain', '歐洲中央銀行'),
            'pboc': ('institution', 2.5, 'negative', '中國人民銀行'),
            'blackrock': ('institution', 2.5, 'positive', '全球最大資產管理公司'),
            'fidelity': ('institution', 2.3, 'positive', '富達投資'),
            'grayscale': ('institution', 2.2, 'positive', '灰度投資'),
            'jpmorgan': ('institution', 2.0, 'uncertain', '摩根大通'),
            'goldman sachs': ('institution', 2.0, 'uncertain', '高盛'),
            'microstrategy': ('institution', 2.0, 'positive', '持有大量比特幣的公司'),
            'tesla': ('institution', 2.2, 'uncertain', '特斯拉，曾購入比特幣'),
            'binance': ('institution', 2.5, 'uncertain', '全球最大加密貨幣交易所'),
            'coinbase': ('institution', 2.3, 'uncertain', '美國最大合規交易所'),
            'ftx': ('institution', 2.0, 'negative', '已破產交易所'),
            'paypal': ('institution', 2.0, 'positive', '支付公司，支持加密貨幣'),
        }
        
        for kw, (cat, weight, sentiment, desc) in institutions.items():
            self.keywords[kw] = Keyword(
                keyword=kw, category=cat, base_weight=weight,
                dynamic_weight=1.0, sentiment_bias=sentiment, description=desc,
                added_date=today, last_updated=today
            )
        
        # ========================================
        # 📰 重要事件
        # ========================================
        events = {
            # 央行政策
            'rate hike': ('event', 3.0, 'negative', '升息'),
            'rate cut': ('event', 3.0, 'positive', '降息'),
            'interest rate': ('event', 2.8, 'uncertain', '利率決策'),
            'quantitative easing': ('event', 2.5, 'positive', '量化寬鬆'),
            'qe': ('event', 2.5, 'positive', '量化寬鬆'),
            'tapering': ('event', 2.3, 'negative', '縮減購債'),
            'inflation': ('event', 2.5, 'uncertain', '通膨數據'),
            'cpi': ('event', 2.5, 'uncertain', '消費者物價指數'),
            'nonfarm': ('event', 2.3, 'uncertain', '非農就業'),
            
            # ETF
            'etf approved': ('event', 3.0, 'positive', 'ETF 獲批'),
            'etf approval': ('event', 3.0, 'positive', 'ETF 批准'),
            'etf rejected': ('event', 2.5, 'negative', 'ETF 被拒'),
            'spot etf': ('event', 2.8, 'positive', '現貨 ETF'),
            'etf filing': ('event', 2.0, 'positive', 'ETF 申請'),
            
            # 安全事件
            'hack': ('event', 3.0, 'negative', '駭客攻擊'),
            'hacked': ('event', 3.0, 'negative', '被駭'),
            'exploit': ('event', 3.0, 'negative', '漏洞利用'),
            'stolen': ('event', 2.8, 'negative', '被盜'),
            'rug pull': ('event', 3.0, 'negative', '捲款跑路'),
            'scam': ('event', 2.5, 'negative', '詐騙'),
            
            # 監管
            'lawsuit': ('event', 2.5, 'negative', '訴訟'),
            'investigation': ('event', 2.3, 'negative', '調查'),
            'ban': ('event', 2.8, 'negative', '禁止'),
            'banned': ('event', 2.8, 'negative', '被禁'),
            'crackdown': ('event', 2.5, 'negative', '打壓'),
            'regulation': ('event', 2.0, 'uncertain', '監管'),
            
            # 市場事件
            'halving': ('event', 2.8, 'positive', '減半'),
            'all-time high': ('event', 2.0, 'positive', '歷史新高'),
            'ath': ('event', 2.0, 'positive', '歷史新高'),
            'crash': ('event', 2.5, 'negative', '崩盤'),
            'plunge': ('event', 2.3, 'negative', '暴跌'),
            'surge': ('event', 2.0, 'positive', '暴漲'),
            'rally': ('event', 1.8, 'positive', '反彈'),
            'liquidation': ('event', 2.3, 'negative', '清算'),
            'bankruptcy': ('event', 2.8, 'negative', '破產'),
            
            # 技術事件
            'hard fork': ('event', 2.0, 'uncertain', '硬分叉'),
            'upgrade': ('event', 1.8, 'positive', '升級'),
            'mainnet': ('event', 2.0, 'positive', '主網上線'),
            'listing': ('event', 2.0, 'positive', '上市'),
            'delisting': ('event', 2.0, 'negative', '下架'),
            'partnership': ('event', 1.8, 'positive', '合作'),
            'whale': ('event', 2.0, 'uncertain', '大戶動向'),
        }
        
        for kw, (cat, weight, sentiment, desc) in events.items():
            self.keywords[kw] = Keyword(
                keyword=kw, category=cat, base_weight=weight,
                dynamic_weight=1.0, sentiment_bias=sentiment, description=desc,
                added_date=today, last_updated=today
            )
        
        # ========================================
        # 🪙 幣種
        # ========================================
        coins = {
            'bitcoin': ('coin', 2.0, 'neutral', 'BTC'),
            'btc': ('coin', 2.0, 'neutral', 'BTC'),
            'ethereum': ('coin', 2.0, 'neutral', 'ETH'),
            'eth': ('coin', 2.0, 'neutral', 'ETH'),
            'solana': ('coin', 1.8, 'neutral', 'SOL'),
            'sol': ('coin', 1.8, 'neutral', 'SOL'),
            'xrp': ('coin', 1.8, 'neutral', 'XRP'),
            'dogecoin': ('coin', 1.8, 'uncertain', 'DOGE'),
            'doge': ('coin', 1.8, 'uncertain', 'DOGE'),
            'tether': ('coin', 1.8, 'uncertain', 'USDT'),
            'usdt': ('coin', 1.5, 'neutral', 'Tether'),
            'usdc': ('coin', 1.5, 'neutral', 'USD Coin'),
        }
        
        for kw, (cat, weight, sentiment, desc) in coins.items():
            self.keywords[kw] = Keyword(
                keyword=kw, category=cat, base_weight=weight,
                dynamic_weight=1.0, sentiment_bias=sentiment, description=desc,
                added_date=today, last_updated=today
            )
    
    def _load_keywords(self):
        """從 JSON 載入關鍵字"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for kw_data in data.get('keywords', []):
                kw = Keyword(**kw_data)
                self.keywords[kw.keyword] = kw
            
            logger.info(f"📰 從 {self.config_path} 載入 {len(self.keywords)} 個關鍵字")
        except Exception as e:
            logger.error(f"載入關鍵字失敗: {e}")
            self._initialize_default_keywords()
    
    def _save_keywords(self):
        """保存關鍵字到 JSON"""
        try:
            # 確保目錄存在
            Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                'version': '2.0',
                'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'total_keywords': len(self.keywords),
                'keywords': [asdict(kw) for kw in self.keywords.values()]
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"💾 關鍵字已保存到 {self.config_path}")
        except Exception as e:
            logger.error(f"保存關鍵字失敗: {e}")
    
    def find_matches(self, text: str) -> List[KeywordMatch]:
        """在文本中查找匹配的關鍵字"""
        text_lower = text.lower()
        matches = []
        
        for kw in self.keywords.values():
            pattern = r'\b' + re.escape(kw.keyword) + r'\b'
            if re.search(pattern, text_lower, re.IGNORECASE):
                # 記錄命中
                kw.hit_count += 1
                
                matches.append(KeywordMatch(
                    keyword=kw.keyword,
                    category=kw.category,
                    effective_weight=kw.effective_weight,
                    sentiment_bias=kw.sentiment_bias,
                    description=kw.description,
                    accuracy=kw.accuracy,
                    days_old=kw.days_since_added
                ))
        
        # 按有效權重排序
        matches.sort(key=lambda x: x.effective_weight, reverse=True)
        return matches
    
    def record_prediction(
        self, 
        keyword: str, 
        predicted_direction: str,  # positive, negative, neutral
        price_before: float = 0.0,
        news_title: str = ""
    ) -> int:
        """
        記錄預測（第一步）
        
        Args:
            keyword: 關鍵字
            predicted_direction: 預測方向 (positive/negative/neutral)
            price_before: 預測時的價格
            news_title: 新聞標題
            
        Returns:
            prediction_id: 預測記錄ID，用於後續驗證
        """
        kw_lower = keyword.lower()
        if kw_lower not in self.keywords:
            logger.warning(f"關鍵字 '{keyword}' 不存在")
            return -1
        
        kw = self.keywords[kw_lower]
        kw.prediction_count += 1
        kw.last_updated = datetime.now().strftime("%Y-%m-%d")
        
        # 存儲到資料庫
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO prediction_history 
            (keyword, news_title, predicted_direction, price_before, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (kw_lower, news_title, predicted_direction, price_before, now))
        
        prediction_id = cursor.lastrowid
        
        # 更新關鍵字的 prediction_count
        cursor.execute('''
            UPDATE keywords SET prediction_count = ?, last_updated = ?
            WHERE keyword = ?
        ''', (kw.prediction_count, kw.last_updated, kw_lower))
        
        conn.commit()
        conn.close()
        
        logger.info(f"📝 預測已記錄 [ID:{prediction_id}] {keyword} -> {predicted_direction}")
        self._save_keywords()
        
        return prediction_id if prediction_id is not None else -1
    
    def verify_prediction(
        self,
        prediction_id: int,
        actual_direction: str,  # positive, negative, neutral
        price_after: float = 0.0
    ) -> bool:
        """
        驗證預測結果（第二步）
        
        Args:
            prediction_id: 預測記錄ID
            actual_direction: 實際方向 (positive/negative/neutral)
            price_after: 驗證時的價格
            
        Returns:
            is_correct: 預測是否正確
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 獲取預測記錄
        cursor.execute('''
            SELECT keyword, predicted_direction, price_before 
            FROM prediction_history WHERE id = ?
        ''', (prediction_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            logger.warning(f"找不到預測記錄 ID: {prediction_id}")
            return False
        
        keyword, predicted_direction, price_before = row
        
        # 判斷預測是否正確
        is_correct = (predicted_direction == actual_direction)
        
        # 計算價格變動
        price_change_pct = 0.0
        if price_before and price_after:
            price_change_pct = ((price_after - price_before) / price_before) * 100
            
            # 如果價格變動超過 2%，更看重實際方向
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
        
        # 🆕 動態調整權重
        if kw:
            if is_correct:
                kw.dynamic_weight = min(
                    kw.dynamic_weight * self.WEIGHT_INCREASE_FACTOR,
                    self.MAX_DYNAMIC_WEIGHT
                )
            else:
                kw.dynamic_weight = max(
                    kw.dynamic_weight * self.WEIGHT_DECREASE_FACTOR,
                    self.MIN_DYNAMIC_WEIGHT
                )
            
            # 更新資料庫
            cursor.execute('''
                UPDATE keywords SET 
                    correct_count = ?, dynamic_weight = ?, last_updated = ?
                WHERE keyword = ?
            ''', (kw.correct_count, kw.dynamic_weight, 
                  datetime.now().strftime("%Y-%m-%d"), keyword))
        
        conn.commit()
        conn.close()
        
        # 記錄日誌
        result_emoji = "✅" if is_correct else "❌"
        logger.info(f"{result_emoji} 預測驗證 [ID:{prediction_id}] {keyword}: "
                   f"預測={predicted_direction}, 實際={actual_direction}, "
                   f"價格變動={price_change_pct:+.2f}%")
        
        if kw:
            logger.info(f"   📊 {keyword} 更新: "
                       f"準確率={kw.accuracy:.1%}, 動態權重={kw.dynamic_weight:.2f}")
        
        self._save_keywords()
        return is_correct
    
    def record_and_verify_prediction(
        self, 
        keyword: str, 
        predicted_direction: str,
        actual_direction: str,
        price_change_pct: float = 0.0
    ):
        """
        向下兼容的方法：直接記錄並驗證預測
        
        Args:
            keyword: 關鍵字
            predicted_direction: 預測方向
            actual_direction: 實際方向
            price_change_pct: 價格變動百分比
        """
        price_before = 1000.0  # 假設初始價格
        price_after = price_before * (1 + price_change_pct / 100)
        
        pred_id = self.record_prediction(keyword, predicted_direction, price_before)
        if pred_id > 0:
            self.verify_prediction(pred_id, actual_direction, price_after)
    
    def add_keyword(
        self,
        keyword: str,
        category: str,
        base_weight: float,
        sentiment_bias: str,
        description: str
    ):
        """新增關鍵字"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        self.keywords[keyword.lower()] = Keyword(
            keyword=keyword.lower(),
            category=category,
            base_weight=base_weight,
            dynamic_weight=1.0,
            sentiment_bias=sentiment_bias,
            description=description,
            added_date=today,
            last_updated=today
        )
        
        self._save_keywords()
        logger.info(f"➕ 新增關鍵字: {keyword}")
    
    def remove_keyword(self, keyword: str):
        """移除關鍵字"""
        kw_lower = keyword.lower()
        if kw_lower in self.keywords:
            del self.keywords[kw_lower]
            self._save_keywords()
            logger.info(f"➖ 移除關鍵字: {keyword}")
    
    def get_stale_keywords(self) -> List[Keyword]:
        """獲取過時的關鍵字（超過 90 天未更新且準確率低）"""
        return [kw for kw in self.keywords.values() if kw.is_stale]
    
    def get_top_keywords(self, n: int = 20) -> List[Keyword]:
        """獲取權重最高的 N 個關鍵字"""
        sorted_kw = sorted(
            self.keywords.values(), 
            key=lambda x: x.effective_weight, 
            reverse=True
        )
        return sorted_kw[:n]
    
    def get_statistics(self) -> Dict:
        """獲取關鍵字統計"""
        total = len(self.keywords)
        by_category = {}
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
        """
        獲取預測歷史記錄
        
        Args:
            keyword: 篩選特定關鍵字（可選）
            limit: 返回數量限制
            only_verified: 只返回已驗證的記錄
            
        Returns:
            預測記錄列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM prediction_history"
        params = []
        
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
        """獲取尚未驗證的預測"""
        return self.get_prediction_history(only_verified=False)
    
    def get_overall_accuracy(self) -> Tuple[float, int, int]:
        """
        獲取整體準確率
        
        Returns:
            (準確率, 正確數, 總數)
        """
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
    
    def get_keyword_performance(self, min_predictions: int = 5) -> List[Dict]:
        """
        獲取關鍵字表現排名
        
        Args:
            min_predictions: 最少預測次數
            
        Returns:
            按準確率排序的關鍵字表現列表
        """
        performance = []
        
        for kw in self.keywords.values():
            if kw.prediction_count >= min_predictions:
                performance.append({
                    'keyword': kw.keyword,
                    'category': kw.category,
                    'accuracy': kw.accuracy,
                    'predictions': kw.prediction_count,
                    'correct': kw.correct_count,
                    'effective_weight': kw.effective_weight,
                    'days_old': kw.days_since_added,
                    'is_stale': kw.is_stale
                })
        
        # 按準確率排序
        performance.sort(key=lambda x: x['accuracy'], reverse=True)
        return performance
    
    def get_importance_score(self, text: str) -> Tuple[float, List[str]]:
        """計算文本的重要性分數"""
        matches = self.find_matches(text)
        
        if not matches:
            return 0.0, []
        
        # 取最高的幾個關鍵字，加權計算
        top_matches = matches[:3]
        total_weight = sum(m.effective_weight for m in top_matches)
        
        # 考慮準確率加成
        accuracy_bonus = sum(m.accuracy * 0.5 for m in top_matches)
        
        score = min((total_weight + accuracy_bonus) * 1.2, 10.0)
        keywords = [m.keyword for m in matches]
        
        return round(score, 2), keywords
    
    def get_sentiment_bias(self, text: str) -> Tuple[str, float]:
        """根據關鍵字判斷情緒傾向"""
        matches = self.find_matches(text)
        
        if not matches:
            return 'neutral', 0.0
        
        positive_score = 0.0
        negative_score = 0.0
        
        for match in matches:
            # 權重 × 準確率
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
        """印出關鍵字報告"""
        stats = self.get_statistics()
        stale = self.get_stale_keywords()
        top = self.get_top_keywords(10)
        
        print("=" * 60)
        print("📊 關鍵字系統報告")
        print("=" * 60)
        print(f"\n總關鍵字數: {stats['total']}")
        print(f"\n📁 分類統計:")
        for cat, count in stats['by_category'].items():
            print(f"   {cat}: {count}")
        
        print(f"\n📈 準確率統計:")
        print(f"   高準確率 (>70%): {stats['high_accuracy_count']}")
        print(f"   低準確率 (<30%): {stats['low_accuracy_count']}")
        
        print(f"\n🔝 權重最高的關鍵字:")
        for kw in top:
            print(f"   • {kw.keyword}: {kw.effective_weight:.2f} "
                  f"(基礎:{kw.base_weight}, 動態:{kw.dynamic_weight:.2f}, "
                  f"準確率:{kw.accuracy:.0%})")
        
        if stale:
            print(f"\n⚠️  過時關鍵字 (需要檢視):")
            for kw in stale[:5]:
                print(f"   • {kw.keyword}: {kw.days_since_updated} 天未更新, "
                      f"準確率:{kw.accuracy:.0%}")
        
        print("\n" + "=" * 60)


# 全局實例
_keyword_manager: Optional[KeywordManager] = None


def get_keyword_manager() -> KeywordManager:
    """獲取全局關鍵字管理器"""
    global _keyword_manager
    if _keyword_manager is None:
        _keyword_manager = KeywordManager()
    return _keyword_manager


# 向下兼容的類別（保持舊 API）
class MarketKeywords:
    """向下兼容的靜態類別"""
    
    @classmethod
    def find_matches(cls, text: str) -> List[KeywordMatch]:
        return get_keyword_manager().find_matches(text)
    
    @classmethod
    def get_importance_score(cls, text: str) -> Tuple[float, List[str]]:
        return get_keyword_manager().get_importance_score(text)
    
    @classmethod
    def get_sentiment_bias(cls, text: str) -> Tuple[str, float]:
        return get_keyword_manager().get_sentiment_bias(text)
    
    @classmethod
    def is_high_impact_news(cls, text: str, threshold: float = 2.5) -> Tuple[bool, List[str]]:
        return get_keyword_manager().is_high_impact_news(text, threshold)


# ========================================
# 測試
# ========================================
if __name__ == "__main__":
    print("=" * 60)
    print("📰 關鍵字管理器測試（動態學習版 v2.0）")
    print("=" * 60)
    
    km = KeywordManager()
    
    # 測試新聞
    test_headlines = [
        "Federal Reserve raises interest rate by 25 basis points",
        "Elon Musk tweets about Dogecoin, price surges 20%",
        "SEC files lawsuit against Binance",
        "BlackRock spot Bitcoin ETF approved by SEC",
        "Major hack: $100M stolen from DeFi protocol",
    ]
    
    print("\n📝 新聞分析測試:")
    for headline in test_headlines:
        print(f"\n標題: {headline}")
        print("-" * 50)
        
        matches = km.find_matches(headline)
        score, keywords = km.get_importance_score(headline)
        sentiment, strength = km.get_sentiment_bias(headline)
        is_high, high_kw = km.is_high_impact_news(headline)
        
        if matches:
            print("   匹配關鍵字:")
            for m in matches[:3]:
                print(f"      • {m.keyword} [權重:{m.effective_weight:.2f}] "
                      f"[{m.sentiment_bias}] ({m.days_old}天前新增)")
        
        print(f"   重要性: {score}/10 | 情緒: {sentiment} ({strength:.0%})")
        print(f"   高影響: {'是 ⚠️' if is_high else '否'}")
    
    # 🆕 模擬兩階段預測記錄
    print("\n" + "=" * 60)
    print("📊 模擬兩階段預測記錄:")
    print("-" * 60)
    
    # 第一步：記錄預測
    print("\n步驟 1: 記錄預測")
    pred_id1 = km.record_prediction(
        keyword="fed",
        predicted_direction="negative",
        price_before=65000.0,
        news_title="Fed hints at rate hike"
    )
    print(f"   預測 ID: {pred_id1}")
    
    pred_id2 = km.record_prediction(
        keyword="elon musk",
        predicted_direction="positive",
        price_before=65000.0,
        news_title="Musk tweets about Bitcoin"
    )
    print(f"   預測 ID: {pred_id2}")
    
    # 第二步：3天後驗證結果
    print("\n步驟 2: 驗證預測結果 (模擬3天後)")
    km.verify_prediction(pred_id1, actual_direction="negative", price_after=63500.0)
    km.verify_prediction(pred_id2, actual_direction="positive", price_after=68000.0)
    
    # 使用向下兼容方法
    print("\n使用向下兼容方法:")
    km.record_and_verify_prediction("hack", "negative", "negative", -8.0)
    
    # 查看預測歷史
    print("\n" + "=" * 60)
    print("📜 最近預測歷史:")
    print("-" * 60)
    history = km.get_prediction_history(limit=5)
    for record in history:
        status = "✅" if record.is_correct else "❌" if record.is_correct is False else "⏳"
        print(f"   {status} [{record.keyword}] "
              f"預測:{record.predicted_direction} "
              f"實際:{record.actual_direction or '未驗證'} "
              f"價格變動:{record.price_change_pct or 0:.2f}%")
    
    # 整體準確率
    accuracy, correct, total = km.get_overall_accuracy()
    print(f"\n📈 整體準確率: {accuracy:.1%} ({correct}/{total})")
    
    # 印出報告
    print()
    km.print_report()
