import numpy as np

from app.ingestion import semantic_chunk, split_sentences


def test_split_sentences_basic():
    text = "This is one sentence. This is another! And a third?"
    assert split_sentences(text) == [
        "This is one sentence.",
        "This is another!",
        "And a third?",
    ]


def test_split_sentences_empty():
    assert split_sentences("   ") == []


def _fake_embed_similar(sentences: list[str]) -> np.ndarray:
    """Every sentence gets the identical embedding -> similarity always 1.0,
    so semantic_chunk should never split on similarity, only on max_chars."""
    return np.ones((len(sentences), 4))


def _fake_embed_alternating(sentences: list[str]) -> np.ndarray:
    """Alternate between two orthogonal embeddings so similarity between
    consecutive sentences is always 0.0 -> semantic_chunk should split on
    every sentence boundary."""
    vectors = []
    for i in range(len(sentences)):
        vec = np.zeros(4)
        vec[i % 2] = 1.0
        vectors.append(vec)
    return np.array(vectors)


def test_semantic_chunk_keeps_similar_sentences_together():
    text = "Cats are mammals. Cats have fur. Cats like to sleep."
    chunks = semantic_chunk(text, _fake_embed_similar, max_chars=1000, similarity_threshold=0.5)
    assert len(chunks) == 1
    assert chunks[0] == "Cats are mammals. Cats have fur. Cats like to sleep."


def test_semantic_chunk_splits_on_low_similarity():
    text = "Cats are mammals. The stock market fell today. Cats have fur."
    chunks = semantic_chunk(text, _fake_embed_alternating, max_chars=1000, similarity_threshold=0.5)
    assert len(chunks) == 3


def test_semantic_chunk_splits_on_max_chars():
    text = "AAAAAAAAAA. BBBBBBBBBB. CCCCCCCCCC."
    chunks = semantic_chunk(text, _fake_embed_similar, max_chars=15, similarity_threshold=0.0)
    assert len(chunks) == 3
    assert all(len(c) <= 15 for c in chunks)


def test_semantic_chunk_single_sentence():
    chunks = semantic_chunk("Just one sentence here.", _fake_embed_similar)
    assert chunks == ["Just one sentence here."]


def test_semantic_chunk_empty_text():
    assert semantic_chunk("   ", _fake_embed_similar) == []
