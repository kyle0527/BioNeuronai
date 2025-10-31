"""Routing helpers that use neuron novelty to trigger external systems."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable, Optional, Protocol, Sequence


class SupportsNoveltyScore(Protocol):
    """Protocol for objects exposing a ``novelty_score`` method."""

    def novelty_score(self) -> float:
        ...


@dataclass
class ToolSpec:
    """Specification of a callable tool that can be triggered by the router."""

    name: str
    handler: Callable[[str], Optional[str]]
    matcher: Optional[Callable[[str], bool]] = None
    keywords: Optional[Sequence[str]] = None
    description: str | None = None

    def matches(self, query: str) -> bool:
        """Return ``True`` when the tool should handle *query*."""

        if self.matcher is not None:
            return bool(self.matcher(query))

        if self.keywords:
            lowered = query.lower()
            return any(keyword.lower() in lowered for keyword in self.keywords)

        return False


@dataclass
class RoutingDecision:
    """Container describing the routing decision made by :class:`NoveltyRouter`."""

    route: str
    output: str
    novelty: float
    tool: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        data = {
            "route": self.route,
            "output": self.output,
            "novelty": self.novelty,
        }
        if self.tool is not None:
            data["tool"] = self.tool
        return data


class NoveltyRouter:
    """Route incoming queries based on neuron novelty and available tools.

    Parameters
    ----------
    novelty_source:
        Either a callable returning the latest novelty score or an object with a
        ``novelty_score`` method (for example :class:`~bioneuronai.core.BioNeuron`).
    rag_callback:
        Callable invoked when the novelty is above the threshold and no tool has
        been triggered. It should execute a retrieval-augmented generation (RAG)
        step and return a string response.
    base_model_callback:
        Callable that generates a response without external retrieval.
    novelty_threshold:
        Novelty score threshold above which the router activates the RAG
        pipeline. Defaults to ``0.5``.
    tools:
        Optional iterable of :class:`ToolSpec` describing available tools. The
        router invokes the first tool whose matcher returns ``True`` for the
        incoming query.
    fallback_callback:
        Optional callable to execute if the RAG branch fails (returns ``None`` or
        an empty string). When omitted, the router falls back to
        ``base_model_callback``.
    """

    def __init__(
        self,
        novelty_source: Callable[[], float] | SupportsNoveltyScore,
        rag_callback: Callable[[str], Optional[str]],
        base_model_callback: Callable[[str], str],
        novelty_threshold: float = 0.5,
        tools: Optional[Iterable[ToolSpec]] = None,
        fallback_callback: Optional[Callable[[str], str]] = None,
    ) -> None:
        if callable(novelty_source) and not hasattr(novelty_source, "novelty_score"):
            self._novelty_fn = novelty_source  # type: ignore[assignment]
        elif hasattr(novelty_source, "novelty_score"):
            self._novelty_fn = novelty_source.novelty_score  # type: ignore[assignment]
        else:
            raise TypeError(
                "novelty_source must be callable or expose a 'novelty_score' method"
            )

        self.rag_callback = rag_callback
        self.base_model_callback = base_model_callback
        self.novelty_threshold = float(novelty_threshold)
        self.tools: Sequence[ToolSpec] = tuple(tools or ())
        self.fallback_callback = fallback_callback

    def _run_tools(self, query: str, novelty: float) -> Optional[RoutingDecision]:
        for tool in self.tools:
            if tool.matches(query):
                output = tool.handler(query)
                if output:
                    return RoutingDecision(
                        route="tool",
                        output=output,
                        novelty=novelty,
                        tool=tool.name,
                    )
        return None

    def route(self, query: str) -> dict:
        """Route the query and return diagnostic information."""

        novelty = float(self._novelty_fn())
        result = self._run_tools(query, novelty)
        if result is not None:
            return result.to_dict()

        # Step 2: fallback between RAG and base model depending on novelty.
        if novelty >= self.novelty_threshold:
            rag_response = self.rag_callback(query)
            if rag_response:
                return RoutingDecision(
                    route="rag",
                    output=rag_response,
                    novelty=novelty,
                ).to_dict()
            if self.fallback_callback is not None:
                return RoutingDecision(
                    route="fallback",
                    output=self.fallback_callback(query),
                    novelty=novelty,
                ).to_dict()

        # Default path: base model generation.
        return RoutingDecision(
            route="base",
            output=self.base_model_callback(query),
            novelty=novelty,
        ).to_dict()
