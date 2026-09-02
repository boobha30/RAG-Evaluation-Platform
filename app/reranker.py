from functools import lru_cache

# pyrefly: ignore [missing-import]
# pyrefly: ignore [import-error]
from sentence_transformers import CrossEncoder

from app.config import settings


class Reranker:
    def __init__(self, model_name: str):
        self._model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: list[dict], top_k: int) -> list[dict]:
        if not candidates:
            return []
        pairs = [(query, c["text"]) for c in candidates]
        scores = self._model.predict(pairs)
        reranked = [
            {**c, "rerank_score": float(score)}
            for c, score in zip(candidates, scores)
        ]
        reranked.sort(key=lambda c: c["rerank_score"], reverse=True)
        return reranked[:top_k]


@lru_cache(maxsize=1)
def get_reranker() -> Reranker:
    return Reranker(settings.reranker_model)
