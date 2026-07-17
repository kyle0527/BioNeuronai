"""Rolling multi-window walk-forward validation.

Recovered design from the pre-cleanup ``archived/backtesting/walk_forward.py``
(commit parent of ``9f6e271``), re-implemented against the current
``run_strategy_suite_backtest`` service so results come from real CLI/runtime
paths — not unit tests.

Modes
-----
- **single**: one 70/30 (or custom ratio) IS/OOS split (legacy simple behaviour).
- **rolling**: rolling train/test windows with degradation / robustness metrics
  (old preferred design). Falls back to single when the range is too short.

Legacy ``param_grid`` / train-window optimize then OOS validate is ported via
``param_grid`` / ``wf_param_grid`` (see ``expand_param_grid_candidates``).
Legacy source: ``docs/archive/recovered_from_git/backtesting/walk_forward.py``.
"""

from __future__ import annotations

import itertools
import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

logger = logging.getLogger(__name__)

DEFAULT_TRAIN_DAYS = 90
DEFAULT_TEST_DAYS = 30
DEFAULT_STEP_DAYS = 30
DEFAULT_SINGLE_SPLIT_RATIO = 0.7
# Sharpe (or return) degradation above this % marks a fold as overfit-like.
OVERFIT_DEGRADATION_PCT = 30.0


@dataclass(frozen=True)
class WalkForwardWindow:
    """One rolling IS/OOS pair."""

    window_id: int
    train_start: str  # YYYY-MM-DD
    train_end: str
    test_start: str
    test_end: str

    @property
    def train_days(self) -> int:
        return (
            datetime.strptime(self.train_end, "%Y-%m-%d")
            - datetime.strptime(self.train_start, "%Y-%m-%d")
        ).days

    @property
    def test_days(self) -> int:
        return (
            datetime.strptime(self.test_end, "%Y-%m-%d")
            - datetime.strptime(self.test_start, "%Y-%m-%d")
        ).days

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def compute_single_split_date(
    start_date: Optional[str],
    end_date: Optional[str],
    split_ratio: float = DEFAULT_SINGLE_SPLIT_RATIO,
) -> Optional[str]:
    """IS/OOS cut date for single-split mode (ratio of total calendar days)."""
    if not start_date or not end_date:
        return None
    try:
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return None
    total_days = (end - start).days
    if total_days <= 0:
        return None
    split_days = max(1, int(total_days * split_ratio))
    return (start + timedelta(days=split_days)).strftime("%Y-%m-%d")


def generate_rolling_windows(
    start_date: str,
    end_date: str,
    *,
    train_window_days: int = DEFAULT_TRAIN_DAYS,
    test_window_days: int = DEFAULT_TEST_DAYS,
    step_days: int = DEFAULT_STEP_DAYS,
) -> List[WalkForwardWindow]:
    """Generate non-leaking rolling windows (train then immediately following test).

    Design recovered from legacy ``WalkForwardTester.generate_windows``:
    train [t, t+train), test [t+train, t+train+test); advance by ``step_days``.
    """
    try:
        overall_start = datetime.strptime(start_date, "%Y-%m-%d")
        overall_end = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(
            f"walk-forward 日期需為 YYYY-MM-DD: start={start_date!r} end={end_date!r}"
        ) from exc

    if overall_end <= overall_start:
        return []

    train_window_days = max(1, int(train_window_days))
    test_window_days = max(1, int(test_window_days))
    step_days = max(1, int(step_days))

    windows: List[WalkForwardWindow] = []
    window_id = 1
    current_train_start = overall_start

    while True:
        train_end = current_train_start + timedelta(days=train_window_days)
        test_start = train_end
        test_end = test_start + timedelta(days=test_window_days)
        if test_end > overall_end:
            break
        windows.append(
            WalkForwardWindow(
                window_id=window_id,
                train_start=current_train_start.strftime("%Y-%m-%d"),
                train_end=train_end.strftime("%Y-%m-%d"),
                test_start=test_start.strftime("%Y-%m-%d"),
                test_end=test_end.strftime("%Y-%m-%d"),
            )
        )
        window_id += 1
        current_train_start += timedelta(days=step_days)

    logger.info(
        "Walk-forward rolling: %d windows (train=%dd test=%dd step=%dd) %s → %s",
        len(windows),
        train_window_days,
        test_window_days,
        step_days,
        start_date,
        end_date,
    )
    return windows


def _metric_from_suite(result: Dict[str, Any], metric: str = "total_return") -> float:
    """Best ranking entry metric from a strategy-suite result."""
    ranking = result.get("ranking") or []
    if not ranking:
        return 0.0
    stats = ranking[0].get("stats") or {}
    raw = stats.get(metric)
    if raw is None and metric == "total_return":
        raw = stats.get("sharpe_ratio")
    try:
        return float(raw or 0.0)
    except (TypeError, ValueError):
        return 0.0


def _per_template_metrics(result: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for item in result.get("executable") or result.get("ranking") or []:
        key = str(item.get("template_key") or "")
        if not key:
            continue
        stats = item.get("stats") or {}
        out[key] = {
            "total_return": float(stats.get("total_return") or 0.0),
            "sharpe_ratio": float(stats.get("sharpe_ratio") or 0.0),
            "win_rate": float(stats.get("win_rate") or 0.0),
            "trade_count": float(item.get("trade_count") or 0),
        }
    return out


def _degradation_pct(train: float, test: float) -> float:
    if abs(train) < 1e-12:
        return 0.0 if abs(test) < 1e-12 else 100.0
    return (1.0 - test / train) * 100.0


def _robustness_score(
    *,
    avg_test_return: float,
    avg_degradation: float,
    overfitting_rate: float,
    return_stability: float,
) -> float:
    """0–100 score adapted from legacy WalkForwardTester._calculate_robustness_score."""
    score = 50.0
    # Prefer positive OOS return
    if avg_test_return > 0:
        score += min(20.0, avg_test_return * 2.0)
    else:
        score -= min(20.0, abs(avg_test_return) * 2.0)
    # Penalise degradation and overfit folds
    score -= min(25.0, max(0.0, avg_degradation) * 0.4)
    score -= overfitting_rate * 20.0
    # Stability: lower std is better (scaled roughly)
    score -= min(15.0, return_stability * 0.5)
    return max(0.0, min(100.0, score))


SuiteRunner = Callable[..., Dict[str, Any]]


def _set_dotted(target: Dict[str, Any], dotted: str, value: Any) -> None:
    """Set ``a.b.c`` on a nested dict, creating intermediate dicts."""
    parts = [p for p in dotted.split(".") if p]
    if not parts:
        return
    cursor: Dict[str, Any] = target
    for part in parts[:-1]:
        nxt = cursor.get(part)
        if not isinstance(nxt, dict):
            nxt = {}
            cursor[part] = nxt
        cursor = nxt
    cursor[parts[-1]] = value


def load_param_grid(
    param_grid: Optional[Union[str, Path, Dict[str, Any], List[Any]]],
) -> Optional[Any]:
    """Load param grid from path or pass through in-memory structure."""
    if param_grid is None:
        return None
    if isinstance(param_grid, (str, Path)):
        path = Path(param_grid)
        if not path.exists():
            raise FileNotFoundError(f"找不到 WF param_grid 檔: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload
    return param_grid


def expand_param_grid_candidates(
    param_grid: Optional[Any],
    *,
    max_candidates: int = 48,
) -> List[Dict[str, Any]]:
    """Expand a param grid into full ``parameter_overrides`` candidates.

    Supported forms (recovered from legacy WalkForwardTester intent):

    1. **Candidate list**::

        {"candidates": [ {"MA_Crossover_Trend": {...}}, {...} ]}

    2. **Single-template dotted grid**::

        {
          "template_key": "MA_Crossover_Trend",
          "grid": {
            "entry_conditions.fast_ma_period": [10, 21],
            "entry_conditions.slow_ma_period": [50, 100]
          }
        }

    3. **Nested lists under one template key**::

        {
          "MA_Crossover_Trend": {
            "entry_conditions": {
              "fast_ma_period": [10, 21],
              "slow_ma_period": [50]
            }
          }
        }

    Returns a list of ``parameter_overrides`` dicts (may be empty → no optimize).
    """
    if param_grid is None:
        return []

    if isinstance(param_grid, list):
        out = [dict(item) for item in param_grid if isinstance(item, dict)]
        return out[:max_candidates]

    if not isinstance(param_grid, dict):
        raise ValueError("param_grid 必須是 JSON object 或 candidate 陣列")

    if "candidates" in param_grid:
        raw = param_grid.get("candidates") or []
        out = [dict(item) for item in raw if isinstance(item, dict)]
        return out[:max_candidates]

    if "template_key" in param_grid and "grid" in param_grid:
        template_key = str(param_grid["template_key"])
        grid = param_grid.get("grid") or {}
        if not isinstance(grid, dict) or not grid:
            return []
        keys = list(grid.keys())
        value_lists = []
        for key in keys:
            vals = grid[key]
            if not isinstance(vals, (list, tuple)) or not vals:
                raise ValueError(f"param_grid.grid[{key!r}] 必須是非空陣列")
            value_lists.append(list(vals))
        combos = list(itertools.product(*value_lists))
        if len(combos) > max_candidates:
            logger.warning(
                "param_grid 組合 %d 超過 max_candidates=%d，截斷",
                len(combos),
                max_candidates,
            )
            combos = combos[:max_candidates]
        candidates: List[Dict[str, Any]] = []
        for combo in combos:
            nested: Dict[str, Any] = {}
            for key, value in zip(keys, combo):
                _set_dotted(nested, str(key), value)
            candidates.append({template_key: nested})
        return candidates

    # Nested list form: { "TemplateName": { "entry_conditions": { "x": [..] } } }
    # Only one top-level template key with list leaves is expanded.
    if len(param_grid) == 1:
        template_key = next(iter(param_grid.keys()))
        tree = param_grid[template_key]
        if isinstance(tree, dict):
            dotted: Dict[str, List[Any]] = {}

            def _walk(node: Any, prefix: str) -> None:
                if isinstance(node, dict):
                    for k, v in node.items():
                        path = f"{prefix}.{k}" if prefix else str(k)
                        _walk(v, path)
                elif isinstance(node, list):
                    dotted[prefix] = node
                else:
                    dotted[prefix] = [node]

            _walk(tree, "")
            if dotted:
                return expand_param_grid_candidates(
                    {"template_key": template_key, "grid": dotted},
                    max_candidates=max_candidates,
                )

    # Treat whole dict as a single fixed override candidate
    return [dict(param_grid)]


def optimize_parameters_on_train(
    suite_runner: SuiteRunner,
    *,
    train_start: str,
    train_end: str,
    candidates: List[Dict[str, Any]],
    metric: str,
    base_kwargs: Dict[str, Any],
) -> tuple[Dict[str, Any], Dict[str, Any], float]:
    """Pick parameter_overrides with best train-window metric (legacy optimize).

    Returns ``(best_overrides, best_train_result, best_score)``.
    If ``candidates`` is empty, runs once with base kwargs overrides.
    """
    base = dict(base_kwargs)
    if not candidates:
        result = suite_runner(
            start_date=train_start,
            end_date=train_end,
            **base,
        )
        score = _metric_from_suite(result, metric)
        overrides = base.get("parameter_overrides") or {}
        if not isinstance(overrides, dict):
            overrides = {}
        return dict(overrides), result, score

    best_overrides: Dict[str, Any] = {}
    best_result: Optional[Dict[str, Any]] = None
    best_score = -float("inf")

    for index, overrides in enumerate(candidates, 1):
        run_kwargs = dict(base)
        run_kwargs["parameter_overrides"] = overrides
        result = suite_runner(
            start_date=train_start,
            end_date=train_end,
            **run_kwargs,
        )
        score = _metric_from_suite(result, metric)
        logger.info(
            "WF train optimize %d/%d score=%.6f overrides_keys=%s",
            index,
            len(candidates),
            score,
            list(overrides.keys()),
        )
        if score > best_score:
            best_score = score
            best_overrides = dict(overrides)
            best_result = result

    if best_result is None:
        raise RuntimeError("param_grid 優化失敗：沒有有效訓練結果")
    return best_overrides, best_result, best_score


def run_rolling_walk_forward(
    suite_runner: SuiteRunner,
    *,
    start_date: str,
    end_date: str,
    train_window_days: int = DEFAULT_TRAIN_DAYS,
    test_window_days: int = DEFAULT_TEST_DAYS,
    step_days: int = DEFAULT_STEP_DAYS,
    metric: str = "total_return",
    param_grid: Optional[Any] = None,
    max_grid_candidates: int = 48,
    **suite_kwargs: Any,
) -> Dict[str, Any]:
    """Run multi-window walk-forward via the real strategy-suite backtest entry.

    ``suite_runner`` must accept the same kwargs as
    ``run_strategy_suite_backtest`` and **must** be called with
    ``walk_forward=False`` to avoid recursion (this function enforces that).

    When ``param_grid`` is set, each fold runs legacy-style IS optimization
    then OOS validation with the winning overrides.
    """
    windows = generate_rolling_windows(
        start_date,
        end_date,
        train_window_days=train_window_days,
        test_window_days=test_window_days,
        step_days=step_days,
    )
    if not windows:
        return {
            "enabled": False,
            "mode": "rolling",
            "reason": (
                "區間太短，無法產生任何完整 train+test 窗；"
                f"需要至少 train({train_window_days})+test({test_window_days}) 天"
            ),
            "windows": [],
        }

    base_kwargs = dict(suite_kwargs)
    base_kwargs["walk_forward"] = False
    # Nested golden profile writes are noisy; only top-level should update.
    base_kwargs["update_golden_profile"] = False

    grid_payload = load_param_grid(param_grid)
    candidates = expand_param_grid_candidates(
        grid_payload,
        max_candidates=max_grid_candidates,
    )
    optimize_enabled = bool(candidates)

    fold_results: List[Dict[str, Any]] = []
    test_returns: List[float] = []
    train_returns: List[float] = []
    degradations: List[float] = []
    overfit_count = 0

    for window in windows:
        if optimize_enabled:
            best_overrides, train_result, train_m = optimize_parameters_on_train(
                suite_runner,
                train_start=window.train_start,
                train_end=window.train_end,
                candidates=candidates,
                metric=metric,
                base_kwargs=base_kwargs,
            )
            test_kwargs = dict(base_kwargs)
            test_kwargs["parameter_overrides"] = best_overrides
            test_result = suite_runner(
                start_date=window.test_start,
                end_date=window.test_end,
                **test_kwargs,
            )
            optimal_params: Optional[Dict[str, Any]] = best_overrides
        else:
            train_result = suite_runner(
                start_date=window.train_start,
                end_date=window.train_end,
                **base_kwargs,
            )
            test_result = suite_runner(
                start_date=window.test_start,
                end_date=window.test_end,
                **base_kwargs,
            )
            train_m = _metric_from_suite(train_result, metric)
            optimal_params = None

        test_m = _metric_from_suite(test_result, metric)
        deg = _degradation_pct(train_m, test_m)
        is_overfit = deg > OVERFIT_DEGRADATION_PCT
        if is_overfit:
            overfit_count += 1

        train_returns.append(train_m)
        test_returns.append(test_m)
        degradations.append(deg)

        fold_results.append(
            {
                "window": window.to_dict(),
                "train_metric": train_m,
                "test_metric": test_m,
                "degradation_pct": round(deg, 4),
                "is_overfitting": is_overfit,
                "optimal_params": optimal_params,
                "param_optimize": optimize_enabled,
                "grid_candidates": len(candidates) if optimize_enabled else 0,
                "train_executable_count": train_result.get("executable_count", 0),
                "test_executable_count": test_result.get("executable_count", 0),
                "train_by_template": _per_template_metrics(train_result),
                "test_by_template": _per_template_metrics(test_result),
                "train_ranking": train_result.get("ranking", [])[:5],
                "test_ranking": test_result.get("ranking", [])[:5],
            }
        )
        logger.info(
            "WF fold %s train %s→%s metric=%.4f | test %s→%s metric=%.4f deg=%.1f%%%s",
            window.window_id,
            window.train_start,
            window.train_end,
            train_m,
            window.test_start,
            window.test_end,
            test_m,
            deg,
            " OVERFIT" if is_overfit else "",
        )

    n = len(fold_results)
    avg_train = sum(train_returns) / n
    avg_test = sum(test_returns) / n
    avg_deg = sum(degradations) / n
    overfit_rate = overfit_count / n
    # Population std of OOS metrics
    mean_t = avg_test
    return_stability = (
        (sum((x - mean_t) ** 2 for x in test_returns) / n) ** 0.5 if n else 0.0
    )
    robustness = _robustness_score(
        avg_test_return=avg_test,
        avg_degradation=avg_deg,
        overfitting_rate=overfit_rate,
        return_stability=return_stability,
    )

    return {
        "enabled": True,
        "mode": "rolling",
        "metric": metric,
        "param_optimize": optimize_enabled,
        "grid_candidates": len(candidates) if optimize_enabled else 0,
        "train_window_days": train_window_days,
        "test_window_days": test_window_days,
        "step_days": step_days,
        "overall_period": f"{start_date} ~ {end_date}",
        "total_windows": n,
        "overfitting_windows": overfit_count,
        "overfitting_rate": round(overfit_rate, 4),
        "avg_train_metric": round(avg_train, 6),
        "avg_test_metric": round(avg_test, 6),
        "avg_degradation_pct": round(avg_deg, 4),
        "return_stability": round(return_stability, 6),
        "robustness_score": round(robustness, 2),
        "is_robust": robustness >= 55.0 and overfit_rate <= 0.4,
        "folds": fold_results,
        # Compat fields for CLI printers that expect single-split shape
        "is_period": f"rolling train×{n}",
        "oos_period": f"rolling test×{n}",
        "oos_ranking": fold_results[-1]["test_ranking"] if fold_results else [],
    }


def run_single_split_walk_forward(
    suite_runner: SuiteRunner,
    *,
    start_date: str,
    end_date: str,
    split_ratio: float = DEFAULT_SINGLE_SPLIT_RATIO,
    **suite_kwargs: Any,
) -> Dict[str, Any]:
    """One-shot IS then OOS (previous default behaviour)."""
    split_date = compute_single_split_date(start_date, end_date, split_ratio)
    if not split_date:
        return {
            "enabled": False,
            "mode": "single",
            "reason": "walk_forward 需要同時提供 --start-date 和 --end-date",
        }

    base_kwargs = dict(suite_kwargs)
    base_kwargs["walk_forward"] = False

    # IS pass is the outer caller's main result; this helper only builds OOS block
    # when used standalone. For service integration, see run_strategy_suite_backtest.
    is_result = suite_runner(
        start_date=start_date,
        end_date=split_date,
        update_golden_profile=False,
        **base_kwargs,
    )
    oos_result = suite_runner(
        start_date=split_date,
        end_date=end_date,
        update_golden_profile=base_kwargs.get("update_golden_profile", True),
        **base_kwargs,
    )
    return {
        "enabled": True,
        "mode": "single",
        "split_ratio": split_ratio,
        "split_date": split_date,
        "is_period": f"{start_date} ~ {split_date}",
        "oos_period": f"{split_date} ~ {end_date}",
        "is_executable_count": is_result.get("executable_count", 0),
        "oos_executable_count": oos_result.get("executable_count", 0),
        "is_ranking": is_result.get("ranking", []),
        "oos_ranking": oos_result.get("ranking", []),
        "is_by_template": _per_template_metrics(is_result),
        "oos_by_template": _per_template_metrics(oos_result),
    }
