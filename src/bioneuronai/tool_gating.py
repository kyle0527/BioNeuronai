"""Tool gating utilities for novelty-aware controllers.

This module defines the :class:`ToolGatingManager`, a reusable base class that can be
shared between traditional tool orchestrators and Retrieval-Augmented Generation (RAG)
controllers.  The manager evaluates the trade-off between a task's novelty and the
expected cost of calling external tools so that the cheapest suitable tool is selected
without sacrificing task coverage.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple


NoveltyThresholdStrategy = Callable[[float, "ToolDescriptor", Optional[Dict[str, Any]]], float]


@dataclass(frozen=True)
class ToolDescriptor:
    """Metadata that describes how and when a tool should be used.

    Parameters
    ----------
    name:
        Unique identifier for the tool.
    metadata:
        Arbitrary metadata attached to the tool.  Typical fields include
        ``category`` (e.g. ``"retrieval"`` vs ``"computation"``) and a human
        readable ``description``.
    cost:
        Normalised cost value (0.0-1.0) representing latency, price or other
        resource usage.  Higher numbers make the tool less attractive.
    novelty_weight:
        Multiplier applied to the task novelty score when scoring this tool.
        Higher numbers favour the tool when novelty is high.
    min_novelty:
        Baseline novelty threshold below which the tool is never considered.
    """

    name: str
    metadata: Dict[str, Any]
    cost: float = 1.0
    novelty_weight: float = 1.0
    min_novelty: float = 0.0


class ToolGatingManager:
    """Select tools based on novelty and cost signals.

    The manager keeps track of registered tools, computes a simple utility score
    ``(novelty_weight * novelty_score) - cost`` for eligible tools and returns the
    highest scoring option.  Eligibility is governed by a novelty threshold
    strategy which can be customised per deployment.

    The implementation is intentionally lightweight so that it can be shared
    between the BioNeuronAI smart assistant, bespoke tool chains and RAG
    controllers.
    """

    def __init__(
        self,
        tools: Optional[Iterable[ToolDescriptor]] = None,
        novelty_threshold_strategy: Optional[NoveltyThresholdStrategy] = None,
    ) -> None:
        self._tools: Dict[str, ToolDescriptor] = {}
        self._novelty_strategy: NoveltyThresholdStrategy = (
            novelty_threshold_strategy or self._default_novelty_threshold
        )

        if tools is not None:
            for tool in tools:
                self.register_tool(tool)

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------
    def register_tool(self, tool: ToolDescriptor) -> None:
        """Register a new tool descriptor.

        Parameters
        ----------
        tool:
            Tool metadata definition.  The tool name must be unique.
        """

        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' already registered")
        self._tools[tool.name] = tool

    def update_tool(self, name: str, **updates: Any) -> ToolDescriptor:
        """Update a registered tool and return the new descriptor."""

        if name not in self._tools:
            raise KeyError(f"Unknown tool '{name}'")

        descriptor = self._tools[name]
        updated = replace(descriptor, **updates)
        self._tools[name] = updated
        return updated

    def remove_tool(self, name: str) -> None:
        """Remove a tool from the registry."""

        if name not in self._tools:
            raise KeyError(f"Unknown tool '{name}'")
        del self._tools[name]

    def set_novelty_threshold_strategy(self, strategy: NoveltyThresholdStrategy) -> None:
        """Override the novelty threshold strategy used during selection."""

        self._novelty_strategy = strategy

    # ------------------------------------------------------------------
    # Selection logic
    # ------------------------------------------------------------------
    def select_tool(
        self,
        novelty_score: float,
        context: Optional[Dict[str, Any]] = None,
        *,
        return_details: bool = False,
    ) -> Tuple[Optional[ToolDescriptor], Optional[List[Dict[str, Any]]]]:
        """Select the most suitable tool for the given novelty score.

        Parameters
        ----------
        novelty_score:
            Normalised novelty value (0.0-1.0) describing how unusual the task
            is.  Higher numbers increase the preference for specialised tools.
        context:
            Optional task metadata.  The novelty threshold strategy may inspect
            the context to provide dynamic gating.
        return_details:
            When ``True`` the method returns a tuple ``(tool, details)`` where
            ``details`` contains per-tool diagnostics.
        """

        diagnostics: List[Dict[str, Any]] = []
        best_tool: Optional[ToolDescriptor] = None
        best_score = float("-inf")

        for tool in self._tools.values():
            threshold = float(self._novelty_strategy(novelty_score, tool, context))
            threshold = max(0.0, min(1.0, threshold))
            allowed = novelty_score >= threshold
            utility = tool.novelty_weight * novelty_score - tool.cost

            diagnostics.append(
                {
                    "name": tool.name,
                    "threshold": threshold,
                    "allowed": allowed,
                    "score": utility,
                    "cost": tool.cost,
                    "metadata": tool.metadata,
                }
            )

            if not allowed:
                continue

            if utility > best_score + 1e-9:
                best_tool = tool
                best_score = utility
            elif abs(utility - best_score) <= 1e-9 and best_tool is not None:
                # Tie-breaker: prefer cheaper tools
                if tool.cost < best_tool.cost:
                    best_tool = tool
                    best_score = utility

        if return_details:
            return best_tool, diagnostics
        return best_tool, None

    def rank_tools(
        self, novelty_score: float, context: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[ToolDescriptor, float]]:
        """Return tools sorted by their utility for the given novelty score."""

        rankings: List[Tuple[ToolDescriptor, float]] = []
        for tool in self._tools.values():
            threshold = float(self._novelty_strategy(novelty_score, tool, context))
            if novelty_score < threshold:
                continue
            utility = tool.novelty_weight * novelty_score - tool.cost
            rankings.append((tool, utility))

        rankings.sort(key=lambda item: item[1], reverse=True)
        return rankings

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    @property
    def tools(self) -> Dict[str, ToolDescriptor]:
        """Expose the registered tools (read-only mapping)."""

        return dict(self._tools)

    @staticmethod
    def _default_novelty_threshold(
        novelty_score: float, tool: ToolDescriptor, context: Optional[Dict[str, Any]]
    ) -> float:
        """Default threshold strategy that uses ``tool.min_novelty`` only."""

        return tool.min_novelty


__all__ = ["ToolDescriptor", "ToolGatingManager", "NoveltyThresholdStrategy"]
