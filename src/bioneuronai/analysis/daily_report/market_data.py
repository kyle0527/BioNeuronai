"""
市場數據收集器
==============

負責收集全球市場數據：
1. 全球股市指數 (Yahoo Finance)
2. 加密貨幣恐慌貪婪指數
3. Binance 市場情緒
4. 經濟日曆事件

遵循 CODE_FIX_GUIDE.md 規範
"""

# 1. 標準庫
import logging
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any

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
            logger.error(f"獲取全球市場數據失敗: {e}")
            return None
    
    def check_economic_calendar(self) -> List[str]:
        """
        檢查經濟日曆
        
        Returns:
            重要經濟事件列表
        """
        try:
            # 未實現：需要整合經濟日曆 API
            # 可選方案: Investing.com, TradingEconomics, FRED
            logger.warning("經濟日曆功能未實現，返回空列表")
            return []
        except Exception as e:
            logger.error(f"檢查經濟日曆失敗: {e}")
            return []
    
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
                        previous_close = meta.get('previousClose', 0)
                        
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
