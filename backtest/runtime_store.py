"""Persistence helpers for replay runtime artifacts."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from .contracts import ExecutionReceipt, OrderIntent
from .paths import RUNTIME_ROOT, ensure_backtest_dirs


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value):
        return asdict(value)
    return str(value)


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )


class ReplayRunRecorder:
    """Stores a replay run under backtest/runtime/<run_id>/."""

    def __init__(
        self,
        mode: str,
        config: Optional[Dict[str, Any]] = None,
        runtime_root: Path = RUNTIME_ROOT,
    ) -> None:
        ensure_backtest_dirs([runtime_root])
        self.mode = mode
        self.run_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}"
        self.run_dir = runtime_root / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=False)

        self._orders_path = self.run_dir / "orders.jsonl"
        self._status_path = self.run_dir / "status.json"
        self._summary_path = self.run_dir / "summary.json"
        self._account_path = self.run_dir / "account.json"
        self._result_path = self.run_dir / "result.json"
        self._runtime_state_path = self.run_dir / "runtime_state.json"

        self.started_at = datetime.now()
        self.completed_at: Optional[datetime] = None
        self.config = config or {}
        self.order_count = 0
        self.fill_count = 0

        _write_json(
            self._status_path,
            {
                "run_id": self.run_id,
                "mode": self.mode,
                "status": "running",
                "started_at": self.started_at,
                "completed_at": None,
                "config": self.config,
                "run_dir": self.run_dir,
            },
        )

    def record_order(self, intent: OrderIntent, receipt: ExecutionReceipt) -> None:
        self.order_count += 1
        if receipt.accepted and receipt.filled_qty > 0:
            self.fill_count += 1

        with self._orders_path.open("a", encoding="utf-8") as handle:
            handle.write(
                json.dumps(
                    {
                        "recorded_at": datetime.now(),
                        "intent": intent,
                        "receipt": receipt,
                    },
                    ensure_ascii=False,
                    default=_json_default,
                )
                + "\n"
            )

    def save_runtime_state(self, payload: Dict[str, Any]) -> None:
        _write_json(self._runtime_state_path, payload)

    def save_account(self, payload: Dict[str, Any]) -> None:
        _write_json(self._account_path, payload)

    def save_result(self, payload: Dict[str, Any]) -> None:
        _write_json(self._result_path, payload)

    def finalize(
        self,
        summary: Dict[str, Any],
        status: str = "completed",
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        self.completed_at = datetime.now()
        payload = {
            **summary,
            "run_id": self.run_id,
            "mode": self.mode,
            "run_dir": str(self.run_dir),
            "status": status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "orders_recorded": self.order_count,
            "fills_recorded": self.fill_count,
            "error": error,
        }
        _write_json(self._summary_path, payload)
        _write_json(
            self._status_path,
            {
                "run_id": self.run_id,
                "mode": self.mode,
                "status": status,
                "started_at": self.started_at,
                "completed_at": self.completed_at,
                "config": self.config,
                "run_dir": self.run_dir,
                "orders_recorded": self.order_count,
                "fills_recorded": self.fill_count,
                "error": error,
            },
        )
        return payload


def list_runs(limit: int = 20, runtime_root: Path = RUNTIME_ROOT) -> Dict[str, Any]:
    ensure_backtest_dirs([runtime_root])
    runs: List[Dict[str, Any]] = []
    for directory in sorted(
        [path for path in runtime_root.iterdir() if path.is_dir()],
        key=lambda path: path.name,
        reverse=True,
    )[:limit]:
        summary_path = directory / "summary.json"
        status_path = directory / "status.json"
        if summary_path.exists():
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        elif status_path.exists():
            payload = json.loads(status_path.read_text(encoding="utf-8"))
        else:
            payload = {"run_id": directory.name, "run_dir": str(directory), "status": "unknown"}
        runs.append(payload)
    return {"runtime_root": str(runtime_root), "run_count": len(runs), "runs": runs}


def load_run(run_id: str, runtime_root: Path = RUNTIME_ROOT) -> Dict[str, Any]:
    ensure_backtest_dirs([runtime_root])
    run_dir = runtime_root / run_id
    if not run_dir.exists():
        raise FileNotFoundError(f"找不到 replay run: {run_id}")

    payload: Dict[str, Any] = {"run_id": run_id, "run_dir": str(run_dir)}
    for name in ("status", "summary", "account", "result", "runtime_state"):
        path = run_dir / f"{name}.json"
        if path.exists():
            payload[name] = json.loads(path.read_text(encoding="utf-8"))

    orders_path = run_dir / "orders.jsonl"
    orders: List[Dict[str, Any]] = []
    if orders_path.exists():
        with orders_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    orders.append(json.loads(line))
    payload["orders"] = orders
    return payload
