"""
AI 實際交易執行 - 使用 next_tick() 推進 [Legacy Wrapper]
=========================================================

此腳本為向下相容的舊版入口，核心邏輯已移至：
    src/bioneuronai/cli/main.py  ->  cmd_backtest()

建議改用統一 CLI 入口：
    python main.py backtest --symbol ETHUSDT --interval 15m \\
        --start-date 2026-01-10 --end-date 2026-01-15

若仍需使用本腳本的 next_tick() 原始行為，
請直接操作 backtest.MockBinanceConnector，詳見 backtest/ 模組說明。
"""

import sys
from pathlib import Path

# 路徑設定：專案根目錄
_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))  # for backtest/ module

from bioneuronai.cli.main import cli_main

if __name__ == "__main__":
    # 以 backtest 模式啟動，預設參數對應原始腳本設定
    cli_main([
        "backtest",
        "--symbol", "ETHUSDT",
        "--interval", "15m",
        "--start-date", "2026-01-10",
        "--end-date", "2026-01-15",
        "--balance", "10000",
    ])
