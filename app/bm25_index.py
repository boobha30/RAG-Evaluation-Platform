import pickle
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

from app.ingestion import Chunk

BM25_FILENAME = "bm25.pkl"

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def build_bm25_index(chunks: list[Chunk]) -> BM25Okapi:
    tokenized = [tokenize(c.text) for c in chunks]
    return BM25Okapi(tokenized)


def save_bm25_index(bm25: BM25Okapi, index_dir: Path) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    with open(index_dir / BM25_FILENAME, "wb") as f:
        pickle.dump(bm25, f)


def load_bm25_index(index_dir: Path) -> BM25Okapi:
    path = index_dir / BM25_FILENAME
    if not path.exists():
        raise FileNotFoundError(
            f"No BM25 index found in {index_dir}. Run scripts/build_index.py first."
        )
    with open(path, "rb") as f:
        return pickle.load(f)


def bm25_search(bm25: BM25Okapi, metadata: list[dict], query: str, top_k: int = 4) -> list[dict]:
    scores = bm25.get_scores(tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    results = []
    for idx in ranked:
        if scores[idx] <= 0:
            continue
        chunk = metadata[idx]
        results.append({**chunk, "score": float(scores[idx])})
    return results
