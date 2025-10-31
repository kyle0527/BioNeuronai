import pytest

from bioneuronai.agents.retrieval_controller import (
    InMemoryVectorRetriever,
    RetrievalController,
)


class StubRetriever:
    def __init__(self) -> None:
        self.calls = []

    def retrieve(self, query: str, top_k: int = 5):
        self.calls.append((query, top_k))
        results = ["doc1", "doc2", "doc3"]
        return results[:top_k]


def test_retrieval_triggered_on_high_novelty():
    retriever = StubRetriever()
    controller = RetrievalController(retriever, novelty_threshold=0.4)

    conversation = ["hello", "let's talk about databases"]
    decision = controller.maybe_retrieve(conversation, top_k=1)

    assert decision.triggered is True
    assert decision.results == ["doc1"]
    assert retriever.calls == [(conversation[-1], 1)]


def test_retrieval_not_triggered_on_low_novelty():
    retriever = StubRetriever()
    controller = RetrievalController(retriever, novelty_threshold=0.9)

    conversation = ["retrieval augmented generation", "retrieval augmented generation"]
    decision = controller.maybe_retrieve(conversation)

    assert decision.triggered is False
    assert decision.results == []
    assert retriever.calls == []


def test_in_memory_vector_retriever_orders_by_similarity():
    documents = {
        "alpha": "machine learning with embeddings",
        "beta": "cooking recipes and ingredients",
        "gamma": "embeddings and vector search",
    }
    retriever = InMemoryVectorRetriever(documents)

    results = retriever.retrieve("vector embeddings", top_k=2)

    assert results == ["gamma", "alpha"]


def test_controller_accepts_message_dictionaries():
    retriever = StubRetriever()
    controller = RetrievalController(retriever, novelty_threshold=0.4)

    conversation = [
        {"role": "system", "content": "hi there"},
        {"role": "user", "content": "tell me about databases"},
    ]

    decision = controller.maybe_retrieve(conversation, top_k=2)

    assert decision.triggered is True
    assert retriever.calls[-1][0] == conversation[-1]["content"]


def test_retrieval_controller_validates_threshold():
    with pytest.raises(ValueError):
        RetrievalController(StubRetriever(), novelty_threshold=1.5)


def test_empty_latest_message_skips_retrieval():
    retriever = StubRetriever()
    controller = RetrievalController(retriever, novelty_threshold=0.4)

    conversation = ["context", "   "]
    decision = controller.maybe_retrieve(conversation)

    assert decision.triggered is False
    assert retriever.calls == []
