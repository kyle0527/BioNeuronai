from __future__ import annotations

from typing import Optional

import pytest

from bioneuronai.agents import NoveltyRouter, ToolSpec


class StubNovelty:
    def __init__(self, score: float) -> None:
        self.score = score

    def novelty_score(self) -> float:
        return self.score


@pytest.fixture
def base_callbacks():
    calls: dict[str, list[str]] = {"rag": [], "base": [], "fallback": []}

    def rag_cb(question: str) -> Optional[str]:
        calls["rag"].append(question)
        return "rag-response"

    def base_cb(question: str) -> str:
        calls["base"].append(question)
        return "base-response"

    def fallback_cb(question: str) -> str:
        calls["fallback"].append(question)
        return "fallback-response"

    return calls, rag_cb, base_cb, fallback_cb


def test_high_novelty_triggers_rag(base_callbacks):
    calls, rag_cb, base_cb, fallback_cb = base_callbacks
    router = NoveltyRouter(
        novelty_source=StubNovelty(0.8),
        rag_callback=rag_cb,
        base_model_callback=base_cb,
        novelty_threshold=0.5,
        fallback_callback=fallback_cb,
    )

    result = router.route("question")

    assert result["route"] == "rag"
    assert result["output"] == "rag-response"
    assert calls["rag"] == ["question"]
    assert calls["base"] == []
    assert calls["fallback"] == []


def test_low_novelty_uses_base_model(base_callbacks):
    calls, rag_cb, base_cb, fallback_cb = base_callbacks
    router = NoveltyRouter(
        novelty_source=StubNovelty(0.1),
        rag_callback=rag_cb,
        base_model_callback=base_cb,
        novelty_threshold=0.5,
        fallback_callback=fallback_cb,
    )

    result = router.route("question")

    assert result["route"] == "base"
    assert result["output"] == "base-response"
    assert calls["base"] == ["question"]
    assert calls["rag"] == []
    assert calls["fallback"] == []


def test_tool_takes_precedence_over_novelty(base_callbacks):
    calls, rag_cb, base_cb, fallback_cb = base_callbacks
    tool_calls: list[str] = []

    tool = ToolSpec(
        name="echo",
        matcher=lambda q: True,
        handler=lambda q: tool_calls.append(q) or "tool-response",
    )

    router = NoveltyRouter(
        novelty_source=StubNovelty(0.9),
        rag_callback=rag_cb,
        base_model_callback=base_cb,
        novelty_threshold=0.5,
        tools=[tool],
        fallback_callback=fallback_cb,
    )

    result = router.route("question")

    assert result["route"] == "tool"
    assert result["tool"] == "echo"
    assert result["output"] == "tool-response"
    assert tool_calls == ["question"]
    assert calls["rag"] == []
    assert calls["base"] == []


def test_tool_keyword_matching(base_callbacks):
    calls, rag_cb, base_cb, fallback_cb = base_callbacks

    calculator_calls: list[str] = []

    def calculator_handler(question: str) -> Optional[str]:
        calculator_calls.append(question)
        return "calc-response"

    tool = ToolSpec(
        name="calculator",
        keywords=("add", "sum"),
        handler=calculator_handler,
    )

    router = NoveltyRouter(
        novelty_source=StubNovelty(0.2),
        rag_callback=rag_cb,
        base_model_callback=base_cb,
        tools=[tool],
        fallback_callback=fallback_cb,
    )

    result = router.route("Can you add two numbers?")

    assert result["route"] == "tool"
    assert result["tool"] == "calculator"
    assert result["output"] == "calc-response"
    assert calculator_calls == ["Can you add two numbers?"]
    assert calls["base"] == []
    assert calls["rag"] == []


def test_tool_failure_allows_rag_flow(base_callbacks):
    calls, rag_cb, base_cb, fallback_cb = base_callbacks

    def failing_tool(question: str) -> Optional[str]:
        return ""

    tool = ToolSpec(
        name="failing",
        matcher=lambda q: True,
        handler=failing_tool,
    )

    router = NoveltyRouter(
        novelty_source=StubNovelty(0.9),
        rag_callback=rag_cb,
        base_model_callback=base_cb,
        novelty_threshold=0.5,
        tools=[tool],
        fallback_callback=fallback_cb,
    )

    result = router.route("question")

    assert result["route"] == "rag"
    assert calls["rag"] == ["question"]
    assert calls["base"] == []


def test_fallback_used_when_rag_returns_empty():
    calls: dict[str, list[str]] = {"rag": [], "base": [], "fallback": []}

    def rag_cb(question: str) -> Optional[str]:
        calls["rag"].append(question)
        return ""

    def base_cb(question: str) -> str:
        calls["base"].append(question)
        return "base-response"

    def fallback_cb(question: str) -> str:
        calls["fallback"].append(question)
        return "fallback-response"

    router = NoveltyRouter(
        novelty_source=StubNovelty(0.9),
        rag_callback=rag_cb,
        base_model_callback=base_cb,
        novelty_threshold=0.5,
        fallback_callback=fallback_cb,
    )

    result = router.route("question")

    assert result["route"] == "fallback"
    assert result["output"] == "fallback-response"
    assert calls["fallback"] == ["question"]
    assert calls["base"] == []
