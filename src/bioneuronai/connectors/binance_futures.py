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
from typing import Dict, List, Optional, Callable
from collections import deque
from pathlib import Path

from ..data_models import MarketData, OrderResult

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
            self.rest_base = "https://testnet.binancefuture.com"
            self.ws_base = "wss://stream.binancefuture.com"
        else:
            self.rest_base = "https://fapi.binance.com"
            self.ws_base = "wss://fstream.binance.com"
        
        # WebSocket 管理
        self.ws_connections = {}
        self.ws_reconnect_delay = 5
        self.ws_max_reconnect_attempts = 10
        
        # API 限流控制
        self.request_timestamps = deque(maxlen=1200)
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
            return response.json()
            
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
            return MarketData(
                symbol=data['symbol'],
                price=float(data['price']),
                timestamp=int(time.time() * 1000)
            )
        return None
    
    def get_ticker_24hr(self, symbol: str = "BTCUSDT") -> Optional[Dict]:
        """獲取 24 小時行情統計"""
        return self._make_request("GET", "/fapi/v1/ticker/24hr", {"symbol": symbol})
    
    def get_account_info(self) -> Optional[Dict]:
        """獲取賬戶信息"""
        return self._make_request("GET", "/fapi/v2/account", signed=True)
    
    def get_exchange_info(self, symbol: str) -> Optional[Dict]:
        """獲取交易對信息"""
        data = self._make_request("GET", "/fapi/v1/exchangeInfo", {"symbol": symbol})
        
        if data and 'symbols' in data and len(data['symbols']) > 0:
            return data['symbols'][0]
        return None
    
    def format_quantity(self, symbol: str, quantity: float) -> str:
        """格式化數量"""
        if "BTC" in symbol:
            return f"{quantity:.3f}"
        return f"{quantity:.2f}"
    
    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Optional[OrderResult]:
        """下單"""
        if not self.api_key or not self.api_secret:
            logger.warning("未配置 API Key，無法下單")
            return None
        
        try:
            formatted_qty = self.format_quantity(symbol, quantity)
            
            params = {
                "symbol": symbol,
                "side": side,
                "type": order_type,
                "quantity": formatted_qty
            }
            
            if order_type == "LIMIT":
                if price is None:
                    raise ValueError("LIMIT 訂單必須指定價格")
                params['price'] = f"{price:.2f}"
                params['timeInForce'] = 'GTC'
            
            result = self._make_request("POST", "/fapi/v1/order", params, signed=True)
            
            if result:
                order_result = OrderResult(
                    order_id=result.get('orderId'),
                    symbol=symbol,
                    side=side,
                    quantity=quantity,
                    price=price,
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
                order_id=None,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                status="ERROR",
                error=str(e)
            )
    
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
            
            result = self._make_request("POST", "/fapi/v1/order", params, signed=True)
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
            
            result = self._make_request("POST", "/fapi/v1/order", params, signed=True)
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
                logger.warning(f"WebSocket 連接關閉")
                
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
            except:
                pass
        self.ws_connections.clear()