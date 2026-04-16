"""Replay service layer for CLI/API/UI.

These helpers orchestrate replay runs and persist runtime artifacts.
They do not replace the project's strategy logic.
"""

from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
            account_balance=float(connector.get_total_equity()),
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
        account_snapshot = mock.get_account_snapshot()
        stats = mock.get_stats()
        trade_history = mock.get_trade_history_snapshot()
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
            "available_balance": float(account_snapshot.get("available_balance", balance)),
            "stats": stats,
        }
        recorder.save_account(
            {
                "account_info": account,
                "account_snapshot": account_snapshot,
                "stats": stats,
                "trades": trade_history,
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

        position = connector.get_position_snapshot(bar.symbol)
        position_amt = float(position["positionAmt"]) if position else 0.0

        if action == "BUY" and position_amt <= 0:
            if position_amt < 0:
                connector.place_order(
                    bar.symbol,
                    "BUY",
                    "MARKET",
                    abs(position_amt),
                )
            connector.place_order(bar.symbol, "BUY", "MARKET", 0.05)
        elif action == "SELL" and position_amt >= 0:
            if position_amt > 0:
                connector.place_order(
                    bar.symbol,
                    "SELL",
                    "MARKET",
                    position_amt,
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


# ============================================================================
# 訓練資料收集：輸出 signal_history.jsonl 供 unified_trainer 使用
# ============================================================================

def _try_load_inference_engine() -> Optional[Any]:
    """嘗試載入 InferenceEngine；失敗時返回 None。"""
    try:
        from bioneuronai.core.inference_engine import InferenceEngine
        ie = InferenceEngine()
        ie.load_model()
        return ie
    except Exception:
        return None


def _infer_signal(ie: Optional[Any], buf: deque) -> Optional[List[float]]:
    """用 InferenceEngine 推算 signal 向量；失敗或 ie 為 None 時返回 None。"""
    if ie is None:
        return None
    try:
        feat_seq = np.stack(list(buf), axis=0)        # (seq_len, 1024)
        signal_output, _ = ie.predictor.predict(feat_seq)
        return signal_output.tolist()
    except Exception:
        return None


def _extract_features(feature_pipeline: Any, bar: Any, connector: Any) -> Optional[List]:
    """提取當前 bar 的 1024 維特徵；資料不足或出錯時返回 None。"""
    klines = connector.data_stream.get_klines_until_now(300)
    if len(klines) < 30:
        return None
    try:
        return feature_pipeline.build_features(
            current_price=bar.close,
            klines=klines,
        ).tolist()
    except Exception:
        return None


def collect_signal_training_data(
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    balance: float = 10000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_dir: Optional[Union[str, Any]] = DEFAULT_DATA_DIR,
    warmup_bars: int = 100,
    seq_len: int = 16,
    output_path: Optional[Union[str, Path]] = None,
    max_samples: int = 50000,
) -> Dict[str, Any]:
    """
    運行回測並收集 (feature_seq, signal_output) 對，輸出為 JSONL 格式。

    每行格式：
    {
        "features": [[f0...f1023], ...(共 seq_len 行)],   # shape (seq_len, 1024)
        "signal":   [s0, s1, ..., s511]                   # shape (512,)
    }

    輸出檔案預設位置：data/signal_history.jsonl
    可直接作為 unified_trainer.py --signal-data 的輸入。

    Args:
        seq_len:      每個樣本包含幾個時間步（對應 TinyLLMConfig.numeric_seq_len=16）
        output_path:  JSONL 輸出路徑（None 則用 data/signal_history.jsonl）
        max_samples:  最多收集幾筆（避免過大）

    Returns:
        {"samples_collected": N, "output_path": "..."}
    """
    import sys
    _root = Path(__file__).resolve().parents[1]
    for p in [str(_root / "src"), str(_root)]:
        if p not in sys.path:
            sys.path.insert(0, p)

    try:
        from bioneuronai.core.inference_engine import FeaturePipeline
    except Exception as exc:
        return {"error": f"InferenceEngine 不可用: {exc}", "samples_collected": 0}

    resolved_root = resolve_data_dir(data_dir)
    dest = Path(output_path) if output_path else (_root / "data" / "signal_history.jsonl")
    dest.parent.mkdir(parents=True, exist_ok=True)

    feature_pipeline = FeaturePipeline()
    ie = _try_load_inference_engine()
    if ie is None:
        return {
            "error": "InferenceEngine 無法載入，已停止收集以避免寫入全零 signal 標籤。",
            "samples_collected": 0,
        }

    dest.write_text("", encoding="utf-8")   # 清空舊檔案
    buf: deque = deque(maxlen=seq_len)
    samples_collected = 0
    skipped_samples = 0

    def _collect_callback(bar: Any, connector: Any) -> None:
        nonlocal samples_collected, skipped_samples
        if samples_collected >= max_samples:
            return
        feats = _extract_features(feature_pipeline, bar, connector)
        if feats is None:
            return
        buf.append(feats)
        if len(buf) < seq_len:
            return
        signal = _infer_signal(ie, buf)
        if signal is None:
            skipped_samples += 1
            return
        record = {"features": list(buf), "signal": signal}
        with open(dest, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        samples_collected += 1

    engine = BacktestEngine(
        data_dir=resolved_root,
        symbol=symbol,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        initial_balance=balance,
    )
    engine.config.warmup_bars = warmup_bars
    engine.run(_collect_callback, print_summary=False)

    return {
        "samples_collected": samples_collected,
        "skipped_samples": skipped_samples,
        "output_path": str(dest),
        "seq_len": seq_len,
    }


def get_runtime_run(run_id: str) -> Dict[str, Any]:
    """讀取指定 replay runtime run。"""
    return load_run(run_id)
