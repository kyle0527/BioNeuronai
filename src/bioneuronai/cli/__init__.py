"""
BioNeuronai CLI 模組
====================

統一命令列介面入口，整合所有操作命令：
- backtest  : 歷史數據回測
- simulate  : 紙交易模擬 (MockConnector)
- trade     : 實盤 / 測試網交易
- plan      : 每日 SOP 交易計劃
- news      : 新聞情緒分析
- status    : 系統健康狀態

使用方式:
    python main.py <command> [options]
    python main.py --help
"""


def cli_main() -> None:
    """Lazy import to avoid runpy warnings when executing cli.main as a module."""
    from .main import cli_main as _cli_main

    _cli_main()


__all__ = ["cli_main"]
