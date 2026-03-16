#!/usr/bin/env python3
"""
BioNeuronai - 統一入口點
=========================

所有 CLI 操作請透過此檔案執行，而非直接呼叫 tools/ 下的個別腳本。

使用方式:
    python main.py <command> [options]
    python main.py --help

可用命令:
    backtest   歷史數據回測
    simulate   紙交易模擬 (next_tick 推進，不產生真實訂單)
    trade      實盤 / 測試網交易
    plan       生成每日 SOP 交易計劃 (10 步驟)
    news       新聞情緒分析
    pretrade   進場前技術面 / 基本面 / 風險驗核
    status     系統健康狀態檢查

命令範例:
    python main.py backtest  --symbol ETHUSDT --interval 1h
    python main.py simulate  --symbol BTCUSDT --interval 15m --balance 50000
    python main.py trade     --testnet
    python main.py plan      --output daily_plan.json
    python main.py news      --symbol BTCUSDT --max-items 5
    python main.py pretrade  --symbol BTCUSDT --action long
    python main.py status
"""

import sys
from pathlib import Path

# 確保 src/ 在路徑中，讓 bioneuronai 套件可以被找到
_SRC = Path(__file__).parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from bioneuronai.cli.main import cli_main

if __name__ == "__main__":
    cli_main()
