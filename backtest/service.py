"""Replay service layer for CLI/API/UI.

These helpers orchestrate replay runs and persist runtime artifacts.
They do not replace the project's strategy logic.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

import numpy as np

from .backtest_engine import BacktestEngine
from .data_stream import DEFAULT_DATA_DIR, resolve_data_dir
from .mock_connector import MockBinanceConnector
from .runtime_store import ReplayRunRecorder, list_runs, load_run


def _build_engine_holder() -> Dict[str, Any]:
    holder: Dict[str, Any] = {"engine": None, "ai_ready": False, "strategy_ready": False}
    try:
        from bioneuronai.core.trading_engine import TradingEngine

        engine = TradingEngine(testnet=True)
        holder["engine"] = engine
        holder["ai_ready"] = bool(engine.inference_engine and engine.ai_model_loaded)
        holder["strategy_ready"] = hasattr(engine, "generate_trading_signal")
    except Exception as exc:
        holder["error"] = str(exc)
    return holder


def _klines_dicts_to_numpy(klines: list[dict[str, Any]]) -> np.ndarray:
    """將 replay 歷史資料轉為策略層使用的 OHLCV ndarray。"""
    if not klines:
        return np.empty((0, 6), dtype=np.float64)

    return np.asarray(
        [
            [
                float(item.get("open_time", 0)),
                float(item.get("open", 0.0)),
                float(item.get("high", 0.0)),
                float(item.get("low", 0.0)),
                float(item.get("close", 0.0)),
                float(item.get("volume", 0.0)),
            ]
            for item in klines
        ],
        dtype=np.float64,
    )


def _resolve_secondary_symbol(primary_symbol: str) -> Optional[str]:
    """為配對交易挑選次資產。"""
    mapping = {
        "BTCUSDT": "ETHUSDT",
        "ETHUSDT": "BTCUSDT",
        "BNBUSDT": "BTCUSDT",
        "SOLUSDT": "ETHUSDT",
    }
    return mapping.get(primary_symbol.upper())


def _load_secondary_ohlcv(
    connector: MockBinanceConnector,
    primary_symbol: str,
    interval: str,
    limit: int,
) -> Optional[np.ndarray]:
    """嘗試載入配對策略需要的次資產 OHLCV。"""
    secondary_symbol = _resolve_secondary_symbol(primary_symbol)
    if not secondary_symbol:
        return None

    try:
        secondary = connector.get_klines(secondary_symbol, interval=interval, limit=limit)
    except Exception:
        return None

    if not secondary:
        return None

    return np.asarray(
        [
            [
                float(item[0]),
                float(item[1]),
                float(item[2]),
                float(item[3]),
                float(item[4]),
                float(item[5]),
            ]
            for item in secondary
        ],
        dtype=np.float64,
    )


def run_strategy_instance_backtest(
    strategy: Any,
    *,
    symbol: str = "ETHUSDT",
    interval: str = "1h",
    balance: float = 10000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_dir: Optional[Union[str, Any]] = DEFAULT_DATA_DIR,
    warmup_bars: int = 100,
) -> Dict[str, Any]:
    """使用正式 replay 評估單一策略實例。"""
    resolved_root = resolve_data_dir(data_dir)

    def strategy_callback(bar: Any, connector: Any) -> None:
        klines = connector.data_stream.get_klines_until_now(300)
        ohlcv = _klines_dicts_to_numpy(klines)
        if len(ohlcv) < max(20, warmup_bars):
            return

        additional_data: Dict[str, Any] = {"symbol": bar.symbol}
        strategy_name = getattr(strategy, "name", "").lower().replace(" ", "_")
        if "pair" in strategy_name:
            secondary_ohlcv = _load_secondary_ohlcv(connector, bar.symbol, interval, 300)
            if secondary_ohlcv is not None:
                additional_data["secondary_ohlcv"] = secondary_ohlcv

        strategy.run_iteration(
            ohlcv_data=ohlcv,
            current_price=bar.close,
            account_balance=float(connector.account.get_total_equity()),
            connector=connector,
            additional_data=additional_data,
        )

    engine = BacktestEngine(
        data_dir=resolved_root,
        symbol=symbol,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        initial_balance=balance,
    )
    engine.config.warmup_bars = warmup_bars
    result = engine.run(strategy_callback, print_summary=False)
    stats = dict(result.stats)
    stats["trade_count"] = len(result.trades)
    stats["equity_points"] = len(result.equity_curve)
    return stats


def run_simulation_summary(
    symbol: str = "ETHUSDT",
    interval: str = "1h",
    balance: float = 100000.0,
    bars: int = 200,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_dir: Optional[Union[str, Any]] = DEFAULT_DATA_DIR,
) -> Dict[str, Any]:
    """執行 replay simulate，回傳簡潔摘要。"""
    holder = _build_engine_holder()
    resolved_root = resolve_data_dir(data_dir)
    recorder = ReplayRunRecorder(
        mode="simulate",
        config={
            "symbol": symbol,
            "interval": interval,
            "balance": balance,
            "bars": bars,
            "start_date": start_date,
            "end_date": end_date,
            "data_dir": str(resolved_root),
        },
    )

    try:
        mock = MockBinanceConnector(
            data_dir=resolved_root,
            symbol=symbol,
            interval=interval,
            initial_balance=balance,
            start_date=start_date,
            end_date=end_date,
            run_recorder=recorder,
        )

        bar_count = 0
        signals_emitted = 0
        signal_counts: Dict[str, int] = {}

        while mock.next_tick() and bar_count < bars:
            bar = mock._current_bar
            if bar is None:
                continue
            bar_count += 1

            engine = holder.get("engine")
            if holder.get("strategy_ready") and engine is not None:
                try:
                    klines = mock.data_stream.get_klines_until_now(50)
                    signal = engine.generate_trading_signal(
                        symbol=bar.symbol,
                        current_price=bar.close,
                        klines=klines,
                    )
                    if signal is None:
                        continue
                    signal_name = signal.signal_type.value
                    signal_counts[signal_name] = signal_counts.get(signal_name, 0) + 1
                    signals_emitted += 1
                except Exception:
                    pass

        account = mock.get_account_info() or {}
        stats = mock.virtual_account.get_stats()
        summary = {
            "mode": "simulate",
            "resolved_root": str(resolved_root),
            "symbol": symbol,
            "interval": interval,
            "bars_requested": bars,
            "bars_processed": bar_count,
            "start_date": start_date,
            "end_date": end_date,
            "ai_ready": holder.get("ai_ready", False),
            "strategy_ready": holder.get("strategy_ready", False),
            "engine_error": holder.get("error"),
            "signals_emitted": signals_emitted,
            "signal_counts": signal_counts,
            "final_balance": float(account.get("totalWalletBalance", balance)),
            "stats": stats,
        }
        recorder.save_account(
            {
                "account_info": account,
                "stats": stats,
                "trades": [trade.to_dict() for trade in mock.virtual_account.trade_history],
            }
        )
        recorder.save_runtime_state(mock.get_runtime_snapshot())
        return recorder.finalize(summary)
    except Exception as exc:
        recorder.finalize(
            {
                "mode": "simulate",
                "resolved_root": str(resolved_root),
                "symbol": symbol,
                "interval": interval,
            },
            status="failed",
            error=str(exc),
        )
        raise


def run_backtest_summary(
    symbol: str = "ETHUSDT",
    interval: str = "1h",
    balance: float = 10000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_dir: Optional[Union[str, Any]] = DEFAULT_DATA_DIR,
    warmup_bars: int = 100,
) -> Dict[str, Any]:
    """執行 replay backtest，回傳摘要與結果。"""
    holder = _build_engine_holder()
    resolved_root = resolve_data_dir(data_dir)
    recorder = ReplayRunRecorder(
        mode="backtest",
        config={
            "symbol": symbol,
            "interval": interval,
            "balance": balance,
            "start_date": start_date,
            "end_date": end_date,
            "warmup_bars": warmup_bars,
            "data_dir": str(resolved_root),
        },
    )

    def ai_strategy(bar: Any, connector: Any) -> None:
        engine = holder.get("engine")
        if engine is None:
            return
        if not holder.get("strategy_ready"):
            return

        klines = connector.data_stream.get_klines_until_now(100)
        if not klines or len(klines) < 20:
            return

        signal = engine.generate_trading_signal(
            symbol=bar.symbol,
            current_price=bar.close,
            klines=klines,
        )
        if signal is None:
            return
        action = signal.action.upper()

        account = connector.get_account_info() or {}
        pos = next(
            (
                p
                for p in account["positions"]
                if p["symbol"] == bar.symbol and abs(float(p["positionAmt"])) > 0
            ),
            None,
        )

        if action == "BUY" and (not pos or float(pos["positionAmt"]) <= 0):
            if pos and float(pos["positionAmt"]) < 0:
                connector.place_order(
                    bar.symbol,
                    "BUY",
                    "MARKET",
                    abs(float(pos["positionAmt"])),
                )
            connector.place_order(bar.symbol, "BUY", "MARKET", 0.05)
        elif action == "SELL" and (not pos or float(pos["positionAmt"]) >= 0):
            if pos and float(pos["positionAmt"]) > 0:
                connector.place_order(
                    bar.symbol,
                    "SELL",
                    "MARKET",
                    float(pos["positionAmt"]),
                )
            connector.place_order(bar.symbol, "SELL", "MARKET", 0.05)

    try:
        engine = BacktestEngine(
            data_dir=resolved_root,
            symbol=symbol,
            interval=interval,
            start_date=start_date,
            end_date=end_date,
            initial_balance=balance,
            run_recorder=recorder,
        )
        engine.config.warmup_bars = warmup_bars
        result = engine.run(ai_strategy, print_summary=False)
        stats = result.stats

        summary = {
            "mode": "backtest",
            "resolved_root": str(resolved_root),
            "symbol": symbol,
            "interval": interval,
            "start_date": start_date,
            "end_date": end_date,
            "warmup_bars": warmup_bars,
            "ai_ready": holder.get("ai_ready", False),
            "strategy_ready": holder.get("strategy_ready", False),
            "engine_error": holder.get("error"),
            "stats": stats,
            "trade_count": len(result.trades),
            "equity_points": len(result.equity_curve),
        }
        return recorder.finalize(summary)
    except Exception as exc:
        recorder.finalize(
            {
                "mode": "backtest",
                "resolved_root": str(resolved_root),
                "symbol": symbol,
                "interval": interval,
                "start_date": start_date,
                "end_date": end_date,
                "warmup_bars": warmup_bars,
            },
            status="failed",
            error=str(exc),
        )
        raise


def list_runtime_runs(limit: int = 20) -> Dict[str, Any]:
    """列出 replay runtime runs。"""
    return list_runs(limit=limit)


def get_runtime_run(run_id: str) -> Dict[str, Any]:
    """讀取指定 replay runtime run。"""
    return load_run(run_id)
