"""
Mock Binance Connector - 接口偽裝
================================

完全模擬 BinanceFuturesConnector 的所有方法接口
讓 TradingEngine 無需修改任何代碼即可切換到回測模式

設計原則：
1. 接口完全一致：所有方法簽名與真實 Connector 相同
2. 返回格式相同：數據結構模擬 Binance API 響應
3. 狀態一致性：內部維護虛擬帳戶狀態
4. 無縫切換：只需替換連接器實例
"""

import logging
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any, Union, Generator
from datetime import datetime
from dataclasses import dataclass

from .data_stream import HistoricalDataStream, KlineBar
from .virtual_account import VirtualAccount, OrderStatus

try:
    from bioneuronai.trading_strategies import MarketData
    from bioneuronai.data.binance_futures import OrderResult
except ImportError:
    # 備用定義
    @dataclass
    class MarketData:  # type: ignore[no-redef]
        symbol: str
        price: float
        volume: float
        timestamp: datetime
        high: float
        low: float
        open: float
        close: float
        bid: float
        ask: float
        funding_rate: float = 0.0
        open_interest: float = 0.0
    
    @dataclass
    class OrderResult:  # type: ignore[no-redef]
        symbol: str
        side: str
        order_type: str = "MARKET"
        quantity: float = 0.0
        price: float = 0.0
        status: str = "UNKNOWN"
        order_id: str = ""
        timestamp: Optional[datetime] = None
        error: str = ""

logger = logging.getLogger(__name__)


class MockBinanceConnector:
    """
    🎭 Mock Binance Futures Connector
    
    完全偽裝成真實的 BinanceFuturesConnector
    TradingEngine 完全無法區分這是真實還是模擬
    
    使用方式:
    
    # === 方法 1: 直接替換連接器 ===
    from backtest import MockBinanceConnector
    
    mock = MockBinanceConnector(
        data_dir="data_downloads/binance_historical",
        symbol="BTCUSDT",
        start_date="2025-01-01",
        end_date="2025-06-30"
    )
    
    # 在 TradingEngine 中使用
    engine = TradingEngine()
    engine.connector = mock  # 替換連接器
    
    # === 方法 2: 自動回放模式 ===
    mock.start_playback()  # 開始回放歷史數據
    
    # TradingEngine 調用的所有方法都會收到模擬數據
    price = mock.get_ticker_price("BTCUSDT")  # 返回歷史價格
    mock.place_order(...)  # 模擬撮合
    
    mock.stop_playback()  # 停止回放
    """
    
    def __init__(
        self,
        data_dir: Union[str, Path] = "data_downloads/binance_historical",
        symbol: str = "BTCUSDT",
        interval: str = "1m",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        initial_balance: float = 10000.0,
        leverage: int = 1,
        maker_fee: float = 0.0002,
        taker_fee: float = 0.0004,
        slippage_rate: float = 0.0001,
        speed_multiplier: float = 0.0,  # 無延遲模式
        **kwargs  # 偽裝用參數 (api_key, api_secret, testnet)
    ):
        """
        初始化 Mock Connector
        
        Args:
            data_dir: 歷史數據目錄
            symbol: 主要交易對
            interval: K線間隔
            start_date: 回測開始日期
            end_date: 回測結束日期
            initial_balance: 初始餘額
            leverage: 槓桿倍數
            maker_fee: Maker 手續費
            taker_fee: Taker 手續費
            slippage_rate: 滑點率
            speed_multiplier: 回放速度倍數
            **kwargs: 偽裝用參數 (api_key, api_secret, testnet) 用於與真實 Connector 接口兼容
        """
        # 偽裝參數（讓 TradingEngine 以為是真實連接）
        self.api_key = kwargs.get('api_key', '') or "MOCK_API_KEY_FOR_BACKTEST"
        self.api_secret = kwargs.get('api_secret', '') or "MOCK_SECRET_FOR_BACKTEST"
        self.testnet = kwargs.get('testnet', True)
        
        # 偽裝 API 端點
        self.rest_base = "https://mock-fapi.binance.com"
        self.ws_base = "wss://mock-stream.binance.com"
        
        # 核心組件
        self.data_stream = HistoricalDataStream(
            data_dir=data_dir,
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            speed_multiplier=speed_multiplier,
        )
        
        self.account = VirtualAccount(
            initial_balance=initial_balance,
            leverage=leverage,
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            slippage_rate=slippage_rate,
        )
        
        # 狀態
        self.symbol = symbol
        self.interval = interval
        self.leverage = leverage
        self._is_playing = False
        self._playback_thread: Optional[threading.Thread] = None
        self._current_bar: Optional[KlineBar] = None
        self._bar_generator: Optional[Generator[KlineBar, None, None]] = None  # 用於 next_tick()
        
        # 公開 account 為 virtual_account（兼容性）
        self.virtual_account = self.account
        
        # 多交易對支持 {symbol: HistoricalDataStream}
        self._streams: Dict[str, HistoricalDataStream] = {symbol: self.data_stream}
        
        # WebSocket 回調存儲
        self._ticker_callbacks: Dict[str, Callable] = {}
        self._ws_connections: Dict[str, Any] = {}
        
        # 限流控制（偽裝用，實際不需要）
        self.request_timestamps: List[float] = []
        self.weight_used = 0
        self.last_weight_reset = time.time()
        
        # WebSocket 相關（僞装用）
        self.ws_connections: Dict[str, Any] = {}
        self.ws_reconnect_delay = 5
        self.ws_max_reconnect_attempts = 10
        
        logger.info("=" * 60)
        logger.info("🎭 Mock Binance Connector 初始化")
        logger.info("=" * 60)
        logger.info("模式: 歷史數據回放 (AI 無法區分真假)")
        logger.info(f"交易對: {symbol}")
        logger.info(f"時間區間: {start_date or '最早'} ~ {end_date or '最新'}")
        logger.info(f"初始餘額: {initial_balance} USDT")
        logger.info(f"槓桿: {leverage}x")
        logger.info("=" * 60)
    
    # ================================================================
    # 🔥 核心方法：完全模擬 BinanceFuturesConnector 接口
    # ================================================================
    
    def get_ticker_price(self, symbol: str = "BTCUSDT") -> Optional[MarketData]:
        """
        獲取最新價格 - 完全模擬 BinanceFuturesConnector.get_ticker_price
        
        返回歷史數據中「當前時間點」的價格
        """
        bar = self._get_current_bar(symbol)
        if bar is None:
            return None
        
        return MarketData(
            symbol=symbol,
            volume=bar.volume,
            timestamp=datetime.fromtimestamp(bar.close_time / 1000),
            high=bar.high,
            low=bar.low,
            open=bar.open,
            close=bar.close,
            bid=bar.close * 0.9999,  # 模擬買一價
            ask=bar.close * 1.0001,  # 模擬賣一價
        )
    
    def get_ticker_24hr(self, symbol: str = "BTCUSDT") -> Optional[Dict]:
        """
        獲取 24 小時行情統計 - 模擬 API
        """
        klines = self.data_stream.get_klines_until_now(limit=1440)  # 24h * 60min
        if not klines:
            return None
        
        prices = [k['close'] for k in klines]
        volumes = [k['volume'] for k in klines]
        
        current = klines[-1] if klines else None
        if not current:
            return None
        
        return {
            'symbol': symbol,
            'priceChange': str(current['close'] - klines[0]['open']),
            'priceChangePercent': str((current['close'] - klines[0]['open']) / klines[0]['open'] * 100),
            'weightedAvgPrice': str(sum(prices) / len(prices)),
            'lastPrice': str(current['close']),
            'lastQty': str(current['volume']),
            'openPrice': str(klines[0]['open']),
            'highPrice': str(max(prices)),
            'lowPrice': str(min(prices)),
            'volume': str(sum(volumes)),
            'quoteVolume': str(sum(k['quote_volume'] for k in klines)),
            'openTime': klines[0]['open_time'],
            'closeTime': current['close_time'],
            'count': len(klines),
        }
    
    def get_klines(
        self,
        symbol: str,
        interval: str = "1h",
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None
    ) -> Optional[List[List]]:
        """
        獲取 K線數據 - 完全模擬 BinanceFuturesConnector.get_klines
        
        返回格式與 Binance API 完全相同:
        [openTime, open, high, low, close, volume, closeTime, quoteVolume, trades, takerBuyBase, takerBuyQuote, ignore]
        
        🔒 防偷看：只返回「當前時間點」之前的數據
        """
        # start_time 和 end_time 保留用於未來支援指定時間範圍查詢
        _ = (start_time, end_time)
        
        # 如果是主交易對和主間隔，直接用主數據流
        if symbol == self.symbol and interval == self.interval:
            return self.data_stream.get_klines_list_format(limit=limit)
        
        # 否則獲取對應的數據流
        stream = self._get_stream(symbol, interval)
        return stream.get_klines_list_format(limit=limit)
    
    def get_order_book(self, symbol: str, limit: int = 100) -> Optional[Dict]:
        """
        獲取訂單簿 - 模擬深度數據
        
        基於當前價格生成假的訂單簿
        """
        bar = self._get_current_bar(symbol)
        if bar is None:
            return None
        
        price = bar.close
        spread = price * 0.0001  # 0.01% 價差
        
        # 生成模擬訂單簿
        bids = []
        asks = []
        
        for i in range(limit):
            bid_price = price - spread * (i + 1)
            ask_price = price + spread * (i + 1)
            quantity = bar.volume / limit * (1 + i * 0.1)  # 越遠量越大
            
            bids.append([str(bid_price), str(quantity)])
            asks.append([str(ask_price), str(quantity)])
        
        return {
            'lastUpdateId': int(time.time() * 1000),
            'bids': bids,
            'asks': asks,
        }
    
    def get_funding_rate(self, symbol: str, limit: int = 1) -> Optional[List[Dict]]:
        """
        獲取資金費率 - 模擬數據
        
        返回固定的模擬資金費率
        """
        # limit 參數保留用於未來支援多筆資金費率查詢
        _ = limit
        current_time = self.data_stream.state.current_time
        timestamp = int(current_time.timestamp() * 1000) if current_time else int(time.time() * 1000)
        
        return [{
            'symbol': symbol,
            'fundingRate': '0.00010000',  # 0.01% 固定模擬值
            'fundingTime': timestamp,
        }]
    
    def get_open_interest(self, symbol: str) -> Optional[Dict]:
        """
        獲取持倉量 - 模擬數據
        """
        bar = self._get_current_bar(symbol)
        if bar is None:
            return None
        
        # 基於成交量估算持倉量
        estimated_oi = bar.volume * bar.close * 10  # 簡單模擬
        
        return {
            'openInterest': str(estimated_oi),
            'symbol': symbol,
            'time': bar.close_time,
        }
    
    def get_account_info(self) -> Optional[Dict]:
        """
        獲取帳戶信息 - 返回虛擬帳戶數據
        """
        return self.account.get_account_info()
    
    def get_exchange_info(self, symbol: str) -> Optional[Dict]:
        """
        獲取交易對信息 - 返回模擬數據
        """
        return {
            'symbol': symbol,
            'pair': symbol.replace('USDT', ''),
            'contractType': 'PERPETUAL',
            'deliveryDate': 4133404800000,
            'onboardDate': 1569398400000,
            'status': 'TRADING',
            'maintMarginPercent': '2.5000',
            'requiredMarginPercent': '5.0000',
            'baseAsset': symbol.replace('USDT', ''),
            'quoteAsset': 'USDT',
            'pricePrecision': 2,
            'quantityPrecision': 3,
            'baseAssetPrecision': 8,
            'quotePrecision': 8,
            'filters': [
                {'filterType': 'PRICE_FILTER', 'minPrice': '0.10', 'maxPrice': '1000000', 'tickSize': '0.10'},
                {'filterType': 'LOT_SIZE', 'minQty': '0.001', 'maxQty': '1000', 'stepSize': '0.001'},
            ],
        }
    
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
        """
        下單 - 完全模擬 BinanceFuturesConnector.place_order
        
        會觸發虛擬帳戶的訂單撮合邏輯
        """
        try:
            # 更新當前價格
            bar = self._get_current_bar(symbol)
            if bar:
                self.account.update_price(symbol, bar.close)
            
            # 下單
            order = self.account.place_order(
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price,
            )
            
            # 處理止損止盈
            if stop_loss and order.status == OrderStatus.FILLED:
                self._place_stop_loss_order(symbol, side, quantity, stop_loss)
            
            if take_profit and order.status == OrderStatus.FILLED:
                self._place_take_profit_order(symbol, side, quantity, take_profit)
            
            # 轉換為 OrderResult 格式
            return OrderResult(
                order_id=order.order_id,
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=order.filled_price if order.filled_price > 0 else (price or 0),
                status=order.status.value,
                timestamp=order.timestamp,
            )
            
        except Exception as e:
            logger.error(f"❌ 模擬下單失敗: {e}")
            return OrderResult(
                order_id="",
                symbol=symbol,
                side=side,
                order_type=order_type,
                quantity=quantity,
                price=price or 0,
                status="ERROR",
                error=str(e),
            )
    
    def _place_stop_loss_order(self, symbol: str, original_side: str, quantity: float, stop_price: float):
        """下止損單"""
        side = "SELL" if original_side.upper() == "BUY" else "BUY"
        self.account.place_order(
            symbol=symbol,
            side=side,
            order_type="STOP_MARKET",
            quantity=quantity,
            stop_price=stop_price,
        )
        logger.info(f"🛡️ 止損單已設置: {stop_price:.2f}")
    
    def _place_take_profit_order(self, symbol: str, original_side: str, quantity: float, take_profit_price: float):
        """下止盈單"""
        side = "SELL" if original_side.upper() == "BUY" else "BUY"
        self.account.place_order(
            symbol=symbol,
            side=side,
            order_type="TAKE_PROFIT_MARKET",
            quantity=quantity,
            stop_price=take_profit_price,
        )
        logger.info(f"🎯 止盈單已設置: {take_profit_price:.2f}")
    
    def subscribe_ticker_stream(
        self,
        symbol: str,
        callback: Callable,
        auto_reconnect: bool = True
    ):
        """
        訂閱實時價格流 - 模擬 WebSocket 訂閱
        
        實際上是使用歷史數據回放來觸發回調
        """
        # auto_reconnect 參數保留用於接口相容
        _ = auto_reconnect
        self._ticker_callbacks[symbol] = callback
        
        logger.info(f"📡 訂閱 Ticker 流: {symbol} (使用歷史數據回放)")
        
        # 返回假的 WebSocket 對象
        class MockWebSocket:
            def close(self):
                # 模擬 WebSocket 關閉，實際無操作
                pass
        
        ws = MockWebSocket()
        self._ws_connections[symbol] = ws
        return ws
    
    def close_all_connections(self):
        """關閉所有連接"""
        self._ws_connections.clear()
        self._ticker_callbacks.clear()
        self.stop_playback()
        logger.info("關閉所有模擬連接")
    
    # ================================================================
    # 📺 回放控制方法
    # ================================================================
    
    def start_playback(self, callback: Optional[Callable[[KlineBar], None]] = None):
        """
        開始回放歷史數據
        
        Args:
            callback: 每根 K線的回調函數
        """
        if self._is_playing:
            logger.warning("回放已在進行中")
            return
        
        self._is_playing = True
        
        def playback_loop():
            logger.info("🎬 開始歷史數據回放...")
            
            for bar in self.data_stream.stream_bars():
                if not self._is_playing:
                    break
                
                # 更新當前 K線
                self._current_bar = bar
                
                # 更新帳戶價格
                self.account.update_price(bar.symbol, bar.close)
                
                # 觸發 ticker 回調
                if bar.symbol in self._ticker_callbacks:
                    ticker_data = {
                        'e': '24hrTicker',
                        's': bar.symbol,
                        'c': str(bar.close),
                        'o': str(bar.open),
                        'h': str(bar.high),
                        'l': str(bar.low),
                        'v': str(bar.volume),
                        'q': str(bar.quote_volume),
                    }
                    self._ticker_callbacks[bar.symbol](ticker_data)
                
                # 用戶回調
                if callback:
                    callback(bar)
            
            logger.info("🎬 歷史數據回放結束")
            self._is_playing = False
        
        self._playback_thread = threading.Thread(target=playback_loop, daemon=True)
        self._playback_thread.start()
    
    def stop_playback(self):
        """停止回放"""
        self._is_playing = False
        self.data_stream.stop()
        
        if self._playback_thread:
            self._playback_thread.join(timeout=2)
        
        logger.info("⏹️ 回放已停止")
    
    def pause_playback(self):
        """暫停回放"""
        self.data_stream.pause()
    
    def resume_playback(self):
        """繼續回放"""
        self.data_stream.resume()
    
    def next_tick(self) -> bool:
        """
        【時間推進器】
        呼叫一次，時間就往後走一格 (一根 K 線)。
        回傳 False 代表歷史數據播完了。
        
        這是訓練模式的核心方法！
        """
        try:
            # 從生成器獲取下一根 K 線
            if not hasattr(self, '_bar_generator') or self._bar_generator is None:
                self._bar_generator = self.data_stream.stream_bars()
            
            bar = next(self._bar_generator)
            self._current_bar = bar
            self.account.update_price(bar.symbol, bar.close)
            
            # 觸發 ticker 回調（如果有訂閱）
            if bar.symbol in self._ticker_callbacks:
                ticker_data = {
                    'e': '24hrTicker',
                    's': bar.symbol,
                    'c': str(bar.close),
                    'o': str(bar.open),
                    'h': str(bar.high),
                    'l': str(bar.low),
                    'v': str(bar.volume),
                    'q': str(bar.quote_volume),
                }
                self._ticker_callbacks[bar.symbol](ticker_data)
            
            return True
            
        except StopIteration:
            logger.info("📺 歷史數據播放完畢")
            return False
    
    def step(self) -> Optional[KlineBar]:
        """
        單步執行 - 手動推進一根 K線（別名方法）
        
        適合需要精確控制的場景
        """
        if self.next_tick():
            return self._current_bar
        return None
    
    def run_backtest(
        self,
        on_bar: Callable[[KlineBar, 'MockBinanceConnector'], None],
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict[str, Any]:
        """
        運行完整回測
        
        Args:
            on_bar: 每根 K線的處理函數，接收 (bar, connector)
            progress_callback: 進度回調，接收 (current, total)
            
        Returns:
            回測統計結果
        """
        logger.info("🚀 開始運行回測...")
        
        bar_count = 0
        
        for bar in self.data_stream.stream_bars():
            # 更新狀態
            self._current_bar = bar
            self.account.update_price(bar.symbol, bar.close)
            
            # 調用策略處理
            on_bar(bar, self)
            
            bar_count += 1
            
            # 進度回調
            if progress_callback:
                current, total, _ = self.data_stream.get_progress()
                progress_callback(current, total)
        
        # 返回統計結果
        stats = self.account.get_stats()
        stats['total_bars'] = bar_count
        stats['data_period'] = {
            'start': self.data_stream.start_date,
            'end': self.data_stream.end_date,
        }
        
        logger.info("✅ 回測完成!")
        self._print_backtest_summary(stats)
        
        return stats
    
    def _print_backtest_summary(self, stats: Dict):
        """打印回測摘要"""
        print("\n" + "=" * 60)
        print("📊 回測結果摘要")
        print("=" * 60)
        print(f"初始餘額:     {stats['initial_balance']:,.2f} USDT")
        print(f"最終餘額:     {stats['current_balance']:,.2f} USDT")
        print(f"總權益:       {stats['total_equity']:,.2f} USDT")
        print(f"總收益率:     {stats['total_return']:+.2f}%")
        print("-" * 60)
        print(f"總交易次數:   {stats['total_trades']}")
        print(f"勝率:         {stats['win_rate']:.1f}%")
        print(f"盈利交易:     {stats['winning_trades']}")
        print(f"虧損交易:     {stats['losing_trades']}")
        print("-" * 60)
        print(f"實現盈虧:     {stats['total_realized_pnl']:+,.2f} USDT")
        print(f"總手續費:     {stats['total_commission']:.2f} USDT")
        print(f"最大回撤:     {stats['max_drawdown']:.2f}%")
        print("=" * 60 + "\n")
    
    # ================================================================
    # 內部輔助方法
    # ================================================================
    
    def _get_current_bar(self, symbol: str) -> Optional[KlineBar]:
        """獲取當前 K線"""
        if self._current_bar and self._current_bar.symbol == symbol:
            return self._current_bar
        
        return self.data_stream.get_current_bar()
    
    def _get_stream(self, symbol: str, interval: str) -> HistoricalDataStream:
        """獲取數據流（支持多交易對）"""
        key = f"{symbol}_{interval}"
        
        if key not in self._streams:
            # 如果是主交易對但不同間隔，需要創建新的流
            if symbol == self.symbol:
                # 使用相同的數據目錄
                self._streams[key] = HistoricalDataStream(
                    data_dir=self.data_stream.data_dir,
                    symbol=symbol,
                    interval=interval,
                    start_date=self.data_stream.start_date,
                    end_date=self.data_stream.end_date,
                )
            else:
                logger.warning(f"未知交易對 {symbol}，返回主流")
                return self.data_stream
        
        return self._streams.get(key, self.data_stream)
    
    def _check_rate_limit(self):
        """檢查速率限制 - 偽裝用，實際不執行"""
        pass
    
    def _sign_request(self, params: Dict) -> Dict:
        """簽名請求 - 偽裝用"""
        params['timestamp'] = int(time.time() * 1000)
        params['signature'] = 'MOCK_SIGNATURE'
        return params
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, signed: bool = False) -> Optional[Dict]:
        """發送請求 - 偽裝用"""
        # params 和 signed 參數保留用於接口相容
        _ = (params, signed)
        logger.debug(f"模擬 API 請求: {method} {endpoint}")
        return {}
    
    # ================================================================
    # 便利屬性
    # ================================================================
    
    @property
    def current_time(self) -> Optional[datetime]:
        """當前模擬時間"""
        return self.data_stream.get_current_time()
    
    @property
    def current_price(self) -> float:
        """當前價格"""
        return self.data_stream.get_current_price()
    
    @property
    def balance(self) -> float:
        """帳戶餘額"""
        return self.account.get_balance()
    
    @property
    def equity(self) -> float:
        """帳戶權益"""
        return self.account.get_total_equity()
    
    @property
    def positions(self) -> List:
        """所有倉位"""
        return self.account.get_all_positions()
    
    def get_position(self, symbol: str):
        """獲取指定倉位"""
        return self.account.get_position(symbol)
