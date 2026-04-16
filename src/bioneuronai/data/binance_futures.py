"""
Binance Futures API 連接器
專門處理與 Binance 的 API 交互
"""

import json
import time
import hmac
import hashlib
import requests
import websocket
import threading
import logging
from typing import Any, cast, Dict, List, Optional, Callable
from collections import deque
from dataclasses import dataclass
from datetime import datetime

# 遵循 CODE_FIX_GUIDE：直接從 schemas 套件導入，避免循環依賴
from schemas.market import MarketData

@dataclass
class OrderResult:
    """訂單結果數據模型"""
    symbol: str
    side: str
    order_type: str = "MARKET"
    quantity: float = 0.0
    price: float = 0.0
    status: str = "UNKNOWN"
    order_id: str = ""
    timestamp: Optional[datetime] = None
    error: str = ""  # 錯誤訊息

    def get(self, key: str, default: Any = None) -> Any:
        """兼容舊策略以 dict 方式讀取訂單結果。"""
        key_map = {
            "orderId": "order_id",
            "avgPrice": "price",
            "type": "order_type",
        }
        return getattr(self, key_map.get(key, key), default)

    def to_dict(self) -> Dict[str, Any]:
        """轉換為交易所風格字典格式。"""
        return {
            "symbol": self.symbol,
            "side": self.side,
            "type": self.order_type,
            "quantity": self.quantity,
            "price": self.price,
            "avgPrice": self.price,
            "status": self.status,
            "orderId": self.order_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "error": self.error,
        }

logger = logging.getLogger(__name__)


class BinanceFuturesConnector:
    """
    幣安期貨 API 連接器
    
    支持：
    - REST API 請求（下單、查詢）
    - WebSocket 實時數據流
    - 簽名認證
    - 自動重連機制
    - 速率限制控制
    """
    
    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        
        # API 基礎 URL
        if testnet:
            # Demo Trading 環境 (demo.binance.com)
            self.rest_base = "https://demo-fapi.binance.com"
            self.ws_base = "wss://fstream.binancefuture.com"
        else:
            # 主網（真實交易）
            self.rest_base = "https://fapi.binance.com"
            self.ws_base = "wss://fstream.binance.com"
        
        # WebSocket 管理
        self.ws_connections: Dict[str, Any] = {}
        self.ws_reconnect_delay = 5
        self.ws_max_reconnect_attempts = 10
        
        # API 限流控制
        self.request_timestamps: deque[float] = deque(maxlen=1200)
        self.weight_used = 0
        self.last_weight_reset = time.time()
        
        logger.info(f"初始化 Binance Futures Connector (Testnet={testnet})")
    
    def _check_rate_limit(self):
        """檢查並控制 API 請求速率"""
        current_time = time.time()
        
        # 重置權重計數器（每分鐘）
        if current_time - self.last_weight_reset > 60:
            self.weight_used = 0
            self.last_weight_reset = current_time
            self.request_timestamps.clear()
        
        # 記錄請求時間
        self.request_timestamps.append(current_time)
        
        # 檢查是否超過限制
        if len(self.request_timestamps) >= 1190:
            logger.warning("接近 API 速率限制，暫停 1 秒")
            time.sleep(1)
    
    def _sign_request(self, params: Dict) -> Dict:
        """生成 API 簽名"""
        params['timestamp'] = int(time.time() * 1000)
        
        if not self.api_secret:
            return params
        
        query_string = '&'.join([f"{k}={v}" for k, v in sorted(params.items())])
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        return params
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, signed: bool = False) -> Optional[Dict]:
        """統一的 API 請求處理"""
        try:
            self._check_rate_limit()
            
            url = f"{self.rest_base}{endpoint}"
            headers = {}
            
            if signed and self.api_key:
                params = self._sign_request(params or {})
                headers["X-MBX-APIKEY"] = self.api_key
            
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method.upper() == "POST":
                response = requests.post(url, params=params, headers=headers, timeout=10)
            else:
                raise ValueError(f"不支持的請求方法: {method}")
            
            response.raise_for_status()
            return cast(Optional[Dict[str, Any]], response.json())
            
        except requests.exceptions.Timeout:
            logger.error(f"請求超時: {endpoint}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP 錯誤: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"請求失敗: {e}")
            return None
        except Exception as e:
            logger.error(f"未預期錯誤: {e}")
            return None

    def _make_list_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[List[Dict]]:
        """統一的 API 請求處理（回傳 List 的端點）"""
        try:
            self._check_rate_limit()
            url = f"{self.rest_base}{endpoint}"
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            if isinstance(data, list):
                return cast(Optional[List[Dict[str, Any]]], data)
            return None
        except requests.exceptions.Timeout:
            logger.error(f"請求超時: {endpoint}")
            return None
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP 錯誤: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"請求失敗: {e}")
            return None
        except Exception as e:
            logger.error(f"未預期錯誤: {e}")
            return None
    
    def get_ticker_price(self, symbol: str = "BTCUSDT") -> Optional[MarketData]:
        """獲取最新價格"""
        data = self._make_request("GET", "/fapi/v1/ticker/price", {"symbol": symbol})
        
        if data:
            price = float(data['price'])
            return MarketData(
                symbol=data['symbol'],
                volume=0.0,
                timestamp=datetime.now(),
                high=price,
                low=price,
                open=price,
                close=price,
                bid=price,
                ask=price
            )
        return None
    
    def get_ticker_24hr(self, symbol: str = "BTCUSDT") -> Optional[Dict]:
        """獲取 24 小時行情統計"""
        return self._make_request("GET", "/fapi/v1/ticker/24hr", {"symbol": symbol})
    
    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 500, 
                   start_time: Optional[int] = None, end_time: Optional[int] = None) -> Optional[List[List]]:
        """
        獲取 K線/蠟燭圖數據
        
        參數:
            symbol: 交易對符號，例如 "BTCUSDT"
            interval: K線時間間隔 (1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M)
            limit: 返回的數據條數，默認 500，最大 1500
            start_time: 起始時間（毫秒時間戳）
            end_time: 結束時間（毫秒時間戳）
        
        返回:
            List[List]: K線數據列表，每個元素為 [openTime, open, high, low, close, volume, closeTime, ...]
        """
        params = {
            "symbol": symbol,
            "interval": interval,
            "limit": limit
        }
        
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        
        result = self._make_request("GET", "/fapi/v1/klines", params)
        # K線數據是列表格式，直接返回（如果是 dict 表示錯誤）
        if isinstance(result, list):
            return result
        return None
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Optional[Dict]:
        """
        獲取訂單簿/深度數據
        
        參數:
            symbol: 交易對符號，例如 "BTCUSDT"
            limit: 深度檔位數量，默認 100，可選值: 5, 10, 20, 50, 100, 500, 1000
        
        返回:
            Dict: 包含 bids (買單) 和 asks (賣單) 的訂單簿數據
            {
                "lastUpdateId": 1027024,
                "bids": [["price", "quantity"], ...],
                "asks": [["price", "quantity"], ...]
            }
        """
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        return self._make_request("GET", "/fapi/v1/depth", params)
    
    def get_funding_rate(self, symbol: str, limit: int = 1) -> Optional[List[Dict]]:
        """
        獲取資金費率歷史
        
        參數:
            symbol: 交易對符號，例如 "BTCUSDT"
            limit: 返回的數據條數，默認 1 (最新一筆)，最大 1000
        
        返回:
            List[Dict]: 資金費率數據列表
            [{
                "symbol": "BTCUSDT",
                "fundingRate": "0.00010000",
                "fundingTime": 1577433600000
            }, ...]
        """
        params = {
            "symbol": symbol,
            "limit": limit
        }
        
        result = self._make_request("GET", "/fapi/v1/fundingRate", params)
        # 資金費率數據是列表格式
        if isinstance(result, list):
            return result
        return None
    
    def get_book_ticker(self, symbol: str) -> Optional[Dict]:
        """取得最佳買賣價（即時買賣價差計算用）

        返回:
            {"symbol": "BTCUSDT", "bidPrice": "...", "bidQty": "...",
             "askPrice": "...", "askQty": "..."}
        """
        return self._make_request("GET", "/fapi/v1/bookTicker", {"symbol": symbol})

    def get_premium_index(self, symbol: str) -> Optional[Dict]:
        """取得即時資金費率與標記價格

        返回:
            {"symbol": "...", "markPrice": "...", "lastFundingRate": "...",
             "nextFundingTime": <ms timestamp>}

        注意：lastFundingRate 可能為負值（負費率時多單收入、空單付費）。
        """
        return self._make_request("GET", "/fapi/v1/premiumIndex", {"symbol": symbol})

    def get_funding_info(self, symbol: str) -> Optional[Dict]:
        """取得資金費率結算資訊，包含實際結算間隔小時數

        返回:
            {"symbol": "...", "fundingIntervalHours": 8,
             "adjustedFundingRateCap": "...", "adjustedFundingRateFloor": "..."}

        Binance 可能將特定幣對改為 4h 或其他間隔，需用此端點取得實際值。
        """
        return self._make_request("GET", "/fapi/v1/fundingInfo", {"symbol": symbol})

    def get_open_interest(self, symbol: str) -> Optional[Dict]:
        """
        獲取當前未平倉合約數（持倉量）
        
        參數:
            symbol: 交易對符號，例如 "BTCUSDT"
        
        返回:
            Dict: 持倉量數據
            {
                "openInterest": "10659.509",
                "symbol": "BTCUSDT",
                "time": 1589437530011
            }
        """
        params = {"symbol": symbol}
        
        return self._make_request("GET", "/fapi/v1/openInterest", params)
    
    def get_account_info(self) -> Optional[Dict]:
        """獲取賬戶信息"""
        return self._make_request("GET", "/fapi/v2/account", signed=True)
    
    def get_exchange_info(self, symbol: str) -> Optional[Dict]:
        """獲取單一交易對信息"""
        data = self._make_request("GET", "/fapi/v1/exchangeInfo", {"symbol": symbol})
        
        if data and 'symbols' in data and len(data['symbols']) > 0:
            return cast(Optional[Dict[str, Any]], data['symbols'][0])
        return None

    def get_all_exchange_info(self) -> Optional[Dict]:
        """獲取所有交易對的交易所信息（不帶 symbol 過濾）

        返回:
            完整的 /fapi/v1/exchangeInfo 回應，包含 "symbols" 陣列
        """
        return self._make_request("GET", "/fapi/v1/exchangeInfo")

    def get_all_tickers_24hr(self) -> Optional[List[Dict]]:
        """獲取所有交易對的 24 小時行情統計（不帶 symbol 過濾）

        返回:
            列表，每個元素為一個交易對的 24hr ticker 字典
        """
        return self._make_list_request("/fapi/v1/ticker/24hr")
    
    def format_quantity(self, symbol: str, quantity: float) -> str:
        """格式化數量"""
        if "BTC" in symbol:
            return f"{quantity:.3f}"
        return f"{quantity:.2f}"
    
    _ORDER_ENDPOINT = "/fapi/v1/order"

    def _build_order_params(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float],
        **kwargs: Any,
    ) -> Dict:
        """組裝下單參數（抽出以降低 place_order 認知複雜度）"""
        formatted_qty = self.format_quantity(symbol, quantity)
        params: Dict = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "quantity": formatted_qty,
        }
        stop_price = kwargs.get("stop_price")
        time_in_force = kwargs.get("time_in_force")
        if order_type == "LIMIT":
            if price is None:
                raise ValueError("LIMIT 訂單必須指定價格")
            params["price"] = f"{price:.2f}"
            params["timeInForce"] = time_in_force or "GTC"
        elif stop_price is not None:
            params["stopPrice"] = f"{float(stop_price):.2f}"
        return params

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        **kwargs: Any,
    ) -> Optional[OrderResult]:
        """下單"""
        if not self.api_key or not self.api_secret:
            logger.warning("未配置 API Key，無法下單")
            return None

        try:
            params = self._build_order_params(
                symbol, side, order_type, quantity, price, **kwargs
            )
            result = self._make_request("POST", self._ORDER_ENDPOINT, params, signed=True)
            
            if result:
                order_result = OrderResult(
                    order_id=str(result.get('orderId', '')),
                    symbol=symbol,
                    side=side,
                    order_type=order_type,
                    quantity=quantity,
                    price=float(result.get('avgPrice') or result.get('price') or price or 0.0),
                    status=result.get('status', 'UNKNOWN')
                )
                
                logger.info(f"✅ 訂單已提交: {side} {formatted_qty} {symbol}")
                
                # 處理止損止盈
                if stop_loss:
                    self._place_stop_loss_order(symbol, side, quantity, stop_loss)
                if take_profit:
                    self._place_take_profit_order(symbol, side, quantity, take_profit)
                
                return order_result
            
        except Exception as e:
            logger.error(f"❌ 下單失敗: {e}")
            return OrderResult(
                order_id="",
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price if price is not None else 0.0,
                status="ERROR",
                error=str(e)
            )
        
        return None
    
    def _place_stop_loss_order(self, symbol: str, original_side: str, quantity: float, stop_price: float):
        """下止損單"""
        try:
            side = "SELL" if original_side == "BUY" else "BUY"
            formatted_qty = self.format_quantity(symbol, quantity)
            
            params = {
                "symbol": symbol,
                "side": side,
                "type": "STOP_MARKET",
                "quantity": formatted_qty,
                "stopPrice": f"{stop_price:.2f}"
            }
            
            result = self._make_request("POST", self._ORDER_ENDPOINT, params, signed=True)
            if result:
                logger.info(f"🛡️ 止損單已設置: {stop_price:.2f}")
        except Exception as e:
            logger.error(f"設置止損失敗: {e}")
    
    def _place_take_profit_order(self, symbol: str, original_side: str, quantity: float, take_profit_price: float):
        """下止盈單"""
        try:
            side = "SELL" if original_side == "BUY" else "BUY"
            formatted_qty = self.format_quantity(symbol, quantity)
            
            params = {
                "symbol": symbol,
                "side": side,
                "type": "TAKE_PROFIT_MARKET",
                "quantity": formatted_qty,
                "stopPrice": f"{take_profit_price:.2f}"
            }
            
            result = self._make_request("POST", self._ORDER_ENDPOINT, params, signed=True)
            if result:
                logger.info(f"🎯 止盈單已設置: {take_profit_price:.2f}")
        except Exception as e:
            logger.error(f"設置止盈失敗: {e}")
    
    def subscribe_ticker_stream(self, symbol: str, callback: Callable, auto_reconnect: bool = True):
        """訂閱實時價格流"""
        try:
            stream = f"{symbol.lower()}@ticker"
            ws_url = f"{self.ws_base}/ws/{stream}"
            reconnect_attempts = 0
            
            def on_message(ws, message):
                try:
                    data = json.loads(message)
                    callback(data)
                except Exception as e:
                    logger.error(f"處理 WebSocket 消息失敗: {e}")
            
            def on_error(ws, error):
                logger.error(f"WebSocket 錯誤: {error}")
            
            def on_close(ws, close_status_code, close_msg):
                nonlocal reconnect_attempts
                logger.warning("WebSocket 連接關閉")
                
                if auto_reconnect and reconnect_attempts < self.ws_max_reconnect_attempts:
                    reconnect_attempts += 1
                    delay = self.ws_reconnect_delay * reconnect_attempts
                    logger.info(f"將在 {delay} 秒後重連")
                    time.sleep(delay)
                    self.subscribe_ticker_stream(symbol, callback, auto_reconnect)
            
            def on_open(ws):
                nonlocal reconnect_attempts
                reconnect_attempts = 0
                logger.info(f"WebSocket 已連接: {stream}")
            
            ws = websocket.WebSocketApp(
                ws_url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            
            self.ws_connections[symbol] = ws
            
            wst = threading.Thread(target=ws.run_forever, kwargs={'ping_interval': 30, 'ping_timeout': 10})
            wst.daemon = True
            wst.start()
            
            return ws
            
        except Exception as e:
            logger.error(f"WebSocket 連接失敗: {e}")
            return None
    
    def close_all_connections(self):
        """關閉所有 WebSocket 連接"""
        for symbol, ws in self.ws_connections.items():
            try:
                ws.close()
                logger.info(f"關閉 {symbol} 連接")
            except Exception:
                pass
        self.ws_connections.clear()
