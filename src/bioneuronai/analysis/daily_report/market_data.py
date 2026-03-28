"""
市場數據收集器
==============

負責收集全球市場數據：
1. 全球股市指數 (Yahoo Finance)
2. 加密貨幣恐慌貪婪指數
3. Binance 市場情緒
4. 經濟日曆事件（Binance 資金費率、季度交割、FOMC）

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

# Binance Futures REST API 根路徑（無需 API Key 的公開端點）
_BINANCE_FUTURES_API = "https://fapi.binance.com"

# FOMC 2026 利率決議日期（美聯儲官方公告排程，非 mock 資料）
# 來源：Federal Reserve FOMC meeting calendar 2026
_FOMC_DATES_2026: List[datetime] = [
    datetime(2026, 1, 28, 19, 0, 0, tzinfo=timezone.utc),
    datetime(2026, 3, 18, 18, 0, 0, tzinfo=timezone.utc),
    datetime(2026, 4, 29, 18, 0, 0, tzinfo=timezone.utc),
    datetime(2026, 6, 10, 18, 0, 0, tzinfo=timezone.utc),
    datetime(2026, 7, 29, 18, 0, 0, tzinfo=timezone.utc),
    datetime(2026, 9, 16, 18, 0, 0, tzinfo=timezone.utc),
    datetime(2026, 10, 28, 18, 0, 0, tzinfo=timezone.utc),
    datetime(2026, 12, 9, 19, 0, 0, tzinfo=timezone.utc),
]

# 查詢資金費率的主要永續合約
_FUNDING_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT"]

# 季度合約類型
_QUARTERLY_CONTRACT_TYPES = {"CURRENT_QUARTER", "NEXT_QUARTER"}

logger = logging.getLogger(__name__)


class MarketDataCollector:
    """
    市場數據收集器
    
    功能：
    - 獲取全球股市指數
    - 分析市場趨勢
    - 獲取加密貨幣情緒指標
    """
    
    def __init__(self):
        self.request_timeout = 10
        self.user_agent = 'Mozilla/5.0'
    
    # ========================================
    # 主要接口
    # ========================================
    
    def get_global_market_data(self) -> Optional[Dict]:
        """
        獲取全球市場數據
        
        Returns:
            包含全球股市、加密貨幣情緒的綜合數據
        """
        try:
            # 收集各模塊數據
            global_indices = self._get_global_stock_indices()
            fng_data = self._get_fear_greed_index()
            market_sentiment = self._get_binance_market_sentiment()
            
            # 分析全球股市趨勢
            stock_analysis = self._analyze_global_stock_trends(global_indices)
            
            # 分析加密貨幣綜合情緒
            crypto_analysis = self._analyze_crypto_sentiment(fng_data, market_sentiment)
            
            # 構建完整市場數據
            return self._build_market_data_response(
                global_indices, stock_analysis, crypto_analysis, fng_data, market_sentiment
            )
            
        except Exception as e:
            raise RuntimeError(f"獲取全球市場數據失敗: {e}") from e
    
    def check_economic_calendar(self) -> List[str]:
        """
        檢查經濟日曆

        整合三個事件來源（依優先級排序）：
        1. Binance 永續合約資金費率結算（即時 API，無需 Key）
        2. Binance 季度合約交割日期（即時 API，無需 Key）
        3. FOMC 利率決議（美聯儲官方公告排程）

        Returns:
            重要事件描述列表，每項為可讀字串
        """
        events: List[str] = []

        funding_events = self._get_binance_funding_events()
        events.extend(funding_events)
        logger.info(f"   ✓ Binance 資金費率事件: {len(funding_events)} 項")

        delivery_events = self._get_binance_delivery_events()
        events.extend(delivery_events)
        logger.info(f"   ✓ Binance 季度交割事件: {len(delivery_events)} 項")

        macro_events = self._get_macro_events()
        events.extend(macro_events)
        logger.info(f"   ✓ 總體經濟事件: {len(macro_events)} 項")

        return events

    def _get_binance_funding_events(self) -> List[str]:
        """
        從 Binance 永續合約 API 取得下次資金費率結算時間與預估費率。

        端點：GET /fapi/v1/premiumIndex（公開，無需 API Key）

        Returns:
            事件描述列表
        """
        events: List[str] = []
        now_utc = datetime.now(tz=timezone.utc)

        for symbol in _FUNDING_SYMBOLS:
            try:
                url = f"{_BINANCE_FUTURES_API}/fapi/v1/premiumIndex?symbol={symbol}"
                response = requests.get(
                    url,
                    timeout=self.request_timeout,
                    headers={"User-Agent": self.user_agent},
                )
                response.raise_for_status()
                data = response.json()

                next_funding_ms: int = int(data.get("nextFundingTime", 0))
                last_rate: float = float(data.get("lastFundingRate", 0.0)) * 100

                if next_funding_ms <= 0:
                    continue

                next_time = datetime.fromtimestamp(next_funding_ms / 1000, tz=timezone.utc)
                delta_min = int((next_time - now_utc).total_seconds() / 60)

                if delta_min < 0:
                    continue  # 已結算，跳過

                direction = "+" if last_rate >= 0 else ""
                payer = "多方付空方" if last_rate >= 0 else "空方付多方"
                events.append(
                    f"【資金費率】{symbol} | 下次結算: {next_time.strftime('%H:%M UTC')}"
                    f"（約 {delta_min} 分鐘後）| 費率: {direction}{last_rate:.4f}% | {payer}"
                )
            except Exception as e:
                logger.warning(f"獲取 {symbol} 資金費率失敗: {e}")

        return events

    def _get_binance_delivery_events(self) -> List[str]:
        """
        從 Binance 合約交易所資訊取得季度合約交割日期。

        端點：GET /fapi/v1/exchangeInfo（公開，無需 API Key）
        過濾條件：contractType in {CURRENT_QUARTER, NEXT_QUARTER} and status == TRADING

        Returns:
            事件描述列表（僅顯示 90 天內的交割）
        """
        events: List[str] = []
        now_utc = datetime.now(tz=timezone.utc)

        try:
            url = f"{_BINANCE_FUTURES_API}/fapi/v1/exchangeInfo"
            response = requests.get(
                url,
                timeout=self.request_timeout,
                headers={"User-Agent": self.user_agent},
            )
            response.raise_for_status()
            data = response.json()

            for sym_info in data.get("symbols", []):
                contract_type: str = sym_info.get("contractType", "")
                status: str = sym_info.get("status", "")

                if contract_type not in _QUARTERLY_CONTRACT_TYPES or status != "TRADING":
                    continue

                delivery_ms: int = int(sym_info.get("deliveryDate", 0))
                symbol: str = sym_info.get("symbol", "")

                if delivery_ms <= 0:
                    continue

                delivery_time = datetime.fromtimestamp(delivery_ms / 1000, tz=timezone.utc)
                days_until = (delivery_time - now_utc).days

                if days_until < 0 or days_until > 90:
                    continue

                label = "今日" if days_until == 0 else f"距今 {days_until} 天"
                events.append(
                    f"【季度交割】{symbol} | 交割: {delivery_time.strftime('%Y-%m-%d %H:%M UTC')}"
                    f"（{label}）| 類型: {contract_type}"
                )

        except Exception as e:
            logger.warning(f"獲取 Binance 季度合約交割事件失敗: {e}")

        return events

    def _get_macro_events(self) -> List[str]:
        """
        返回 14 天視窗內的總體經濟重大事件。

        資料來源：美聯儲官方公告之 FOMC 2026 會議排程（非 mock 資料）。
        BTC/ETH 對 FOMC 決議歷史上有顯著的當日波動反應。

        Returns:
            事件描述列表
        """
        events: List[str] = []
        now_utc = datetime.now(tz=timezone.utc)
        window_days_before = 1   # 顯示 1 天前的事件（仍有餘波）
        window_days_after = 14   # 顯示 14 天內的即將事件

        for fomc_dt in _FOMC_DATES_2026:
            days_delta = (fomc_dt - now_utc).days

            if days_delta < -window_days_before or days_delta > window_days_after:
                continue

            if days_delta < 0:
                timing_label = f"{abs(days_delta)} 天前（仍有餘波影響）"
            elif days_delta == 0:
                timing_label = "今日（市場高度警戒）"
            elif days_delta == 1:
                timing_label = "明日（提前佈局期）"
            else:
                timing_label = f"距今 {days_delta} 天"

            events.append(
                f"【總體經濟】FOMC 利率決議 {fomc_dt.strftime('%Y-%m-%d %H:%M UTC')}"
                f"（{timing_label}）| 影響: 高 | BTC/ETH 通常出現大幅波動"
            )

        return events
    
    # ========================================
    # 股市數據
    # ========================================
    
    def _get_global_stock_indices(self) -> Optional[Dict]:
        """
        獲取全球主要股市指數 (美股、歐股、日股)
        
        使用 Yahoo Finance API
        """
        try:
            symbols = {
                # 美股
                '^GSPC': 'S&P 500',
                '^DJI': 'Dow Jones',
                '^IXIC': 'NASDAQ',
                # 歐股
                '^FTSE': 'FTSE 100',
                '^GDAXI': 'DAX',
                '^FCHI': 'CAC 40',
                # 日股
                '^N225': 'Nikkei 225',
                '^TPX': 'TOPIX'
            }
            
            indices_data = {}
            base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
            
            for symbol, name in symbols.items():
                try:
                    url = f"{base_url}{symbol}?interval=1d&range=5d"
                    response = requests.get(
                        url, 
                        timeout=self.request_timeout,
                        headers={'User-Agent': self.user_agent}
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    if 'chart' in data and 'result' in data['chart'] and len(data['chart']['result']) > 0:
                        result = data['chart']['result'][0]
                        meta = result.get('meta', {})
                        
                        current_price = meta.get('regularMarketPrice', 0)
                        # Yahoo Finance v8 chart API 使用 chartPreviousClose（非 previousClose）
                        previous_close = meta.get('chartPreviousClose') or meta.get('previousClose', 0)

                        # 計算漲跌幅
                        change_percent = 0
                        if previous_close > 0:
                            change_percent = ((current_price - previous_close) / previous_close) * 100
                        
                        indices_data[name] = {
                            'symbol': symbol,
                            'price': current_price,
                            'previous_close': previous_close,
                            'change_percent': round(change_percent, 2)
                        }
                except Exception as e:
                    logger.warning(f"獲取 {name} 數據失敗: {e}")
            
            return indices_data if indices_data else None
            
        except Exception as e:
            logger.error(f"獲取全球股市指數失敗: {e}")
            return None
    
    def _analyze_global_stock_trends(self, global_indices: Optional[Dict]) -> Dict[str, Any]:
        """分析全球股市趨勢"""
        if not global_indices:
            return {
                'global_stock_trend': "NEUTRAL",
                'global_stock_avg_change': 0,
                'us_markets': "NEUTRAL",
                'european_markets': "NEUTRAL",
                'asian_markets': "NEUTRAL"
            }
        
        # 計算全球平均變化
        changes = [data['change_percent'] for data in global_indices.values()]
        global_stock_avg_change = sum(changes) / len(changes) if changes else 0
        
        # 判斷全球趨勢
        global_trend = self._classify_market_trend(global_stock_avg_change)
        
        # 分析各區域市場
        us_markets = self._analyze_regional_market(
            global_indices, ['S&P 500', 'Dow Jones', 'NASDAQ']
        )
        european_markets = self._analyze_regional_market(
            global_indices, ['FTSE 100', 'DAX', 'CAC 40']
        )
        asian_markets = self._analyze_regional_market(
            global_indices, ['Nikkei 225', 'TOPIX']
        )
        
        return {
            'global_stock_trend': global_trend,
            'global_stock_avg_change': round(global_stock_avg_change, 2),
            'us_markets': us_markets,
            'european_markets': european_markets,
            'asian_markets': asian_markets
        }
    
    def _classify_market_trend(self, avg_change: float) -> str:
        """分類市場趨勢"""
        if avg_change >= 1.0:
            return "STRONG_BULLISH"
        elif avg_change >= 0.3:
            return "BULLISH"
        elif avg_change >= -0.3:
            return "NEUTRAL"
        elif avg_change >= -1.0:
            return "BEARISH"
        else:
            return "STRONG_BEARISH"
    
    def _analyze_regional_market(
        self, 
        global_indices: Dict, 
        market_names: List[str]
    ) -> str:
        """分析區域市場趨勢"""
        changes = [
            global_indices[name]['change_percent']
            for name in market_names
            if name in global_indices
        ]
        
        if not changes:
            return "NEUTRAL"
        
        avg = sum(changes) / len(changes)
        if avg > 0.3:
            return "BULLISH"
        elif avg < -0.3:
            return "BEARISH"
        return "NEUTRAL"
    
    # ========================================
    # 加密貨幣情緒
    # ========================================
    
    def _get_fear_greed_index(self) -> Optional[Dict]:
        """獲取加密貨幣恐慌貪婪指數"""
        try:
            url = "https://api.alternative.me/fng/?limit=1"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if 'data' in data and len(data['data']) > 0:
                    fng = data['data'][0]
                    return {
                        'value': int(fng['value']),
                        'classification': fng['value_classification'],
                        'timestamp': fng['timestamp'],
                        'time_until_update': fng.get('time_until_update')
                    }
            
            logger.warning("Fear & Greed Index API 返回異常")
            return None
        except Exception as e:
            logger.error(f"獲取 Fear & Greed Index 失敗: {e}")
            return None
    
    def _get_binance_market_sentiment(self) -> Optional[Dict]:
        """從 Binance 24hr Ticker 獲取市場情緒"""
        try:
            symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
            sentiment_data = {}
            
            for symbol in symbols:
                url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
                response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    data = response.json()
                    price_change_pct = float(data['priceChangePercent'])
                    sentiment_data[symbol] = {
                        'price_change_pct': price_change_pct,
                        'volume': float(data['volume']),
                        'quote_volume': float(data['quoteVolume'])
                    }
            
            if not sentiment_data:
                return None
            
            # 計算平均漲跌幅
            avg_change = sum(d['price_change_pct'] for d in sentiment_data.values()) / len(sentiment_data)
            
            # 判斷市場情緒
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
                'symbols': sentiment_data,
                'avg_change_pct': round(avg_change, 2),
                'market_state': market_state
            }
        except Exception as e:
            logger.error(f"獲取 Binance 市場情緒失敗: {e}")
            return None
    
    def _analyze_crypto_sentiment(
        self,
        fng_data: Optional[Dict],
        market_sentiment: Optional[Dict]
    ) -> Dict[str, Any]:
        """分析加密貨幣綜合情緒"""
        if not (fng_data and market_sentiment):
            return {
                'crypto_sentiment': "NEUTRAL",
                'crypto_sentiment_score': 50
            }
        
        # Fear & Greed Index (0-100)
        fng_score = fng_data['value']
        
        # Binance sentiment mapping
        sentiment_map = {
            'STRONG_BULLISH': 85,
            'BULLISH': 65,
            'NEUTRAL': 50,
            'BEARISH': 35,
            'STRONG_BEARISH': 15
        }
        binance_score = sentiment_map.get(market_sentiment['market_state'], 50)
        
        # 計算加權平均 (Fear & Greed 60%, Binance 40%)
        crypto_sentiment_score = int(fng_score * 0.6 + binance_score * 0.4)
        
        # 決定綜合情緒
        crypto_sentiment = self._classify_crypto_sentiment(crypto_sentiment_score)
        
        return {
            'crypto_sentiment': crypto_sentiment,
            'crypto_sentiment_score': crypto_sentiment_score
        }
    
    def _classify_crypto_sentiment(self, score: int) -> str:
        """分類加密貨幣情緒"""
        if score >= 70:
            return "STRONG_BULLISH"
        elif score >= 55:
            return "BULLISH"
        elif score >= 45:
            return "NEUTRAL"
        elif score >= 30:
            return "BEARISH"
        else:
            return "STRONG_BEARISH"
    
    # ========================================
    # 數據整合
    # ========================================
    
    def _build_market_data_response(
        self,
        global_indices: Optional[Dict],
        stock_analysis: Dict[str, Any],
        crypto_analysis: Dict[str, Any],
        fng_data: Optional[Dict],
        market_sentiment: Optional[Dict]
    ) -> Dict:
        """構建市場數據響應"""
        return {
            # 全球股市指數
            'global_stock_indices': global_indices,
            'global_stock_trend': stock_analysis['global_stock_trend'],
            'global_stock_avg_change': stock_analysis['global_stock_avg_change'],
            'us_futures': stock_analysis['us_markets'],
            'european_markets': stock_analysis['european_markets'],
            'asian_markets': stock_analysis['asian_markets'],
            
            # 加密貨幣市場
            'crypto_sentiment': crypto_analysis['crypto_sentiment'],
            'crypto_sentiment_score': crypto_analysis['crypto_sentiment_score'],
            'crypto_fear_greed': fng_data,
            'binance_sentiment': market_sentiment,
            
            # 綜合評估
            'overall_sentiment': (
                stock_analysis['global_stock_trend'] 
                if global_indices 
                else crypto_analysis['crypto_sentiment']
            ),
            'sentiment_score': (
                stock_analysis['global_stock_avg_change'] 
                if global_indices 
                else (crypto_analysis['crypto_sentiment_score'] - 50) / 50
            ),
            'data_source': 'Yahoo Finance + Fear & Greed Index + Binance 24hr Ticker',
            'last_update': datetime.now().isoformat()
        }
