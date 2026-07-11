"""Trading readiness gate for pre-live validation.

This module turns the BTC/ETH multi-timeframe backtest requirement into a
runtime command. It uses the existing strategy suite replay path and produces a
single PASS/FAIL artifact that can be reviewed before testnet or live trading.
"""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .catalog import get_catalog
from .data_stream import DEFAULT_DATA_DIR, resolve_data_dir
from .service import run_strategy_suite_backtest

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "trading_readiness_gate.json"


DEFAULT_GATE_CONFIG: Dict[str, Any] = {
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "intervals": ["1h", "4h"],
    "start_date": "2020-01-01",
    "end_date": "2020-03-31",
    "balance": 10000.0,
    "warmup_bars": 100,
    "execution_mode": "template_rules",
    "commission_bps": 4.0,
    "slippage_bps": 1.0,
    "walk_forward": True,
    "thresholds": {
        "min_executable_count": 1,
        "max_unavailable_count": 0,
        "min_best_trade_count": 1,
        "min_best_total_return": -20.0,
        "max_best_drawdown": 35.0,
        "min_best_profit_factor": 0.0,
        "require_walk_forward": True,
        "min_oos_executable_count": 1,
        "min_best_oos_total_return": -25.0,
    },
}


def load_readiness_gate_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load readiness-gate JSON config, falling back to built-in defaults."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if not path.exists():
        return dict(DEFAULT_GATE_CONFIG)

    loaded = json.loads(path.read_text(encoding="utf-8"))
    config = dict(DEFAULT_GATE_CONFIG)
    config.update({k: v for k, v in loaded.items() if k != "thresholds"})
    thresholds = dict(DEFAULT_GATE_CONFIG["thresholds"])
    thresholds.update(loaded.get("thresholds", {}) or {})
    config["thresholds"] = thresholds
    return config


def run_trading_readiness_gate(
    *,
    config_path: Optional[Union[str, Path]] = None,
    symbols: Optional[List[str]] = None,
    intervals: Optional[List[str]] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    data_dir: Optional[Union[str, Path]] = None,
    output: Optional[Union[str, Path]] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Run the configured readiness matrix and return a PASS/FAIL report."""
    config = load_readiness_gate_config(config_path)
    if symbols:
        config["symbols"] = symbols
    if intervals:
        config["intervals"] = intervals
    if start_date:
        config["start_date"] = start_date
    if end_date:
        config["end_date"] = end_date
    if data_dir is not None:
        config["data_dir"] = str(data_dir)

    resolved_root = resolve_data_dir(config.get("data_dir", data_dir or DEFAULT_DATA_DIR))
    catalog = get_catalog(data_dir=resolved_root)
    datasets_value = catalog.get("datasets", [])
    datasets = datasets_value if isinstance(datasets_value, list) else []
    dataset_map = {
        (str(item["symbol"]).upper(), str(item["interval"])): item
        for item in datasets
        if isinstance(item, dict) and "symbol" in item and "interval" in item
    }

    report: Dict[str, Any] = {
        "mode": "trading_readiness_gate",
        "status": "DRY_RUN" if dry_run else "PASS",
        "generated_at": datetime.now().isoformat(),
        "config_path": str(Path(config_path).resolve()) if config_path else str(DEFAULT_CONFIG_PATH),
        "data_root": str(resolved_root),
        "symbols": config["symbols"],
        "intervals": config["intervals"],
        "start_date": config.get("start_date"),
        "end_date": config.get("end_date"),
        "thresholds": config["thresholds"],
        "cases": [],
        "summary": {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "planned": 0,
        },
    }

    for symbol in config["symbols"]:
        for interval in config["intervals"]:
            case = _run_gate_case(
                symbol=str(symbol).upper(),
                interval=str(interval),
                config=config,
                dataset_map=dataset_map,
                resolved_root=resolved_root,
                dry_run=dry_run,
            )
            report["cases"].append(case)
            report["summary"]["total"] += 1
            if case["status"] == "PASS":
                report["summary"]["passed"] += 1
            elif case["status"] == "PLANNED":
                report["summary"]["planned"] += 1
            else:
                report["summary"]["failed"] += 1

    if not dry_run and report["summary"]["failed"] > 0:
        report["status"] = "FAIL"

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(_json_safe(report), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        report["output"] = str(output_path)

    return report


def _run_gate_case(
    *,
    symbol: str,
    interval: str,
    config: Dict[str, Any],
    dataset_map: Dict[tuple[str, str], Dict[str, Any]],
    resolved_root: Path,
    dry_run: bool,
) -> Dict[str, Any]:
    dataset = dataset_map.get((symbol, interval))
    case: Dict[str, Any] = {
        "symbol": symbol,
        "interval": interval,
        "status": "PLANNED" if dry_run else "PASS",
        "checks": [],
    }

    if dataset is None:
        case["status"] = "FAIL"
        case["checks"].append(_check(False, "dataset_available", f"missing {symbol} {interval} replay dataset"))
        return case

    case["dataset"] = dataset
    case["checks"].append(_check(True, "dataset_available", "replay dataset found"))
    case["checks"].extend(_check_dataset_coverage(dataset, config))

    if any(not item["passed"] for item in case["checks"]):
        case["status"] = "FAIL"
        return case

    if dry_run:
        return case

    result = run_strategy_suite_backtest(
        symbol=symbol,
        interval=interval,
        balance=float(config.get("balance", 10000.0)),
        start_date=config.get("start_date"),
        end_date=config.get("end_date"),
        data_dir=resolved_root,
        warmup_bars=int(config.get("warmup_bars", 100)),
        close_open_positions_on_end=True,
        execution_mode=str(config.get("execution_mode", "template_rules")),
        commission_bps=float(config.get("commission_bps", 4.0)),
        slippage_bps=float(config.get("slippage_bps", 1.0)),
        walk_forward=bool(config.get("walk_forward", True)),
        update_golden_profile=False,
    )

    case["result"] = _summarize_strategy_result(result)
    case["checks"].extend(_check_strategy_result(result, config["thresholds"]))
    if any(not item["passed"] for item in case["checks"]):
        case["status"] = "FAIL"
    return case


def _check_dataset_coverage(dataset: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    start = config.get("start_date")
    end = config.get("end_date")
    dataset_start = dataset.get("start_date")
    dataset_end = dataset.get("end_date")

    if start and dataset_start:
        checks.append(_check(str(dataset_start) <= str(start), "dataset_start_covers", f"{dataset_start} <= {start}"))
    if end and dataset_end:
        checks.append(_check(str(dataset_end) >= str(end), "dataset_end_covers", f"{dataset_end} >= {end}"))
    return checks


def _check_strategy_result(result: Dict[str, Any], thresholds: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks: List[Dict[str, Any]] = []
    executable_count = int(result.get("executable_count", 0) or 0)
    unavailable_count = int(result.get("unavailable_count", 0) or 0)
    best = (result.get("ranking") or [{}])[0]
    best_stats = best.get("stats", {}) if isinstance(best, dict) else {}

    checks.append(_check(
        executable_count >= int(thresholds.get("min_executable_count", 1)),
        "min_executable_count",
        f"{executable_count} >= {thresholds.get('min_executable_count', 1)}",
    ))
    checks.append(_check(
        unavailable_count <= int(thresholds.get("max_unavailable_count", 0)),
        "max_unavailable_count",
        f"{unavailable_count} <= {thresholds.get('max_unavailable_count', 0)}",
    ))
    checks.append(_check(
        int(best.get("trade_count", 0) or 0) >= int(thresholds.get("min_best_trade_count", 1)),
        "min_best_trade_count",
        f"{int(best.get('trade_count', 0) or 0)} >= {thresholds.get('min_best_trade_count', 1)}",
    ))
    checks.append(_check(
        _float(best_stats.get("total_return")) >= float(thresholds.get("min_best_total_return", -20.0)),
        "min_best_total_return",
        f"{_float(best_stats.get('total_return')):.4f} >= {thresholds.get('min_best_total_return', -20.0)}",
    ))
    checks.append(_check(
        _float(best_stats.get("max_drawdown")) <= float(thresholds.get("max_best_drawdown", 35.0)),
        "max_best_drawdown",
        f"{_float(best_stats.get('max_drawdown')):.4f} <= {thresholds.get('max_best_drawdown', 35.0)}",
    ))
    checks.append(_check(
        _float(best_stats.get("profit_factor"), default=0.0, inf_value=999999.0)
        >= float(thresholds.get("min_best_profit_factor", 0.0)),
        "min_best_profit_factor",
        f"{_float(best_stats.get('profit_factor'), default=0.0, inf_value=999999.0):.4f} >= {thresholds.get('min_best_profit_factor', 0.0)}",
    ))

    wf = result.get("walk_forward") or {}
    if bool(thresholds.get("require_walk_forward", True)):
        checks.append(_check(bool(wf.get("enabled")), "walk_forward_enabled", str(wf.get("enabled", False))))
        if wf.get("enabled"):
            oos_ranking = wf.get("oos_ranking") or []
            oos_best = oos_ranking[0] if oos_ranking else {}
            oos_stats = oos_best.get("stats", {}) if isinstance(oos_best, dict) else {}
            checks.append(_check(
                int(wf.get("oos_executable_count", 0) or 0) >= int(thresholds.get("min_oos_executable_count", 1)),
                "min_oos_executable_count",
                f"{int(wf.get('oos_executable_count', 0) or 0)} >= {thresholds.get('min_oos_executable_count', 1)}",
            ))
            checks.append(_check(
                _float(oos_stats.get("total_return")) >= float(thresholds.get("min_best_oos_total_return", -25.0)),
                "min_best_oos_total_return",
                f"{_float(oos_stats.get('total_return')):.4f} >= {thresholds.get('min_best_oos_total_return', -25.0)}",
            ))

    return checks


def _summarize_strategy_result(result: Dict[str, Any]) -> Dict[str, Any]:
    ranking = result.get("ranking") or []
    best = ranking[0] if ranking else {}
    wf = result.get("walk_forward") or {}
    oos_ranking = wf.get("oos_ranking") or []
    return {
        "symbol": result.get("symbol"),
        "interval": result.get("interval"),
        "executable_count": result.get("executable_count"),
        "unavailable_count": result.get("unavailable_count"),
        "best_template": best.get("template_key") if isinstance(best, dict) else None,
        "best_stats": best.get("stats", {}) if isinstance(best, dict) else {},
        "walk_forward": {
            "enabled": wf.get("enabled", False),
            "split_date": wf.get("split_date"),
            "is_period": wf.get("is_period"),
            "oos_period": wf.get("oos_period"),
            "oos_executable_count": wf.get("oos_executable_count"),
            "oos_best_template": oos_ranking[0].get("template_key") if oos_ranking else None,
            "oos_best_stats": oos_ranking[0].get("stats", {}) if oos_ranking else {},
        },
    }


def _check(passed: bool, name: str, detail: str) -> Dict[str, Any]:
    return {"name": name, "passed": bool(passed), "detail": detail}


def _float(value: Any, *, default: float = 0.0, inf_value: float = 999999.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    if math.isinf(parsed):
        return inf_value
    if math.isnan(parsed):
        return default
    return parsed


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, float):
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"
        if math.isnan(value):
            return None
    return value


__all__ = [
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_GATE_CONFIG",
    "load_readiness_gate_config",
    "run_trading_readiness_gate",
]
