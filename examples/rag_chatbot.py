"""Example script showing how to wire the retrieval controller into a chatbot."""

from __future__ import annotations

from bioneuronai.agents.retrieval_controller import (
    InMemoryVectorRetriever,
    RetrievalController,
)


def main() -> None:
    documents = {
        "vector_database": "Vector databases store embeddings for similarity search.",
        "rag": "Retrieval augmented generation enriches model answers with documents.",
        "llms": "Large language models can call tools such as retrievers when needed.",
    }
    retriever = InMemoryVectorRetriever(documents)
    controller = RetrievalController(retriever, novelty_threshold=0.4)

    conversation = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "hi there"},
        {"role": "assistant", "content": "sure, what would you like to know?"},
        {
            "role": "user",
            "content": "can you explain retrieval augmented generation?",
        },
    ]

    decision = controller.maybe_retrieve(conversation, top_k=2)

    if decision.triggered:
        print(f"Novelty score {decision.score:.2f} exceeded threshold; retrieved docs:")
        for doc_id in decision.results:
            print(f" - {doc_id}: {documents[doc_id]}")
    else:
        print(
            "Novelty score was too low; the chatbot can answer using existing context."
        )


if __name__ == "__main__":
    main()
