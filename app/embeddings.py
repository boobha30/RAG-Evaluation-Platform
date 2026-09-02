from functools import lru_cache

import numpy as np
# pyrefly: ignore [missing-import]
# pyrefly: ignore [import-error]
from sentence_transformers import SentenceTransformer

from app.config import settings 


class Embedder:
    def __init__(self, model_name: str):
        self._model = SentenceTransformer(model_name)

    def encode(self, texts: list[str]) -> np.ndarray:
        return self._model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )

    @property
    def dimension(self) -> int:
        return self._model.get_sentence_embedding_dimension()


@lru_cache(maxsize=1)
def get_embedder() -> Embedder:
    return Embedder(settings.embedding_model)
