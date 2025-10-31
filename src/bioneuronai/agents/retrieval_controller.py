"""新穎性門控檢索工具。

本模組封裝一組新穎性門控邏輯與可插拔的檢索器實作，提供
:class:`RetrievalController` 以便在對話流程中依據最新訊息的
新穎性決定是否啟動檢索程序。

預設的新穎性評分器會計算最新輸入與先前上下文的 Jaccard 距離；
當分數超過指定的閾值時，控制器會使用最新訊息作為查詢呼叫
檢索器。對話資料可以是純文字序列，也可以是具備 ``content`` 欄位
的訊息物件或字典，控制器會自動轉換成文字內容。

範例
----
>>> retriever = InMemoryVectorRetriever({"doc1": "alpha beta", "doc2": "beta gamma"})
>>> controller = RetrievalController(retriever, novelty_threshold=0.4)
>>> controller.maybe_retrieve(["alpha beta", "tell me about gamma"])
RetrievalDecision(triggered=True, score=0.67..., results=['doc2'])
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Callable, Dict, List, Mapping, Protocol, Sequence


class RetrieverProtocol(Protocol):
    """Abstract protocol for retrievers.

    Implementations must accept a query string and return the identifiers or
    payloads of the retrieved documents ranked by relevance.
    """

    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        """Retrieve up to ``top_k`` documents for the given ``query``."""


class SupportsContent(Protocol):
    """Minimal協定，用於抽象具有 ``content`` 屬性的訊息物件。"""

    content: Any


ConversationItem = str | Mapping[str, Any] | SupportsContent
NoveltyScorer = Callable[[Sequence[str]], float]


def default_novelty_scorer(conversation: Sequence[str]) -> float:
    """Estimate how novel the latest utterance is compared to the context.

    The function compares the token set of the latest utterance with all prior
    utterances in the conversation using a Jaccard distance. A score of 0.0
    indicates that the latest utterance shares all of its tokens with the
    preceding context, while 1.0 indicates there is no token overlap.
    """

    if not conversation:
        return 0.0

    latest_tokens = _tokenize(conversation[-1])
    if len(conversation) == 1:
        return 1.0 if latest_tokens else 0.0

    context_tokens = set()
    for message in conversation[:-1]:
        context_tokens.update(_tokenize(message))

    if not context_tokens:
        return 1.0 if latest_tokens else 0.0

    intersection = len(latest_tokens & context_tokens)
    union = len(latest_tokens | context_tokens)
    if union == 0:
        return 0.0
    return 1.0 - (intersection / union)


@dataclass
class RetrievalDecision:
    """Information about the retrieval decision."""

    triggered: bool
    score: float
    results: List[str]


class RetrievalController:
    """Evaluate conversation novelty and invoke a retriever when necessary."""

    def __init__(
        self,
        retriever: RetrieverProtocol,
        novelty_threshold: float = 0.5,
        novelty_scorer: NoveltyScorer | None = None,
    ) -> None:
        self._retriever = retriever
        if not 0.0 <= novelty_threshold <= 1.0:
            raise ValueError("novelty_threshold must be between 0.0 and 1.0 inclusive")
        self._threshold = novelty_threshold
        self._scorer = novelty_scorer or default_novelty_scorer

    def maybe_retrieve(
        self,
        conversation: Sequence[ConversationItem],
        top_k: int = 5,
    ) -> RetrievalDecision:
        """Return retrieval results if the novelty score exceeds the threshold."""

        normalized = _normalize_conversation(conversation)
        score = self._scorer(normalized)
        if score >= self._threshold and normalized and normalized[-1]:
            query = normalized[-1]
            results = self._retriever.retrieve(query, top_k=top_k)
            return RetrievalDecision(triggered=True, score=score, results=results)
        return RetrievalDecision(triggered=False, score=score, results=[])


class InMemoryVectorRetriever(RetrieverProtocol):
    """A lightweight retriever backed by an in-memory vector store."""

    def __init__(self, documents: Dict[str, str]) -> None:
        if not documents:
            raise ValueError("documents must not be empty")
        self._documents = documents
        self._document_vectors = {
            doc_id: _vectorize(text) for doc_id, text in documents.items()
        }

    def retrieve(self, query: str, top_k: int = 5) -> List[str]:
        if top_k <= 0:
            return []
        query_vector = _vectorize(query)
        scored = [
            (doc_id, _cosine_similarity(query_vector, doc_vector))
            for doc_id, doc_vector in self._document_vectors.items()
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return [doc_id for doc_id, similarity in scored[:top_k] if similarity > 0]


# ---- helpers -----------------------------------------------------------------

_TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)


def _tokenize(text: str) -> set[str]:
    tokens = {token for token in _TOKEN_PATTERN.findall(text.lower()) if token}
    if tokens:
        return tokens
    # 沒有標準分詞的語句（例如中文）時，退回以字元為單位
    return {char for char in text.lower() if not char.isspace()}


def _normalize_conversation(conversation: Sequence[ConversationItem]) -> List[str]:
    normalized: List[str] = []
    for message in conversation:
        if isinstance(message, str):
            normalized.append(message.strip())
            continue
        if isinstance(message, Mapping):
            content = message.get("content")
            if content is None:
                continue
            normalized.append(str(content).strip())
            continue
        content = getattr(message, "content", None)
        if content is not None:
            normalized.append(str(content).strip())
            continue
        normalized.append(str(message).strip())
    return normalized


def _vectorize(text: str) -> Dict[str, float]:
    counts: Dict[str, float] = {}
    for token in text.split():
        token = token.lower()
        counts[token] = counts.get(token, 0.0) + 1.0
    return counts


def _cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    if not vec_a or not vec_b:
        return 0.0

    intersection = set(vec_a) & set(vec_b)
    numerator = sum(vec_a[token] * vec_b[token] for token in intersection)

    sum_sq_a = sum(value * value for value in vec_a.values())
    sum_sq_b = sum(value * value for value in vec_b.values())
    denominator = (sum_sq_a ** 0.5) * (sum_sq_b ** 0.5)
    if denominator == 0:
        return 0.0
    return numerator / denominator


__all__ = [
    "RetrieverProtocol",
    "RetrievalController",
    "RetrievalDecision",
    "InMemoryVectorRetriever",
    "default_novelty_scorer",
]
