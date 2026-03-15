"""
模擬交易環境 [Legacy Wrapper]
==============================

此腳本為向下相容的舊版入口，核心邏輯已移至：
    src/bioneuronai/cli/main.py  ->  cmd_simulate()

建議改用統一 CLI 入口：
    python main.py simulate --symbol BTCUSDT --balance 100000 --bars 200

若需完整的舊版模擬行為（MockBinanceConnector + async 事件），
請參考 backtest/ 模組與 src/bioneuronai/core/trading_engine.py。
"""

import sys
from pathlib import Path

# 路徑設定：專案根目錄
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from bioneuronai.cli.main import cli_main

if __name__ == "__main__":
    cli_main([
        "simulate",
        "--symbol", "BTCUSDT",
        "--balance", "100000",
        "--bars", "200",
    ])
