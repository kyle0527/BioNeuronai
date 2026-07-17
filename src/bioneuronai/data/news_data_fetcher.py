"""同步新聞資料抓取器。

新聞資料的正式入口固定為兩個，且兩者都是戰略層的新鮮資料必要條件：

* CoinDesk RSS：幣圈新聞；
* Google News RSS：全球總經、地緣政治與金融事件（固定 `en-US`、`zh-TW` 查詢）。

這個模組只負責抓取與正規化文章。它不把事件預先判成多或空，也不在
來源失敗時以其他來源、空清單或舊資料偽裝成一次新的成功抓取。
"""

from __future__ import annotations

import html
import logging
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)

COINDESK_RSS_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"
GOOGLE_NEWS_MACRO_EN_RSS_URL = (
    "https://news.google.com/rss/search?"
    "q=(Federal%20Reserve%20OR%20ECB%20OR%20inflation%20OR%20recession%20"
    "OR%20war%20OR%20geopolitical%20OR%20economic%20data)"
    "&hl=en-US&gl=US&ceid=US:en"
)
GOOGLE_NEWS_MACRO_ZH_RSS_URL = (
    "https://news.google.com/rss/search?"
    "q=(%E8%81%AF%E6%BA%96%E6%9C%83%20OR%20%E6%AD%90%E6%B4%B2%E5%A4%AE%E8%A1%8C%20"
    "OR%20%E9%80%9A%E8%86%A8%20OR%20%E7%B6%93%E6%BF%9F%E8%A1%B0%E9%80%80%20OR%20"
    "%E6%88%B0%E7%88%AD%20OR%20%E5%9C%B0%E7%B7%A3%E6%94%BF%E6%B2%BB%20OR%20"
    "%E7%B6%93%E6%BF%9F%E6%95%B8%E6%93%9A)"
    "&hl=zh-TW&gl=TW&ceid=TW:zh-Hant"
)


class NewsSourceUnavailableError(RuntimeError):
    """其中一個正式新聞來源無法取得或解析時拋出。"""


class NewsDataFetcher:
    """集中處理兩個正式 RSS 來源的 HTTP 請求。"""

    def __init__(
        self,
        request_timeout: int = 10,
        coindesk_url: str = COINDESK_RSS_URL,
        google_news_macro_en_url: str = GOOGLE_NEWS_MACRO_EN_RSS_URL,
        google_news_macro_zh_url: str = GOOGLE_NEWS_MACRO_ZH_RSS_URL,
    ) -> None:
        self.request_timeout = request_timeout
        self.coindesk_url = coindesk_url
        self.google_news_macro_en_url = google_news_macro_en_url
        self.google_news_macro_zh_url = google_news_macro_zh_url

    def fetch_strategic_news(self) -> List[Dict[str, Any]]:
        """取得一次完整戰略新聞快照。

        CoinDesk 與 Google News 各自是必要來源。任一來源 HTTP、XML 或文章
        結構異常都會明確拋出例外；呼叫端不得把它轉成「本輪沒有新聞」。
        """
        crypto_articles = self._fetch_required_feed(
            source_id="coindesk",
            feed_url=self.coindesk_url,
            source_scope="crypto",
            language="en",
        )
        macro_english_articles = self._fetch_required_feed(
            source_id="google_news_macro",
            feed_url=self.google_news_macro_en_url,
            source_scope="macro",
            language="en",
        )
        macro_chinese_articles = self._fetch_required_feed(
            source_id="google_news_macro",
            feed_url=self.google_news_macro_zh_url,
            source_scope="macro",
            language="zh",
        )
        return self._deduplicate(crypto_articles + macro_english_articles + macro_chinese_articles)

    def _fetch_required_feed(
        self,
        source_id: str,
        feed_url: str,
        source_scope: str,
        language: str,
    ) -> List[Dict[str, Any]]:
        try:
            response = requests.get(
                feed_url,
                timeout=self.request_timeout,
                headers={"User-Agent": "BioNeuronai/1.0 (+news-analysis)"},
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise NewsSourceUnavailableError(
                f"正式新聞來源 {source_id} 無法取得：{exc}"
            ) from exc

        try:
            root = ET.fromstring(response.content)
        except ET.ParseError as exc:
            raise NewsSourceUnavailableError(
                f"正式新聞來源 {source_id} 回傳的 RSS 無法解析：{exc}"
            ) from exc

        articles = self._parse_rss_items(root, source_id, source_scope, language)
        if not articles:
            raise NewsSourceUnavailableError(
                f"正式新聞來源 {source_id} 未提供可用文章；不以空結果降級。"
            )
        return articles

    @staticmethod
    def _parse_rss_items(
        root: ET.Element,
        source_id: str,
        source_scope: str,
        language: str,
    ) -> List[Dict[str, Any]]:
        articles: List[Dict[str, Any]] = []
        for item in root.findall(".//item"):
            title = NewsDataFetcher._text(item.find("title"))
            link = NewsDataFetcher._text(item.find("link"))
            if not title or not link:
                continue

            publisher = NewsDataFetcher._text(item.find("source")) or source_id
            summary = NewsDataFetcher._clean_html(
                NewsDataFetcher._text(item.find("description"))
            )
            published_at = NewsDataFetcher._parse_published_at(
                NewsDataFetcher._text(item.find("pubDate"))
            )
            articles.append(
                {
                    "title": NewsDataFetcher._clean_html(title),
                    "source": publisher,
                    "source_id": source_id,
                    "source_scope": source_scope,
                    "language": language,
                    "url": link,
                    "published_at": published_at,
                    "summary": summary or NewsDataFetcher._clean_html(title),
                }
            )
        return articles

    @staticmethod
    def _text(element: Optional[ET.Element]) -> str:
        return element.text.strip() if element is not None and element.text else ""

    @staticmethod
    def _clean_html(value: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(value))).strip()

    @staticmethod
    def _parse_published_at(value: str) -> datetime:
        if not value:
            return datetime.now()
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is not None:
                parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
            return parsed
        except (TypeError, ValueError):
            logger.warning("RSS 文章缺少可解析發布時間，改以目前時間記錄：%s", value)
            return datetime.now()

    @staticmethod
    def _deduplicate(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen: set[str] = set()
        result: List[Dict[str, Any]] = []
        for article in sorted(articles, key=lambda item: item["published_at"], reverse=True):
            key = article["url"].strip().casefold() or article["title"].strip().casefold()
            if key in seen:
                continue
            seen.add(key)
            result.append(article)
        return result
