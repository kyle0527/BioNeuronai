"""
Backtest Module - 回測引擎模組
=============================

時光機機制：將歷史數據變成即時串流，讓 AI 以為是真實交易

核心組件：
- MockBinanceConnector: 完全模擬 BinanceFuturesConnector 的接口
- HistoricalDataStream: 歷史數據串流生成器 (防偷看機制)
- VirtualAccount: 虛擬帳戶狀態仿真
- BacktestEngine: 回測引擎主類

使用方式：
    from bioneuronai.backtest import MockBinanceConnector
    
    # 用 MockBinanceConnector 替換真實連接器，無需修改 TradingEngine
    mock_connector = MockBinanceConnector(
        data_dir="data_downloads/binance_historical",
        symbol="BTCUSDT",
        start_date="2025-01-01",
        end_date="2025-12-31"
    )
"""

__version__ = "1.0.0"

from .mock_connector import MockBinanceConnector
from .data_stream import HistoricalDataStream, KlineBar
from .virtual_account import VirtualAccount
from .backtest_engine import BacktestEngine, BacktestConfig, quick_backtest, create_mock_connector

__all__ = [
    "MockBinanceConnector",
    "HistoricalDataStream",
    "KlineBar",
    "VirtualAccount",
    "BacktestEngine",
    "BacktestConfig",
    "quick_backtest",
    "create_mock_connector",
]
