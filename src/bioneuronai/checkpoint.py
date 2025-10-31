"""Checkpoint utilities for BioNeuronAI networks."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class CheckpointManager:
    """Utility to snapshot and rollback BioNeuronAI networks."""

    def __init__(self, network: Any, history_limit: Optional[int] = 10) -> None:
        if not hasattr(network, "to_dict") or not hasattr(network, "load_state"):
            raise TypeError("network must expose to_dict() and load_state() methods")

        self.network = network
        self.history_limit = history_limit
        self._history: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Snapshot and rollback
    # ------------------------------------------------------------------
    def snapshot(self) -> Dict[str, Any]:
        """Capture and store the current network state."""

        state = self.network.to_dict()
        state_copy = json.loads(json.dumps(state))
        self._history.append(state_copy)
        if self.history_limit is not None and len(self._history) > self.history_limit:
            self._history = self._history[-self.history_limit :]
        return state_copy

    def rollback(self, steps: int = 1) -> Dict[str, Any]:
        """Restore a previous snapshot from history."""

        if steps <= 0:
            raise ValueError("steps must be positive")
        if steps > len(self._history):
            raise ValueError("not enough snapshots to rollback")

        state = self._history[-steps]
        self.network.load_state(state)
        return state

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def save(self, path: str | Path, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Persist a network state to disk."""

        if state is None:
            state = self.network.to_dict()
        target = Path(path)
        if target.parent:
            target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(state))
        return state

    async def save_async(self, path: str | Path, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Asynchronously persist a network state to disk."""

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.save, path, state)

    def load(self, path: str | Path, push_history: bool = True) -> Dict[str, Any]:
        """Load network state from disk and optionally push to history."""

        source = Path(path)
        state = json.loads(source.read_text())
        self.network.load_state(state)
        if push_history:
            self._history.append(json.loads(json.dumps(state)))
            if self.history_limit is not None and len(self._history) > self.history_limit:
                self._history = self._history[-self.history_limit :]
        return state

    @property
    def history(self) -> List[Dict[str, Any]]:
        return list(self._history)


__all__ = ["CheckpointManager"]

