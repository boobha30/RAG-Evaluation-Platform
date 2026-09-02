import json
from pathlib import Path

import faiss
import numpy as np

from app.ingestion import Chunk

INDEX_FILENAME = "index.faiss"
METADATA_FILENAME = "metadata.json"


def build_index(embeddings: np.ndarray) -> faiss.Index:
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)
    index.add(embeddings)
    return index


def save_index(index: faiss.Index, chunks: list[Chunk], index_dir: Path) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(index_dir / INDEX_FILENAME))
    metadata = [{"id": c.id, "source": c.source, "text": c.text} for c in chunks]
    (index_dir / METADATA_FILENAME).write_text(json.dumps(metadata, indent=2))


def load_index(index_dir: Path) -> tuple[faiss.Index, list[dict]]:
    index_path = index_dir / INDEX_FILENAME
    metadata_path = index_dir / METADATA_FILENAME
    if not index_path.exists() or not metadata_path.exists():
        raise FileNotFoundError(
            f"No index found in {index_dir}. Run scripts/build_index.py first."
        )
    index = faiss.read_index(str(index_path))
    metadata = json.loads(metadata_path.read_text())
    return index, metadata


def search(
    index: faiss.Index,
    metadata: list[dict],
    query_embedding: np.ndarray,
    top_k: int = 4,
) -> list[dict]:
    scores, indices = index.search(query_embedding.reshape(1, -1), top_k)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx == -1:
            continue
        chunk = metadata[idx]
        results.append({**chunk, "score": float(score)})
    return results
