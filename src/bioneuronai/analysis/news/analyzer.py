"""
加密貨幣新聞分析器
==================

CryptoNewsAnalyzer - 主要新聞分析類

功能：
- 從多種來源獲取加密貨幣新聞 (CryptoPanic, RSS)
- 情緒分析與評分
- 關鍵字提取與事件檢測
- 重要性評分 (來源權威、時效性、相關性)
- 新聞記錄保存用於後續關鍵字學習

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import re
import os
import json
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, cast
from collections import Counter

# 2. 本地模組
from .models import NewsArticle, NewsAnalysisResult

# 設置日誌
logger = logging.getLogger(__name__)

# 事件類型常量
EVENT_SECURITY = '🔒 安全事件'
EVENT_REGULATION = '⚖️ 監管風險'

# ========================================
# 關鍵字系統整合
# ========================================
KEYWORDS_AVAILABLE = False
_imported_get_keyword_manager: Optional[Callable[[], Any]] = None

try:
    from ...analysis.keywords import get_keyword_manager as _imported_get_keyword_manager
    KEYWORDS_AVAILABLE = True
    logger.info("✅ 已載入 217 個關鍵字系統 (keywords)")
except ImportError:
    logger.warning("⚠️ keywords 不可用，使用內建關鍵字")

get_keyword_manager = cast(Optional[Callable[[], Any]], _imported_get_keyword_manager)


class CryptoNewsAnalyzer:
    """
    加密貨幣新聞分析器
    
    核心功能：
    1. 從 CryptoPanic API 和 RSS 獲取新聞
    2. 情緒分析 (正面/負面/中性)
    3. 關鍵字提取與事件檢測
    4. 重要性評分 (0-10)
    5. 交易建議生成
    
    使用範例：
        analyzer = CryptoNewsAnalyzer()
        result = analyzer.analyze_news("BTCUSDT", hours=24)
        print(result.recommendation)
    """
    
    # ========================================
    # 情緒關鍵字定義
    # ========================================
    
    # 正面關鍵字
    POSITIVE_KEYWORDS = {
        # 強正面 (權重 2.0)
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
        
        # 中性偏正 (權重 1.0)
        'positive': 1.0, 'optimistic': 1.0, 'bullish outlook': 1.2,
        'support': 0.8, 'momentum': 0.9, 'recovery': 1.0,
        'innovation': 1.0, 'development': 0.8,
        'launch': 0.9, 'release': 0.8,
        'accumulation': 1.0, 'buying': 0.8,
    }
    
    # 負面關鍵字
    NEGATIVE_KEYWORDS = {
        # 強負面 (權重 2.0)
        'hack': 2.0, 'hacked': 2.0, 'exploit': 2.0, 'breach': 1.8,
        'scam': 2.0, 'fraud': 2.0, 'rug pull': 2.0, 'ponzi': 2.0,
        'ban': 1.8, 'banned': 1.8, 'illegal': 1.8, 'crackdown': 1.8,
        'sec lawsuit': 1.8, 'regulatory action': 1.5,
        'crash': 1.8, 'plunge': 1.7, 'collapse': 1.8,
        'bankruptcy': 2.0, 'insolvent': 2.0, 'liquidation': 1.8,
        
        # 中性偏負 (權重 1.0)
        'bearish': 1.3, 'bear market': 1.5,
        'selloff': 1.3, 'sell-off': 1.3, 'dumping': 1.3,
        'decline': 1.0, 'drop': 0.9, 'fall': 0.8, 'down': 0.6,
        'concern': 0.8, 'warning': 1.0, 'risk': 0.7,
        'delay': 0.8, 'postpone': 0.8, 'reject': 1.2, 'rejected': 1.2,
        'negative': 1.0, 'pessimistic': 1.0,
        'investigation': 1.2, 'probe': 1.1,
        'fear': 1.0, 'uncertainty': 0.8, 'doubt': 0.8,
    }
    
    # 事件類型正則模式
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
    # 來源權威度 (0-2.0)
    # ========================================
    SOURCE_AUTHORITY = {
        # 頂級媒體
        'coindesk.com': 2.0,
        'cointelegraph.com': 2.0,
        'bloomberg.com': 2.0,
        'reuters.com': 2.0,
        'wsj.com': 2.0,
        'forbes.com': 1.8,
        
        # 專業媒體
        'decrypt.co': 1.8,
        'theblock.co': 1.8,
        'bitcoinmagazine.com': 1.7,
        'cryptoslate.com': 1.5,
        'cryptobriefing.com': 1.5,
        
        # 一般媒體
        'cryptopanic.com': 1.3,
        'newsbtc.com': 1.2,
        'bitcoinist.com': 1.2,
        'coingape.com': 1.0,
        
        # 預設
        'default': 0.8,
    }
    
    # 事件重要性 (0-3.0)
    EVENT_IMPORTANCE = {
        'security': 3.0,      # 安全事件 - 最高優先
        'regulation': 2.8,    # 監管 - 影響深遠
        'etf': 2.5,           # ETF 相關 - 市場熱點
        'halving': 2.5,       # 減半 - 週期性重要事件
        'listing': 2.0,       # 上市/下市 - 直接影響價格
        'partnership': 1.8,   # 合作夥伴 - 中等重要
        'upgrade': 1.5,       # 技術升級 - 基礎面
        'whale': 1.5,         # 大戶動向 - 市場信號
        'market': 1.0,        # 一般市場 - 普通新聞
        'general': 0.5,       # 一般 - 低重要性
    }
    
    # 幣種關鍵字
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
    
    _ADAPTIVE_WINDOW_DEFAULT_HOURS = 24
    _ADAPTIVE_WINDOW_MIN_HOURS = 1
    _ADAPTIVE_WINDOW_MAX_HOURS = 168
    _ADAPTIVE_WINDOW_OVERLAP_MINUTES = 5

    def __init__(
        self,
        enable_rag_ingest: bool = True,
        news_fetcher: Any = None,
    ) -> None:
        """
        Args:
            enable_rag_ingest: 是否將新聞注入 RAG 知識庫。
            news_fetcher:      NewsDataFetcher 實例（用於 CryptoPanic + RSS HTTP 請求）。
                               若未提供，自動建立預設實例。
        """
        self._cache: Dict[str, Tuple[NewsAnalysisResult, datetime]] = {}
        self._cache_ttl = 300  # 5 分鐘
        self._lock = threading.Lock()
        self.enable_rag_ingest = enable_rag_ingest

        # 注入或自建 NewsDataFetcher
        if news_fetcher is not None:
            self._news_fetcher = news_fetcher
        else:
            try:
                from ...data.news_data_fetcher import NewsDataFetcher
                self._news_fetcher = NewsDataFetcher()
            except Exception as exc:
                logger.warning(f"NewsDataFetcher 建立失敗，新聞抓取將不可用: {exc}")
                self._news_fetcher = None

        # 新聞記錄文件路徑
        self._news_records_dir = Path(__file__).parent.parent.parent.parent / "data" / "bioneuronai" / "trading" / "sop"
        self._news_records_file = self._news_records_dir / "news_records.json"
        self._news_fetch_state_file = self._news_records_dir / "news_fetch_state.json"
        self._news_records_dir.mkdir(exist_ok=True, parents=True)

        logger.info("✅ CryptoNewsAnalyzer 初始化完成")
    
    # ========================================
    # 主要公開 API
    # ========================================
    
    def analyze_news(
        self,
        symbol: str = "BTCUSDT",
        hours: Optional[int] = None,
    ) -> NewsAnalysisResult:
        """
        分析加密貨幣新聞
        
        Args:
            symbol: 交易對，如 BTCUSDT
            hours: 分析時間範圍；None 表示使用自適應時間窗
        
        Returns:
            NewsAnalysisResult 分析結果
        """
        window_hours, cutoff = self._resolve_analysis_window(symbol, hours)

        # 檢查快取
        cache_key = f"{symbol}_{hours if hours is not None else 'adaptive'}"
        with self._lock:
            if cache_key in self._cache:
                result, cached_at = self._cache[cache_key]
                if (datetime.now() - cached_at).total_seconds() < self._cache_ttl:
                    return result
        
        # 解析幣種
        coin = symbol.replace("USDT", "").replace("USD", "")
        
        # 獲取新聞
        articles = self._fetch_news(coin, cutoff=cutoff)
        
        # 分析新聞
        result = self._analyze_articles(symbol, articles)

        # Analysis -> RAG 知識入庫（B.6）
        self._ingest_analysis_to_rag(result=result, symbol=symbol, hours=window_hours)

        if articles:
            self._save_last_fetch_time(symbol, datetime.now())
        
        # 更新快取
        with self._lock:
            self._cache[cache_key] = (result, datetime.now())
        
        return result

    def _resolve_analysis_window(
        self,
        symbol: str,
        hours: Optional[int],
    ) -> Tuple[int, datetime]:
        """解析分析時間窗；未指定時使用上次成功抓取時間自適應。"""
        if hours is not None:
            normalized_hours = max(self._ADAPTIVE_WINDOW_MIN_HOURS, min(int(hours), self._ADAPTIVE_WINDOW_MAX_HOURS))
            return normalized_hours, datetime.now() - timedelta(hours=normalized_hours)

        last_fetch = self._get_last_fetch_time(symbol)
        if last_fetch is None:
            default_hours = self._ADAPTIVE_WINDOW_DEFAULT_HOURS
            return default_hours, datetime.now() - timedelta(hours=default_hours)

        cutoff = last_fetch - timedelta(minutes=self._ADAPTIVE_WINDOW_OVERLAP_MINUTES)
        elapsed_hours = max(
            self._ADAPTIVE_WINDOW_MIN_HOURS,
            int((datetime.now() - cutoff).total_seconds() / 3600) + 1,
        )
        normalized_hours = min(elapsed_hours, self._ADAPTIVE_WINDOW_MAX_HOURS)
        return normalized_hours, cutoff

    def _get_last_fetch_time(self, symbol: str) -> Optional[datetime]:
        """讀取指定交易對上次成功抓取新聞的時間。"""
        if not self._news_fetch_state_file.exists():
            return None

        try:
            with open(self._news_fetch_state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            timestamp = data.get(symbol)
            if not timestamp:
                return None
            return datetime.fromisoformat(timestamp)
        except Exception as e:
            logger.debug(f"讀取新聞抓取狀態失敗: {e}")
            return None

    def _save_last_fetch_time(self, symbol: str, fetched_at: datetime) -> None:
        """保存指定交易對上次成功抓取新聞的時間。"""
        state: Dict[str, str] = {}
        if self._news_fetch_state_file.exists():
            try:
                with open(self._news_fetch_state_file, 'r', encoding='utf-8') as f:
                    state = cast(Dict[str, str], json.load(f))
            except Exception as e:
                logger.debug(f"讀取既有抓取狀態失敗，將覆寫: {e}")

        state[symbol] = fetched_at.isoformat()
        try:
            with open(self._news_fetch_state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"保存新聞抓取狀態失敗: {e}")

    def _ingest_analysis_to_rag(
        self,
        result: NewsAnalysisResult,
        symbol: str,
        hours: int,
    ) -> None:
        """將分析結果寫入 RAG 知識庫（失敗不影響主流程）"""
        if not self.enable_rag_ingest:
            return

        try:
            # 延遲導入避免循環依賴
            from rag.services.news_adapter import ingest_news_analysis_with_status

            ingest_result = ingest_news_analysis_with_status(
                analysis_result=result,
                symbol=symbol,
                hours=hours,
            )
            status = str(ingest_result.get("status", "ERROR"))
            docs = int(ingest_result.get("ingested_docs", 0) or 0)
            message = str(ingest_result.get("message", ""))

            if status == "OK":
                logger.info(f"✅ 新聞分析結果已寫入知識庫: {symbol} | docs={docs}")
            elif status == "NO_DATA":
                logger.warning(f"[NO_DATA] 新聞分析無可入庫資料: {symbol} | {message}")
            else:
                logger.error(f"[ERROR] 新聞分析結果入庫失敗: {symbol} | {message}")
        except Exception as e:
            logger.warning(f"新聞分析結果入庫失敗（不中斷主流程）: {e}")
    
    def get_quick_summary(self, symbol: str = "BTCUSDT", hours: Optional[int] = None) -> str:
        """獲取快速摘要"""
        result = self.analyze_news(symbol, hours=hours)
        
        sentiment_emoji = {
            'positive': '🟢',
            'negative': '🔴',
            'neutral': '⚪'
        }
        
        emoji = sentiment_emoji.get(result.overall_sentiment, '⚪')
        
        summary = f"""
📰 {symbol} 新聞分析 ({result.signal_valid_hours}小時有效)

📊 統計: {result.total_articles} 則新聞
{emoji} 情緒: {result.overall_sentiment.upper()} (分數: {result.sentiment_score:+.2f})

正面: {result.positive_count} | 負面: {result.negative_count} | 中性: {result.neutral_count}
"""
        
        if result.key_events:
            summary += f"\n🔥 重要事件: {', '.join(result.key_events)}\n"
        
        if result.recent_headlines:
            summary += "\n📌 最新標題:\n"
            for i, headline in enumerate(result.recent_headlines[:3], 1):
                short_headline = headline[:50] + "..." if len(headline) > 50 else headline
                summary += f"   {i}. {short_headline}\n"
        
        summary += f"\n💡 建議: {result.recommendation}\n"
        
        return summary
    
    def should_trade(self, symbol: str = "BTCUSDT", hours: Optional[int] = None) -> Tuple[bool, str]:
        """
        判斷是否適合交易
        
        Returns:
            (是否可交易, 原因)
        """
        result = self.analyze_news(symbol, hours=hours)
        
        # 檢查危險事件
        danger_events = [EVENT_SECURITY]
        if any(e in result.key_events for e in danger_events):
            return False, "存在安全事件/駭客風險"
        
        # 檢查極端負面情緒
        if result.sentiment_score < -0.5:
            return False, f"新聞情緒過度負面 ({result.sentiment_score:.2f})"
        
        # 新聞太少無法判斷
        if result.total_articles < 2:
            return True, "新聞資料不足，謹慎交易"
        
        return True, f"情緒正常: {result.overall_sentiment} ({result.sentiment_score:+.2f})"
    
    def evaluate_pending_news(self) -> Dict[str, int]:
        """評估待處理的新聞，更新關鍵字權重
        
        Returns:
            統計結果 {'evaluated': 5, 'bullish': 3, 'bearish': 2}
        """
        if not self._news_records_file.exists():
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
                # 注意：關鍵字權重更新由 NewsPredictionLoop.validate_pending_predictions()
                # 統一負責（含正確/錯誤追蹤），此處不重複更新以避免雙重計算。
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
    
    # ========================================
    # 新聞獲取方法
    # ========================================
    
    def _fetch_news(self, coin: str, cutoff: datetime) -> List[NewsArticle]:
        """獲取新聞"""
        articles = self._collect_articles(coin)
        recent_articles = self._filter_articles_by_time(articles, cutoff)
        unique_articles = self._deduplicate_articles(recent_articles)
        logger.info(f"✅ 獲取 {len(unique_articles)} 則 {coin} 新聞")
        return unique_articles

    def _collect_articles(self, coin: str) -> List[NewsArticle]:
        """聚合各來源新聞。"""
        articles: List[NewsArticle] = []
        articles.extend(self._fetch_from_cryptopanic(coin))
        articles.extend(self._fetch_from_rss(coin))
        return articles

    @staticmethod
    def _filter_articles_by_time(articles: List[NewsArticle], cutoff: datetime) -> List[NewsArticle]:
        """依時間窗過濾文章。"""
        return [article for article in articles if article.published_at >= cutoff]

    @staticmethod
    def _deduplicate_articles(articles: List[NewsArticle]) -> List[NewsArticle]:
        """對文章做標題級去重。"""
        seen_titles = set()
        unique_articles: List[NewsArticle] = []
        for article in sorted(articles, key=lambda item: item.published_at, reverse=True):
            title_key = article.title.lower()[:50]
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            unique_articles.append(article)
        return unique_articles
    
    def _fetch_from_cryptopanic(self, coin: str) -> List[NewsArticle]:
        """透過注入的 NewsDataFetcher 從 CryptoPanic API 獲取新聞"""
        if self._news_fetcher is None:
            logger.warning("_fetch_from_cryptopanic: NewsDataFetcher 不可用，跳過")
            return []

        raw_items = self._news_fetcher.fetch_cryptopanic(coin)
        articles: List[NewsArticle] = []
        for item in raw_items:
            try:
                articles.append(
                    NewsArticle(
                        title=item["title"],
                        source=item["source"],
                        url=item["url"],
                        published_at=item["published_at"],
                        summary=item["summary"],
                    )
                )
            except Exception:
                continue
        return articles

    def _fetch_from_rss(self, coin: str) -> List[NewsArticle]:
        """透過注入的 NewsDataFetcher 從 RSS Feeds 獲取新聞"""
        if self._news_fetcher is None:
            logger.warning("_fetch_from_rss: NewsDataFetcher 不可用，跳過")
            return []

        articles: List[NewsArticle] = []
        try:
            for feed_url in self._news_fetcher.rss_feeds:
                feed_articles = self._process_single_rss_feed(feed_url, coin)
                articles.extend(feed_articles)
        except Exception as e:
            logger.warning(f"RSS 獲取失敗: {e}")
        return articles

    def _process_single_rss_feed(self, feed_url: str, coin: str) -> List[NewsArticle]:
        """透過注入的 NewsDataFetcher 處理單個 RSS 源，並套用相關性過濾"""
        if self._news_fetcher is None:
            return []

        articles: List[NewsArticle] = []
        raw_items = self._news_fetcher.fetch_rss_feed(feed_url, coin)
        for item in raw_items:
            try:
                title_text = item["title"]
                desc_text = (item.get("summary") or "")[:200]
                full_text = f"{title_text} {desc_text}"
                matched_keywords = self._check_content_relevance(full_text, coin)
                if not matched_keywords:
                    continue
                articles.append(
                    NewsArticle(
                        title=title_text,
                        source=feed_url.split("/")[2] if "/" in feed_url else feed_url,
                        url=item.get("url", ""),
                        published_at=item["published_at"],
                        summary=desc_text,
                        keywords=matched_keywords,
                    )
                )
            except Exception as e:
                logger.debug(f"RSS 條目處理失敗: {e}")
        return articles
    
    def _check_content_relevance(self, full_text: str, coin: str) -> List[str]:
        """檢查內容相關性"""
        matched_keywords = []
        
        if KEYWORDS_AVAILABLE:
            matched_keywords = self._match_with_keywords(full_text)
            if matched_keywords:
                return matched_keywords
        
        return self._match_with_coin_keywords(full_text, coin)
    
    def _match_with_keywords(self, full_text: str) -> List[str]:
        """使用關鍵字系統匹配"""
        try:
            from ...analysis.keywords import MarketKeywords
            matches = MarketKeywords.find_matches(full_text)
            if matches:
                return [m.keyword for m in matches]
        except Exception as e:
            logger.debug(f"關鍵字匹配失敗: {e}")
        
        return []
    
    def _match_with_coin_keywords(self, full_text: str, coin: str) -> List[str]:
        """使用幣種關鍵字匹配"""
        coin_keywords = self.COIN_KEYWORDS.get(coin, [coin.lower()])
        matched = [kw for kw in coin_keywords if kw in full_text.lower()]
        return matched if matched else []

    # ========================================
    # 新聞分析方法
    # ========================================
    
    def _analyze_articles(self, symbol: str, articles: List[NewsArticle]) -> NewsAnalysisResult:
        """分析新聞文章"""
        target_coin = symbol.replace("USDT", "").replace("USD", "")
        
        if not articles:
            analysis_time = datetime.now()
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
                analysis_time=analysis_time,
                signal_valid_hours=0,
                signal_expires_at=analysis_time,
                signal_urgency="low",
                applicable_timeframes=[],
                articles=[]
            )
        
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        all_keywords = []
        key_events = set()
        
        # 獲取當前價格
        current_price = self._get_current_price(symbol)
        
        for article in articles:
            article.target_coin = target_coin
            
            # 情緒分析
            sentiment, score = self._analyze_sentiment(article.title + " " + article.summary)
            article.sentiment = sentiment
            article.sentiment_score = score
            
            if sentiment == "positive":
                positive_count += 1
            elif sentiment == "negative":
                negative_count += 1
            else:
                neutral_count += 1
            
            # 關鍵字提取
            keywords = self._extract_keywords(article.title)
            article.keywords = keywords
            all_keywords.extend(keywords)
            
            # 事件檢測
            events = self._detect_key_events(article.title)
            key_events.update(events)
            
            # 重要性評分
            article.importance_score = self._calculate_importance_score(article, target_coin)
            
            # 保存記錄
            if current_price > 0 and article.keywords:
                article.price_at_news = current_price
                self._save_news_record(article, current_price)
        
        # 按重要性排序
        articles.sort(key=lambda x: x.importance_score, reverse=True)
        
        # 計算加權情緒分數
        weighted_score = 0.0
        total_weight = 0.0
        for article in articles:
            weight = article.importance_score / 10.0
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
        
        # 最新標題
        recent_headlines = [
            a.title for a in sorted(articles, key=lambda x: x.published_at, reverse=True)[:5]
        ]
        
        # 生成建議
        recommendation = self._generate_recommendation(
            overall_sentiment, avg_score, list(key_events), positive_count, negative_count
        )
        analysis_time = datetime.now()
        signal_valid_hours, signal_urgency, applicable_timeframes = self._estimate_signal_validity(
            score=avg_score,
            key_events=list(key_events),
            articles=articles,
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
            analysis_time=analysis_time,
            signal_valid_hours=signal_valid_hours,
            signal_expires_at=analysis_time + timedelta(hours=signal_valid_hours),
            signal_urgency=signal_urgency,
            applicable_timeframes=applicable_timeframes,
            articles=sorted(articles, key=lambda x: x.published_at, reverse=True)
        )
    
    def _get_current_price(self, symbol: str) -> float:
        """獲取當前價格"""
        try:
            from config.trading_config import resolve_binance_testnet
            from ...data.binance_futures import BinanceFuturesConnector
            # 確保是完整交易對（如 BTCUSDT 而非 BTC）
            full_symbol = symbol if symbol.endswith("USDT") else symbol + "USDT"
            _testnet = resolve_binance_testnet(default=True)
            connector = BinanceFuturesConnector(testnet=_testnet)
            price_data = connector.get_ticker_price(full_symbol)
            if price_data:
                logger.info(f"獲取 {full_symbol} 當前價格: ${price_data.price:,.2f}")
                return price_data.price
        except Exception as e:
            logger.debug(f"無法獲取 {symbol} 價格: {e}")
        return 0.0
    
    def _analyze_sentiment(self, text: str) -> Tuple[str, float]:
        """情緒分析"""
        text_lower = text.lower()
        
        positive_score = 0.0
        negative_score = 0.0
        
        for keyword, weight in self.POSITIVE_KEYWORDS.items():
            if keyword in text_lower:
                positive_score += weight
        
        for keyword, weight in self.NEGATIVE_KEYWORDS.items():
            if keyword in text_lower:
                negative_score += weight
        
        total = positive_score + negative_score
        if total == 0:
            return "neutral", 0.0
        
        score = (positive_score - negative_score) / max(total, 1)
        score = max(-1.0, min(1.0, score))
        
        if score > 0.15:
            return "positive", score
        elif score < -0.15:
            return "negative", score
        else:
            return "neutral", score
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取關鍵字"""
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
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
            'where', 'why', 'how', 'all', 'each', 'every',
            'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'its', 'it', 'this', 'that', 'these', 'those', 'what'
        }
        
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        return keywords
    
    def _detect_key_events(self, text: str) -> List[str]:
        """檢測重要事件"""
        text_lower = text.lower()
        events = []
        
        for event_type, pattern in self.KEY_EVENT_PATTERNS.items():
            if re.search(pattern, text_lower, re.IGNORECASE):
                event_labels = {
                    'etf': '📈 ETF 相關',
                    'regulation': EVENT_REGULATION,
                    'hack': EVENT_SECURITY,
                    'partnership': '🤝 合作夥伴',
                    'upgrade': '⬆️ 技術升級',
                    'listing': '📝 上市/下市',
                    'whale': '🐋 大戶動向',
                    'halving': '⏳ 減半事件',
                }
                events.append(event_labels.get(event_type, event_type))
        
        return events
    
    def _detect_event_type(self, text: str) -> str:
        """檢測事件類型"""
        text_lower = text.lower()
        
        if KEYWORDS_AVAILABLE:
            event_type = self._detect_with_keywords(text)
            if event_type != 'general':
                return event_type
        
        return self._detect_with_regex(text_lower)
    
    def _detect_with_keywords(self, text: str) -> str:
        """使用關鍵字檢測事件類型"""
        try:
            from ...analysis.keywords import MarketKeywords
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
        """使用正則檢測事件類型"""
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
    
    def _calculate_time_score(self, hours_old: float) -> float:
        """計算時效性分數 (max 2.0)"""
        thresholds = [(1, 2.0), (4, 1.5), (12, 1.0), (24, 0.5)]
        for threshold, score in thresholds:
            if hours_old < threshold:
                return score
        return 0.2
    
    def _calculate_relevance_score(
        self, text_lower: str, target_coin: str
    ) -> float:
        """計算相關性分數 (max 2.0)"""
        coin_keywords = self.COIN_KEYWORDS.get(target_coin, [target_coin.lower()])
        
        if any(kw in text_lower for kw in coin_keywords):
            return 2.0
        if any(kw in text_lower for kw in ['crypto', 'bitcoin', 'cryptocurrency']):
            return 1.0
        return 0.3
    
    def _calculate_importance_score(self, article: NewsArticle, target_coin: str) -> float:
        """計算重要性評分 (0-10)"""
        score = 0.0
        
        # 1. 來源權威度 (max 2.0)
        source_domain = article.source.lower()
        source_score = self.SOURCE_AUTHORITY.get('default', 0.8)
        for domain, auth_score in self.SOURCE_AUTHORITY.items():
            if domain in source_domain:
                source_score = auth_score
                break
        score += source_score
        
        # 2. 事件重要性 (max 3.0)
        event_type = self._detect_event_type(article.title + " " + article.summary)
        article.category = event_type
        event_score = self.EVENT_IMPORTANCE.get(event_type, 0.5)
        score += event_score
        
        # 3. 時效性 (max 2.0)
        hours_old = (datetime.now() - article.published_at).total_seconds() / 3600
        time_score = self._calculate_time_score(hours_old)
        score += time_score
        
        # 4. 相關性 (max 2.0)
        text_lower = (article.title + " " + article.summary).lower()
        relevance_score = self._calculate_relevance_score(text_lower, target_coin)
        score += relevance_score
        article.relevance_score = relevance_score
        
        # 5. 情緒強度 (max 1.0)
        sentiment_intensity = abs(article.sentiment_score)
        intensity_score = min(sentiment_intensity * 1.5, 1.0)
        score += intensity_score
        
        # 6. 關鍵字系統加成 (max 3.0)
        if KEYWORDS_AVAILABLE:
            try:
                from ...analysis.keywords import MarketKeywords
                kw_score, _ = MarketKeywords.get_importance_score(
                    article.title + " " + article.summary
                )
                keyword_bonus = min(kw_score * 0.3, 3.0)
                score += keyword_bonus
                
                is_high_impact, high_kw = MarketKeywords.is_high_impact_news(article.title)
                if is_high_impact:
                    article.keywords = high_kw + article.keywords
            except Exception as e:
                logger.debug(f"關鍵字評分失敗: {e}")
        
        return round(min(score, 10.0), 2)
    
    def _generate_recommendation(
        self,
        sentiment: str,
        score: float,
        key_events: List[str],
        positive: int,
        negative: int
    ) -> str:
        """生成交易建議"""
        danger_events = [EVENT_SECURITY, EVENT_REGULATION]
        has_danger = any(e in key_events for e in danger_events)
        
        if has_danger:
            return "🚨 存在重大風險，建議暫停交易/觀望"
        
        if sentiment == "positive" and score > 0.4:
            return "🟢 強烈看漲信號，可考慮做多"
        elif sentiment == "positive":
            return "🟢 偏多信號，謹慎做多"
        elif sentiment == "negative" and score < -0.4:
            return "🔴 強烈看跌信號，建議觀望或做空"
        elif sentiment == "negative":
            return "🟡 偏空信號，謹慎操作"
        else:
            return "⚪ 中性市場，維持現有策略"

    def _estimate_signal_validity(
        self,
        score: float,
        key_events: List[str],
        articles: List[NewsArticle],
    ) -> Tuple[int, str, List[str]]:
        """估算新聞信號有效時間、緊急程度與適用時間框架。"""
        now = datetime.now()
        latest_published = max((article.published_at for article in articles), default=now)
        age_hours = max(0.0, (now - latest_published).total_seconds() / 3600)
        max_importance = max((article.importance_score for article in articles), default=0.0)
        has_danger = any(event in key_events for event in [EVENT_SECURITY, EVENT_REGULATION])

        if has_danger:
            base_hours = 6
            urgency = "high"
        elif abs(score) >= 0.45 or max_importance >= 8.5:
            base_hours = 12
            urgency = "high"
        elif abs(score) >= 0.25 or max_importance >= 7.0:
            base_hours = 24
            urgency = "medium"
        else:
            base_hours = 36
            urgency = "low"

        remaining_hours = max(1, int(round(max(1.0, base_hours - age_hours))))
        if remaining_hours <= 6:
            applicable_timeframes = ["5m", "15m", "1h"]
        elif remaining_hours <= 24:
            applicable_timeframes = ["15m", "1h", "4h"]
        else:
            applicable_timeframes = ["1h", "4h", "1d"]
        return remaining_hours, urgency, applicable_timeframes
    
    # ========================================
    # 新聞記錄與評估
    # ========================================
    
    def _save_news_record(self, article: NewsArticle, current_price: float) -> None:
        """保存新聞記錄"""
        try:
            news_id = hashlib.md5(
                f"{article.title}{article.published_at}".encode()
            ).hexdigest()[:16]
            
            record = {
                'news_id': news_id,
                'title': article.title,
                'url': article.url,
                'source': article.source,
                'keywords': article.keywords,
                'target_coin': article.target_coin,
                'symbol': article.target_coin + 'USDT',
                'timestamp': article.published_at.isoformat(),
                'price_at_news': current_price,
                'category': article.category,
                'sentiment': article.sentiment,
                'evaluated': False,
                'evaluation_window_hours': 24
            }
            
            records = []
            if os.path.exists(self._news_records_file):
                try:
                    with open(self._news_records_file, 'r', encoding='utf-8') as f:
                        records = json.load(f)
                except Exception:
                    records = []
            
            if not any(r['news_id'] == news_id for r in records):
                records.append(record)
                
                cutoff = (datetime.now() - timedelta(days=30)).isoformat()
                records = [r for r in records if r['timestamp'] > cutoff]
                
                with open(self._news_records_file, 'w', encoding='utf-8') as f:
                    json.dump(records, f, ensure_ascii=False, indent=2)
                    
                logger.debug(f"已保存新聞記錄: {news_id}")
        except Exception as e:
            logger.warning(f"保存新聞記錄失敗: {e}")
    
    def _evaluate_single_news(self, record: Dict) -> Optional[Dict]:
        """評估單則新聞"""
        try:
            raw_symbol = record.get('symbol') or (record['target_coin'] + 'USDT')
            # 確保是完整交易對
            symbol = raw_symbol if raw_symbol.endswith("USDT") else raw_symbol + "USDT"
            
            from config.trading_config import resolve_binance_testnet
            from ...data.binance_futures import BinanceFuturesConnector
            _testnet = resolve_binance_testnet(default=True)
            connector = BinanceFuturesConnector(testnet=_testnet)
            price_data = connector.get_ticker_price(symbol)

            if not price_data:
                logger.warning(f"無法獲取 {symbol} 當前價格")
                return None
            
            current_price = price_data.price
            old_price = record['price_at_news']
            price_change = ((current_price - old_price) / old_price) * 100
            
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
    
    def _calculate_weight_factor(self, direction: str, impact: str) -> float:
        """計算關鍵字權重調整因子"""
        is_directional = direction in ['bullish', 'bearish']
        
        factor_map = {
            'strong': (1.15, 0.85),
            'moderate': (1.08, 0.92),
        }
        
        if impact in factor_map:
            return factor_map[impact][0] if is_directional else factor_map[impact][1]
        return 0.95
    
    def _update_single_keyword(self, km: Any, kw: str, factor: float, result: Dict) -> None:
        """更新單個關鍵字權重"""
        direction = result['direction']

        if hasattr(km, 'record_and_verify_prediction'):
            km.record_and_verify_prediction(
                kw,
                direction,
                direction,
                price_before=result['old_price'],
                price_after=result['new_price'],
                adjustment_factor=factor,
                news_title=result.get('headline', ''),
            )
        elif hasattr(km, 'record_prediction'):
            km.record_prediction(kw, direction, result['old_price'])
    
    def _update_keyword_weights(self, keywords: List[str], result: Dict) -> None:
        """更新關鍵字權重"""
        if not KEYWORDS_AVAILABLE or get_keyword_manager is None:
            return
        
        try:
            direction = result['direction']
            impact = result['impact']
            factor = self._calculate_weight_factor(direction, impact)
            
            km = get_keyword_manager()
            if km is not None:
                enriched_result = {**result, 'headline': ', '.join(keywords[:3])}
                for kw in keywords:
                    self._update_single_keyword(km, kw, factor, enriched_result)
                
                logger.info(f"已更新 {len(keywords)} 個關鍵字權重 (factor={factor})")
        except Exception as e:
            logger.warning(f"更新關鍵字權重失敗: {e}")


# ========================================
# 單例管理
# ========================================

_news_analyzer: Optional[CryptoNewsAnalyzer] = None


def get_news_analyzer() -> CryptoNewsAnalyzer:
    """獲取新聞分析器單例"""
    global _news_analyzer
    if _news_analyzer is None:
        _news_analyzer = CryptoNewsAnalyzer()
    return _news_analyzer


# ========================================
# 主程式入口
# ========================================

if __name__ == "__main__":
    print("🚀 加密貨幣新聞分析器")
    print("=" * 60)
    
    analyzer = CryptoNewsAnalyzer()
    
    print("\n📰 分析 BTCUSDT 新聞...\n")
    
    result = analyzer.analyze_news("BTCUSDT", hours=24)
    
    print("📊 分析結果:")
    print(f"   新聞數量: {result.total_articles} 則")
    print(f"   正面: {result.positive_count} | 負面: {result.negative_count} | 中性: {result.neutral_count}")
    print(f"\n🎯 情緒: {result.overall_sentiment.upper()} (分數: {result.sentiment_score:+.3f})")
    
    if result.key_events:
        print("\n🔥 重要事件:")
        for event in result.key_events:
            print(f"   • {event}")
    
    if result.top_keywords:
        print("\n📌 熱門關鍵字:")
        for kw, count in result.top_keywords[:5]:
            print(f"   • {kw}: {count}")
    
    print(f"\n💡 建議: {result.recommendation}")
    
    print("\n" + "=" * 60)
    print("\n📋 快速摘要:\n")
    print(analyzer.get_quick_summary("BTCUSDT"))
    
    print("\n" + "=" * 60)
    can_trade, reason = analyzer.should_trade("BTCUSDT")
    trade_status = "✅ 可交易" if can_trade else "❌ 暫停交易"
    print(f"\n🤔 交易狀態: {trade_status}")
    print(f"   原因: {reason}")
