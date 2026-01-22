"""加密貨幣新聞分析器 (Crypto News Analyzer)
=================================================

智能新聞情緒分析與交易信號生成系統，支援多來源新聞抓取與實時分析。

核心功能：

1. 新聞情緒分析
   - 自動識別正面/負面/中性情緒
   - 情緒強度量化評分 (-1.0 到 +1.0)
   - 情緒趨勢追蹤與預測
   - 多維度情緒指標計算

2. 關鍵事件識別
   - 駭客攻擊與安全事件
   - 監管動態與政策變化
   - 重大合作與技術升級
   - 機構投資與資金流向

3. ETF 相關新聞追蹤
   - 專門監控 ETF 申請進度
   - ETF 批准/拒絕事件追蹤
   - 機構 ETF 持倉變化
   - ETF 市場影響評估

4. 新聞來源評分
   - 基於來源權威度評分
   - 主流媒體優先級設定
   - 假新聞過濾機制
   - 多源交叉驗證

5. 重要性評估
   - 事件影響力量化評分 (0-10)
   - 市場相關性計算
   - 時效性權重調整
   - 歷史事件影響回測

6. 交易建議生成
   - 基於新聞情緒的操作建議
   - 風險等級自動評估
   - 進場時機提示
   - 止損止盈建議

7. 多幣種支持
   - BTC, ETH, BNB 等主流幣種
   - 自動識別相關幣種
   - 幣種間關聯性分析
   - 板塊輪動監控

8. 新聞記錄管理
   - 自動存儲歷史新聞
   - 價格變化追蹤記錄
   - 新聞效果評估
   - 數據回測支持

應用場景：
- 開盤前市場情緒評估
- 即時新聞監控與預警
- 歷史新聞影響回測
- 交易決策輔助系統
- 風險事件及時通知

使用範例：
    from bioneuronai.analysis import CryptoNewsAnalyzer
    
    analyzer = CryptoNewsAnalyzer()
    result = analyzer.analyze_news("BTCUSDT", hours=24)
    print(f"情緒: {result.overall_sentiment}")
    print(f"評分: {result.sentiment_score}")
    print(f"建議: {result.recommendation}")

Author: BioNeuronai Team
Version: 1.0
"""


import re
import logging
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter
import threading

try:
    import requests
except ImportError:
    requests = None

# 
try:
    from .market_keywords import MarketKeywords, KeywordMatch, get_keyword_manager
    KEYWORDS_AVAILABLE = True
except ImportError:
    KEYWORDS_AVAILABLE = False
    get_keyword_manager = None  # 確保未定義時為 None

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """"""
    title: str
    source: str
    url: str
    published_at: datetime
    summary: str = ""
    sentiment: str = "neutral"  # positive, negative, neutral
    sentiment_score: float = 0.0  # -1.0  1.0
    relevance_score: float = 0.0  # 
    importance_score: float = 0.0  # 0-10
    keywords: List[str] = field(default_factory=list)  # 匹配到的關鍵字名稱
    keyword_score: float = 0.0  # 關鍵字權重總分 (base_weight × dynamic_weight 總和)
    time_decay_score: float = 1.0  # 時間衰減係數 (0.3-1.0)
    source_credibility: float = 1.0  # 來源可信度 (0.5-2.0)
    final_score: float = 0.0  # 綜合評分 = keyword_score × time_decay × source_credibility × sentiment_factor
    coins_mentioned: List[str] = field(default_factory=list)
    category: str = "general"  # : regulation, security, market, partnership, technical
    # 新增：用於追蹤評估
    news_id: str = ""  # 唯一識別碼
    target_coin: str = ""  # 目標幣種 (BTC, ETH...)
    price_at_news: float = 0.0  # 新聞發布時的價格
    evaluated: bool = False  # 是否已評估


@dataclass
class NewsAnalysisResult:
    """新聞分析結果"""
    symbol: str
    total_articles: int
    positive_count: int
    negative_count: int
    neutral_count: int
    overall_sentiment: str
    sentiment_score: float  # -1.0 到 1.0
    key_events: List[str]
    top_keywords: List[Tuple[str, int]]
    recent_headlines: List[str]  # 標題列表 (向後兼容)
    recommendation: str
    analysis_time: datetime
    articles: List['NewsArticle'] = field(default_factory=list)  # 完整文章列表 (含連結)
    
    def get_headlines_with_urls(self) -> List[Dict]:
        """取得標題和連結的列表"""
        return [
            {
                'title': a.title,
                'url': a.url,
                'source': a.source,
                'published_at': a.published_at.strftime('%Y-%m-%d %H:%M') if a.published_at else '',
                'sentiment': a.sentiment,
                'keywords': a.keywords  # 加入關鍵字
            }
            for a in sorted(self.articles, key=lambda x: x.published_at, reverse=True)
        ]
    
    def _get_sentiment_icon(self, sentiment: str) -> str:
        """根據情感類型獲取相應的圖標"""
        if sentiment == 'positive':
            return '🟢'
        elif sentiment == 'negative':
            return '🔴'
        else:
            return '⚪'
    
    def print_news_with_links(self, max_items: int = 10) -> None:
        """印出新聞標題和連結"""
        print(f"\n📰 {self.symbol} 新聞摘要 ({self.total_articles} 則)")
        print(f"情緒: {self.overall_sentiment} (分數: {self.sentiment_score:.2f})")
        print(f"建議: {self.recommendation}")
        print("-" * 70)
        
        sorted_articles = sorted(self.articles, key=lambda x: x.published_at, reverse=True)
        for i, article in enumerate(sorted_articles[:max_items], 1):
            sentiment_icon = self._get_sentiment_icon(article.sentiment)
            print(f"{i}. {sentiment_icon} {article.title}")
            print(f"   📅 {article.published_at.strftime('%Y-%m-%d %H:%M')} | 🌐 {article.source}")
            # 顯示匹配到的關鍵字
            if article.keywords:
                keywords_str = ', '.join(article.keywords[:5])  # 最多顯示 5 個
                print(f"   🔑 關鍵字: {keywords_str}")
            print(f"   🔗 {article.url}")
            print()


class CryptoNewsAnalyzer:
    """
    
    
    
    - 
    - 
    - 
    - 
    """
    
    # 
    POSITIVE_KEYWORDS = {
        #  ( 2.0)
        'etf approved': 2.0, 'etf approval': 2.0, 'spot etf': 1.8,
        'institutional adoption': 1.8, 'mass adoption': 1.8,
        'all-time high': 1.5, 'ath': 1.5, 'new high': 1.5,
        'bullish': 1.3, 'bull run': 1.5, 'bull market': 1.5,
        'partnership': 1.2, 'collaboration': 1.2,
        'upgrade': 1.2, 'improvement': 1.1,
        'adoption': 1.3, 'accepted': 1.2,
        'investment': 1.1, 'funding': 1.1,
        'growth': 1.1, 'surge': 1.3, 'soar': 1.3, 'rally': 1.3,
        'breakthrough': 1.4, 'milestone': 1.3,
        
        #  ( 1.0)
        'positive': 1.0, 'optimistic': 1.0, 'bullish outlook': 1.2,
        'support': 0.8, 'momentum': 0.9, 'recovery': 1.0,
        'innovation': 1.0, 'development': 0.8,
        'launch': 0.9, 'release': 0.8,
        'accumulation': 1.0, 'buying': 0.8,
    }
    
    # 
    NEGATIVE_KEYWORDS = {
        #  ( 2.0)
        'hack': 2.0, 'hacked': 2.0, 'exploit': 2.0, 'breach': 1.8,
        'scam': 2.0, 'fraud': 2.0, 'rug pull': 2.0, 'ponzi': 2.0,
        'ban': 1.8, 'banned': 1.8, 'illegal': 1.8, 'crackdown': 1.8,
        'sec lawsuit': 1.8, 'regulatory action': 1.5,
        'crash': 1.8, 'plunge': 1.7, 'collapse': 1.8,
        'bankruptcy': 2.0, 'insolvent': 2.0, 'liquidation': 1.8,
        
        #  ( 1.0)
        'bearish': 1.3, 'bear market': 1.5,
        'selloff': 1.3, 'sell-off': 1.3, 'dumping': 1.3,
        'decline': 1.0, 'drop': 0.9, 'fall': 0.8, 'down': 0.6,
        'concern': 0.8, 'warning': 1.0, 'risk': 0.7,
        'delay': 0.8, 'postpone': 0.8, 'reject': 1.2, 'rejected': 1.2,
        'negative': 1.0, 'pessimistic': 1.0,
        'investigation': 1.2, 'probe': 1.1,
        'fear': 1.0, 'uncertainty': 0.8, 'doubt': 0.8,
    }
    
    # 
    KEY_EVENT_PATTERNS = {
        'etf': r'\b(etf|exchange.traded.fund)\b',
        'regulation': r'\b(sec|regulation|regulatory|compliance|law|legal)\b',
        'hack': r'\b(hack|exploit|breach|attack|vulnerability)\b',
        'partnership': r'\b(partner|collaboration|deal|agreement)\b',
        'upgrade': r'\b(upgrade|hard.?fork|update|improvement)\b',
        'listing': r'\b(list|listing|delist|trading.pair)\b',
        'whale': r'\b(whale|large.transfer|massive.move)\b',
        'halving': r'\b(halving|halvening|block.reward)\b',
    }
    
    # ========================================
    #  
    # ========================================
    
    #  2.0
    SOURCE_AUTHORITY = {
        # 
        'coindesk.com': 2.0,
        'cointelegraph.com': 2.0,
        'bloomberg.com': 2.0,
        'reuters.com': 2.0,
        'wsj.com': 2.0,
        'forbes.com': 1.8,
        
        # 
        'decrypt.co': 1.8,
        'theblock.co': 1.8,
        'bitcoinmagazine.com': 1.7,
        'cryptoslate.com': 1.5,
        'cryptobriefing.com': 1.5,
        
        # 
        'cryptopanic.com': 1.3,
        'newsbtc.com': 1.2,
        'bitcoinist.com': 1.2,
        'coingape.com': 1.0,
        
        # 
        'default': 0.8,
    }
    
    #  3.0
    EVENT_IMPORTANCE = {
        'security': 3.0,      # - 
        'regulation': 2.8,    #  - 
        'etf': 2.5,           # ETF  - 
        'halving': 2.5,       #  - 
        'listing': 2.0,       # / - 
        'partnership': 1.8,   #  - 
        'upgrade': 1.5,       #  - 
        'whale': 1.5,         #  - 
        'market': 1.0,        #  - 
        'general': 0.5,       #  - 
    }
    
    # 
    COIN_KEYWORDS = {
        'BTC': ['bitcoin', 'btc', 'satoshi'],
        'ETH': ['ethereum', 'eth', 'ether', 'vitalik'],
        'BNB': ['binance', 'bnb'],
        'SOL': ['solana', 'sol'],
        'XRP': ['ripple', 'xrp'],
        'DOGE': ['dogecoin', 'doge', 'elon'],
        'ADA': ['cardano', 'ada'],
        'AVAX': ['avalanche', 'avax'],
        'DOT': ['polkadot', 'dot'],
        'LINK': ['chainlink', 'link'],
        'SHIB': ['shiba', 'shib'],
        'PEPE': ['pepe'],
    }
    
    def __init__(self):
        self._cache: Dict[str, Tuple[NewsAnalysisResult, datetime]] = {}
        self._cache_ttl = 300  # 5 
        self._lock = threading.Lock()
        
        # 新聞記錄文件路徑
        import os
        self._news_records_dir = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'sop_automation_data')
        self._news_records_file = os.path.join(self._news_records_dir, 'news_records.json')
        os.makedirs(self._news_records_dir, exist_ok=True)
        
        logger.info(" ")
    
    def _calculate_importance_score(self, article: NewsArticle, target_coin: str) -> float:
        """
         10 
        
        
        1.  (0-2 )
        2.  (0-3 )
        3.  (0-2 )
        4.  (0-2 )
        5.  (0-1 )
        
        Returns:
            float: 0-10 
        """
        score = 0.0
        
        # 1.  2.0
        source_domain = article.source.lower()
        source_score = self.SOURCE_AUTHORITY.get('default', 0.8)
        for domain, auth_score in self.SOURCE_AUTHORITY.items():
            if domain in source_domain:
                source_score = auth_score
                break
        score += source_score
        
        # 2.  3.0
        event_type = self._detect_event_type(article.title + " " + article.summary)
        article.category = event_type
        event_score = self.EVENT_IMPORTANCE.get(event_type, 0.5)
        score += event_score
        
        # 3.  2.0
        hours_old = (datetime.now() - article.published_at).total_seconds() / 3600
        if hours_old < 1:       # 1 
            time_score = 2.0
        elif hours_old < 4:     # 4 
            time_score = 1.5
        elif hours_old < 12:    # 12 
            time_score = 1.0
        elif hours_old < 24:    # 24 
            time_score = 0.5
        else:
            time_score = 0.2
        score += time_score
        
        # 4.  2.0
        text_lower = (article.title + " " + article.summary).lower()
        coin_keywords = self.COIN_KEYWORDS.get(target_coin, [target_coin.lower()])
        
        # 
        direct_mention = any(kw in text_lower for kw in coin_keywords)
        if direct_mention:
            relevance_score = 2.0
        #  crypto/bitcoin 
        elif any(kw in text_lower for kw in ['crypto', 'bitcoin', 'cryptocurrency']):
            relevance_score = 1.0
        else:
            relevance_score = 0.3
        score += relevance_score
        article.relevance_score = relevance_score
        
        # 5.  1.0
        sentiment_intensity = abs(article.sentiment_score)
        intensity_score = min(sentiment_intensity * 1.5, 1.0)
        score += intensity_score
        
        #  6.  MarketKeywords 
        if KEYWORDS_AVAILABLE:
            try:
                from .market_keywords import MarketKeywords
                kw_score, _ = MarketKeywords.get_importance_score(
                    article.title + " " + article.summary
                )
                #  +3 
                keyword_bonus = min(kw_score * 0.3, 3.0)
                score += keyword_bonus
                
                # 
                is_high_impact, high_kw = MarketKeywords.is_high_impact_news(article.title)
                if is_high_impact:
                    article.keywords = high_kw + article.keywords
            except Exception as e:
                logger.debug(f": {e}")
        
        return round(min(score, 10.0), 2)  #  10 
    
    def _save_news_record(self, article: NewsArticle, current_price: float) -> None:
        """保存新聞記錄用於後續評估"""
        try:
            import os
            import json
            import hashlib
            
            # 生成唯一 ID
            news_id = hashlib.md5(
                f"{article.title}{article.published_at}".encode()
            ).hexdigest()[:16]
            
            record = {
                'news_id': news_id,
                'title': article.title,
                'url': article.url,
                'source': article.source,
                'keywords': article.keywords,
                'target_coin': article.target_coin,  # BTC, ETH, ...
                'symbol': article.target_coin + 'USDT',  # BTCUSDT, ETHUSDT, ...
                'timestamp': article.published_at.isoformat(),
                'price_at_news': current_price,
                'category': article.category,
                'sentiment': article.sentiment,
                'evaluated': False,
                'evaluation_window_hours': 24  # 預設 24 小時後評估
            }
            
            # 讀取現有記錄
            records = []
            if os.path.exists(self._news_records_file):
                try:
                    with open(self._news_records_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                except Exception:
                    records = []
            
            # 檢查是否已存在
            if not any(r['news_id'] == news_id for r in records):
                records.append(record)
                
                # 保存（只保留最近 30 天的記錄）
                cutoff = (datetime.now() - timedelta(days=30)).isoformat()
                records = [r for r in records if r['timestamp'] > cutoff]
                
                with open(self._news_records_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
                    
                logger.debug(f"已保存新聞記錄: {news_id}")
        except Exception as e:
            logger.warning(f"保存新聞記錄失敗: {e}")
    
    def evaluate_pending_news(self) -> Dict[str, int]:
        """評估待處理的新聞，更新關鍵字權重
        
        Returns:
            統計結果 {'evaluated': 5, 'bullish': 3, 'bearish': 2}
        """
        import os
        import json
        
        if not os.path.exists(self._news_records_file):
            logger.info("沒有待評估的新聞記錄")
            return {'evaluated': 0}
        
        try:
            with open(self._news_records_file, 'r', encoding='utf-8') as f:
                records = json.load(f)
        except Exception as e:
            logger.error(f"讀取新聞記錄失敗: {e}")
            return {'evaluated': 0}
        
        stats = {'evaluated': 0, 'bullish': 0, 'bearish': 0, 'neutral': 0, 'failed': 0}
        updated_records = []
        
        for record in records:
            if record.get('evaluated', False):
                updated_records.append(record)
                continue
            
            # 檢查是否到評估時間
            news_time = datetime.fromisoformat(record['timestamp'])
            eval_hours = record.get('evaluation_window_hours', 24)
            if datetime.now() < news_time + timedelta(hours=eval_hours):
                updated_records.append(record)
                continue
            
            # 評估新聞影響
            result = self._evaluate_single_news(record)
            if result:
                record['evaluated'] = True
                record['evaluation_result'] = result
                record['evaluated_at'] = datetime.now().isoformat()
                stats['evaluated'] += 1
                stats[result['direction']] += 1
                
                # 更新關鍵字權重
                self._update_keyword_weights(record['keywords'], result)
            else:
                stats['failed'] += 1
            
            updated_records.append(record)
        
        # 保存更新後的記錄
        try:
            with open(self._news_records_file, 'w', encoding='utf-8') as f:
                json.dump(updated_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存評估結果失敗: {e}")
        
        logger.info(f"評估完成: {stats}")
        return stats
    
    def _evaluate_single_news(self, record: Dict) -> Optional[Dict]:
        """評估單則新聞的市場影響"""
        try:
            # 從記錄中獲取交易對
            symbol = record.get('symbol') or (record['target_coin'] + 'USDT')
            
            # 獲取當前價格
            from ..data.binance_futures import BinanceFuturesConnector
            connector = BinanceFuturesConnector(testnet=True)
            price_data = connector.get_ticker_price(symbol)
            
            if not price_data:
                logger.warning(f"無法獲取 {symbol} 當前價格")
                return None
            
            current_price = price_data.price
            old_price = record['price_at_news']
            price_change = ((current_price - old_price) / old_price) * 100
            
            # 判定方向和強度
            if price_change > 3.0:
                direction = 'bullish'
                impact = 'strong'
            elif price_change > 1.0:
                direction = 'bullish'
                impact = 'moderate'
            elif price_change < -3.0:
                direction = 'bearish'
                impact = 'strong'
            elif price_change < -1.0:
                direction = 'bearish'
                impact = 'moderate'
            else:
                direction = 'neutral'
                impact = 'weak'
            
            return {
                'price_change': round(price_change, 2),
                'old_price': old_price,
                'new_price': current_price,
                'direction': direction,
                'impact': impact
            }
        except Exception as e:
            logger.warning(f"評估新聞失敗: {e}")
            return None
    
    def _update_keyword_weights(self, keywords: List[str], result: Dict) -> None:
        """根據評估結果更新關鍵字權重"""
        if not KEYWORDS_AVAILABLE or get_keyword_manager is None:
            return
        
        try:
            from .market_keywords import MarketKeywords
            
            direction = result['direction']
            impact = result['impact']
            
            # 根據影響強度決定調整幅度
            if impact == 'strong':
                factor = 1.15 if direction in ['bullish', 'bearish'] else 0.85
            elif impact == 'moderate':
                factor = 1.08 if direction in ['bullish', 'bearish'] else 0.92
            else:
                factor = 0.95  # 中性/弱影響則降低權重
            
            # 更新每個關鍵字
            km = get_keyword_manager()
            if km is not None:
                for kw in keywords:
                    # 使用存在的方法或跳過
                    if hasattr(km, 'update_keyword_weight'):
                        km.update_keyword_weight(kw, factor)  # type: ignore
                    if direction in ['bullish', 'bearish']:
                        if hasattr(km, 'record_and_verify_prediction'):
                            km.record_and_verify_prediction(kw, direction, direction, result['price_change'])  # type: ignore
                    else:
                        if hasattr(km, 'record_prediction'):
                            km.record_prediction(kw, 'neutral', result['old_price'])  # type: ignore
                
                logger.info(f"已更新 {len(keywords)} 個關鍵字權重 (factor={factor})")
        except Exception as e:
            logger.warning(f"更新關鍵字權重失敗: {e}")
    
    def _detect_event_type(self, text: str) -> str:
        """檢測新聞事件類型 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離不同檢測邏輯
        """
        text_lower = text.lower()
        
        # 優先使用關鍵字系統檢測
        if KEYWORDS_AVAILABLE:
            event_type = self._detect_with_keywords(text)
            if event_type != 'general':
                return event_type
        
        # 備用方案：使用規則檢測
        return self._detect_with_regex(text_lower)
    
    def _detect_with_keywords(self, text: str) -> str:
        """使用關鍵字系統檢測事件類型"""
        try:
            from .market_keywords import MarketKeywords
            matches = MarketKeywords.find_matches(text)
            
            for match in matches:
                if match.category == 'event':
                    return self._classify_keyword_event(match.keyword)
            
        except Exception as e:
            logger.debug(f"關鍵字檢測失敗: {e}")
        
        return 'general'
    
    def _classify_keyword_event(self, keyword: str) -> str:
        """根據關鍵字分類事件"""
        security_keywords = ['hack', 'exploit', 'stolen']
        if any(kw in keyword for kw in security_keywords):
            return 'security'
        
        if 'etf' in keyword:
            return 'etf'
        
        if 'halving' in keyword:
            return 'halving'
        
        regulation_keywords = ['lawsuit', 'ban', 'banned', 'crackdown', 'investigation']
        if keyword in regulation_keywords:
            return 'regulation'
        
        listing_keywords = ['listing', 'delisting']
        if keyword in listing_keywords:
            return 'listing'
        
        if keyword == 'partnership':
            return 'partnership'
        
        upgrade_keywords = ['upgrade', 'hard fork', 'mainnet']
        if keyword in upgrade_keywords:
            return 'upgrade'
        
        if keyword == 'whale':
            return 'whale'
        
        return 'general'
    
    def _detect_with_regex(self, text_lower: str) -> str:
        """使用正則表達式檢測事件類型"""
        # 安全事件
        if re.search(r'\b(hack|exploit|breach|attack|stolen|vulnerability)\b', text_lower):
            return 'security'
        
        # 監管事件
        if re.search(r'\b(sec|regulation|regulatory|ban|legal|lawsuit|compliance)\b', text_lower):
            return 'regulation'
        
        # ETF事件
        if re.search(r'\b(etf|exchange.traded.fund)\b', text_lower):
            return 'etf'
        
        # 減半事件
        if re.search(r'\b(halving|halvening)\b', text_lower):
            return 'halving'
        
        # 上市事件
        if re.search(r'\b(list|listing|delist)\b', text_lower):
            return 'listing'
        
        # 合作事件
        if re.search(r'\b(partner|collaboration|deal|agreement)\b', text_lower):
            return 'partnership'
        
        # 升級事件
        if re.search(r'\b(upgrade|fork|update|v2|mainnet)\b', text_lower):
            return 'upgrade'
        
        # 鯨魚事件
        if re.search(r'\b(whale|large.transfer)\b', text_lower):
            return 'whale'
        
        # 市場事件
        if re.search(r'\b(price|market|trading|bull|bear)\b', text_lower):
            return 'market'
        
        return 'general'
    
    def analyze_news(self, symbol: str = "BTCUSDT", hours: int = 24) -> NewsAnalysisResult:
        """
        
        
        Args:
            symbol:  BTCUSDT
            hours: 
        
        Returns:
            NewsAnalysisResult 
        """
        # 
        cache_key = f"{symbol}_{hours}"
        with self._lock:
            if cache_key in self._cache:
                result, cached_at = self._cache[cache_key]
                if (datetime.now() - cached_at).total_seconds() < self._cache_ttl:
                    return result
        
        # 
        coin = symbol.replace("USDT", "").replace("USD", "")
        
        # 
        articles = self._fetch_news(coin, hours)
        
        # 
        result = self._analyze_articles(symbol, articles)
        
        # 
        with self._lock:
            self._cache[cache_key] = (result, datetime.now())
        
        return result
    
    def _fetch_news(self, coin: str, hours: int) -> List[NewsArticle]:
        """"""
        articles = []
        
        #  1: CryptoPanic API ()
        articles.extend(self._fetch_from_cryptopanic(coin))
        
        #  2: RSS Feeds
        articles.extend(self._fetch_from_rss(coin))
        
        # 
        cutoff = datetime.now() - timedelta(hours=hours)
        articles = [a for a in articles if a.published_at >= cutoff]
        
        # 
        seen_titles = set()
        unique_articles = []
        for article in articles:
            title_key = article.title.lower()[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        logger.info(f"  {len(unique_articles)}  {coin} ")
        return unique_articles
    
    def _fetch_from_cryptopanic(self, coin: str) -> List[NewsArticle]:
        """ CryptoPanic  API"""
        articles = []
        
        try:
            import requests
            
            # CryptoPanic API - 需要有效的 API Key
            # 獲取免費 API Key: https://cryptopanic.com/developers/api/
            import os
            api_token = os.getenv('CRYPTOPANIC_API_TOKEN', 'free')
            
            if api_token == 'free':
                logger.warning(
                    "⚠️ 使用 CryptoPanic 免費限制模式。"
                    "請設置環境變數 CRYPTOPANIC_API_TOKEN 以獲得完整功能。"
                    "註冊地址: https://cryptopanic.com/developers/api/"
                )
            
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                'auth_token': api_token,
                'currencies': coin,
                'filter': 'important',
                'public': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get('results', [])[:20]:
                    try:
                        pub_date = datetime.fromisoformat(
                            item['published_at'].replace('Z', '+00:00')
                        ).replace(tzinfo=None)
                        
                        article = NewsArticle(
                            title=item.get('title', ''),
                            source=item.get('source', {}).get('title', 'CryptoPanic'),
                            url=item.get('url', ''),
                            published_at=pub_date,
                            summary=item.get('title', '')
                        )
                        articles.append(article)
                    except Exception:
                        continue
        
        except Exception as e:
            #  requests 
            error_msg = str(e)
            if 'timeout' in error_msg.lower():
                logger.warning("CryptoPanic API ")
            elif 'request' in error_msg.lower():
                logger.warning(f"CryptoPanic API : {e}")
            else:
                logger.warning(f" CryptoPanic : {e}")
        
        return articles
    
    def _fetch_from_rss(self, coin: str) -> List[NewsArticle]:
        """從RSS Feeds獲取新聞 - 重構降低複雜度
        
        複雜度降低策略：Extract Method 分離RSS處理邏輯
        """
        articles = []
        
        # 主要RSS源
        rss_feeds = [
            'https://cointelegraph.com/rss',
            'https://decrypt.co/feed',
            'https://www.coindesk.com/arc/outboundfeeds/rss/',
        ]
        
        try:
            import requests
            import xml.etree.ElementTree as ET
            
            for feed_url in rss_feeds:
                feed_articles = self._process_single_rss_feed(feed_url, coin, requests)
                articles.extend(feed_articles)
        
        except ImportError:
            logger.warning("缺少 requests 庫，跳過 RSS")
        except Exception as e:
            logger.warning(f"RSS獲取失敗: {e}")
        
        return articles
    
    def _process_single_rss_feed(self, feed_url: str, coin: str, requests) -> List[NewsArticle]:
        """處理單個RSS源"""
        articles = []
        
        try:
            response = requests.get(feed_url, timeout=5)
            if response.status_code != 200:
                return articles
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            
            # 處理RSS條目
            for item in root.findall('.//item')[:20]:  # 限制20則以避免過載
                article = self._parse_rss_item(item, feed_url, coin)
                if article:
                    articles.append(article)
        
        except Exception as e:
            logger.debug(f"RSS源 {feed_url} 處理失敗: {e}")
        
        return articles
    
    def _parse_rss_item(self, item, feed_url: str, coin: str) -> Optional[NewsArticle]:
        """解析RSS條目"""
        title = item.find('title')
        link = item.find('link')
        pub_date = item.find('pubDate')
        description = item.find('description')
        
        if title is None:
            return None
        
        # 提取文本內容
        title_text = title.text or ''
        desc_text = description.text[:200] if description is not None and description.text else ''
        full_text = f"{title_text} {desc_text}"
        
        # 檢查內容相關性
        matched_keywords = self._check_content_relevance(full_text, coin)
        if not matched_keywords:
            return None  # 不相關的內容跳過
        
        # 解析發布時間
        parsed_date = self._parse_publication_date(pub_date)
        
        # 創建新聞文章對象
        return NewsArticle(
            title=title_text,
            source=feed_url.split('/')[2],
            url=link.text.strip() if link is not None and link.text else '',
            published_at=parsed_date,
            summary=desc_text,
            keywords=matched_keywords  # 保存匹配到的關鍵字
        )
    
    def _check_content_relevance(self, full_text: str, coin: str) -> List[str]:
        """檢查內容相關性並返回匹配的關鍵字"""
        matched_keywords = []
        
        # 優先使用關鍵字系統
        if KEYWORDS_AVAILABLE:
            matched_keywords = self._match_with_keywords(full_text)
            if matched_keywords:
                return matched_keywords
        
        # 備用方案：使用幣種關鍵字
        return self._match_with_coin_keywords(full_text, coin)
    
    def _match_with_keywords(self, full_text: str) -> List[str]:
        """使用181個關鍵字系統進行匹配"""
        try:
            from .market_keywords import MarketKeywords
            matches = MarketKeywords.find_matches(full_text)
            if matches:
                return [m.keyword for m in matches]
        except Exception as e:
            logger.debug(f"關鍵字匹配失敗: {e}")
        
        return []
    
    def _match_with_coin_keywords(self, full_text: str, coin: str) -> List[str]:
        """使用基本幣種關鍵字匹配"""
        coin_keywords = self.COIN_KEYWORDS.get(coin, [coin.lower()])
        matched = [kw for kw in coin_keywords if kw in full_text.lower()]
        return matched if matched else []  # 沒匹配到返回空列表
    
    def _parse_publication_date(self, pub_date) -> datetime:
        """解析發布時間"""
        try:
            from email.utils import parsedate_to_datetime
            if pub_date is not None and pub_date.text:
                parsed_date = parsedate_to_datetime(pub_date.text)
                return parsed_date.replace(tzinfo=None)
        except Exception:
            pass
        
        return datetime.now()
    
    def _analyze_articles(self, symbol: str, articles: List[NewsArticle]) -> NewsAnalysisResult:
        """ - """
        
        # 
        target_coin = symbol.replace("USDT", "").replace("USD", "")
        
        if not articles:
            return NewsAnalysisResult(
                symbol=symbol,
                total_articles=0,
                positive_count=0,
                negative_count=0,
                neutral_count=0,
                overall_sentiment="neutral",
                sentiment_score=0.0,
                key_events=[],
                top_keywords=[],
                recent_headlines=[],
                recommendation="無新聞資料",
                analysis_time=datetime.now(),
                articles=[]
            )
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        # 移除未使用的total_score註釋
        all_keywords = []
        key_events = set()
        
        # 獲取當前價格（用於保存記錄）
        current_price = 0.0
        try:
            from ..data.binance_futures import BinanceFuturesConnector
            connector = BinanceFuturesConnector(testnet=True)
            price_data = connector.get_ticker_price(symbol)
            if price_data:
                current_price = price_data.price
                logger.info(f"獲取 {symbol} 當前價格: ${current_price:,.2f}")
        except Exception as e:
            logger.debug(f"無法獲取 {symbol} 價格: {e}")
        
        # 
        for article in articles:
            # 設置目標幣種
            article.target_coin = target_coin
            
            # 1. 
            sentiment, score = self._analyze_sentiment(article.title + " " + article.summary)
            article.sentiment = sentiment
            article.sentiment_score = score
            
            if sentiment == "positive":
                positive_count += 1
            elif sentiment == "negative":
                negative_count += 1
            else:
                neutral_count += 1
            

            
            # 2. 
            keywords = self._extract_keywords(article.title)
            article.keywords = keywords
            all_keywords.extend(keywords)
            
            # 3. 
            events = self._detect_key_events(article.title)
            key_events.update(events)
            
            # 4.  
            article.importance_score = self._calculate_importance_score(article, target_coin)
            
            # 5. 保存新聞記錄（用於後續評估）
            if current_price > 0 and article.keywords:  # 只保存有關鍵字的新聞
                article.price_at_news = current_price
                self._save_news_record(article, current_price)
        
        #  
        articles.sort(key=lambda x: x.importance_score, reverse=True)
        
        #  
        weighted_score = 0.0
        total_weight = 0.0
        for article in articles:
            weight = article.importance_score / 10.0  #  0-1
            weighted_score += article.sentiment_score * weight
            total_weight += weight
        
        avg_score = weighted_score / total_weight if total_weight > 0 else 0
        
        if avg_score > 0.2:
            overall_sentiment = "positive"
        elif avg_score < -0.2:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        # 
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(10)
        
        # 
        recent_headlines = [a.title for a in sorted(articles, key=lambda x: x.published_at, reverse=True)[:5]]
        
        # 
        recommendation = self._generate_recommendation(
            overall_sentiment, avg_score, list(key_events), positive_count, negative_count
        )
        
        # 排序文章 (最新在前)
        sorted_articles = sorted(articles, key=lambda x: x.published_at, reverse=True)
        
        return NewsAnalysisResult(
            symbol=symbol,
            total_articles=len(articles),
            positive_count=positive_count,
            negative_count=negative_count,
            neutral_count=neutral_count,
            overall_sentiment=overall_sentiment,
            sentiment_score=round(avg_score, 3),
            key_events=list(key_events),
            top_keywords=top_keywords,
            recent_headlines=recent_headlines,
            recommendation=recommendation,
            analysis_time=datetime.now(),
            articles=sorted_articles  # 包含完整文章資訊 (含連結)
        )
    
    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """"""
        text_lower = text.lower()
        
        positive_score = 0.0
        negative_score = 0.0
        
        # 
        for keyword, weight in self.POSITIVE_KEYWORDS.items():
            if keyword in text_lower:
                positive_score += weight
        
        # 
        for keyword, weight in self.NEGATIVE_KEYWORDS.items():
            if keyword in text_lower:
                negative_score += weight
        
        #  (-1  1)
        total = positive_score + negative_score
        if total == 0:
            return "neutral", 0.0
        
        score = (positive_score - negative_score) / max(total, 1)
        score = max(-1.0, min(1.0, score))  #  -1  1
        
        if score > 0.15:
            return "positive", score
        elif score < -0.15:
            return "negative", score
        else:
            return "neutral", score
    
    def _extract_keywords(self, text: str) -> List[str]:
        """"""
        # 
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # 
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'again', 'further', 'then', 'once',
            'and', 'but', 'or', 'nor', 'so', 'yet', 'both', 'either',
            'neither', 'not', 'only', 'own', 'same', 'than', 'too',
            'very', 'just', 'also', 'now', 'here', 'there', 'when',
            'where', 'why', 'how', 'all', 'each', 'every', 'both',
            'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'its', 'it', 'this', 'that', 'these', 'those', 'what'
        }
        
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords
    
    def _detect_key_events(self, text: str) -> List[str]:
        """"""
        text_lower = text.lower()
        events = []
        
        for event_type, pattern in self.KEY_EVENT_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                event_labels = {
                    'etf': ' ETF ',
                    'regulation': ' ',
                    'hack': ' ',
                    'partnership': '🤝 ',
                    'upgrade': ' ',
                    'listing': ' /',
                    'whale': ' ',
                    'halving': ' ',
                }
                events.append(event_labels.get(event_type, event_type))
        
        return events
    
    def _generate_recommendation(
        self, 
        sentiment: str, 
        score: float, 
        key_events: List[str],
        positive: int,
        negative: int
    ) -> str:
        """"""
        
        # 
        danger_events = [' ', ' ']
        has_danger = any(e in key_events for e in danger_events)
        
        if has_danger:
            return " /"
        
        # 
        if sentiment == "positive" and score > 0.4:
            return "🟢 "
        elif sentiment == "positive":
            return "🟢 "
        elif sentiment == "negative" and score < -0.4:
            return " "
        elif sentiment == "negative":
            return "🟡 "
        else:
            return " "
    
    def get_quick_summary(self, symbol: str = "BTCUSDT") -> str:
        """"""
        result = self.analyze_news(symbol, hours=24)
        
        sentiment_emoji = {
            'positive': '🟢',
            'negative': '',
            'neutral': ''
        }
        
        emoji = sentiment_emoji.get(result.overall_sentiment, '')
        
        summary = f"""

   {symbol}  24 

   : {result.total_articles} 
  {emoji} : {result.overall_sentiment.upper()} (: {result.sentiment_score:+.2f})
  
   : {result.positive_count} |  : {result.negative_count} |  : {result.neutral_count}
"""
        
        if result.key_events:
            summary += f"""
   : {', '.join(result.key_events)}
"""
        
        if result.recent_headlines:
            summary += """
   :
"""
            for i, headline in enumerate(result.recent_headlines[:3], 1):
                # 
                short_headline = headline[:50] + "..." if len(headline) > 50 else headline
                summary += f"     {i}. {short_headline}\n"
        
        summary += f"""
   : {result.recommendation}
"""
        
        return summary
    
    def should_trade(self, symbol: str = "BTCUSDT") -> Tuple[bool, str]:
        """
        
        
        Returns:
            (, )
        """
        result = self.analyze_news(symbol, hours=12)
        
        # 
        danger_events = [' ']
        if any(e in result.key_events for e in danger_events):
            return False, "/"
        
        # 
        if result.sentiment_score < -0.5:
            return False, f" ({result.sentiment_score:.2f})"
        
        # 
        if result.total_articles < 2:
            return True, ""
        
        return True, f": {result.overall_sentiment} ({result.sentiment_score:+.2f})"


# 
_news_analyzer: Optional[CryptoNewsAnalyzer] = None


def get_news_analyzer() -> CryptoNewsAnalyzer:
    """"""
    global _news_analyzer
    if _news_analyzer is None:
        _news_analyzer = CryptoNewsAnalyzer()
    return _news_analyzer


if __name__ == "__main__":
    print(" ")
    print("=" * 60)
    
    analyzer = CryptoNewsAnalyzer()
    
    #  BTC 
    print("\n  BTCUSDT ...\n")
    
    result = analyzer.analyze_news("BTCUSDT", hours=24)
    
    print("節目分析結果 :")
    print(f"   : {result.total_articles} ")
    print(f"   : {result.positive_count} | : {result.negative_count} | : {result.neutral_count}")
    print(f"\n : {result.overall_sentiment.upper()} (: {result.sentiment_score:+.3f})")
    
    if result.key_events:
        print("\n重要事件:")
        for event in result.key_events:
            print(f"   • {event}")
    
    if result.top_keywords:
        print("\n熱門關鍵字:")
        for kw, count in result.top_keywords[:5]:
            print(f"   • {kw}: {count}")
    
    if result.recent_headlines:
        print("\n最新標題:")
        for i, headline in enumerate(result.recent_headlines[:3], 1):
            short = headline[:60] + "..." if len(headline) > 60 else headline
            print(f"   {i}. {short}")
    
    print("\n投資建議:")
    print(f"   {result.recommendation}")
    
    # 
    print("\n" + "=" * 60)
    print("\n :\n")
    print(analyzer.get_quick_summary("BTCUSDT"))
    
    # 
    print("\n" + "=" * 60)
    can_trade, reason = analyzer.should_trade("BTCUSDT")
    trade_status = "可交易" if can_trade else "暫停交易"
    print(f"\n🤔 交易狀態: {trade_status}")
    print(f"   原因: {reason}")
