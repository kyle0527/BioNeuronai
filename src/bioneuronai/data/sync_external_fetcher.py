"""
同步外部市場數據抓取器
======================

職責：統一管理加密及傳統金融市場外部 HTTP 請求（同步版），
符合「外部 API 集中在 data/ 層」架構原則。

數據源：
1. Alternative.me    — 恐慌貪婪指數
2. Yahoo Finance     — 全球主要股市指數
3. Binance Spot API  — 現貨 24hr 行情（市場情緒）

此類別為同步版本，供 analysis/ 模組直接呼叫。
非同步版本（WebDataFetcher）供有事件迴圈的環境使用。

更新日期: 2026-04-13
"""

import logging
import requests
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_FEAR_GREED_URL = "https://api.alternative.me/fng/?limit=1"
_BINANCE_SPOT_TICKER_URL = "https://api.binance.com/api/v3/ticker/24hr"
_YAHOO_FINANCE_CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/"

# 全球主要股市指數清單
_GLOBAL_INDICES: Dict[str, str] = {
    "^GSPC":  "S&P 500",
    "^DJI":   "Dow Jones",
    "^IXIC":  "NASDAQ",
    "^FTSE":  "FTSE 100",
    "^GDAXI": "DAX",
    "^FCHI":  "CAC 40",
    "^N225":  "Nikkei 225",
    "^TPX":   "TOPIX",
}

# Binance Spot 情緒監控標的
_SPOT_SENTIMENT_SYMBOLS: List[str] = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]


class SyncExternalDataFetcher:
    """
    同步外部市場數據抓取器

    功能：
    - 取得加密貨幣恐慌貪婪指數
    - 取得全球股市指數（Yahoo Finance）
    - 取得 Binance 現貨 24hr 市場情緒

    失敗時均回傳 None 或空 dict，不拋出例外。

    使用範例：
        fetcher = SyncExternalDataFetcher()
        fng = fetcher.fetch_fear_greed_index()
        indices = fetcher.fetch_global_stock_indices()
        sentiment = fetcher.fetch_binance_spot_sentiment()
    """

    def __init__(self, request_timeout: int = 10) -> None:
        self.request_timeout = request_timeout
        self._user_agent = "Mozilla/5.0"

    # ──────────────────────────────────────────────────────
    # 恐慌貪婪指數
    # ──────────────────────────────────────────────────────

    def fetch_fear_greed_index(self) -> Optional[Dict]:
        """
        取得加密貨幣恐慌貪婪指數。

        數據源: Alternative.me（免費，無需 API Key）

        Returns:
            {value, classification, timestamp, time_until_update}
            失敗時回傳 None。
        """
        try:
            response = requests.get(_FEAR_GREED_URL, timeout=self.request_timeout)
            if response.status_code != 200:
                logger.warning(f"Fear & Greed API 回應 {response.status_code}")
                return None

            data = response.json()
            if "data" not in data or not data["data"]:
                logger.warning("Fear & Greed Index 數據格式錯誤")
                return None

            fng = data["data"][0]
            return {
                "value": int(fng["value"]),
                "classification": fng["value_classification"],
                "timestamp": fng["timestamp"],
                "time_until_update": fng.get("time_until_update"),
            }
        except Exception as exc:
            logger.error(f"獲取 Fear & Greed Index 失敗: {exc}")
            return None

    # ──────────────────────────────────────────────────────
    # 全球股市指數（Yahoo Finance）
    # ──────────────────────────────────────────────────────

    def fetch_global_stock_indices(
        self,
        indices: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict]:
        """
        取得全球主要股市指數（Yahoo Finance v8 chart API）。

        Args:
            indices: {symbol: display_name} 映射；若未提供則使用預設清單。

        Returns:
            {display_name: {symbol, price, previous_close, change_percent}}
            失敗或無資料時回傳 None。
        """
        target = indices or _GLOBAL_INDICES
        indices_data: Dict[str, Dict] = {}

        for symbol, name in target.items():
            try:
                url = f"{_YAHOO_FINANCE_CHART_URL}{symbol}?interval=1d&range=5d"
                response = requests.get(
                    url,
                    timeout=self.request_timeout,
                    headers={"User-Agent": self._user_agent},
                )
                response.raise_for_status()
                payload = response.json()

                chart = payload.get("chart", {})
                results = chart.get("result") or []
                if not results:
                    continue

                meta = results[0].get("meta", {})
                current_price: float = float(meta.get("regularMarketPrice", 0))
                previous_close: float = float(
                    meta.get("chartPreviousClose") or meta.get("previousClose") or 0
                )
                change_percent = (
                    (current_price - previous_close) / previous_close * 100
                    if previous_close > 0
                    else 0.0
                )
                indices_data[name] = {
                    "symbol": symbol,
                    "price": current_price,
                    "previous_close": previous_close,
                    "change_percent": round(change_percent, 2),
                }

            except Exception as exc:
                logger.warning(f"獲取 {name} ({symbol}) 數據失敗: {exc}")

        return indices_data if indices_data else None

    # ──────────────────────────────────────────────────────
    # Binance 現貨市場情緒
    # ──────────────────────────────────────────────────────

    def fetch_binance_spot_sentiment(
        self,
        symbols: Optional[List[str]] = None,
    ) -> Optional[Dict]:
        """
        取得 Binance 現貨 24hr Ticker 並計算市場情緒。

        Args:
            symbols: 要查詢的交易對清單；若未提供則使用 BTCUSDT / ETHUSDT / BNBUSDT。

        Returns:
            {
                symbols: {symbol: {price_change_pct, volume, quote_volume}},
                avg_change_pct: float,
                market_state: str,   # STRONG_BULLISH / BULLISH / NEUTRAL / BEARISH / STRONG_BEARISH
            }
            失敗或無資料時回傳 None。
        """
        target_symbols = symbols or _SPOT_SENTIMENT_SYMBOLS
        sentiment_data: Dict[str, Dict] = {}

        for symbol in target_symbols:
            try:
                response = requests.get(
                    _BINANCE_SPOT_TICKER_URL,
                    params={"symbol": symbol},
                    timeout=self.request_timeout,
                )
                if response.status_code != 200:
                    continue
                data = response.json()
                price_change_pct = float(data["priceChangePercent"])
                sentiment_data[symbol] = {
                    "price_change_pct": price_change_pct,
                    "volume": float(data["volume"]),
                    "quote_volume": float(data["quoteVolume"]),
                }
            except Exception as exc:
                logger.warning(f"獲取 {symbol} Binance Spot 情緒失敗: {exc}")

        if not sentiment_data:
            return None

        avg_change = (
            sum(d["price_change_pct"] for d in sentiment_data.values())
            / len(sentiment_data)
        )

        if avg_change > 5:
            market_state = "STRONG_BULLISH"
        elif avg_change > 2:
            market_state = "BULLISH"
        elif avg_change > -2:
            market_state = "NEUTRAL"
        elif avg_change > -5:
            market_state = "BEARISH"
        else:
            market_state = "STRONG_BEARISH"

        return {
            "symbols": sentiment_data,
            "avg_change_pct": round(avg_change, 2),
            "market_state": market_state,
        }
