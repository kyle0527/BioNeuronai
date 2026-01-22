"""市場關鍵字匹配系統 (Market Keywords Matcher)
===================================================

智能化關鍵字識別與情緒分析系統，支援多語言、近義詞擴展與實體識別。

主要功能：

1. 多語言支持
   - 中文、英文關鍵字自動識別
   - 繁簡體轉換與處理
   - 語言混合文本分析

2. 近義詞擴展
   - 自動匹配相關詞彙
   - 語義相似度計算
   - 上下文感知匹配

3. 情緒分析
   - 正面/負面/中性情緒識別
   - 情緒強度量化評分
   - 市場情緒趨勢追蹤

4. 實體識別
   - 貨幣符號提取 (BTC, ETH, etc.)
   - 機構名稱識別
   - 重大事件標記

5. 關鍵字管理
   - SQLite 資料庫存儲
   - 動態更新與維護
   - 自定義關鍵字規則

6. 重要性評分
   - 基於來源權威度
   - 事件影響力評估
   - 時間衰減計算

7. 自定義規則
   - 正則表達式支持
   - 自定義匹配字典
   - 靈活的擴展機制

使用範例：
    from bioneuronai.analysis.market_keywords import get_keyword_manager
    
    km = get_keyword_manager()
    matches = km.find_matches("Fed raises interest rate by 0.25%")
    for match in matches:
        print(f"{match.keyword}: {match.score}")

Author: BioNeuronai Team
Version: 2.0
"""

import json
import os
import sqlite3
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Keyword:
    """"""
    keyword: str  # noqa: A003  # Ignore shadowing built-in
    category: str           # person, institution, event, coin
    base_weight: float      #  1.0-3.0
    dynamic_weight: float   # 
    sentiment_bias: str     # positive, negative, neutral, uncertain
    description: str
    
    #  
    added_date: str         #  (YYYY-MM-DD)
    last_updated: str       # 
    
    #  
    hit_count: int = 0           # 
    prediction_count: int = 0    # 
    correct_count: int = 0       # 
    
    @property
    def accuracy(self) -> float:
        """"""
        if self.prediction_count == 0:
            return 0.5  #  50%
        return self.correct_count / self.prediction_count
    
    @property
    def effective_weight(self) -> float:
        """ =  × """
        return self.base_weight * self.dynamic_weight
    
    @property
    def days_since_added(self) -> int:
        """"""
        added = datetime.strptime(self.added_date, "%Y-%m-%d")
        return (datetime.now() - added).days
    
    @property
    def days_since_updated(self) -> int:
        """"""
        updated = datetime.strptime(self.last_updated, "%Y-%m-%d")
        return (datetime.now() - updated).days
    
    @property
    def is_stale(self) -> bool:
        """ 90 """
        return self.days_since_updated > 90 and self.accuracy < 0.4


@dataclass
class PredictionRecord:
    """"""
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
    """"""
    keyword: str
    category: str
    effective_weight: float
    sentiment_bias: str
    description: str
    accuracy: float
    days_old: int


class KeywordManager:
    """
     v2.0
    
    
    1. 
    2. 
    3. 
    4.  SQLite+ JSON
    5.  
    """
    
    # 
    DEFAULT_CONFIG_PATH = "config/market_keywords.json"
    DEFAULT_DB_PATH = "config/market_keywords.db"
    
    # 
    WEIGHT_INCREASE_FACTOR = 1.08  #  8%
    WEIGHT_DECREASE_FACTOR = 0.92  #  8%
    MAX_DYNAMIC_WEIGHT = 2.0       # 
    MIN_DYNAMIC_WEIGHT = 0.3       # 
    
    def __init__(self, config_path: Optional[str] = None, db_path: Optional[str] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.db_path = db_path or self.DEFAULT_DB_PATH
        self.keywords: Dict[str, Keyword] = {}
        
        #  SQLite 
        self._init_database()
        
        # 
        if self._load_from_database():
            logger.info(f"  {len(self.keywords)} ")
        elif os.path.exists(self.config_path):
            self._load_keywords()
            self._save_to_database()  # 
        else:
            self._initialize_default_keywords()
            self._save_keywords()
            self._save_to_database()
        
        logger.info(f"  {len(self.keywords)} ")
    
    def _init_database(self):
        """ SQLite """
        # 
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 
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
        
        #  
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
        
        # 
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pred_keyword ON prediction_history(keyword)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pred_created ON prediction_history(created_at)')
        
        conn.commit()
        conn.close()
        logger.debug(f": {self.db_path}")
    
    def _load_from_database(self) -> bool:
        """"""
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
            logger.error(f": {e}")
            return False
    
    def _save_to_database(self):
        """"""
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
            logger.debug("")
        except Exception as e:
            logger.error(f": {e}")
    
    def _initialize_default_keywords(self):
        """"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # ========================================
        # 🧑 
        # ========================================
        persons = {
            'elon musk': ('person', 2.5, 'uncertain', 'CEO'),
            'musk': ('person', 2.5, 'uncertain', ''),
            'vitalik': ('person', 2.0, 'neutral', ''),
            'vitalik buterin': ('person', 2.0, 'neutral', ''),
            'cz': ('person', 2.0, 'neutral', 'CEO'),
            'changpeng zhao': ('person', 2.0, 'neutral', 'CEO'),
            'michael saylor': ('person', 2.0, 'positive', 'MicroStrategy CEO'),
            'saylor': ('person', 2.0, 'positive', 'MicroStrategy CEO'),
            'cathie wood': ('person', 1.8, 'positive', 'ARK Invest CEO'),
            'brian armstrong': ('person', 1.5, 'neutral', 'Coinbase CEO'),
            'sam bankman': ('person', 2.0, 'negative', 'FTX CEO'),
            'sbf': ('person', 2.0, 'negative', 'FTX CEO'),
            'powell': ('person', 3.0, 'uncertain', ''),
            'jerome powell': ('person', 3.0, 'uncertain', ''),
            'yellen': ('person', 2.8, 'uncertain', ''),
            'janet yellen': ('person', 2.8, 'uncertain', ''),
            'gensler': ('person', 2.5, 'negative', 'SEC '),
            'gary gensler': ('person', 2.5, 'negative', 'SEC '),
            'lagarde': ('person', 2.5, 'uncertain', ''),
            'trump': ('person', 2.5, 'uncertain', '/'),
            'biden': ('person', 2.3, 'uncertain', ''),
            'warren buffett': ('person', 2.0, 'negative', ''),
            'buffett': ('person', 2.0, 'negative', ''),
            'larry fink': ('person', 2.2, 'positive', 'BlackRock CEO ETF'),
            'sam altman': ('person', 2.5, 'uncertain', 'OpenAI CEO / Worldcoin  AI '),
            'jensen huang': ('person', 2.0, 'positive', ' NVIDIA CEO AI '),
            'justin sun': ('person', 2.0, 'uncertain', ''),
            'arthur hayes': ('person', 1.8, 'uncertain', 'BitMEX  KOL'),
            'stani kulechov': ('person', 1.8, 'neutral', 'Aave DeFi '),
        }
        
        for kw, (cat, weight, sentiment, desc) in persons.items():
            self.keywords[kw] = Keyword(
                keyword=kw, category=cat, base_weight=weight,
                dynamic_weight=1.0, sentiment_bias=sentiment, description=desc,
                added_date=today, last_updated=today
            )
        
        # ========================================
        #  
        # ========================================
        institutions = {
            'fed': ('institution', 3.0, 'uncertain', ''),
            'federal reserve': ('institution', 3.0, 'uncertain', ''),
            'fomc': ('institution', 3.0, 'uncertain', ''),
            'sec': ('institution', 2.8, 'uncertain', ''),
            'cftc': ('institution', 2.5, 'uncertain', ''),
            'treasury': ('institution', 2.5, 'uncertain', ''),
            'doj': ('institution', 2.5, 'negative', ''),
            'ecb': ('institution', 2.5, 'uncertain', ''),
            'pboc': ('institution', 2.5, 'negative', ''),
            'blackrock': ('institution', 2.5, 'positive', ''),
            'fidelity': ('institution', 2.3, 'positive', ''),
            'grayscale': ('institution', 2.2, 'positive', ''),
            'jpmorgan': ('institution', 2.0, 'uncertain', ''),
            'goldman sachs': ('institution', 2.0, 'uncertain', ''),
            'microstrategy': ('institution', 2.0, 'positive', ''),
            'tesla': ('institution', 2.2, 'uncertain', ''),
            'binance': ('institution', 2.5, 'uncertain', ''),
            'coinbase': ('institution', 2.3, 'uncertain', ''),
            'ftx': ('institution', 2.0, 'negative', ''),
            'paypal': ('institution', 2.0, 'positive', ''),
            'mica': ('institution', 2.5, 'uncertain', ''),
            'fca': ('institution', 2.3, 'uncertain', ''),
            'sfc': ('institution', 2.2, 'uncertain', ''),
            'circle': ('institution', 2.0, 'neutral', 'USDC '),
            'eigenlayer': ('institution', 2.5, 'positive', 'Restaking '),
        }
        
        for kw, (cat, weight, sentiment, desc) in institutions.items():
            self.keywords[kw] = Keyword(
                keyword=kw, category=cat, base_weight=weight,
                dynamic_weight=1.0, sentiment_bias=sentiment, description=desc,
                added_date=today, last_updated=today
            )
        
        # ========================================
        #  
        # ========================================
        events = {
            # 
            'rate hike': ('event', 3.0, 'negative', ''),
            'rate cut': ('event', 3.0, 'positive', ''),
            'interest rate': ('event', 2.8, 'uncertain', ''),
            'quantitative easing': ('event', 2.5, 'positive', ''),
            'qe': ('event', 2.5, 'positive', ''),
            'tapering': ('event', 2.3, 'negative', ''),
            'inflation': ('event', 2.5, 'uncertain', ''),
            'cpi': ('event', 2.5, 'uncertain', ''),
            'nonfarm': ('event', 2.3, 'uncertain', ''),
            
            # ETF
            'etf approved': ('event', 3.0, 'positive', 'ETF '),
            'etf approval': ('event', 3.0, 'positive', 'ETF '),
            'etf rejected': ('event', 2.5, 'negative', 'ETF '),
            'spot etf': ('event', 2.8, 'positive', ' ETF'),
            'etf filing': ('event', 2.0, 'positive', 'ETF '),
            
            # 
            'hack': ('event', 3.0, 'negative', ''),
            'hacked': ('event', 3.0, 'negative', ''),
            'exploit': ('event', 3.0, 'negative', ''),
            'stolen': ('event', 2.8, 'negative', ''),
            'rug pull': ('event', 3.0, 'negative', ''),
            'scam': ('event', 2.5, 'negative', ''),
            
            # 
            'lawsuit': ('event', 2.5, 'negative', ''),
            'investigation': ('event', 2.3, 'negative', ''),
            'ban': ('event', 2.8, 'negative', ''),
            'banned': ('event', 2.8, 'negative', ''),
            'crackdown': ('event', 2.5, 'negative', ''),
            'regulation': ('event', 2.0, 'uncertain', ''),
            
            # 
            'halving': ('event', 2.8, 'positive', ''),
            'all-time high': ('event', 2.0, 'positive', ''),
            'ath': ('event', 2.0, 'positive', ''),
            'crash': ('event', 2.5, 'negative', ''),
            'plunge': ('event', 2.3, 'negative', ''),
            'surge': ('event', 2.0, 'positive', ''),
            'rally': ('event', 1.8, 'positive', ''),
            'liquidation': ('event', 2.3, 'negative', ''),
            'bankruptcy': ('event', 2.8, 'negative', ''),
            
            # 
            'hard fork': ('event', 2.0, 'uncertain', ''),
            'upgrade': ('event', 1.8, 'positive', ''),
            'mainnet': ('event', 2.0, 'positive', ''),
            'listing': ('event', 2.0, 'positive', ''),
            'delisting': ('event', 2.0, 'negative', ''),
            'partnership': ('event', 1.8, 'positive', ''),
            'whale': ('event', 2.0, 'uncertain', ''),
            
            # 
            'ai': ('event', 2.8, 'positive', ' WLD, TAO, RNDR'),
            'depin': ('event', 2.3, 'positive', ''),
            'rwa': ('event', 2.5, 'positive', ' BUIDL'),
            'restaking': ('event', 2.2, 'positive', ''),
            'airdrop': ('event', 2.0, 'uncertain', ''),
            'points': ('event', 1.5, 'neutral', ''),
            'layer 2': ('event', 2.0, 'positive', 'L2  Base, Arbitrum, Optimism'),
            'l2': ('event', 2.0, 'positive', 'Layer 2 '),
        }
        
        for kw, (cat, weight, sentiment, desc) in events.items():
            self.keywords[kw] = Keyword(
                keyword=kw, category=cat, base_weight=weight,
                dynamic_weight=1.0, sentiment_bias=sentiment, description=desc,
                added_date=today, last_updated=today
            )
        
        # ========================================
        # 🪙 
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
            'wld': ('coin', 2.2, 'uncertain', 'Worldcoin'),
            'tao': ('coin', 2.0, 'neutral', 'Bittensor'),
            'pepe': ('coin', 2.5, 'uncertain', ''),
            'tia': ('coin', 2.0, 'neutral', 'Celestia'),
            'pyusd': ('coin', 1.5, 'neutral', 'PayPal '),
        }
        
        for kw, (cat, weight, sentiment, desc) in coins.items():
            self.keywords[kw] = Keyword(
                keyword=kw, category=cat, base_weight=weight,
                dynamic_weight=1.0, sentiment_bias=sentiment, description=desc,
                added_date=today, last_updated=today
            )
        
        # ========================================
        #  /
        # ========================================
        crypto_slang = {
            # 
            'whale': ('event', 2.5, 'uncertain', '/'),
            'jujing': ('event', 2.5, 'uncertain', ''),
            'dahu': ('event', 2.5, 'uncertain', ''),
            'whale alert': ('event', 2.3, 'uncertain', ''),
            'juliang': ('event', 2.5, 'uncertain', ''),
            
            # 
            'sanhu': ('event', 1.8, 'negative', ''),
            'retail investor': ('event', 1.5, 'neutral', ''),
            'fomo': ('event', 2.0, 'uncertain', 'Fear Of Missing Out'),
            'fud': ('event', 2.2, 'negative', 'Fear, Uncertainty, Doubt'),
            
            # 
            'suocangjia': ('event', 2.0, 'uncertain', '/All in'),
            'all in': ('event', 2.0, 'uncertain', ''),
            'didie': ('event', 1.8, 'positive', ''),
            'buy the dip': ('event', 1.8, 'positive', ''),
            'kongpan': ('event', 2.0, 'negative', ''),
            'panic sell': ('event', 2.0, 'negative', ''),
            'zhisun': ('event', 1.5, 'neutral', ''),
            'stop loss': ('event', 1.5, 'neutral', ''),
            'zhuigao': ('event', 1.8, 'uncertain', ''),
            'chase': ('event', 1.8, 'uncertain', ''),
            
            # 
            'niushi': ('event', 2.0, 'positive', '/Bull Market'),
            'bull market': ('event', 2.0, 'positive', ''),
            'xiongshi': ('event', 2.0, 'negative', '/Bear Market'),
            'bear market': ('event', 2.0, 'negative', ''),
            'hengpan': ('event', 1.5, 'neutral', ''),
            'sideways': ('event', 1.5, 'neutral', ''),
            'consolidation': ('event', 1.5, 'neutral', ''),
            'baocang': ('event', 2.8, 'negative', ''),
            'liquidated': ('event', 2.8, 'negative', ''),
            'rekt': ('event', 2.5, 'negative', '/wrecked '),
            
            # 
            'hodl': ('event', 1.8, 'positive', 'Hold '),
            'tunchang': ('event', 1.8, 'positive', ''),
            'to the moon': ('event', 2.0, 'positive', ''),
            'moon': ('event', 2.0, 'positive', ''),
            'lambo': ('event', 1.8, 'positive', ''),
            'wen lambo': ('event', 1.8, 'positive', ''),
            'diamond hands': ('event', 1.8, 'positive', ''),
            'paper hands': ('event', 1.8, 'negative', ''),
            'zuanshou': ('event', 1.8, 'positive', ''),
            'zhishou': ('event', 1.8, 'negative', ''),
            
            # /
            'pump and dump': ('event', 2.5, 'negative', ''),
            'lazhuang': ('event', 2.0, 'uncertain', ''),
            'zaduo': ('event', 2.0, 'negative', ''),
            'dump': ('event', 2.0, 'negative', ''),
            'shill': ('event', 2.0, 'negative', '/'),
            'neimu': ('event', 2.5, 'negative', ''),
            'insider trading': ('event', 2.5, 'negative', ''),
            
            # 
            'zhicheng': ('event', 1.5, 'neutral', ''),
            'support': ('event', 1.5, 'neutral', ''),
            'yali': ('event', 1.5, 'neutral', ''),
            'resistance': ('event', 1.5, 'neutral', ''),
            'tupo': ('event', 2.0, 'positive', ''),
            'breakout': ('event', 2.0, 'positive', ''),
            'jincha': ('event', 1.8, 'positive', ''),
            'golden cross': ('event', 1.8, 'positive', ''),
            'sicha': ('event', 1.8, 'negative', ''),
            'death cross': ('event', 1.8, 'negative', ''),
            
            # 
            'based': ('event', 1.8, 'positive', ' Base '),
            'gm': ('event', 1.2, 'positive', 'Good Morning'),
            'pvp': ('event', 2.0, 'negative', ''),
            'alpha': ('event', 1.8, 'positive', ''),
            'sybil': ('event', 1.5, 'negative', ''),
        }
        
        for kw, (cat, weight, sentiment, desc) in crypto_slang.items():
            self.keywords[kw] = Keyword(
                keyword=kw, category=cat, base_weight=weight,
                dynamic_weight=1.0, sentiment_bias=sentiment, description=desc,
                added_date=today, last_updated=today
            )
    
    def _load_keywords(self):
        """ JSON """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for kw_data in data.get('keywords', []):
                kw = Keyword(**kw_data)
                self.keywords[kw.keyword] = kw
            
            logger.info(f"  {self.config_path}  {len(self.keywords)} ")
        except Exception as e:
            logger.error(f": {e}")
            self._initialize_default_keywords()
    
    def _save_keywords(self):
        """ JSON """
        Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'version': '2.0',
            'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_keywords': len(self.keywords),
            'keywords': [asdict(kw) for kw in self.keywords.values()]
        }
        
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.debug(f" {self.config_path}")
        except Exception as e:
            logger.error(f": {e}")
    
    def add_keyword(
        self,
        keyword: str,
        category: str,
        base_weight: float,
        sentiment_bias: str,
        description: str = ""
    ) -> bool:
        """"""
        kw_lower = keyword.lower()
        
        if kw_lower in self.keywords:
            logger.warning(f" '{keyword}' ")
            return False
        
        today = datetime.now().strftime("%Y-%m-%d")
        new_kw = Keyword(
            keyword=kw_lower,
            category=category,
            base_weight=base_weight,
            dynamic_weight=1.0,
            sentiment_bias=sentiment_bias,
            description=description,
            added_date=today,
            last_updated=today
        )
        
        self.keywords[kw_lower] = new_kw
        self._save_keywords()
        self._save_to_database()
        
        logger.info(f" : {keyword} [{category}] :{base_weight}")
        return True
    
    def update_keywords_from_trending(self, trending_topics: List[Dict[str, Any]]) -> int:
        """"""
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
            logger.info(f"  {added_count} ")
        
        return added_count
    
    def refresh_stale_keywords(self):
        """"""
        today = datetime.now().strftime("%Y-%m-%d")
        refreshed = []
        
        for kw in self.keywords.values():
            if kw.is_stale:
                # 
                old_weight = kw.dynamic_weight
                kw.dynamic_weight = 1.0
                kw.last_updated = today
                refreshed.append((kw.keyword, old_weight))
        
        if refreshed:
            self._save_keywords()
            self._save_to_database()
            logger.info(f"  {len(refreshed)} ")
            for keyword, old_weight in refreshed[:5]:
                logger.debug(f"   • {keyword}: {old_weight:.2f} -> 1.00")
        
        return len(refreshed)
    
    def find_matches(self, text: str) -> List[KeywordMatch]:
        """"""
        text_lower = text.lower()
        matches = []
        
        for kw in self.keywords.values():
            # 
            is_chinese = any('\u4e00' <= c <= '\u9fff' for c in kw.keyword)
            
            if is_chinese:
                # word boundary
                if kw.keyword in text_lower:
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
            else:
                #  word boundary
                pattern = r'\b' + re.escape(kw.keyword) + r'\b'
                if re.search(pattern, text_lower, re.IGNORECASE):
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
        
        # 
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
        
        
        Args:
            keyword: 
            predicted_direction:  (positive/negative/neutral)
            price_before: 
            news_title: 
            
        Returns:
            prediction_id: ID
        """
        kw_lower = keyword.lower()
        if kw_lower not in self.keywords:
            logger.warning(f" '{keyword}' ")
            return -1
        
        kw = self.keywords[kw_lower]
        kw.prediction_count += 1
        kw.last_updated = datetime.now().strftime("%Y-%m-%d")
        
        # 
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO prediction_history 
            (keyword, news_title, predicted_direction, price_before, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (kw_lower, news_title, predicted_direction, price_before, now))
        
        prediction_id = cursor.lastrowid
        
        #  prediction_count
        cursor.execute('''
            UPDATE keywords SET prediction_count = ?, last_updated = ?
            WHERE keyword = ?
        ''', (kw.prediction_count, kw.last_updated, kw_lower))
        
        conn.commit()
        conn.close()
        
        logger.info(f"  [ID:{prediction_id}] {keyword} -> {predicted_direction}")
        self._save_keywords()
        
        return prediction_id if prediction_id is not None else -1
    
    def verify_prediction(
        self,
        prediction_id: int,
        actual_direction: str,  # positive, negative, neutral
        price_after: float = 0.0
    ) -> bool:
        """
        
        
        Args:
            prediction_id: ID
            actual_direction:  (positive/negative/neutral)
            price_after: 
            
        Returns:
            is_correct: 
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 
        cursor.execute('''
            SELECT keyword, predicted_direction, price_before 
            FROM prediction_history WHERE id = ?
        ''', (prediction_id,))
        row = cursor.fetchone()
        
        if not row:
            conn.close()
            logger.warning(f" ID: {prediction_id}")
            return False
        
        keyword, predicted_direction, price_before = row
        
        # 
        is_correct = (predicted_direction == actual_direction)
        
        # 
        price_change_pct = 0.0
        if price_before and price_after:
            price_change_pct = ((price_after - price_before) / price_before) * 100
            
            #  2%
            if abs(price_change_pct) > 2.0:
                if price_change_pct > 0 and actual_direction == 'positive':
                    is_correct = (predicted_direction == 'positive')
                elif price_change_pct < 0 and actual_direction == 'negative':
                    is_correct = (predicted_direction == 'negative')
        
        # 
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
        
        # 
        kw = self.keywords.get(keyword)
        if kw and is_correct:
            kw.correct_count += 1
        
        #  
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
            
            # 
            cursor.execute('''
                UPDATE keywords SET 
                    correct_count = ?, dynamic_weight = ?, last_updated = ?
                WHERE keyword = ?
            ''', (kw.correct_count, kw.dynamic_weight, 
                  datetime.now().strftime("%Y-%m-%d"), keyword))
        
        conn.commit()
        conn.close()
        
        # 
        result_emoji = "✅" if is_correct else "❌"
        logger.info(f"{result_emoji}  [ID:{prediction_id}] {keyword}: "
                   f"={predicted_direction}, ={actual_direction}, "
                   f"={price_change_pct:+.2f}%")
        
        if kw:
            logger.info(f"    {keyword} : "
                       f"={kw.accuracy:.1%}, ={kw.dynamic_weight:.2f}")
        
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
        
        
        Args:
            keyword: 
            predicted_direction: 
            actual_direction: 
            price_change_pct: 
        """
        price_before = 1000.0  # 
        price_after = price_before * (1 + price_change_pct / 100)
        
        pred_id = self.record_prediction(keyword, predicted_direction, price_before)
        if pred_id > 0:
            self.verify_prediction(pred_id, actual_direction, price_after)
    
    def remove_keyword(self, keyword: str):
        """"""
        kw_lower = keyword.lower()
        if kw_lower in self.keywords:
            del self.keywords[kw_lower]
            self._save_keywords()
            logger.info(f" : {keyword}")
    
    def get_stale_keywords(self) -> List[Keyword]:
        """ 90 """
        return [kw for kw in self.keywords.values() if kw.is_stale]
    
    def get_top_keywords(self, n: int = 20) -> List[Keyword]:
        """ N """
        sorted_kw = sorted(
            self.keywords.values(), 
            key=lambda x: x.effective_weight, 
            reverse=True
        )
        return sorted_kw[:n]
    
    def get_statistics(self) -> Dict:
        """"""
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
        
        
        Args:
            keyword: 
            limit: 
            only_verified: 
            
        Returns:
            
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
        """"""
        return self.get_prediction_history(only_verified=False)
    
    def get_overall_accuracy(self) -> Tuple[float, int, int]:
        """
        
        
        Returns:
            (, , )
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
        
        
        Args:
            min_predictions: 
            
        Returns:
            
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
        
        # 
        performance.sort(key=lambda x: x['accuracy'], reverse=True)
        return performance
    
    def get_importance_score(self, text: str) -> Tuple[float, List[str]]:
        """"""
        matches = self.find_matches(text)
        
        if not matches:
            return 0.0, []
        
        # 
        top_matches = matches[:3]
        total_weight = sum(m.effective_weight for m in top_matches)
        
        # 
        accuracy_bonus = sum(m.accuracy * 0.5 for m in top_matches)
        
        score = min((total_weight + accuracy_bonus) * 1.2, 10.0)
        keywords = [m.keyword for m in matches]
        
        return round(score, 2), keywords
    
    def get_sentiment_bias(self, text: str) -> Tuple[str, float]:
        """"""
        matches = self.find_matches(text)
        
        if not matches:
            return 'neutral', 0.0
        
        positive_score = 0.0
        negative_score = 0.0
        
        for match in matches:
            #  × 
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
        """"""
        matches = self.find_matches(text)
        high_impact = [m for m in matches if m.effective_weight >= threshold]
        return len(high_impact) > 0, [m.keyword for m in high_impact]
    
    def print_report(self):
        """"""
        stats = self.get_statistics()
        stale = self.get_stale_keywords()
        top = self.get_top_keywords(10)
        
        print("=" * 60)
        print(" ")
        print("=" * 60)
        print(f"\n: {stats['total']}")
        print("\n :")
        for cat, count in stats['by_category'].items():
            print(f"   {cat}: {count}")
        
        print("\n :")
        print(f"    (>70%): {stats['high_accuracy_count']}")
        print(f"    (<30%): {stats['low_accuracy_count']}")
        
        print("\n :")
        for kw in top:
            print(f"   • {kw.keyword}: {kw.effective_weight:.2f} "
                  f"(:{kw.base_weight}, :{kw.dynamic_weight:.2f}, "
                  f":{kw.accuracy:.0%})")
        
        if stale:
            print("\n   ():")
            for kw in stale[:5]:
                print(f"   • {kw.keyword}: {kw.days_since_updated} , "
                      f":{kw.accuracy:.0%}")
        
        print("\n" + "=" * 60)


# 
_keyword_manager: Optional[KeywordManager] = None


def get_keyword_manager() -> KeywordManager:
    """"""
    global _keyword_manager
    if _keyword_manager is None:
        _keyword_manager = KeywordManager()
    return _keyword_manager


#  API
class MarketKeywords:
    """"""
    
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
# 
# ========================================
if __name__ == "__main__":
    print("=" * 60)
    print("  v2.0")
    print("=" * 60)
    
    km = KeywordManager()
    
    # 
    test_headlines = [
        "Federal Reserve raises interest rate by 25 basis points",
        "Elon Musk tweets about Dogecoin, price surges 20%",
        "SEC files lawsuit against Binance",
        "BlackRock spot Bitcoin ETF approved by SEC",
        "Major hack: $100M stolen from DeFi protocol",
    ]
    
    print("\n :")
    for headline in test_headlines:
        print(f"\n: {headline}")
        print("-" * 50)
        
        matches = km.find_matches(headline)
        score, keywords = km.get_importance_score(headline)
        sentiment, strength = km.get_sentiment_bias(headline)
        is_high, high_kw = km.is_high_impact_news(headline)
        
        if matches:
            print("   :")
            for m in matches[:3]:
                print(f"      • {m.keyword} [:{m.effective_weight:.2f}] "
                      f"[{m.sentiment_bias}] ({m.days_old})")
        
        print(f"   : {score}/10 | : {sentiment} ({strength:.0%})")
        print(f"   : {' ' if is_high else ''}")
    
    #  
    print("\n" + "=" * 60)
    print(" :")
    print("-" * 60)
    
    # 
    print("\n 1: ")
    pred_id1 = km.record_prediction(
        keyword="fed",
        predicted_direction="negative",
        price_before=65000.0,
        news_title="Fed hints at rate hike"
    )
    print(f"    ID: {pred_id1}")
    
    pred_id2 = km.record_prediction(
        keyword="elon musk",
        predicted_direction="positive",
        price_before=65000.0,
        news_title="Musk tweets about Bitcoin"
    )
    print(f"    ID: {pred_id2}")
    
    # 3
    print("\n 2:  (3)")
    km.verify_prediction(pred_id1, actual_direction="negative", price_after=63500.0)
    km.verify_prediction(pred_id2, actual_direction="positive", price_after=68000.0)
    
    # 
    print("\n:")
    km.record_and_verify_prediction("hack", "negative", "negative", -8.0)
    
    # 
    print("\n" + "=" * 60)
    print(" :")
    print("-" * 60)
    history = km.get_prediction_history(limit=5)
    for record in history:
        if record.is_correct is True:
            status = "✅"
        elif record.is_correct is False:
            status = "❌"
        else:
            status = "⏳"
        print(f"   {status} [{record.keyword}] "
              f":{record.predicted_direction} "
              f":{record.actual_direction or ''} "
              f":{record.price_change_pct or 0:.2f}%")
    
    # 
    accuracy, correct, total = km.get_overall_accuracy()
    print(f"\n : {accuracy:.1%} ({correct}/{total})")
    
    # 
    print()
    km.print_report()
