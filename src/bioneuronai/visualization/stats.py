"""Utilities for collecting and streaming BioNeuronAI network statistics."""

from __future__ import annotations

import asyncio
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from copy import deepcopy
from typing import (
    Any,
    AsyncIterator,
    Deque,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
)

import numpy as np

try:  # Optional import for typing without runtime dependency
    from bioneuronai.core import BioNet, BioNeuron
except Exception:  # pragma: no cover - fallback for delayed imports
    BioNet = Any  # type: ignore
    BioNeuron = Any  # type: ignore


@dataclass(slots=True)
class SecurityScanStatus:
    """Represents the progress of a simulated safety/security scan."""

    progress: float
    current_phase: str
    issues_found: int = 0
    last_updated: float = field(default_factory=lambda: time.time())
    notes: Optional[str] = None

    def to_payload(self) -> Dict[str, Any]:
        return {
            "progress": float(max(0.0, min(1.0, self.progress))),
            "current_phase": self.current_phase,
            "issues_found": int(self.issues_found),
            "last_updated": self.last_updated,
            "notes": self.notes,
        }

    def clone(self) -> "SecurityScanStatus":
        return SecurityScanStatus(
            progress=float(self.progress),
            current_phase=str(self.current_phase),
            issues_found=int(self.issues_found),
            last_updated=self.last_updated,
            notes=self.notes,
        )


@dataclass(slots=True)
class InputRecord:
    """Represents a single streamed input event."""

    values: Sequence[float]
    novelty: Optional[float] = None
    outputs: Optional[Sequence[float]] = None
    tag: Optional[str] = None
    timestamp: float = field(default_factory=lambda: time.time())

    def to_payload(self) -> Dict[str, Any]:
        return {
            "values": list(map(float, self.values)),
            "novelty": None if self.novelty is None else float(self.novelty),
            "outputs": None if self.outputs is None else list(map(float, self.outputs)),
            "tag": self.tag,
            "timestamp": self.timestamp,
        }


@dataclass(slots=True)
class NetworkSnapshot:
    """Snapshot of network statistics consumed by the dashboard."""

    novelty: Mapping[str, float]
    thresholds: Mapping[str, float]
    weight_distribution: Mapping[str, Dict[str, Any]]
    security_scan: Optional[SecurityScanStatus] = None
    metadata: MutableMapping[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: time.time())

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "novelty": {k: float(v) for k, v in self.novelty.items()},
            "thresholds": {k: float(v) for k, v in self.thresholds.items()},
            "weight_distribution": self.weight_distribution,
            "metadata": dict(self.metadata),
            "timestamp": self.timestamp,
        }
        if self.security_scan is not None:
            payload["security_scan"] = self.security_scan.to_payload()
        return payload

    def clone(self) -> "NetworkSnapshot":
        security_clone = self.security_scan.clone() if self.security_scan else None
        weight_distribution = {
            key: {
                **value,
                "histogram": [dict(bucket) for bucket in value.get("histogram", [])],
            }
            for key, value in self.weight_distribution.items()
        }
        return NetworkSnapshot(
            novelty=dict(self.novelty),
            thresholds=dict(self.thresholds),
            weight_distribution=weight_distribution,
            security_scan=security_clone,
            metadata=deepcopy(self.metadata),
            timestamp=self.timestamp,
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "NetworkSnapshot":
        security_payload = payload.get("security_scan")
        security = None
        if isinstance(security_payload, Mapping):
            security = SecurityScanStatus(
                progress=float(security_payload.get("progress", 0.0)),
                current_phase=str(security_payload.get("current_phase", "")),
                issues_found=int(security_payload.get("issues_found", 0)),
                last_updated=float(security_payload.get("last_updated", time.time())),
                notes=security_payload.get("notes"),
            )

        def _normalise_histogram(entry: Mapping[str, Any]) -> Dict[str, Any]:
            histogram = [
                {
                    "start": float(bucket.get("start", 0.0)),
                    "end": float(bucket.get("end", 0.0)),
                    "count": int(bucket.get("count", 0)),
                }
                for bucket in entry.get("histogram", [])
                if isinstance(bucket, Mapping)
            ]
            result = {
                "min": float(entry.get("min", 0.0)),
                "max": float(entry.get("max", 0.0)),
                "mean": float(entry.get("mean", 0.0)),
                "std": float(entry.get("std", 0.0)),
                "histogram": histogram,
            }
            if "count" in entry:
                result["count"] = int(entry["count"])
            return result

        weight_distribution = {
            key: _normalise_histogram(value)
            for key, value in payload.get("weight_distribution", {}).items()
            if isinstance(value, Mapping)
        }

        timestamp_value = payload.get("timestamp")
        timestamp = float(timestamp_value) if timestamp_value is not None else time.time()

        return cls(
            novelty={k: float(v) for k, v in payload.get("novelty", {}).items()},
            thresholds={k: float(v) for k, v in payload.get("thresholds", {}).items()},
            weight_distribution=weight_distribution,
            security_scan=security,
            metadata=dict(payload.get("metadata", {})),
            timestamp=timestamp,
        )


class NetworkStatsHub:
    """Central broker that stores and streams network statistics."""

    def __init__(self, max_history: int = 200) -> None:
        self._latest_snapshot: Optional[NetworkSnapshot] = None
        self._input_history: Deque[InputRecord] = deque(maxlen=max_history)
        self._novelty_trend: Deque[Dict[str, float]] = deque(maxlen=max_history)
        self._subscribers: set[asyncio.Queue[Dict[str, Any]]] = set()
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------
    def get_network_stats(self) -> Dict[str, Any]:
        with self._lock:
            payload = self._compose_payload_locked()
        return payload

    def get_snapshot(self) -> Optional[NetworkSnapshot]:
        with self._lock:
            if self._latest_snapshot is None:
                return None
            return self._latest_snapshot.clone()

    # ------------------------------------------------------------------
    # Write API
    # ------------------------------------------------------------------
    def update_snapshot(self, snapshot: NetworkSnapshot) -> None:
        snapshot_copy = snapshot.clone()
        with self._lock:
            self._latest_snapshot = snapshot_copy
            summary_value = (
                float(np.mean(list(snapshot_copy.novelty.values())))
                if snapshot_copy.novelty
                else 0.0
            )
            self._novelty_trend.append(
                {"timestamp": snapshot_copy.timestamp, "value": summary_value}
            )
            payload = self._compose_payload_locked()
        self._broadcast(payload)

    def log_input(self, record: InputRecord) -> None:
        with self._lock:
            self._input_history.append(record)
            payload = self._compose_payload_locked()
        self._broadcast(payload)

    def reset(self) -> None:
        with self._lock:
            self._latest_snapshot = None
            self._input_history.clear()
            self._novelty_trend.clear()
            payload = self._compose_payload_locked()
        self._broadcast(payload)

    # ------------------------------------------------------------------
    # Subscription helpers
    # ------------------------------------------------------------------
    async def subscribe(self) -> AsyncIterator[Dict[str, Any]]:
        queue: asyncio.Queue[Dict[str, Any]] = asyncio.Queue(maxsize=5)
        with self._lock:
            initial = self._compose_payload_locked()
            if initial:
                queue.put_nowait(initial)
            self._subscribers.add(queue)
        try:
            while True:
                payload = await queue.get()
                yield payload
        finally:
            with self._lock:
                self._subscribers.discard(queue)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _compose_payload_locked(self) -> Dict[str, Any]:
        snapshot_payload = (
            None
            if self._latest_snapshot is None
            else self._latest_snapshot.to_payload()
        )
        return {
            "snapshot": snapshot_payload,
            "inputs": [rec.to_payload() for rec in self._input_history],
            "novelty_trend": list(self._novelty_trend),
            "summary": self._compose_summary_locked(),
        }

    def _compose_summary_locked(self) -> Dict[str, Any]:
        snapshot = self._latest_snapshot
        novelty_values: Sequence[float] = () if snapshot is None else tuple(snapshot.novelty.values())
        threshold_values: Sequence[float] = () if snapshot is None else tuple(snapshot.thresholds.values())

        def _mean(values: Sequence[float]) -> float:
            return float(np.mean(values)) if values else 0.0

        def _max(values: Sequence[float]) -> float:
            return float(np.max(values)) if values else 0.0

        security = snapshot.security_scan if snapshot else None
        return {
            "inputs_logged": len(self._input_history),
            "novelty_mean": _mean(novelty_values),
            "novelty_max": _max(novelty_values),
            "threshold_mean": _mean(threshold_values),
            "threshold_max": _max(threshold_values),
            "security_phase": None if security is None else security.current_phase,
            "security_progress": None if security is None else float(security.progress),
            "security_issues": None if security is None else int(security.issues_found),
            "last_update": None if snapshot is None else snapshot.timestamp,
        }

    def _broadcast(self, payload: Dict[str, Any]) -> None:
        dead: List[asyncio.Queue[Dict[str, Any]]] = []
        for queue in list(self._subscribers):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                dead.append(queue)
        if dead:
            with self._lock:
                for queue in dead:
                    self._subscribers.discard(queue)


def _calculate_weight_distribution(weights: Sequence[float], bins: int = 10) -> Dict[str, Any]:
    arr = np.asarray(list(weights), dtype=np.float32)
    if arr.size == 0:
        hist = []
        stats = {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0, "count": 0}
    else:
        min_val = float(np.min(arr))
        max_val = float(np.max(arr))
        stats = {
            "min": min_val,
            "max": max_val,
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "count": int(arr.size),
        }
        if np.isclose(min_val, max_val):
            epsilon = max(1e-6, abs(min_val) * 0.1 or 1e-6)
            range_min = min_val - epsilon
            range_max = max_val + epsilon
        else:
            range_min, range_max = min_val, max_val
        hist_counts, bin_edges = np.histogram(arr, bins=bins, range=(range_min, range_max))
        hist = [
            {
                "start": float(bin_edges[i]),
                "end": float(bin_edges[i + 1]),
                "count": int(hist_counts[i]),
            }
            for i in range(len(hist_counts))
        ]
    stats["histogram"] = hist
    return stats


def _gather_layer_stats(layer: Iterable[BioNeuron], name: str) -> Dict[str, Any]:
    novelty: Dict[str, float] = {}
    thresholds: Dict[str, float] = {}
    weight_info: Dict[str, Dict[str, Any]] = {}

    for idx, neuron in enumerate(layer):
        neuron_id = f"{name}_n{idx}"
        novelty[neuron_id] = float(getattr(neuron, "novelty_score", lambda: 0.0)())
        thresholds[neuron_id] = float(getattr(neuron, "threshold", 0.0))
        weight_info[neuron_id] = _calculate_weight_distribution(getattr(neuron, "weights", []))

    return {
        "novelty": novelty,
        "thresholds": thresholds,
        "weight_distribution": weight_info,
    }


def collect_snapshot_from_bionet(
    network: BioNet,
    security_status: Optional[SecurityScanStatus] = None,
    *,
    network_name: str = "BioNet",
) -> NetworkSnapshot:
    """Collect a :class:`NetworkSnapshot` from a ``BioNet`` instance."""

    layer1_stats = _gather_layer_stats(network.layer1.neurons, f"{network_name}_layer1")
    layer2_stats = _gather_layer_stats(network.layer2.neurons, f"{network_name}_layer2")

    novelty = {**layer1_stats["novelty"], **layer2_stats["novelty"]}
    thresholds = {**layer1_stats["thresholds"], **layer2_stats["thresholds"]}
    weight_distribution = {
        **layer1_stats["weight_distribution"],
        **layer2_stats["weight_distribution"],
    }

    metadata: Dict[str, Any] = {
        "network_name": network_name,
        "layer_sizes": {
            "layer1": len(network.layer1.neurons),
            "layer2": len(network.layer2.neurons),
        },
    }

    return NetworkSnapshot(
        novelty=novelty,
        thresholds=thresholds,
        weight_distribution=weight_distribution,
        security_scan=security_status,
        metadata=metadata,
    )


# Default, process-wide hub used by the dashboard and examples.
default_stats_hub = NetworkStatsHub()


__all__ = [
    "NetworkSnapshot",
    "NetworkStatsHub",
    "SecurityScanStatus",
    "InputRecord",
    "collect_snapshot_from_bionet",
    "default_stats_hub",
]
