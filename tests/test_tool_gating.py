"""Tests for the novelty-aware tool gating manager."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bioneuronai.tool_gating import ToolDescriptor, ToolGatingManager
from smart_assistant import SmartLearningAssistant


@pytest.fixture()
def demo_manager() -> ToolGatingManager:
    tools = [
        ToolDescriptor(
            name="baseline",
            metadata={"category": "analysis"},
            cost=0.1,
            novelty_weight=0.4,
            min_novelty=0.0,
        ),
        ToolDescriptor(
            name="compute",
            metadata={"category": "computation"},
            cost=0.32,
            novelty_weight=1.0,
            min_novelty=0.3,
        ),
        ToolDescriptor(
            name="retrieval",
            metadata={"category": "retrieval"},
            cost=0.55,
            novelty_weight=1.45,
            min_novelty=0.5,
        ),
    ]

    def threshold_strategy(novelty_score: float, tool: ToolDescriptor, context):
        if tool.metadata["category"] == "retrieval":
            return 0.6
        if tool.metadata["category"] == "computation":
            return 0.35 if context and context.get("task_type") == "computation" else 0.45
        return tool.min_novelty

    return ToolGatingManager(tools=tools, novelty_threshold_strategy=threshold_strategy)


def test_select_tool_prefers_low_cost_when_novelty_low(demo_manager: ToolGatingManager) -> None:
    tool, details = demo_manager.select_tool(0.2, return_details=True)
    assert tool is not None
    assert tool.name == "baseline"
    assert any(item["allowed"] for item in details if item["name"] == "baseline")
    assert all(not item["allowed"] for item in details if item["name"] != "baseline")


def test_select_tool_switches_to_retrieval_on_high_novelty(demo_manager: ToolGatingManager) -> None:
    tool, _ = demo_manager.select_tool(0.8, context={"task_type": "research"})
    assert tool is not None
    assert tool.name == "retrieval"


def test_select_tool_balances_cost_for_mid_novelty(demo_manager: ToolGatingManager) -> None:
    tool, _ = demo_manager.select_tool(0.5, context={"task_type": "computation"})
    assert tool is not None
    # computation tool clears the threshold and beats baseline due to higher weight
    assert tool.name == "compute"


def test_rank_tools_orders_by_utility(demo_manager: ToolGatingManager) -> None:
    rankings = demo_manager.rank_tools(0.7, context={"task_type": "research"})
    assert [item[0].name for item in rankings] == ["retrieval", "compute", "baseline"]


def test_smart_assistant_recommendation(tmp_path: Path) -> None:
    assistant = SmartLearningAssistant(data_dir=tmp_path / "data")
    assistant.knowledge_base["learned_solutions"] = {"測試覆蓋率": "使用 pytest"}

    known_task = "提升測試覆蓋率與重構建議"
    known_reco = assistant.recommend_tool_for_task(known_task)
    assert known_reco["selected_tool"] == "local_reflection"

    novel_task = "量子模擬搜尋演算法比較"
    novel_reco = assistant.recommend_tool_for_task(novel_task)
    assert novel_reco["selected_tool"] == "retrieval_search"
