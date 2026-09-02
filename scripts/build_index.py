import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.bm25_index import build_bm25_index, save_bm25_index
from app.config import settings
from app.embeddings import get_embedder
from app.ingestion import ingest_documents
from app.vector_store import build_index, save_index


def main() -> None:
    embedder = get_embedder()

    print(f"Loading documents from {settings.raw_docs_dir} ...")
    chunks = ingest_documents(
        raw_dir=settings.raw_docs_dir,
        embed_fn=embedder.encode,
        max_chars=settings.chunk_max_chars,
        similarity_threshold=settings.chunk_similarity_threshold,
    )

    if not chunks:
        print(f"No documents found in {settings.raw_docs_dir}. Add .txt/.md/.pdf files and retry.")
        return

    print(f"Produced {len(chunks)} chunks. Embedding...")
    embeddings = embedder.encode([c.text for c in chunks])

    print("Building FAISS index...")
    index = build_index(embeddings)
    save_index(index, chunks, settings.index_dir)

    print("Building BM25 index...")
    bm25 = build_bm25_index(chunks)
    save_bm25_index(bm25, settings.index_dir)

    print(f"Saved FAISS + BM25 index and metadata to {settings.index_dir}")


if __name__ == "__main__":
    main()
