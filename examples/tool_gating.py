"""示範如何使用 BioNeuronAI 為工具選擇建立新穎性閘門。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Sequence

from bioneuronai import BioNeuron

try:
    from bioneuronai import CuriositDrivenNet
except ImportError:  # pragma: no cover - optional dependency
    CuriositDrivenNet = None  # type: ignore[assignment]


@dataclass
class AssistantTool:
    name: str
    description: str

    def invoke(self, query: str) -> str:
        return f"[{self.name}] 處理輸入：{query}"


def encode_query(query: str) -> Sequence[float]:
    """將純文字查詢轉換為 3 維特徵向量。"""

    length_feature = min(1.0, len(query) / 120)
    question_feature = 1.0 if "?" in query else 0.0
    numeric_feature = min(1.0, sum(char.isdigit() for char in query) / 6)
    return [length_feature, question_feature, numeric_feature]


def choose_tool(query: str, tools: Iterable[AssistantTool]) -> tuple[str, float, float]:
    """使用 BioNeuron 與好奇心網路根據新穎性決定工具。"""

    vector = encode_query(query)
    novelty_gate = BioNeuron(num_inputs=3, threshold=0.4, memory_len=6, seed=7)
    curiosity_net: Optional[CuriositDrivenNet]
    if CuriositDrivenNet is not None:
        curiosity_net = CuriositDrivenNet(input_dim=3, hidden_dim=4)
    else:
        curiosity_net = None

    novelty_gate.forward(vector)
    novelty_score = novelty_gate.novelty_score()
    curiosity = curiosity_net.curious_learn(vector) if curiosity_net else novelty_score

    if novelty_score < 0.25:
        chosen = next(iter(tools))
    else:
        ranked = sorted(tools, key=lambda tool: len(tool.description), reverse=True)
        chosen = ranked[0]

    return chosen.invoke(query), novelty_score, float(curiosity)


def main() -> None:
    tools = [
        AssistantTool("search", "網路查詢並蒐集最新資料"),
        AssistantTool("calc", "進行數值計算與單位轉換"),
        AssistantTool("rag", "整合向量資料庫與知識庫回應"),
    ]

    queries = [
        "給我一段關於 BioNeuronAI 的簡介",
        "今年 NeurIPS 的截止日期是什麼時候?",
        "計算 42 的平方根並與 7*3 比較",
        "把這段實驗數據 101, 98, 105, 99 做 z-score",
    ]

    print("=== 工具新穎性閘門示範 ===")
    for query in queries:
        response, novelty, curiosity = choose_tool(query, tools)
        print(f"\n使用者輸入：{query}")
        print(f"新穎性分數：{novelty:.3f} | 好奇心水平：{curiosity:.3f}")
        print(f"選擇工具輸出：{response}")


if __name__ == "__main__":
    main()
