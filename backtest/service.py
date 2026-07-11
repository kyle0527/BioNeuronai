"""Replay service layer for CLI/API/UI.

These helpers orchestrate replay runs and persist runtime artifacts.
They do not replace the project's strategy logic.
"""

from __future__ import annotations

import json
import logging
import math
import re
from collections import deque
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np

from bioneuronai.strategies.selector.profile import GoldenProfileManager

from .backtest_engine import BacktestConfig, BacktestEngine
from .data_stream import DEFAULT_DATA_DIR, resolve_data_dir
from .mock_connector import MockBinanceConnector
from .runtime_store import ReplayRunRecorder, list_runs, load_run

logger = logging.getLogger(__name__)


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


def _strategy_key_for_template(strategy_type: Any) -> Optional[str]:
    """Map selector config StrategyType values to executable strategy instances."""
    value = getattr(strategy_type, "value", str(strategy_type))
    return {
        "trend_following": "trend_following",
        "mean_reversion": "mean_reversion",
        "breakout": "breakout",
        "swing_trading": "swing_trading",
    }.get(value)


def _json_safe_stats(stats: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize stats before writing CLI/API summaries."""
    normalized: Dict[str, Any] = {}
    for key, value in stats.items():
        if isinstance(value, float) and not np.isfinite(value):
            normalized[key] = None
        else:
            normalized[key] = value
    return normalized


def _merge_nested_dict(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge parameter overrides without replacing unrelated template sections."""
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_nested_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def _load_parameter_overrides(
    parameter_overrides: Optional[Union[str, Path, Dict[str, Any]]],
) -> Dict[str, Any]:
    """Load per-strategy parameter overrides from JSON path or dict."""
    if parameter_overrides is None:
        return {}
    if isinstance(parameter_overrides, (str, Path)):
        path = Path(parameter_overrides)
        if not path.exists():
            raise FileNotFoundError(f"找不到策略參數覆蓋檔: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"策略參數覆蓋檔必須是 JSON object: {path}")
        return dict(payload)
    return dict(parameter_overrides)


def _template_runtime_config(template: Any, override: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert StrategyConfigTemplate to a mutable runtime config."""
    config = {
        "strategy_type": template.strategy_type.value,
        "name": template.name,
        "description": template.description,
        "entry_conditions": deepcopy(template.entry_conditions),
        "exit_conditions": deepcopy(template.exit_conditions),
        "risk_parameters": deepcopy(template.risk_parameters),
        "timeframe": template.timeframe,
        "min_capital": template.min_capital,
    }
    return _merge_nested_dict(config, override or {})


def _sma(values: np.ndarray, period: int) -> Optional[float]:
    if period <= 0 or len(values) < period:
        return None
    return float(np.mean(values[-period:]))


def _rsi(closes: np.ndarray, period: int = 14) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    deltas = np.diff(closes[-(period + 1):])
    gains = deltas[deltas > 0].sum() / period
    losses = abs(deltas[deltas < 0].sum()) / period
    if losses == 0:
        return 100.0
    rs = gains / losses
    return float(100 - (100 / (1 + rs)))


def _interval_minutes(interval: str) -> int:
    match = re.fullmatch(r"(\d+)([mhdw])", interval.strip().lower())
    if not match:
        return 60
    value = int(match.group(1))
    unit = match.group(2)
    if unit == "m":
        return value
    if unit == "h":
        return value * 60
    if unit == "d":
        return value * 1440
    return value * 10080


def _duration_to_bars(value: Any, interval: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return max(1, int(value))
    match = re.fullmatch(r"(\d+)([mhd])", str(value).strip().lower())
    if not match:
        return None
    amount = int(match.group(1))
    unit = match.group(2)
    minutes = amount if unit == "m" else amount * 60 if unit == "h" else amount * 1440
    return max(1, math.ceil(minutes / _interval_minutes(interval)))


def _annualized_volatility(closes: np.ndarray, interval: str, period: int = 48) -> Optional[float]:
    if len(closes) < period + 1:
        return None
    returns = np.diff(np.log(closes[-(period + 1):]))
    std = float(np.std(returns))
    if std == 0:
        return 0.0
    bars_per_year = 365 * 24 * 60 / _interval_minutes(interval)
    return std * math.sqrt(bars_per_year)


def _open_template_position(
    connector: MockBinanceConnector,
    *,
    symbol: str,
    direction: str,
    quantity: float,
    current_price: float,
    stop_loss_pct: float,
    profit_target_pct: float,
    state: Dict[str, Any],
    reason: str,
) -> None:
    side = "BUY" if direction == "LONG" else "SELL"
    order = connector.place_order(
        symbol=symbol,
        side=side,
        order_type="MARKET",
        quantity=quantity,
    )
    if order is None or order.status != "FILLED":
        return

    entry_price = float(order.price or current_price)
    if direction == "LONG":
        stop_price = entry_price * (1 - stop_loss_pct)
        take_profit_price = entry_price * (1 + profit_target_pct)
    else:
        stop_price = entry_price * (1 + stop_loss_pct)
        take_profit_price = entry_price * (1 - profit_target_pct)

    state.update(
        {
            "direction": direction,
            "entry_price": entry_price,
            "stop_price": stop_price,
            "take_profit_price": take_profit_price,
            "bars_held": 0,
            "entry_reason": reason,
            "best_price": entry_price,
        }
    )


def _close_template_position(
    connector: MockBinanceConnector,
    *,
    symbol: str,
    state: Dict[str, Any],
    reason: str,
) -> None:
    position = connector.account.get_position(symbol)
    if position is None or position.quantity <= 0:
        state.clear()
        return
    side = "SELL" if position.side.value == "LONG" else "BUY"
    connector.place_order(
        symbol=symbol,
        side=side,
        order_type="MARKET",
        quantity=position.quantity,
        reduce_only=True,
    )
    state.clear()
    state["last_exit_reason"] = reason


def _compute_walk_forward_split(
    start_date: Optional[str],
    end_date: Optional[str],
    split_ratio: float = 0.7,
) -> Optional[str]:
    """計算 Walk-Forward IS/OOS 切割日期（split_ratio% 為 IS，其餘為 OOS）。"""
    if not start_date or not end_date:
        return None
    from datetime import datetime as _dt
    from datetime import timedelta as _td
    try:
        start = _dt.strptime(start_date, "%Y-%m-%d")
        end = _dt.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return None
    total_days = (end - start).days
    if total_days <= 0:
        return None
    split_days = max(1, int(total_days * split_ratio))
    return (start + _td(days=split_days)).strftime("%Y-%m-%d")


def _template_entry_signal(
    template_key: str,
    config: Dict[str, Any],
    ohlcv: np.ndarray,
    interval: str,
) -> Optional[Dict[str, str]]:
    closes = ohlcv[:, 4]
    highs = ohlcv[:, 2]
    lows = ohlcv[:, 3]
    volumes = ohlcv[:, 5]
    current = float(closes[-1])
    previous = float(closes[-2])
    entry = config["entry_conditions"]

    if template_key == "MA_Crossover_Trend":
        fast_period = int(entry.get("fast_ma_period", 21))
        slow_period = int(entry.get("slow_ma_period", 50))
        fast = _sma(closes, fast_period)
        slow = _sma(closes, slow_period)
        prev_fast = _sma(closes[:-1], fast_period)
        prev_slow = _sma(closes[:-1], slow_period)
        if any(value is None for value in (fast, slow, prev_fast, prev_slow)):
            return None
        assert fast is not None
        assert slow is not None
        assert prev_fast is not None
        assert prev_slow is not None
        trend_strength = abs(fast - slow) / current
        threshold = min(float(entry.get("trend_strength_min", 0.6)) / 100, 0.01)
        if fast > slow and (prev_fast <= prev_slow or trend_strength >= threshold):
            return {"direction": "LONG", "reason": "fast_ma_above_slow_ma"}
        if fast < slow and (prev_fast >= prev_slow or trend_strength >= threshold):
            return {"direction": "SHORT", "reason": "fast_ma_below_slow_ma"}
        return None

    if template_key == "RSI_Mean_Reversion":
        rsi = _rsi(closes, int(entry.get("rsi_period", 14)))
        if rsi is None:
            return None
        if rsi <= float(entry.get("oversold_threshold", 30)):
            return {"direction": "LONG", "reason": "rsi_oversold"}
        if rsi >= float(entry.get("overbought_threshold", 70)):
            return {"direction": "SHORT", "reason": "rsi_overbought"}
        return None

    if template_key == "Momentum_Breakout":
        period = int(entry.get("momentum_period", 20))
        if len(closes) < period + 1:
            return None
        momentum = current / float(closes[-period]) - 1
        avg_volume = float(np.mean(volumes[-period:]))
        volume_ok = volumes[-1] >= avg_volume * float(entry.get("volume_multiplier", 1.5))
        threshold = float(entry.get("momentum_threshold", 0.02))
        if momentum >= threshold and volume_ok:
            return {"direction": "LONG", "reason": "positive_momentum_breakout"}
        if momentum <= -threshold and volume_ok:
            return {"direction": "SHORT", "reason": "negative_momentum_breakout"}
        return None

    if template_key == "High_Frequency_Scalp":
        range_ratio = (float(highs[-1]) - float(lows[-1])) / current
        liquidity = current * float(volumes[-1])
        spread_limit = max(float(entry.get("spread_threshold", 0.001)) * 10, 0.01)
        if range_ratio > spread_limit or liquidity < float(entry.get("liquidity_min", 1_000_000)):
            return None
        micro_ma = _sma(closes, 5)
        if micro_ma is None:
            return None
        if current > micro_ma and current > previous:
            return {"direction": "LONG", "reason": "micro_trend_up"}
        if current < micro_ma and current < previous:
            return {"direction": "SHORT", "reason": "micro_trend_down"}
        return None

    if template_key == "Grid_Trading":
        levels = max(2, int(entry.get("grid_levels", 10)))
        period = max(20, levels * 3)
        if len(closes) < period:
            return None
        recent_high = float(np.max(highs[-period:]))
        recent_low = float(np.min(lows[-period:]))
        middle = (recent_high + recent_low) / 2
        range_ratio = (recent_high - recent_low) / middle if middle > 0 else 0
        if range_ratio > 0.12:
            return None
        spacing = float(entry.get("grid_spacing", 0.01))
        if current <= middle * (1 - spacing):
            return {"direction": "LONG", "reason": "grid_lower_band"}
        if current >= middle * (1 + spacing):
            return {"direction": "SHORT", "reason": "grid_upper_band"}
        return None

    if template_key == "Volatility_Trading":
        vol = _annualized_volatility(closes, interval)
        if vol is None or vol < float(entry.get("volatility_spike", 0.3)):
            return None
        lookback = 24
        if len(closes) < lookback + 1:
            return None
        if current >= float(np.max(highs[-lookback:-1])):
            return {"direction": "LONG", "reason": "high_vol_upside_break"}
        if current <= float(np.min(lows[-lookback:-1])):
            return {"direction": "SHORT", "reason": "high_vol_downside_break"}
        return None

    if template_key == "News_Trading":
        period = 24
        if len(closes) < period + 1:
            return None
        avg_volume = float(np.mean(volumes[-period:]))
        volume_surge = volumes[-1] / avg_volume if avg_volume > 0 else 0
        price_return = current / previous - 1
        sentiment_proxy = max(-1.0, min(1.0, price_return / 0.02)) * min(volume_surge / 2, 1.5)
        threshold = float(entry.get("sentiment_threshold", 0.7))
        if volume_surge >= float(entry.get("volume_surge", 2.0)) and sentiment_proxy >= threshold:
            return {"direction": "LONG", "reason": "volume_sentiment_proxy_positive"}
        if volume_surge >= float(entry.get("volume_surge", 2.0)) and sentiment_proxy <= -threshold:
            return {"direction": "SHORT", "reason": "volume_sentiment_proxy_negative"}
        return None

    if template_key == "Breakout_Trading":
        period = int(entry.get("consolidation_period", 20))
        if len(closes) < period + 1:
            return None
        avg_volume = float(np.mean(volumes[-period:]))
        volume_ok = volumes[-1] >= avg_volume * float(entry.get("volume_confirmation", 1.5))
        threshold = float(entry.get("breakout_threshold", 0.02))
        prior_high = float(np.max(highs[-period - 1:-1]))
        prior_low = float(np.min(lows[-period - 1:-1]))
        if current >= prior_high * (1 + threshold / 2) and volume_ok:
            return {"direction": "LONG", "reason": "range_breakout_up"}
        if current <= prior_low * (1 - threshold / 2) and volume_ok:
            return {"direction": "SHORT", "reason": "range_breakout_down"}
        return None

    if template_key == "Swing_Trading":
        period = 48
        if len(closes) < period:
            return None
        recent_high = float(np.max(highs[-period:]))
        recent_low = float(np.min(lows[-period:]))
        ma = _sma(closes, 20)
        if ma is None:
            return None
        if current <= recent_low * 1.02 and current > previous and current > ma * 0.98:
            return {"direction": "LONG", "reason": "support_rebound"}
        if current >= recent_high * 0.98 and current < previous and current < ma * 1.02:
            return {"direction": "SHORT", "reason": "resistance_rejection"}
        return None

    if template_key == "Arbitrage_Trading":
        fair = _sma(closes, 20)
        if fair is None:
            return None
        spread = (current - fair) / fair
        threshold = float(entry.get("spread_threshold", 0.002))
        if spread >= threshold:
            return {"direction": "SHORT", "reason": "positive_spread_mean_revert"}
        if spread <= -threshold:
            return {"direction": "LONG", "reason": "negative_spread_mean_revert"}
        return None

    return None


def _template_should_exit(
    template_key: str,
    config: Dict[str, Any],
    state: Dict[str, Any],
    ohlcv: np.ndarray,
    interval: str,
) -> Optional[str]:
    closes = ohlcv[:, 4]
    current = float(closes[-1])
    direction = state.get("direction")
    if not direction:
        return None

    state["bars_held"] = int(state.get("bars_held", 0)) + 1
    if direction == "LONG":
        state["best_price"] = max(float(state.get("best_price", current)), current)
        if current <= float(state.get("stop_price", 0)):
            return "stop_loss"
        if current >= float(state.get("take_profit_price", float("inf"))):
            return "take_profit"
    else:
        state["best_price"] = min(float(state.get("best_price", current)), current)
        if current >= float(state.get("stop_price", float("inf"))):
            return "stop_loss"
        if current <= float(state.get("take_profit_price", 0)):
            return "take_profit"

    exit_cfg = config["exit_conditions"]
    time_exit = (
        exit_cfg.get("time_exit")
        or exit_cfg.get("max_grid_age")
        or exit_cfg.get("max_hold_time")
    )
    max_bars = _duration_to_bars(time_exit, interval)
    if max_bars is not None and state["bars_held"] >= max_bars:
        return "time_exit"

    if template_key == "RSI_Mean_Reversion":
        rsi = _rsi(closes, 14)
        neutral = float(exit_cfg.get("rsi_neutral", 50))
        if rsi is not None and ((direction == "LONG" and rsi >= neutral) or (direction == "SHORT" and rsi <= neutral)):
            return "rsi_neutral"

    if template_key == "MA_Crossover_Trend" and exit_cfg.get("ma_cross_reverse"):
        fast = _sma(closes, 21)
        slow = _sma(closes, 50)
        if fast is not None and slow is not None:
            if direction == "LONG" and fast < slow:
                return "ma_cross_reverse"
            if direction == "SHORT" and fast > slow:
                return "ma_cross_reverse"

    if template_key in {"Grid_Trading", "Arbitrage_Trading"}:
        fair = _sma(closes, 20)
        if fair is not None:
            spread = abs(current - fair) / fair
            close_threshold = float(exit_cfg.get("spread_close", exit_cfg.get("grid_spacing", 0.005)))
            if spread <= close_threshold:
                return "spread_closed"

    if template_key == "Volatility_Trading":
        vol = _annualized_volatility(closes, interval)
        if vol is not None and vol <= float(exit_cfg.get("volatility_normalize", 0.8)):
            return "volatility_normalized"

    return None


def run_template_strategy_backtest(
    template_key: str,
    template: Any,
    *,
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    balance: float = 10000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_dir: Optional[Union[str, Any]] = DEFAULT_DATA_DIR,
    warmup_bars: int = 100,
    close_open_positions_on_end: bool = True,
    commission_bps: float = 5.5,
    slippage_bps: float = 1.0,
    parameter_override: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run one StrategyConfigTemplate as a replay-backed rule strategy.

    Args:
        commission_bps: Taker commission in basis points (5.5 bps = 0.055%, Binance VIP0 +10% buffer).
        slippage_bps:   Slippage per fill in basis points (1 bp = 0.01%).
    """
    resolved_root = resolve_data_dir(data_dir)
    runtime_config = _template_runtime_config(template, parameter_override)
    recorder = ReplayRunRecorder(
        mode="strategy_template_backtest",
        config={
            "strategy": template_key,
            "strategy_name": runtime_config["name"],
            "strategy_type": runtime_config["strategy_type"],
            "execution_engine": "template_rules",
            "symbol": symbol,
            "interval": interval,
            "balance": balance,
            "start_date": start_date,
            "end_date": end_date,
            "data_dir": str(resolved_root),
            "warmup_bars": warmup_bars,
            "close_open_positions_on_end": close_open_positions_on_end,
            "commission_bps": commission_bps,
            "slippage_bps": slippage_bps,
            "runtime_config": runtime_config,
        },
    )
    state: Dict[str, Any] = {}

    def strategy_callback(bar: Any, connector: MockBinanceConnector) -> None:
        klines = connector.data_stream.get_klines_until_now(300)
        ohlcv = _klines_dicts_to_numpy(klines)
        if len(ohlcv) < max(20, warmup_bars):
            return

        if connector.has_open_position(bar.symbol):
            exit_reason = _template_should_exit(template_key, runtime_config, state, ohlcv, interval)
            if exit_reason:
                _close_template_position(
                    connector,
                    symbol=bar.symbol,
                    state=state,
                    reason=exit_reason,
                )
            return

        signal = _template_entry_signal(template_key, runtime_config, ohlcv, interval)
        if not signal:
            return

        exit_cfg = runtime_config["exit_conditions"]
        risk_cfg = runtime_config["risk_parameters"]
        stop_loss_pct = float(
            exit_cfg.get("stop_loss")
            or exit_cfg.get("spread_widen")
            or 0.02
        )
        profit_target_pct = float(
            exit_cfg.get("take_profit")
            or exit_cfg.get("profit_target")
            or exit_cfg.get("swing_target")
            or exit_cfg.get("profit_accumulation")
            or 0.03
        )
        equity = float(connector.get_total_equity())
        position_fraction = float(
            risk_cfg.get("position_size")
            or risk_cfg.get("total_grid_allocation", 0.05) / max(int(runtime_config["entry_conditions"].get("grid_levels", 1)), 1)
            or risk_cfg.get("volatility_allocation")
            or 0.03
        )
        notional = max(0.0, equity * min(position_fraction, 0.3))
        quantity = notional / float(bar.close) if bar.close > 0 else 0.0
        if quantity <= 0:
            return

        _open_template_position(
            connector,
            symbol=bar.symbol,
            direction=signal["direction"],
            quantity=quantity,
            current_price=float(bar.close),
            stop_loss_pct=stop_loss_pct,
            profit_target_pct=profit_target_pct,
            state=state,
            reason=signal["reason"],
        )

    _bt_config = BacktestConfig(
        data_dir=resolved_root,
        symbol=symbol,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        initial_balance=balance,
        warmup_bars=warmup_bars,
        close_open_positions_on_end=close_open_positions_on_end,
        taker_fee=commission_bps / 10_000,
        maker_fee=commission_bps / 20_000,
        slippage_rate=slippage_bps / 10_000,
    )
    engine = BacktestEngine(config=_bt_config, run_recorder=recorder)
    result = engine.run(strategy_callback, print_summary=False)
    stats = _json_safe_stats(dict(result.stats))
    stats["trade_count"] = len(result.trades)
    stats["equity_points"] = len(result.equity_curve)
    summary = {
        "strategy": template_key,
        "strategy_name": runtime_config["name"],
        "strategy_type": runtime_config["strategy_type"],
        "execution_engine": "template_rules",
        "symbol": symbol,
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date,
        "warmup_bars": warmup_bars,
        "close_open_positions_on_end": close_open_positions_on_end,
        "commission_bps": commission_bps,
        "slippage_bps": slippage_bps,
        "runtime_config": runtime_config,
        "stats": stats,
        "trade_count": len(result.trades),
        "open_positions_after": engine.connector.get_account_snapshot().get("positions_count", 0),
        "open_orders_after": engine.connector.get_account_snapshot().get("open_orders_count", 0),
        "trades": result.trades,
    }
    return recorder.finalize(summary)


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
    close_open_positions_on_end: bool = False,
    persist_runtime: bool = False,
    include_trades: bool = False,
    strategy_label: Optional[str] = None,
) -> Dict[str, Any]:
    """使用正式 replay 評估單一策略實例。"""
    resolved_root = resolve_data_dir(data_dir)
    label = strategy_label or getattr(strategy, "name", strategy.__class__.__name__)
    recorder = (
        ReplayRunRecorder(
            mode="strategy_backtest",
            config={
                "strategy": label,
                "symbol": symbol,
                "interval": interval,
                "balance": balance,
                "start_date": start_date,
                "end_date": end_date,
                "data_dir": str(resolved_root),
                "warmup_bars": warmup_bars,
                "close_open_positions_on_end": close_open_positions_on_end,
            },
        )
        if persist_runtime
        else None
    )

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
        run_recorder=recorder,
    )
    engine.config.warmup_bars = warmup_bars
    engine.config.close_open_positions_on_end = close_open_positions_on_end
    result = engine.run(strategy_callback, print_summary=False)
    stats = _json_safe_stats(dict(result.stats))
    stats["trade_count"] = len(result.trades)
    stats["equity_points"] = len(result.equity_curve)
    summary: Dict[str, Any] = {
        "strategy": label,
        "symbol": symbol,
        "interval": interval,
        "start_date": start_date,
        "end_date": end_date,
        "warmup_bars": warmup_bars,
        "close_open_positions_on_end": close_open_positions_on_end,
        "stats": stats,
        "trade_count": len(result.trades),
        "open_positions_after": engine.connector.get_account_snapshot().get("positions_count", 0),
        "open_orders_after": engine.connector.get_account_snapshot().get("open_orders_count", 0),
    }
    if include_trades:
        summary["trades"] = result.trades
    if recorder:
        return recorder.finalize(summary)
    if include_trades or close_open_positions_on_end:
        return summary
    return stats


def run_strategy_suite_backtest(
    *,
    symbol: str = "BTCUSDT",
    interval: str = "1h",
    balance: float = 10000.0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_dir: Optional[Union[str, Any]] = DEFAULT_DATA_DIR,
    warmup_bars: int = 100,
    close_open_positions_on_end: bool = True,
    execution_mode: str = "template_rules",
    parameter_overrides: Optional[Union[str, Path, Dict[str, Any]]] = None,
    commission_bps: float = 5.5,
    slippage_bps: float = 1.0,
    walk_forward: bool = False,
    update_golden_profile: bool = True,
) -> Dict[str, Any]:
    """逐一用正式策略實例跑 replay，保留每個策略的進出場紀錄。

    Args:
        commission_bps:  Taker commission in basis points (5.5 bps = 0.055%, Binance VIP0 +10% buffer).
        slippage_bps:    Slippage per fill in basis points (1 bp = 0.01%).
        walk_forward:    若為 True 且 start_date/end_date 已設定，
                         自動在 70%/30% 切割點執行 IS+OOS 兩段回測。
    """
    from bioneuronai.strategies.selector.core import StrategySelector

    resolved_root = resolve_data_dir(data_dir)

    # Walk-forward: modify end_date to IS period, run OOS separately afterward
    _original_end_date = end_date
    _wf_split_date: Optional[str] = None
    if walk_forward:
        _wf_split_date = _compute_walk_forward_split(start_date, end_date)
        if _wf_split_date:
            end_date = _wf_split_date  # main loop = IS period only

    overrides = _load_parameter_overrides(parameter_overrides)
    selector = StrategySelector(
        timeframe=interval,
        enable_ai_fusion=False,
        enable_learning=False,
    )
    templates = selector.strategy_configs
    executable: List[Dict[str, Any]] = []
    unavailable: List[Dict[str, Any]] = []

    for template_key, template in templates.items():
        strategy_key = _strategy_key_for_template(template.strategy_type)
        try:
            if execution_mode == "hybrid" and strategy_key in selector._strategies:
                strategy = selector._strategies[strategy_key]
                run = run_strategy_instance_backtest(
                    strategy,
                    symbol=symbol,
                    interval=interval,
                    balance=balance,
                    start_date=start_date,
                    end_date=end_date,
                    data_dir=resolved_root,
                    warmup_bars=warmup_bars,
                    close_open_positions_on_end=close_open_positions_on_end,
                    persist_runtime=True,
                    include_trades=True,
                    strategy_label=template_key,
                )
                run["execution_engine"] = "strategy_class"
            else:
                run = run_template_strategy_backtest(
                    template_key,
                    template,
                    symbol=symbol,
                    interval=interval,
                    balance=balance,
                    start_date=start_date,
                    end_date=end_date,
                    data_dir=resolved_root,
                    warmup_bars=warmup_bars,
                    close_open_positions_on_end=close_open_positions_on_end,
                    commission_bps=commission_bps,
                    slippage_bps=slippage_bps,
                    parameter_override=overrides.get(template_key),
                )
        except Exception as exc:
            unavailable.append(
                {
                    "template_key": template_key,
                    "name": template.name,
                    "strategy_type": template.strategy_type.value,
                    "executable": False,
                    "reason": str(exc),
                }
            )
            continue
        stats = run.get("stats", {})
        executable.append(
            {
                "template_key": template_key,
                "name": template.name,
                "strategy_type": template.strategy_type.value,
                "executable": True,
                "execution_engine": run.get("execution_engine", execution_mode),
                "run_id": run.get("run_id"),
                "run_dir": run.get("run_dir"),
                "orders_recorded": run.get("orders_recorded", 0),
                "fills_recorded": run.get("fills_recorded", 0),
                "trade_count": run.get("trade_count", 0),
                "open_positions_after": run.get("open_positions_after", 0),
                "open_orders_after": run.get("open_orders_after", 0),
                "stats": stats,
                "trades_sample": run.get("trades", [])[:5],
            }
        )

    ranking = sorted(
        executable,
        key=lambda item: float(item.get("stats", {}).get("total_return") or -10**9),
        reverse=True,
    )
    result: Dict[str, Any] = {
        "mode": "strategy_suite_backtest",
        "resolved_root": str(resolved_root),
        "symbol": symbol,
        "interval": interval,
        "balance": balance,
        "start_date": start_date,
        "end_date": end_date,
        "warmup_bars": warmup_bars,
        "close_open_positions_on_end": close_open_positions_on_end,
        "execution_mode": execution_mode,
        "commission_bps": commission_bps,
        "slippage_bps": slippage_bps,
        "parameter_overrides_applied": sorted(overrides.keys()),
        "total_templates": len(templates),
        "executable_count": len(executable),
        "unavailable_count": len(unavailable),
        "executable": executable,
        "unavailable": unavailable,
        "ranking": ranking,
    }

    # Walk-forward OOS pass
    if walk_forward and _wf_split_date and _original_end_date:
        oos_pass = run_strategy_suite_backtest(
            symbol=symbol,
            interval=interval,
            balance=balance,
            start_date=_wf_split_date,
            end_date=_original_end_date,
            data_dir=resolved_root,
            warmup_bars=warmup_bars,
            close_open_positions_on_end=close_open_positions_on_end,
            execution_mode=execution_mode,
            parameter_overrides=parameter_overrides,
            commission_bps=commission_bps,
            slippage_bps=slippage_bps,
            walk_forward=False,  # 避免無限遞迴
            update_golden_profile=update_golden_profile,
        )
        result["walk_forward"] = {
            "enabled": True,
            "split_date": _wf_split_date,
            "is_period": f"{start_date} ~ {_wf_split_date}",
            "oos_period": f"{_wf_split_date} ~ {_original_end_date}",
            "oos_executable_count": oos_pass.get("executable_count", 0),
            "oos_ranking": oos_pass.get("ranking", []),
        }
    elif walk_forward and not _wf_split_date:
        result["walk_forward"] = {
            "enabled": False,
            "reason": "walk_forward 需要同時提供 --start-date 和 --end-date",
        }

    # 自動生成並固化 Golden Profile (整合後的策略配置)
    if update_golden_profile:
        try:
            GoldenProfileManager.generate_from_backtest(result)
        except Exception as e:
            logger.error(f"自動生成 Golden Profile 失敗: {e}")

    return result


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
# 訓練資料收集：輸出 unified v2 真實未來行情標籤供 unified_trainer 使用
# ============================================================================

def _one_hot(size: int, index: int) -> np.ndarray:
    values = np.zeros(size, dtype=np.float32)
    values[max(0, min(size - 1, index))] = 1.0
    return values


def _hold_period_index(minutes: int) -> int:
    buckets = [5, 15, 60, 240, 1440, 2880, 4320, 10080, 20160]
    return min(range(len(buckets)), key=lambda index: abs(buckets[index] - minutes))


def _build_v2_signal_target(
    entry_price: float,
    future_bars: List[Any],
    interval: str,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    """依真實未來 K 線建立 65 維監督目標，不使用任何模型預測。"""
    closes = np.asarray([float(bar.close) for bar in future_bars], dtype=np.float64)
    highs = np.asarray([float(bar.high) for bar in future_bars], dtype=np.float64)
    lows = np.asarray([float(bar.low) for bar in future_bars], dtype=np.float64)
    returns = closes / entry_price - 1.0
    final_return = float(returns[-1])
    path_volatility = float(np.std(np.diff(np.log(np.maximum(closes, 1e-12)))))
    direction_threshold = max(0.001, path_volatility * 1.5)
    direction_index = 0 if final_return > direction_threshold else 2 if final_return < -direction_threshold else 1

    target = np.zeros(65, dtype=np.float32)
    target[0:3] = _one_hot(3, direction_index)
    move_strength = abs(final_return) / max(path_volatility, 0.001)
    confidence_index = 2 if move_strength >= 4 else 1 if move_strength >= 2 else 0
    target[3:6] = _one_hot(3, confidence_index)

    leverage = max(1, min(10, int(0.02 / max(path_volatility, 0.002))))
    target[6:16] = _one_hot(10, leverage - 1)
    target[16] = min(1.0, abs(final_return) / 0.05)

    if direction_index == 0:
        favorable = max(0.0, float(np.max(highs / entry_price - 1.0)))
        adverse = max(0.0, float(np.max(1.0 - lows / entry_price)))
        best_index = int(np.argmax(highs))
    elif direction_index == 2:
        favorable = max(0.0, float(np.max(1.0 - lows / entry_price)))
        adverse = max(0.0, float(np.max(highs / entry_price - 1.0)))
        best_index = int(np.argmin(lows))
    else:
        favorable = abs(final_return)
        adverse = float(np.max(np.abs(returns)))
        best_index = len(future_bars) - 1
    target[17] = min(0.10, adverse)
    target[18] = min(0.20, favorable)

    hold_minutes = (best_index + 1) * _interval_minutes(interval)
    target[19:29] = _one_hot(10, _hold_period_index(hold_minutes))
    checkpoints = np.linspace(0, len(returns) - 1, 5, dtype=int)
    target[29:34] = np.clip(returns[checkpoints] / max(direction_threshold, 1e-6), -1.0, 1.0)

    last_bar = future_bars[-1]
    previous_bar = future_bars[-2]
    candle_range = max(float(last_bar.high) - float(last_bar.low), 1e-12)
    body_ratio = abs(float(last_bar.close) - float(last_bar.open)) / candle_range
    if body_ratio < 0.1:
        target[53] = 1.0  # doji
    elif (
        float(previous_bar.close) < float(previous_bar.open)
        and float(last_bar.close) > float(last_bar.open)
        and float(last_bar.open) <= float(previous_bar.close)
        and float(last_bar.close) >= float(previous_bar.open)
    ):
        target[51] = 1.0  # engulfing_bull
    elif (
        float(previous_bar.close) > float(previous_bar.open)
        and float(last_bar.close) < float(last_bar.open)
        and float(last_bar.open) >= float(previous_bar.close)
        and float(last_bar.close) <= float(previous_bar.open)
    ):
        target[52] = 1.0  # engulfing_bear

    path_efficiency = abs(final_return) / max(float(np.sum(np.abs(np.diff(closes) / closes[:-1]))), 1e-6)
    target[54] = float(np.clip(1.0 - path_efficiency, 0.0, 1.0))
    if final_return > direction_threshold * 3:
        regime_index = 0
    elif final_return > direction_threshold:
        regime_index = 1
    elif final_return < -direction_threshold * 3:
        regime_index = 6
    elif final_return < -direction_threshold:
        regime_index = 5
    elif path_volatility > 0.03:
        regime_index = 4
    else:
        regime_index = 2
    target[55:65] = _one_hot(10, regime_index)
    outcome = {
        "final_return": final_return,
        "favorable_move": favorable,
        "adverse_move": adverse,
        "path_volatility": path_volatility,
        "direction_index": direction_index,
        "hold_minutes": hold_minutes,
        "regime_index": regime_index,
    }
    return target, outcome


def _build_bilingual_training_text(
    symbol: str,
    interval: str,
    entry_price: float,
    outcome: Dict[str, Any],
) -> Tuple[str, str]:
    direction = {0: ("做多", "LONG"), 1: ("觀望", "HOLD"), 2: ("做空", "SHORT")}[outcome["direction_index"]]
    context = (
        f"{symbol} {interval}，進場觀察價 {entry_price:.8f}。"
        f"Market context for {symbol} on {interval}; observed price {entry_price:.8f}."
    )
    explanation = (
        f"真實未來區間結果支持{direction[0]}：報酬 {outcome['final_return']:.4%}，"
        f"最大有利移動 {outcome['favorable_move']:.4%}，最大不利移動 {outcome['adverse_move']:.4%}。 "
        f"Real future outcome supports {direction[1]}: return {outcome['final_return']:.4%}, "
        f"maximum favorable excursion {outcome['favorable_move']:.4%}, "
        f"maximum adverse excursion {outcome['adverse_move']:.4%}."
    )
    return context, explanation


def _extract_features(
    feature_pipeline: Any,
    bar: Any,
    connector: Any,
) -> Optional[List[Any]]:
    """提取當前 bar 的 1024 維特徵；資料不足或出錯時返回 None。"""
    klines = connector.data_stream.get_klines_until_now(300)
    if len(klines) < 30:
        return None
    try:
        features = feature_pipeline.build_features(
            current_price=bar.close,
            klines=klines,
        )
        return list(features.tolist())
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
    future_horizon: int = 12,
) -> Dict[str, Any]:
    """
    運行回測並從真實未來行情建立 v2 數值、決策與雙語說明配對資料。

    每行格式：
    {
        "features": [[f0...f63], ...(共 seq_len 行)],
        "signal": [s0, ..., s64],
        "context_text": "中英市場脈絡",
        "explanation": "依真實未來結果建立的中英說明"
    }

    輸出檔案預設位置：data/unified_v2_training.jsonl
    可直接作為 unified_trainer.py --signal-data 的輸入。

    Args:
        seq_len:      每個樣本包含幾個歷史時間步
        output_path:  JSONL 輸出路徑（None 則用 data/unified_v2_training.jsonl）
        max_samples:  最多收集幾筆（避免過大）
        future_horizon: 每筆 label 使用幾根真實未來 K 線

    Returns:
        {"samples_collected": N, "output_path": "..."}
    """
    import sys
    if future_horizon < 2:
        raise ValueError("future_horizon 必須至少為 2")
    _root = Path(__file__).resolve().parents[1]
    for p in [str(_root / "src"), str(_root)]:
        if p not in sys.path:
            sys.path.insert(0, p)

    try:
        from bioneuronai.core.inference_engine import FeaturePipeline
    except Exception as exc:
        return {"error": f"InferenceEngine 不可用: {exc}", "samples_collected": 0}

    resolved_root = resolve_data_dir(data_dir)
    dest = Path(output_path) if output_path else (_root / "data" / "unified_v2_training.jsonl")
    dest.parent.mkdir(parents=True, exist_ok=True)

    feature_pipeline = FeaturePipeline()
    buf: deque = deque(maxlen=seq_len)
    pending: deque = deque()
    samples_collected = 0
    skipped_samples = 0

    def _write_ready_samples(bar: Any, output_file: Any) -> None:
        nonlocal samples_collected
        for item in pending:
            item["future_bars"].append(bar)
        while pending and len(pending[0]["future_bars"]) >= future_horizon:
            item = pending.popleft()
            target, outcome = _build_v2_signal_target(
                item["entry_price"], item["future_bars"], interval
            )
            context, explanation = _build_bilingual_training_text(
                symbol, interval, item["entry_price"], outcome
            )
            record = {
                "features": item["features"],
                "signal": target.tolist(),
                "context_text": context,
                "explanation": explanation,
                "future_outcome": outcome,
            }
            output_file.write(json.dumps(record, ensure_ascii=False) + "\n")
            samples_collected += 1
            if samples_collected >= max_samples:
                pending.clear()
                return

    output_file = open(dest, "w", encoding="utf-8")

    def _collect_callback(bar: Any, connector: Any) -> None:
        nonlocal skipped_samples
        _write_ready_samples(bar, output_file)
        if samples_collected >= max_samples:
            connector.data_stream.stop()
            return
        feats = _extract_features(feature_pipeline, bar, connector)
        if feats is None:
            skipped_samples += 1
            return
        buf.append(feats)
        if len(buf) < seq_len or samples_collected >= max_samples:
            return
        compact = feature_pipeline.to_v2_patch(
            np.asarray(list(buf), dtype=np.float32)
        )
        pending.append(
            {
                "features": compact.tolist(),
                "entry_price": float(bar.close),
                "future_bars": [],
            }
        )

    try:
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
    finally:
        output_file.close()
    skipped_samples += len(pending)

    return {
        "samples_collected": samples_collected,
        "skipped_samples": skipped_samples,
        "output_path": str(dest),
        "seq_len": seq_len,
        "future_horizon": future_horizon,
        "label_source": "real_future_market_outcome",
    }


def get_runtime_run(run_id: str) -> Dict[str, Any]:
    """讀取指定 replay runtime run。"""
    return load_run(run_id)


# ============================================================================
# 策略選擇器反饋：將回測排名轉換為 StrategySelector 可用的性能權重
# ============================================================================

def build_selector_performance_weights(
    suite_result: Dict[str, Any],
    metric: str = "sharpe_ratio",
) -> Dict[str, float]:
    """從策略組合回測結果中提取 StrategySelector 用的性能權重。

    按 strategy_type 聚合指定指標（預設為 sharpe_ratio），
    正規化為 [0, 1] 的歸一化權重字典，可直接傳入
    ``StrategySelector.load_performance_weights()``。

    Args:
        suite_result: ``run_strategy_suite_backtest()`` 的回傳值。
        metric:       聚合指標，支援 stats 中的任何數值欄位，
                      例如 ``sharpe_ratio``、``total_return``、``profit_factor``。

    Returns:
        ``{strategy_type_value: normalized_weight}``，
        例如 ``{"trend_following": 0.4, "mean_reversion": 0.35, ...}``。
    """
    type_values: Dict[str, List[float]] = {}
    for item in suite_result.get("ranking", []):
        stype = item.get("strategy_type")
        if not stype:
            continue
        stats = item.get("stats", {})
        raw = stats.get(metric)
        value = float(raw) if raw is not None and np.isfinite(float(raw)) else 0.0
        type_values.setdefault(stype, []).append(value)

    if not type_values:
        return {}

    # 按 strategy_type 取平均
    type_avg: Dict[str, float] = {
        stype: sum(vals) / len(vals) for stype, vals in type_values.items()
    }

    # 平移至非負域
    min_val = min(type_avg.values())
    if min_val < 0:
        type_avg = {k: v - min_val for k, v in type_avg.items()}

    # 歸一化
    total = sum(type_avg.values())
    if total > 0:
        return {k: round(v / total, 6) for k, v in type_avg.items()}
    # 若全為 0，返回均等權重
    n = len(type_avg)
    return {k: round(1.0 / n, 6) for k in type_avg}
