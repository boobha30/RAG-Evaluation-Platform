from pathlib import Path

import faiss
from rank_bm25 import BM25Okapi

from app.bm25_index import bm25_search, load_bm25_index
from app.config import settings
from app.embeddings import Embedder, get_embedder
from app.reranker import Reranker, get_reranker
from app.vector_store import load_index, search


def reciprocal_rank_fusion(
    result_lists: list[list[dict]], k: int = 60
) -> list[dict]:
    """Merge multiple ranked result lists (each a list of dicts with an 'id')
    into one list ordered by fused RRF score. Later duplicate ids keep the
    first-seen chunk payload but accumulate score from every list."""
    scores: dict[int, float] = {}
    payloads: dict[int, dict] = {}
    for results in result_lists:
        for rank, item in enumerate(results):
            item_id = item["id"]
            scores[item_id] = scores.get(item_id, 0.0) + 1.0 / (k + rank + 1)
            payloads.setdefault(item_id, item)

    fused = [
        {**payloads[item_id], "fused_score": score}
        for item_id, score in scores.items()
    ]
    fused.sort(key=lambda x: x["fused_score"], reverse=True)
    return fused


class Retriever:
    def __init__(
        self,
        index: faiss.Index,
        metadata: list[dict],
        embedder: Embedder,
        bm25: BM25Okapi | None = None,
        reranker: Reranker | None = None,
    ):
        self._index = index
        self._metadata = metadata
        self._embedder = embedder
        self._bm25 = bm25
        self._reranker = reranker

    @classmethod
    def from_disk(cls, index_dir: Path = settings.index_dir) -> "Retriever":
        index, metadata = load_index(index_dir)
        bm25 = None
        try:
            bm25 = load_bm25_index(index_dir)
        except FileNotFoundError:
            pass
        reranker = get_reranker() if settings.use_reranker else None
        return cls(index, metadata, get_embedder(), bm25=bm25, reranker=reranker)

    def _dense_search(self, query: str, top_k: int) -> list[dict]:
        query_embedding = self._embedder.encode([query])[0]
        return search(self._index, self._metadata, query_embedding, top_k)

    def _bm25_search(self, query: str, top_k: int) -> list[dict]:
        if self._bm25 is None:
            return []
        return bm25_search(self._bm25, self._metadata, query, top_k)

    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        use_hybrid: bool | None = None,
        use_reranker: bool | None = None,
    ) -> list[dict]:
        """Retrieve the top_k most relevant chunks for `query`.

        use_hybrid/use_reranker default to the app-wide settings but can be
        overridden per call so the eval harness can compare pipeline
        configurations (dense-only vs hybrid vs hybrid+rerank) against the
        same index.
        """
        top_k = top_k or settings.top_k
        use_hybrid = settings.use_hybrid if use_hybrid is None else use_hybrid
        use_reranker = settings.use_reranker if use_reranker is None else use_reranker

        candidate_k = max(settings.fusion_candidate_k, top_k)
        dense_results = self._dense_search(query, candidate_k)

        if use_hybrid and self._bm25 is not None:
            bm25_results = self._bm25_search(query, candidate_k)
            fused = reciprocal_rank_fusion(
                [dense_results, bm25_results], k=settings.rrf_k
            )
        else:
            fused = dense_results

        if use_reranker and self._reranker is not None:
            rerank_pool = fused[: max(settings.rerank_top_n, top_k)]
            return self._reranker.rerank(query, rerank_pool, top_k)

        return fused[:top_k]
