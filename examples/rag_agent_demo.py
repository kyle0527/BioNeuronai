"""Demonstration of the NoveltyRouter triggering RAG and tools."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from math import sqrt
from typing import Iterable, List, Tuple

from bioneuronai.agents import NoveltyRouter, ToolSpec
from bioneuronai.core import BioNeuron


def tokenize(text: str) -> List[str]:
    return [token.strip(".,!?") for token in text.lower().split() if token.strip()]


def cosine_similarity(a: Counter[str], b: Counter[str]) -> float:
    dot = sum(a[token] * b[token] for token in set(a) & set(b))
    norm_a = sqrt(sum(v * v for v in a.values()))
    norm_b = sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


@dataclass
class MemoryDocument:
    text: str
    tokens: Counter[str]


class InMemoryVectorStore:
    """Minimal in-memory vector store with cosine similarity."""

    def __init__(self, docs: Iterable[str] | None = None) -> None:
        self._docs: List[MemoryDocument] = []
        if docs:
            for doc in docs:
                self.add(doc)

    def add(self, text: str) -> None:
        self._docs.append(MemoryDocument(text=text, tokens=Counter(tokenize(text))))

    def search(self, query: str, top_k: int = 1) -> List[Tuple[float, MemoryDocument]]:
        query_tokens = Counter(tokenize(query))
        scored = [
            (cosine_similarity(query_tokens, doc.tokens), doc) for doc in self._docs
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return scored[:top_k]


class StubLanguageModel:
    def __call__(self, prompt: str) -> str:
        return f"[LLM] {prompt}"


def build_router(neuron: BioNeuron, store: InMemoryVectorStore) -> NoveltyRouter:
    lm = StubLanguageModel()

    def rag_callback(question: str) -> str:
        hits = store.search(question, top_k=1)
        if not hits or hits[0][0] == 0.0:
            return ""
        score, doc = hits[0]
        return f"[RAG score={score:.2f}] {doc.text}"

    def base_callback(question: str) -> str:
        return lm(f"Generic answer about: {question}")

    def fallback_callback(question: str) -> str:
        return f"[Fallback to LLM] {lm(question)}"

    def calculator_handler(question: str) -> str:
        cleaned = question.replace("+", " ")
        numbers = [int(token) for token in cleaned.split() if token.isdigit()]
        if len(numbers) >= 2:
            return f"[Tool] The answer is {sum(numbers[:2])}"
        return "[Tool] Unable to parse numbers"

    calculator_tool = ToolSpec(
        name="calculator",
        description="Answer simple addition questions",
        keywords=("add", "sum"),
        handler=calculator_handler,
    )

    return NoveltyRouter(
        novelty_source=neuron,
        rag_callback=rag_callback,
        base_model_callback=base_callback,
        novelty_threshold=0.5,
        tools=[calculator_tool],
        fallback_callback=fallback_callback,
    )


def main() -> None:
    neuron = BioNeuron(num_inputs=2)
    store = InMemoryVectorStore(
        [
            "Retrieval augmented generation combines neural models with search.",
            "Neural novelty signals can decide when to consult a knowledge base.",
        ]
    )
    router = build_router(neuron, store)

    neuron.forward([0.1, 0.1])
    neuron.forward([0.12, 0.11])  # low novelty
    print("Low novelty query:")
    print(router.route("Explain retrieval augmented generation"))

    neuron.forward([0.9, 0.2])  # increase novelty
    print("\nHigh novelty query:")
    print(router.route("How do novelty signals help retrieval?"))

    neuron.forward([0.15, 0.14])  # reset novelty
    neuron.forward([0.16, 0.15])
    print("\nTool triggered query:")
    print(router.route("Please sum 1+1"))


if __name__ == "__main__":
    main()
