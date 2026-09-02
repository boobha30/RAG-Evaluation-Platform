"""Pure retrieval-quality metrics. No API calls, no I/O — easy to unit test.

Relevance ground truth here is coarse but practical: a retrieved chunk is
considered "relevant" to a question if its source document is in the
question's labeled `relevant_sources` set. This is robust to chunking
changes (which shift exact chunk ids/boundaries across rebuilds) while still
giving a meaningful signal on whether the retriever is pulling from the
right documents.
"""


def precision_at_k(retrieved: list[dict], relevant_sources: set[str], k: int) -> float:
    top_k = retrieved[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for r in top_k if r["source"] in relevant_sources)
    return hits / len(top_k)


def recall_at_k(retrieved: list[dict], relevant_sources: set[str], k: int) -> float:
    if not relevant_sources:
        return 0.0
    top_k = retrieved[:k]
    hit_sources = {r["source"] for r in top_k if r["source"] in relevant_sources}
    return len(hit_sources) / len(relevant_sources)


def reciprocal_rank(retrieved: list[dict], relevant_sources: set[str]) -> float:
    for rank, r in enumerate(retrieved, start=1):
        if r["source"] in relevant_sources:
            return 1.0 / rank
    return 0.0


def mrr(per_query_retrieved: list[list[dict]], per_query_relevant: list[set[str]]) -> float:
    """Mean Reciprocal Rank across a batch of queries."""
    if not per_query_retrieved:
        return 0.0
    scores = [
        reciprocal_rank(retrieved, relevant)
        for retrieved, relevant in zip(per_query_retrieved, per_query_relevant)
    ]
    return sum(scores) / len(scores)
