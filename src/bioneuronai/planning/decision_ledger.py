"""Decision ledger for autonomous planning runs.

The ledger is intentionally append-only JSONL.  It records what the
autonomous operator decided and why, without becoming a trading database or
replacing the existing execution/account ledgers.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def _project_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "__dict__"):
        return {
            key: _json_default(item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        }
    return str(value)


class DecisionLedger:
    """Append-only decision log used by the autonomous operator."""

    def __init__(self, path: Optional[str | Path] = None) -> None:
        self.path = Path(path) if path else (
            _project_root()
            / "data"
            / "bioneuronai"
            / "planning"
            / "autonomous"
            / "decision_ledger.jsonl"
        )
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, record: Dict[str, Any]) -> Path:
        payload = dict(record)
        payload.setdefault("recorded_at", datetime.now().isoformat())
        with self.path.open("a", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, default=_json_default)
            handle.write("\n")
        return self.path

    def load_recent(self, limit: int = 100) -> List[Dict[str, Any]]:
        if limit <= 0 or not self.path.exists():
            return []

        lines = self.path.read_text(encoding="utf-8", errors="replace").splitlines()
        records: List[Dict[str, Any]] = []
        for line in lines[-limit:]:
            if not line.strip():
                continue
            try:
                parsed = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                records.append(parsed)
        return records

    def summarize(self, limit: int = 100) -> Dict[str, Any]:
        records = self.load_recent(limit=limit)
        return summarize_decisions(records)


def summarize_decisions(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Summarize recent autonomous outcomes for adaptation rules."""

    rows = list(records)
    realized = [
        row for row in rows
        if isinstance(row.get("outcome"), dict)
        and row["outcome"].get("pnl") is not None
    ]

    wins = 0
    losses = 0
    pnl_values: List[float] = []
    max_drawdown_pct = 0.0

    for row in realized:
        outcome = row["outcome"]
        try:
            pnl = float(outcome.get("pnl", 0.0))
        except (TypeError, ValueError):
            continue
        pnl_values.append(pnl)
        if pnl > 0:
            wins += 1
        elif pnl < 0:
            losses += 1
        try:
            max_drawdown_pct = max(
                max_drawdown_pct,
                abs(float(outcome.get("max_drawdown_pct", 0.0) or 0.0)),
            )
        except (TypeError, ValueError):
            pass

    consecutive_losses = 0
    for row in reversed(realized):
        outcome = row["outcome"]
        try:
            pnl = float(outcome.get("pnl", 0.0))
        except (TypeError, ValueError):
            break
        if pnl < 0:
            consecutive_losses += 1
        else:
            break

    action_counts: Dict[str, int] = {}
    for row in rows:
        action = str(row.get("final_action", "unknown"))
        action_counts[action] = action_counts.get(action, 0) + 1

    total_realized = wins + losses
    win_rate = wins / total_realized if total_realized else None

    ai_outcomes = [
        row for row in rows
        if row.get("type") == "ai_decision_outcome"
        and isinstance(row.get("evaluation"), dict)
    ]
    directional = [
        row for row in ai_outcomes
        if row["evaluation"].get("direction") in {"LONG", "SHORT"}
    ]
    correct = [row for row in ai_outcomes if row["evaluation"].get("correct") is True]
    directional_correct = [
        row for row in directional if row["evaluation"].get("correct") is True
    ]
    returns: List[float] = []
    brier_scores: List[float] = []
    for row in ai_outcomes:
        evaluation = row["evaluation"]
        try:
            returns.append(float(evaluation.get("price_return_pct")))
        except (TypeError, ValueError):
            pass
        try:
            brier_scores.append(float(evaluation.get("brier_score")))
        except (TypeError, ValueError):
            pass

    return {
        "record_count": len(rows),
        "realized_count": total_realized,
        "wins": wins,
        "losses": losses,
        "win_rate": win_rate,
        "pnl_total": sum(pnl_values),
        "consecutive_losses": consecutive_losses,
        "max_drawdown_pct": max_drawdown_pct,
        "action_counts": action_counts,
        "ai_decision_accuracy": {
            "evaluated_count": len(ai_outcomes),
            "correct_count": len(correct),
            "accuracy": len(correct) / len(ai_outcomes) if ai_outcomes else None,
            "directional_count": len(directional),
            "directional_accuracy": (
                len(directional_correct) / len(directional) if directional else None
            ),
            "average_price_return_pct": sum(returns) / len(returns) if returns else None,
            "mean_brier_score": sum(brier_scores) / len(brier_scores) if brier_scores else None,
        },
    }


__all__ = ["DecisionLedger", "summarize_decisions"]
