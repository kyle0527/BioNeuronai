"""Replay/backtest domain exports.

`backtest/` is the project's formal replay runtime:
- historical market data loading
- simulated execution and account state
- runtime artifact persistence

It does not decide whether to trade.
Trading decisions still belong to the project's strategy layer.
"""

__version__ = "2.1"

from .contracts import ExecutionReceipt, OrderIntent, ReplayRuntimeState
from .mock_connector import MockBinanceConnector
from .data_stream import DEFAULT_DATA_DIR, HistoricalDataStream, KlineBar, resolve_data_dir
from .paths import BACKTEST_DATA_DIR, DATA_ROOT, DOCS_ROOT, RUNTIME_ROOT, UI_ROOT, VENDOR_ROOT, ensure_backtest_dirs
from bioneuronai.trading import VirtualAccount
from .backtest_engine import BacktestEngine, BacktestConfig, quick_backtest, create_mock_connector
from .catalog import get_catalog
from .runtime_store import ReplayRunRecorder, list_runs, load_run
from .service import (
    build_selector_performance_weights,
    collect_signal_training_data,
    get_runtime_run,
    list_runtime_runs,
    run_backtest_summary,
    run_simulation_summary,
    run_strategy_suite_backtest,
)
from .web import load_backtest_ui_html

__all__ = [
    "OrderIntent",
    "ExecutionReceipt",
    "ReplayRuntimeState",
    "MockBinanceConnector",
    "DEFAULT_DATA_DIR",
    "HistoricalDataStream",
    "KlineBar",
    "VirtualAccount",
    "BacktestEngine",
    "BacktestConfig",
    "quick_backtest",
    "create_mock_connector",
    "resolve_data_dir",
    "get_catalog",
    "ReplayRunRecorder",
    "list_runs",
    "load_run",
    "run_backtest_summary",
    "run_simulation_summary",
    "run_strategy_suite_backtest",
    "build_selector_performance_weights",
    "collect_signal_training_data",
    "list_runtime_runs",
    "get_runtime_run",
    "BACKTEST_DATA_DIR",
    "DATA_ROOT",
    "DOCS_ROOT",
    "UI_ROOT",
    "RUNTIME_ROOT",
    "VENDOR_ROOT",
    "ensure_backtest_dirs",
    "load_backtest_ui_html",
]
