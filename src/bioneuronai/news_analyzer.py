"""
加密貨幣新聞分析服務
====================
獲取和分析加密貨幣相關新聞，輔助交易決策

功能：
1. 從多個來源獲取即時新聞
2. 情緒分析（正面/負面/中性）
3. 關鍵事件檢測（監管、駭客、ETF 等）
4. 新聞摘要生成
5. 🆕 基於關鍵字的重要性評分
"""

import re
import time
import logging
import requests
from typing import Optional, List, Dict, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import Counter
import threading

# 導入關鍵字模組
try:
    from .market_keywords import MarketKeywords, KeywordMatch
    KEYWORDS_AVAILABLE = True
except ImportError:
    KEYWORDS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """新聞文章"""
    title: str
    source: str
    url: str
    published_at: datetime
    summary: str = ""
    sentiment: str = "neutral"  # positive, negative, neutral
    sentiment_score: float = 0.0  # -1.0 到 1.0
    relevance_score: float = 0.0  # 相關性分數
    importance_score: float = 0.0  # 重要性分數（0-10）
    keywords: List[str] = field(default_factory=list)
    coins_mentioned: List[str] = field(default_factory=list)
    category: str = "general"  # 分類: regulation, security, market, partnership, technical


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
    recent_headlines: List[str]
    recommendation: str
    analysis_time: datetime


class CryptoNewsAnalyzer:
    """
    加密貨幣新聞分析器
    
    特點：
    - 從多個免費來源獲取新聞
    - 關鍵字情緒分析
    - 重大事件檢測
    - 交易建議生成
    """
    
    # 正面關鍵字（權重）
    POSITIVE_KEYWORDS = {
        # 強烈正面 (權重 2.0)
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
        
        # 中等正面 (權重 1.0)
        'positive': 1.0, 'optimistic': 1.0, 'bullish outlook': 1.2,
        'support': 0.8, 'momentum': 0.9, 'recovery': 1.0,
        'innovation': 1.0, 'development': 0.8,
        'launch': 0.9, 'release': 0.8,
        'accumulation': 1.0, 'buying': 0.8,
    }
    
    # 負面關鍵字（權重）
    NEGATIVE_KEYWORDS = {
        # 強烈負面 (權重 2.0)
        'hack': 2.0, 'hacked': 2.0, 'exploit': 2.0, 'breach': 1.8,
        'scam': 2.0, 'fraud': 2.0, 'rug pull': 2.0, 'ponzi': 2.0,
        'ban': 1.8, 'banned': 1.8, 'illegal': 1.8, 'crackdown': 1.8,
        'sec lawsuit': 1.8, 'regulatory action': 1.5,
        'crash': 1.8, 'plunge': 1.7, 'collapse': 1.8,
        'bankruptcy': 2.0, 'insolvent': 2.0, 'liquidation': 1.8,
        
        # 中等負面 (權重 1.0)
        'bearish': 1.3, 'bear market': 1.5,
        'selloff': 1.3, 'sell-off': 1.3, 'dumping': 1.3,
        'decline': 1.0, 'drop': 0.9, 'fall': 0.8, 'down': 0.6,
        'concern': 0.8, 'warning': 1.0, 'risk': 0.7,
        'delay': 0.8, 'postpone': 0.8, 'reject': 1.2, 'rejected': 1.2,
        'negative': 1.0, 'pessimistic': 1.0,
        'investigation': 1.2, 'probe': 1.1,
        'fear': 1.0, 'uncertainty': 0.8, 'doubt': 0.8,
    }
    
    # 重大事件關鍵字
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
    # 📊 重要性評分系統
    # ========================================
    
    # 來源權威性評分（滿分 2.0）
    SOURCE_AUTHORITY = {
        # 頂級媒體（滿分）
        'coindesk.com': 2.0,
        'cointelegraph.com': 2.0,
        'bloomberg.com': 2.0,
        'reuters.com': 2.0,
        'wsj.com': 2.0,
        'forbes.com': 1.8,
        
        # 專業媒體（高分）
        'decrypt.co': 1.8,
        'theblock.co': 1.8,
        'bitcoinmagazine.com': 1.7,
        'cryptoslate.com': 1.5,
        'cryptobriefing.com': 1.5,
        
        # 一般媒體（中分）
        'cryptopanic.com': 1.3,
        'newsbtc.com': 1.2,
        'bitcoinist.com': 1.2,
        'coingape.com': 1.0,
        
        # 預設
        'default': 0.8,
    }
    
    # 事件類型重要性（滿分 3.0）
    EVENT_IMPORTANCE = {
        'security': 3.0,      # 安全事件（駭客、漏洞）- 最高優先
        'regulation': 2.8,    # 監管政策 - 極高
        'etf': 2.5,           # ETF 相關 - 高
        'halving': 2.5,       # 減半事件 - 高
        'listing': 2.0,       # 上市/下架 - 中高
        'partnership': 1.8,   # 合作關係 - 中
        'upgrade': 1.5,       # 技術升級 - 中
        'whale': 1.5,         # 大戶動向 - 中
        'market': 1.0,        # 一般市場 - 低
        'general': 0.5,       # 一般新聞 - 最低
    }
    
    # 幣種關鍵字映射
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
        self._cache_ttl = 300  # 5 分鐘快取
        self._lock = threading.Lock()
        
        logger.info("📰 新聞分析服務已啟動")
    
    def _calculate_importance_score(self, article: NewsArticle, target_coin: str) -> float:
        """
        計算新聞重要性分數（滿分 10 分）
        
        評分維度：
        1. 來源權威性 (0-2 分)
        2. 事件類型 (0-3 分)
        3. 時間新鮮度 (0-2 分)
        4. 幣種相關性 (0-2 分)
        5. 情緒強度 (0-1 分)
        
        Returns:
            float: 0-10 的重要性分數
        """
        score = 0.0
        
        # 1. 來源權威性（滿分 2.0）
        source_domain = article.source.lower()
        source_score = self.SOURCE_AUTHORITY.get('default', 0.8)
        for domain, auth_score in self.SOURCE_AUTHORITY.items():
            if domain in source_domain:
                source_score = auth_score
                break
        score += source_score
        
        # 2. 事件類型（滿分 3.0）
        event_type = self._detect_event_type(article.title + " " + article.summary)
        article.category = event_type
        event_score = self.EVENT_IMPORTANCE.get(event_type, 0.5)
        score += event_score
        
        # 3. 時間新鮮度（滿分 2.0）
        hours_old = (datetime.now() - article.published_at).total_seconds() / 3600
        if hours_old < 1:       # 1 小時內
            time_score = 2.0
        elif hours_old < 4:     # 4 小時內
            time_score = 1.5
        elif hours_old < 12:    # 12 小時內
            time_score = 1.0
        elif hours_old < 24:    # 24 小時內
            time_score = 0.5
        else:
            time_score = 0.2
        score += time_score
        
        # 4. 幣種相關性（滿分 2.0）
        text_lower = (article.title + " " + article.summary).lower()
        coin_keywords = self.COIN_KEYWORDS.get(target_coin, [target_coin.lower()])
        
        # 直接提及目標幣種
        direct_mention = any(kw in text_lower for kw in coin_keywords)
        if direct_mention:
            relevance_score = 2.0
        # 提及 crypto/bitcoin 通用詞
        elif any(kw in text_lower for kw in ['crypto', 'bitcoin', 'cryptocurrency']):
            relevance_score = 1.0
        else:
            relevance_score = 0.3
        score += relevance_score
        article.relevance_score = relevance_score
        
        # 5. 情緒強度（滿分 1.0）
        sentiment_intensity = abs(article.sentiment_score)
        intensity_score = min(sentiment_intensity * 1.5, 1.0)
        score += intensity_score
        
        # 🆕 6. 關鍵字加成（使用 MarketKeywords 模組）
        if KEYWORDS_AVAILABLE:
            try:
                from .market_keywords import MarketKeywords
                kw_score, matched_keywords = MarketKeywords.get_importance_score(
                    article.title + " " + article.summary
                )
                # 關鍵字加成（最多 +3 分）
                keyword_bonus = min(kw_score * 0.3, 3.0)
                score += keyword_bonus
                
                # 記錄匹配到的高影響關鍵字
                is_high_impact, high_kw = MarketKeywords.is_high_impact_news(article.title)
                if is_high_impact:
                    article.keywords = high_kw + article.keywords
            except Exception as e:
                logger.debug(f"關鍵字分析失敗: {e}")
        
        return round(min(score, 10.0), 2)  # 最高 10 分
    
    def _detect_event_type(self, text: str) -> str:
        """檢測新聞事件類型"""
        text_lower = text.lower()
        
        # 🆕 優先使用關鍵字模組
        if KEYWORDS_AVAILABLE:
            try:
                from .market_keywords import MarketKeywords
                matches = MarketKeywords.find_matches(text)
                for match in matches:
                    if match.category == 'event':
                        # 映射到內部分類
                        if 'hack' in match.keyword or 'exploit' in match.keyword or 'stolen' in match.keyword:
                            return 'security'
                        if 'etf' in match.keyword:
                            return 'etf'
                        if 'halving' in match.keyword:
                            return 'halving'
                        if match.keyword in ['lawsuit', 'ban', 'banned', 'crackdown', 'investigation']:
                            return 'regulation'
                        if match.keyword in ['listing', 'delisting']:
                            return 'listing'
                        if match.keyword == 'partnership':
                            return 'partnership'
                        if match.keyword in ['upgrade', 'hard fork', 'mainnet']:
                            return 'upgrade'
                        if match.keyword == 'whale':
                            return 'whale'
            except Exception as e:
                logger.debug(f"關鍵字事件檢測失敗: {e}")
        
        # 回退到原始檢測
        if re.search(r'\b(hack|exploit|breach|attack|stolen|vulnerability)\b', text_lower):
            return 'security'
        if re.search(r'\b(sec|regulation|regulatory|ban|legal|lawsuit|compliance)\b', text_lower):
            return 'regulation'
        if re.search(r'\b(etf|exchange.traded.fund)\b', text_lower):
            return 'etf'
        if re.search(r'\b(halving|halvening)\b', text_lower):
            return 'halving'
        if re.search(r'\b(list|listing|delist)\b', text_lower):
            return 'listing'
        if re.search(r'\b(partner|collaboration|deal|agreement)\b', text_lower):
            return 'partnership'
        if re.search(r'\b(upgrade|fork|update|v2|mainnet)\b', text_lower):
            return 'upgrade'
        if re.search(r'\b(whale|large.transfer)\b', text_lower):
            return 'whale'
        if re.search(r'\b(price|market|trading|bull|bear)\b', text_lower):
            return 'market'
        
        return 'general'
    
    def analyze_news(self, symbol: str = "BTCUSDT", hours: int = 24) -> NewsAnalysisResult:
        """
        分析特定幣種的新聞
        
        Args:
            symbol: 交易對（如 BTCUSDT）
            hours: 分析過去幾小時的新聞
        
        Returns:
            NewsAnalysisResult 分析結果
        """
        # 檢查快取
        cache_key = f"{symbol}_{hours}"
        with self._lock:
            if cache_key in self._cache:
                result, cached_at = self._cache[cache_key]
                if (datetime.now() - cached_at).total_seconds() < self._cache_ttl:
                    return result
        
        # 提取幣種名稱
        coin = symbol.replace("USDT", "").replace("USD", "")
        
        # 獲取新聞
        articles = self._fetch_news(coin, hours)
        
        # 分析新聞
        result = self._analyze_articles(symbol, articles)
        
        # 快取結果
        with self._lock:
            self._cache[cache_key] = (result, datetime.now())
        
        return result
    
    def _fetch_news(self, coin: str, hours: int) -> List[NewsArticle]:
        """從多個來源獲取新聞"""
        articles = []
        
        # 來源 1: CryptoPanic API (免費)
        articles.extend(self._fetch_from_cryptopanic(coin))
        
        # 來源 2: RSS Feeds
        articles.extend(self._fetch_from_rss(coin))
        
        # 過濾時間範圍
        cutoff = datetime.now() - timedelta(hours=hours)
        articles = [a for a in articles if a.published_at >= cutoff]
        
        # 去重（根據標題）
        seen_titles = set()
        unique_articles = []
        for article in articles:
            title_key = article.title.lower()[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        logger.info(f"📰 獲取到 {len(unique_articles)} 篇 {coin} 相關新聞")
        return unique_articles
    
    def _fetch_from_cryptopanic(self, coin: str) -> List[NewsArticle]:
        """從 CryptoPanic 獲取新聞（免費 API）"""
        articles = []
        
        try:
            import requests
            
            # CryptoPanic 免費 API（無需 API Key 的公開端點）
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                'auth_token': 'free',  # 使用免費 token
                'currencies': coin,
                'filter': 'important',
                'public': 'true'
            }
            
            # 備用：直接爬取公開頁面
            alt_url = f"https://cryptopanic.com/news/{coin.lower()}/"
            
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
        
        except requests.exceptions.Timeout:
            logger.warning("CryptoPanic API 請求超時")
        except requests.exceptions.RequestException as e:
            logger.warning(f"CryptoPanic API 請求失敗: {e}")
        except Exception as e:
            logger.warning(f"獲取 CryptoPanic 新聞失敗: {e}")
        
        return articles
    
    def _fetch_from_rss(self, coin: str) -> List[NewsArticle]:
        """從 RSS Feeds 獲取新聞"""
        articles = []
        
        # 加密貨幣新聞 RSS 源
        rss_feeds = [
            'https://cointelegraph.com/rss',
            'https://decrypt.co/feed',
            'https://www.coindesk.com/arc/outboundfeeds/rss/',
        ]
        
        try:
            import requests
            import xml.etree.ElementTree as ET
            
            for feed_url in rss_feeds:
                try:
                    response = requests.get(feed_url, timeout=5)
                    if response.status_code != 200:
                        continue
                    
                    root = ET.fromstring(response.content)
                    
                    # 解析 RSS
                    for item in root.findall('.//item')[:10]:
                        title = item.find('title')
                        link = item.find('link')
                        pub_date = item.find('pubDate')
                        description = item.find('description')
                        
                        if title is None:
                            continue
                        
                        title_text = title.text or ''
                        
                        # 檢查是否與目標幣種相關
                        coin_keywords = self.COIN_KEYWORDS.get(coin, [coin.lower()])
                        is_relevant = any(
                            kw in title_text.lower() 
                            for kw in coin_keywords
                        )
                        
                        # 也檢查通用加密貨幣新聞
                        is_crypto_news = any(
                            kw in title_text.lower() 
                            for kw in ['crypto', 'bitcoin', 'blockchain', 'defi']
                        )
                        
                        if not (is_relevant or is_crypto_news):
                            continue
                        
                        # 解析日期
                        try:
                            from email.utils import parsedate_to_datetime
                            parsed_date = parsedate_to_datetime(pub_date.text) if pub_date is not None and pub_date.text else datetime.now()
                            parsed_date = parsed_date.replace(tzinfo=None)
                        except:
                            parsed_date = datetime.now()
                        
                        article = NewsArticle(
                            title=title_text,
                            source=feed_url.split('/')[2],
                            url=link.text.strip() if link is not None and link.text else '',
                            published_at=parsed_date,
                            summary=description.text[:200] if description is not None and description.text else ''
                        )
                        articles.append(article)
                
                except Exception as e:
                    logger.debug(f"RSS {feed_url} 解析失敗: {e}")
                    continue
        
        except ImportError:
            logger.warning("需要 requests 來獲取 RSS")
        except Exception as e:
            logger.warning(f"RSS 獲取失敗: {e}")
        
        return articles
    
    def _analyze_articles(self, symbol: str, articles: List[NewsArticle]) -> NewsAnalysisResult:
        """分析文章列表 - 含重要性評分和排序"""
        
        # 提取幣種
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
                recommendation="⚪ 無新聞數據，建議謹慎觀望",
                analysis_time=datetime.now()
            )
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        total_score = 0.0
        all_keywords = []
        key_events = set()
        
        # 分析每篇文章
        for article in articles:
            # 1. 情緒分析
            sentiment, score = self._analyze_sentiment(article.title + " " + article.summary)
            article.sentiment = sentiment
            article.sentiment_score = score
            
            if sentiment == "positive":
                positive_count += 1
            elif sentiment == "negative":
                negative_count += 1
            else:
                neutral_count += 1
            
            total_score += score
            
            # 2. 提取關鍵字
            keywords = self._extract_keywords(article.title)
            article.keywords = keywords
            all_keywords.extend(keywords)
            
            # 3. 檢測重大事件
            events = self._detect_key_events(article.title)
            key_events.update(events)
            
            # 4. 🆕 計算重要性分數
            article.importance_score = self._calculate_importance_score(article, target_coin)
        
        # 🆕 按重要性分數排序（高分優先）
        articles.sort(key=lambda x: x.importance_score, reverse=True)
        
        # 🆕 加權計算整體情緒（重要文章權重更高）
        weighted_score = 0.0
        total_weight = 0.0
        for article in articles:
            weight = article.importance_score / 10.0  # 歸一化到 0-1
            weighted_score += article.sentiment_score * weight
            total_weight += weight
        
        avg_score = weighted_score / total_weight if total_weight > 0 else 0
        
        if avg_score > 0.2:
            overall_sentiment = "positive"
        elif avg_score < -0.2:
            overall_sentiment = "negative"
        else:
            overall_sentiment = "neutral"
        
        # 統計關鍵字
        keyword_counts = Counter(all_keywords)
        top_keywords = keyword_counts.most_common(10)
        
        # 最近標題
        recent_headlines = [a.title for a in sorted(articles, key=lambda x: x.published_at, reverse=True)[:5]]
        
        # 生成建議
        recommendation = self._generate_recommendation(
            overall_sentiment, avg_score, list(key_events), positive_count, negative_count
        )
        
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
            analysis_time=datetime.now()
        )
    
    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """分析文本情緒"""
        text_lower = text.lower()
        
        positive_score = 0.0
        negative_score = 0.0
        
        # 計算正面分數
        for keyword, weight in self.POSITIVE_KEYWORDS.items():
            if keyword in text_lower:
                positive_score += weight
        
        # 計算負面分數
        for keyword, weight in self.NEGATIVE_KEYWORDS.items():
            if keyword in text_lower:
                negative_score += weight
        
        # 計算最終分數 (-1 到 1)
        total = positive_score + negative_score
        if total == 0:
            return "neutral", 0.0
        
        score = (positive_score - negative_score) / max(total, 1)
        score = max(-1.0, min(1.0, score))  # 限制在 -1 到 1
        
        if score > 0.15:
            return "positive", score
        elif score < -0.15:
            return "negative", score
        else:
            return "neutral", score
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取關鍵字"""
        # 移除特殊字符，保留字母數字
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # 過濾停用詞
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
        """檢測重大事件"""
        text_lower = text.lower()
        events = []
        
        for event_type, pattern in self.KEY_EVENT_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                event_labels = {
                    'etf': '📊 ETF 相關',
                    'regulation': '⚖️ 監管相關',
                    'hack': '🚨 安全事件',
                    'partnership': '🤝 合作關係',
                    'upgrade': '⬆️ 升級更新',
                    'listing': '📋 上市/下架',
                    'whale': '🐋 大戶動向',
                    'halving': '✂️ 減半事件',
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
        """生成交易建議"""
        
        # 檢查重大負面事件
        danger_events = ['🚨 安全事件', '⚖️ 監管相關']
        has_danger = any(e in key_events for e in danger_events)
        
        if has_danger:
            return "🔴 警告：檢測到重大風險事件（安全/監管），建議暫緩交易並密切關注"
        
        # 根據情緒生成建議
        if sentiment == "positive" and score > 0.4:
            return "🟢 新聞情緒強烈正面，市場氛圍樂觀，可考慮做多但注意追高風險"
        elif sentiment == "positive":
            return "🟢 新聞情緒偏正面，市場氛圍尚可，可配合技術指標考慮進場"
        elif sentiment == "negative" and score < -0.4:
            return "🔴 新聞情緒強烈負面，市場恐慌情緒高，建議觀望或考慮做空"
        elif sentiment == "negative":
            return "🟡 新聞情緒偏負面，建議謹慎，等待更明確信號"
        else:
            return "⚪ 新聞情緒中性，無明顯偏向，建議以技術分析為主"
    
    def get_quick_summary(self, symbol: str = "BTCUSDT") -> str:
        """獲取快速新聞摘要（用於交易前顯示）"""
        result = self.analyze_news(symbol, hours=24)
        
        sentiment_emoji = {
            'positive': '🟢',
            'negative': '🔴',
            'neutral': '⚪'
        }
        
        emoji = sentiment_emoji.get(result.overall_sentiment, '⚪')
        
        summary = f"""
╔══════════════════════════════════════════════════════════╗
║  📰 {symbol} 新聞分析摘要（過去 24 小時）
╠══════════════════════════════════════════════════════════╣
║  📊 新聞數量: {result.total_articles} 篇
║  {emoji} 整體情緒: {result.overall_sentiment.upper()} (分數: {result.sentiment_score:+.2f})
║  
║  📈 正面: {result.positive_count} | 📉 負面: {result.negative_count} | ➖ 中性: {result.neutral_count}
║"""
        
        if result.key_events:
            summary += f"""
║  🎯 重大事件: {', '.join(result.key_events)}
║"""
        
        if result.recent_headlines:
            summary += """
║  📝 最新頭條:
"""
            for i, headline in enumerate(result.recent_headlines[:3], 1):
                # 截斷長標題
                short_headline = headline[:50] + "..." if len(headline) > 50 else headline
                summary += f"║     {i}. {short_headline}\n"
        
        summary += f"""║
║  💡 建議: {result.recommendation}
╚══════════════════════════════════════════════════════════╝"""
        
        return summary
    
    def should_trade(self, symbol: str = "BTCUSDT") -> Tuple[bool, str]:
        """
        根據新聞判斷是否適合交易
        
        Returns:
            (可以交易, 原因)
        """
        result = self.analyze_news(symbol, hours=12)
        
        # 檢查危險事件
        danger_events = ['🚨 安全事件']
        if any(e in result.key_events for e in danger_events):
            return False, "檢測到安全事件（駭客/漏洞），建議暫停交易"
        
        # 檢查極端負面情緒
        if result.sentiment_score < -0.5:
            return False, f"新聞情緒極度負面 ({result.sentiment_score:.2f})，建議觀望"
        
        # 檢查新聞數量（太少可能代表異常）
        if result.total_articles < 2:
            return True, "新聞數據較少，建議以技術分析為主"
        
        return True, f"新聞情緒: {result.overall_sentiment} ({result.sentiment_score:+.2f})"


# 全局實例
_news_analyzer: Optional[CryptoNewsAnalyzer] = None


def get_news_analyzer() -> CryptoNewsAnalyzer:
    """獲取全局新聞分析器實例"""
    global _news_analyzer
    if _news_analyzer is None:
        _news_analyzer = CryptoNewsAnalyzer()
    return _news_analyzer


if __name__ == "__main__":
    print("📰 加密貨幣新聞分析服務測試")
    print("=" * 60)
    
    analyzer = CryptoNewsAnalyzer()
    
    # 測試 BTC 新聞分析
    print("\n🔍 分析 BTCUSDT 新聞中...\n")
    
    result = analyzer.analyze_news("BTCUSDT", hours=24)
    
    print(f"📊 新聞統計:")
    print(f"   總數: {result.total_articles} 篇")
    print(f"   正面: {result.positive_count} | 負面: {result.negative_count} | 中性: {result.neutral_count}")
    print(f"\n🎯 整體情緒: {result.overall_sentiment.upper()} (分數: {result.sentiment_score:+.3f})")
    
    if result.key_events:
        print(f"\n⚡ 重大事件:")
        for event in result.key_events:
            print(f"   • {event}")
    
    if result.top_keywords:
        print(f"\n🔑 熱門關鍵字:")
        for kw, count in result.top_keywords[:5]:
            print(f"   • {kw}: {count}")
    
    if result.recent_headlines:
        print(f"\n📝 最新頭條:")
        for i, headline in enumerate(result.recent_headlines[:3], 1):
            short = headline[:60] + "..." if len(headline) > 60 else headline
            print(f"   {i}. {short}")
    
    print(f"\n💡 交易建議:")
    print(f"   {result.recommendation}")
    
    # 測試快速摘要
    print("\n" + "=" * 60)
    print("\n📋 快速摘要顯示測試:\n")
    print(analyzer.get_quick_summary("BTCUSDT"))
    
    # 測試交易判斷
    print("\n" + "=" * 60)
    can_trade, reason = analyzer.should_trade("BTCUSDT")
    print(f"\n🤔 是否適合交易: {'✅ 是' if can_trade else '❌ 否'}")
    print(f"   原因: {reason}")
