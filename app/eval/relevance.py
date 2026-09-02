import numpy as np

from app.embeddings import Embedder


def answer_relevance(question: str, answer: str, embedder: Embedder) -> float:
    """Cosine similarity between the question and answer embeddings, as a
    cheap proxy for whether the answer actually addresses the question
    (rather than being faithful-but-off-topic)."""
    vectors = embedder.encode([question, answer])
    q, a = vectors[0], vectors[1]
    denom = (np.linalg.norm(q) * np.linalg.norm(a)) or 1e-8
    return float(np.dot(q, a) / denom)
