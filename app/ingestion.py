import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
from pypdf import PdfReader

SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


@dataclass
class Chunk:
    id: int
    source: str
    text: str


def load_documents(raw_dir: Path) -> list[tuple[str, str]]:
    """Return list of (source_filename, full_text) for supported files in raw_dir."""
    documents = []
    for path in sorted(raw_dir.iterdir()):
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if path.suffix.lower() == ".pdf":
            reader = PdfReader(str(path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            text = path.read_text(encoding="utf-8", errors="ignore")
        if text.strip():
            documents.append((path.name, text))
    return documents


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(normalized) if s.strip()]


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-8
    return float(np.dot(a, b) / denom)


def semantic_chunk(
    text: str,
    embed_fn: Callable[[list[str]], np.ndarray],
    max_chars: int = 1000,
    similarity_threshold: float = 0.5,
) -> list[str]:
    """Group sentences into chunks, starting a new chunk when adjacent-sentence
    similarity drops below threshold or the chunk exceeds max_chars."""
    sentences = split_sentences(text)
    if not sentences:
        return []
    if len(sentences) == 1:
        return sentences

    embeddings = embed_fn(sentences)

    chunks: list[str] = []
    current = [sentences[0]]
    current_len = len(sentences[0])

    for i in range(1, len(sentences)):
        sentence = sentences[i]
        sim = _cosine_similarity(embeddings[i - 1], embeddings[i])
        would_exceed = current_len + len(sentence) + 1 > max_chars

        if sim < similarity_threshold or would_exceed:
            chunks.append(" ".join(current))
            current = [sentence]
            current_len = len(sentence)
        else:
            current.append(sentence)
            current_len += len(sentence) + 1

    if current:
        chunks.append(" ".join(current))

    return chunks


def ingest_documents(
    raw_dir: Path,
    embed_fn: Callable[[list[str]], np.ndarray],
    max_chars: int = 1000,
    similarity_threshold: float = 0.5,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    next_id = 0
    for source, text in load_documents(raw_dir):
        for chunk_text in semantic_chunk(text, embed_fn, max_chars, similarity_threshold):
            chunks.append(Chunk(id=next_id, source=source, text=chunk_text))
            next_id += 1
    return chunks
