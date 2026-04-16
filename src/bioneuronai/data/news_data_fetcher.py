"""
新聞數據抓取器（同步版）
========================

職責：統一管理新聞相關外部 HTTP 請求，符合「外部 API 集中在 data/ 層」架構原則。

數據源：
1. CryptoPanic API  — 加密貨幣新聞聚合器
2. RSS Feeds        — CoinTelegraph / Decrypt / CoinDesk

更新日期: 2026-04-13
"""

import logging
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# RSS 來源清單（可由外部傳入覆蓋）
DEFAULT_RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
]

_CRYPTOPANIC_BASE_URL = "https://cryptopanic.com/api/v1/posts/"


class NewsDataFetcher:
    """
    新聞數據抓取器（同步版）

    功能：
    - 從 CryptoPanic API 取得指定幣種的重要新聞
    - 從 RSS Feeds 取得最新加密貨幣新聞
    - 統一錯誤處理，失敗時回傳空列表（不拋出例外）

    使用範例：
        fetcher = NewsDataFetcher()
        articles = fetcher.fetch_cryptopanic("BTC")
        rss_items = fetcher.fetch_rss_feed("https://cointelegraph.com/rss", coin="BTC")
    """

    def __init__(
        self,
        cryptopanic_token: Optional[str] = None,
        request_timeout: int = 10,
        rss_feeds: Optional[List[str]] = None,
    ) -> None:
        """
        Args:
            cryptopanic_token: CryptoPanic API Token；若未提供則讀取
                               環境變數 CRYPTOPANIC_API_TOKEN（預設為 "free"）。
            request_timeout:   HTTP 請求超時秒數。
            rss_feeds:         RSS 來源 URL 清單；若未提供則使用預設清單。
        """
        self.cryptopanic_token: str = (
            cryptopanic_token
            or os.getenv("CRYPTOPANIC_API_TOKEN", "free")
        )
        self.request_timeout = request_timeout
        self.rss_feeds: List[str] = rss_feeds if rss_feeds is not None else DEFAULT_RSS_FEEDS

        if self.cryptopanic_token == "free":
            logger.warning(
                "⚠️ 使用 CryptoPanic 免費限制模式。"
                "請設置環境變數 CRYPTOPANIC_API_TOKEN 以獲得完整功能。"
            )

    # ──────────────────────────────────────────────────────
    # CryptoPanic
    # ──────────────────────────────────────────────────────

    def fetch_cryptopanic(self, coin: str) -> List[Dict]:
        """
        從 CryptoPanic API 取得指定幣種的重要新聞。

        Args:
            coin: 幣種符號，例如 "BTC"、"ETH"。

        Returns:
            List[Dict]，每個元素包含 title / source / url / published_at / summary。
            失敗時回傳空列表。
        """
        articles: List[Dict] = []
        params = {
            "auth_token": self.cryptopanic_token,
            "currencies": coin,
            "filter": "important",
            "public": "true",
        }
        try:
            response = requests.get(
                _CRYPTOPANIC_BASE_URL,
                params=params,
                timeout=self.request_timeout,
            )
            if response.status_code != 200:
                logger.warning(f"CryptoPanic API 回應 {response.status_code}，幣種: {coin}")
                return articles

            data = response.json()
            for item in data.get("results", [])[:20]:
                try:
                    pub_date_str: str = item.get("published_at", "")
                    pub_date = datetime.fromisoformat(
                        pub_date_str.replace("Z", "+00:00")
                    ).replace(tzinfo=None)
                    articles.append(
                        {
                            "title": item.get("title", ""),
                            "source": item.get("source", {}).get("title", "CryptoPanic"),
                            "url": item.get("url", ""),
                            "published_at": pub_date,
                            "summary": item.get("title", ""),
                        }
                    )
                except Exception:
                    continue

        except requests.Timeout:
            logger.warning("CryptoPanic API 請求超時")
        except requests.RequestException as exc:
            logger.warning(f"CryptoPanic API 請求失敗: {exc}")
        except Exception as exc:
            logger.warning(f"獲取 CryptoPanic 失敗: {exc}")

        return articles

    # ──────────────────────────────────────────────────────
    # RSS
    # ──────────────────────────────────────────────────────

    def fetch_rss_feed(self, feed_url: str, coin: str) -> List[Dict]:
        """
        從單個 RSS Feed 取得相關新聞。

        Args:
            feed_url: RSS Feed URL。
            coin:     用於過濾文章標題的幣種關鍵字（不區分大小寫）。

        Returns:
            List[Dict]，結構同 fetch_cryptopanic。失敗時回傳空列表。
        """
        articles: List[Dict] = []
        try:
            response = requests.get(feed_url, timeout=self.request_timeout)
            if response.status_code != 200:
                return articles

            root = ET.fromstring(response.content)
            coin_lower = coin.lower()

            for item in root.findall(".//item")[:20]:
                title_el = item.find("title")
                if title_el is None:
                    continue
                title_text = title_el.text or ""
                if coin_lower not in title_text.lower():
                    continue

                link_el = item.find("link")
                pub_date_el = item.find("pubDate")
                desc_el = item.find("description")

                url = link_el.text if link_el is not None else ""
                summary = desc_el.text if desc_el is not None else title_text

                pub_date: datetime
                if pub_date_el is not None and pub_date_el.text:
                    try:
                        from email.utils import parsedate_to_datetime
                        pub_date = parsedate_to_datetime(pub_date_el.text).replace(tzinfo=None)
                    except Exception:
                        pub_date = datetime.now()
                else:
                    pub_date = datetime.now()

                articles.append(
                    {
                        "title": title_text,
                        "source": feed_url,
                        "url": url or "",
                        "published_at": pub_date,
                        "summary": summary or title_text,
                    }
                )

        except Exception as exc:
            logger.debug(f"RSS 源 {feed_url} 處理失敗: {exc}")

        return articles

    def fetch_all_rss(self, coin: str) -> List[Dict]:
        """
        從所有預設（或初始化時傳入的）RSS 來源取得新聞。

        Args:
            coin: 幣種關鍵字，用於過濾。

        Returns:
            合併後的文章列表。
        """
        articles: List[Dict] = []
        for feed_url in self.rss_feeds:
            articles.extend(self.fetch_rss_feed(feed_url, coin))
        return articles
