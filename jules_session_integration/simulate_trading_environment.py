import sys
import time
import json
import random
import logging
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("simulation_report.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Simulation")

# Import system modules
from bioneuronai import TradingEngine, MarketData, TradingSignal
from bioneuronai.data_models import OrderResult
from bioneuronai.sop_automation import SOPAutomationSystem
from bioneuronai.pretrade_automation import PreTradeCheckSystem

class MockBinanceConnector:
    """Mock connector for simulation"""
    def __init__(self, api_key="", api_secret="", testnet=True):
        self.api_key = api_key
        self.testnet = testnet
        self.base_price = 50000.0
        self.balance = 100000.0
        self.positions = []
        self.last_callback = None # Store callback here
        logger.info("🔧 [Mock] Initialized MockBinanceConnector")

    def get_ticker_price(self, symbol="BTCUSDT"):
        # Simulate random price movement
        change = random.gauss(0, 100)
        self.base_price += change
        logger.info(f"📊 [Mock] Price update for {symbol}: {self.base_price:.2f}")
        return MarketData(
            symbol=symbol,
            price=self.base_price,
            timestamp=int(time.time() * 1000)
        )

    def get_account_info(self):
        logger.info(f"💰 [Mock] Fetching account info. Balance: {self.balance}")
        return {
            "totalWalletBalance": str(self.balance),
            "availableBalance": str(self.balance),
            "totalUnrealizedProfit": "0.0",
            "positions": self.positions
        }

    def place_order(self, symbol, side, order_type, quantity, price=None, stop_loss=None, take_profit=None, reduce_only=False):
        order_id = random.randint(100000, 999999)
        logger.info(f"🚀 [Mock] Order Placed: {side} {quantity} {symbol} @ {price or 'MARKET'} (ID: {order_id})")
        
        # Simulate simple execution
        cost = quantity * (price if price else self.base_price)
        if side == "BUY":
            self.balance -= cost * 0.001 # fee
        
        return OrderResult(
            order_id=str(order_id),
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price if price else self.base_price,
            status="FILLED"
        )

    def subscribe_ticker_stream(self, symbol, callback, auto_reconnect=True):
        logger.info(f"📡 [Mock] Subscribed to ticker stream for {symbol}")
        self.last_callback = callback # Capture callback

    def close_all_connections(self):
        logger.info("🔌 [Mock] Connections closed")

def run_simulation():
    print("=" * 80)
    print("🚀 BioNeuronAI 全功能模擬驗證環境 (Virtual Environment Simulation)")
    print("=" * 80)
    
    # 1. Patch the connector class
    with patch('bioneuronai.trading_engine.BinanceFuturesConnector', side_effect=MockBinanceConnector) as MockConnector:
        
        # 2. SOP Automation Check
        print("\n📝 [Step 1] 執行 SOP 每日開盤前檢查...")
        sop_system = SOPAutomationSystem()
        
        # Mocking external calls in SOP using async def
        async def mock_api_check():
            return {"connected": True, "latency_ms": 45}
        sop_system._check_api_connection = mock_api_check
        
        async def mock_global_data():
            return {"us_futures": "GREEN", "asian_markets": "MIXED"}
        sop_system._get_global_market_data = mock_global_data
        
        # Run SOP
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        sop_results = loop.run_until_complete(sop_system.execute_daily_premarket_check())
        print(f"✅ SOP 檢查完成: {sop_results['overall_assessment']['status']}")
        
        # 3. Initialize Trading Engine
        print("\n🔧 [Step 2] 初始化交易引擎...")
        engine = TradingEngine(api_key="mock_key", api_secret="mock_secret", testnet=True)
        engine.enable_auto_trading() # Enable auto trading to test order placement
        
        # 4. Pre-Trade Automation Check (Mock run)
        print("\n🛡️ [Step 3] 執行交易前檢查 (Pre-Trade Check)...")
        pretrade = PreTradeCheckSystem()
        
        # Mocking data fetch using async def
        async def mock_market_data(s):
            return {
                "symbol": s, "price": 50000, "rsi": 30, # Oversold to trigger buy
                "macd": {"signal": "BULLISH"}, "timeframes": {"1h": "BULLISH"}
            }
        pretrade._get_market_data = mock_market_data
        
        pt_results = loop.run_until_complete(pretrade.execute_pretrade_check(intended_action="BUY"))
        print(f"✅ 交易前檢查完成: {pt_results['overall_assessment']['recommendation']}")

        # 5. Simulate Market Data Loop
        print("\n📈 [Step 4] 開始市場數據流模擬 (10 個數據點)...")
        engine.start_monitoring("BTCUSDT")
        
        # Access the private callback directly from the mock instance attached to engine
        callback = engine.connector.last_callback
        
        if callback:
            logger.info("✅ Captured WebSocket callback")
            
            # Simulate 10 ticks
            for i in range(1, 11):
                # Generate synthetic data packet like Binance WebSocket
                # Create a price pattern that triggers RSI strategy (e.g., sharp drop then recovery)
                # Base price 50000. 
                # If we drop it, RSI drops.
                
                # Let's just oscillate to trigger Bollinger or RSI
                price = 50000 + (i * 200) * (-1 if i % 2 == 0 else 1)
                
                # Mock packet structure from Binance
                data = {
                    's': 'BTCUSDT',
                    'c': str(price),
                    'v': '1000',
                    'h': str(price + 50),
                    'l': str(price - 50),
                    'o': str(price),
                    'b': str(price - 1),
                    'a': str(price + 1)
                }
                print(f"   🔹 Tick #{i}: Price ${price}")
                
                # Feed to engine
                callback(data)
                
                time.sleep(0.1)
        else:
            logger.error("❌ Failed to capture WebSocket callback. Engine might not have started monitoring correctly.")

        # 6. Stop and Report
        print("\n🛑 [Step 5] 停止模擬與報告生成...")
        engine.stop_monitoring()
        engine.save_all_data()
        
        print("\n✅ 模擬驗證完成！詳情請查看 simulation_report.log")
        print(f"📊 生成信號數: {len(engine.signals_history)}")

if __name__ == "__main__":
    run_simulation()
