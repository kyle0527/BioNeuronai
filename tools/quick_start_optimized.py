#!/usr/bin/env python3
"""
快速啟動 BioNeuronAI [Legacy Wrapper]
========================================

此腳本為向下相容的舊版入口，功能已整合至統一 CLI：
    src/bioneuronai/cli/main.py

建議改用：
    python main.py status         # 系統健康檢查
    python main.py trade --testnet  # 啟動測試網交易
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))

from bioneuronai.cli.main import cli_main

if __name__ == "__main__":
    cli_main(["status"])
