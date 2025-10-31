"""RAG 範例：利用 BioNeuronAI 重新排序檢索到的文件。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple

from bioneuronai import BioNeuron

try:
    from bioneuronai import ImprovedBioNeuron
except ImportError:  # pragma: no cover - optional dependency
    ImprovedBioNeuron = BioNeuron  # type: ignore[misc, assignment]


@dataclass
class Document:
    title: str
    content: str


CORPUS: List[Document] = [
    Document("Hebbian 學習", "BioNeuronAI 使用 Hebbian 規則進行突觸強度調整"),
    Document("新穎性門控", "透過比較近期輸入，系統可以估計查詢的新穎性"),
    Document("向量資料庫", "RAG 管線通常結合相似度檢索與語言模型生成"),
    Document("強化學習", "探索/利用平衡是強化學習中的重要議題"),
]


def embed(text: str) -> Sequence[float]:
    letters = sum(ch.isalpha() for ch in text)
    digits = sum(ch.isdigit() for ch in text)
    spaces = text.count(" ")
    length_feature = min(1.0, len(text) / 200)
    alpha_density = letters / max(1, len(text))
    numeric_density = digits / max(1, len(text))
    space_ratio = spaces / max(1, len(text))
    return [length_feature, alpha_density, numeric_density, space_ratio]


def cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    import math

    numerator = sum(x * y for x, y in zip(a, b))
    denom = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return numerator / denom if denom else 0.0


def retrieve(query_vec: Sequence[float], top_k: int = 3) -> List[Tuple[Document, float]]:
    scored = [(doc, cosine_similarity(query_vec, embed(doc.content))) for doc in CORPUS]
    return sorted(scored, key=lambda item: item[1], reverse=True)[:top_k]


def rerank_with_novelty(query_vec: Sequence[float], candidates: Iterable[Tuple[Document, float]]) -> List[Tuple[Document, float, float]]:
    neuron = ImprovedBioNeuron(num_inputs=4, adaptive_threshold=True, seed=123)
    results: List[Tuple[Document, float, float]] = []

    for doc, similarity in candidates:
        doc_vec = embed(doc.content)
        diff_vector = [abs(q - d) for q, d in zip(query_vec, doc_vec)]
        activation = neuron.forward(diff_vector)
        novelty = neuron.enhanced_novelty_score() if hasattr(neuron, "enhanced_novelty_score") else neuron.novelty_score()
        neuron.learn(diff_vector, target=activation)
        score = 0.7 * similarity + 0.3 * (1 - novelty)
        results.append((doc, score, novelty))

    return sorted(results, key=lambda item: item[1], reverse=True)


def main() -> None:
    print("=== RAG 重新排序範例 ===")
    query = "BioNeuronAI 如何結合新穎性門控與 RAG?"
    query_vec = embed(query)

    initial_candidates = retrieve(query_vec)
    reranked = rerank_with_novelty(query_vec, initial_candidates)

    for idx, (doc, score, novelty) in enumerate(reranked, start=1):
        print(f"\n候選 {idx}: {doc.title}")
        print(f"相似度+新穎性分數: {score:.3f}")
        print(f"內容摘要: {doc.content}")
        print(f"新穎性指標: {novelty:.3f}")


if __name__ == "__main__":
    main()
