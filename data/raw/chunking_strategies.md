# Chunking Strategies for RAG

Splitting documents into chunks is one of the highest-leverage decisions in a RAG pipeline, because retrieval quality is bounded by how well a chunk isolates a coherent idea. If a chunk mixes two unrelated topics, its embedding becomes a blurry average that matches neither topic well.

Fixed-size chunking splits text every N characters or tokens, usually with some overlap between consecutive chunks so that ideas spanning a boundary are not lost entirely. It is simple and fast, but it frequently cuts sentences or paragraphs in half, which hurts both embedding quality and the readability of the context passed to the language model.

Recursive character splitting improves on fixed-size chunking by trying larger separators first (paragraph breaks, then sentence breaks, then spaces) and falling back to smaller ones only when a chunk is still too large. This keeps natural boundaries intact more often than naive fixed-size splitting.

Semantic chunking goes a step further by embedding individual sentences and grouping adjacent sentences together only while their embeddings stay similar. When the similarity between one sentence and the next drops below a threshold, a new chunk begins. This tends to produce chunks that correspond to a single topic or argument, which improves both retrieval precision and the coherence of the context given to the generator.

Chunk size is a trade-off. Very small chunks retrieve precisely but may lack the surrounding context a language model needs to answer correctly. Very large chunks carry more context but dilute the embedding and increase the chance of irrelevant text being retrieved alongside the relevant part. A common practical range is 200 to 1000 characters per chunk, tuned per corpus.

Overlap between chunks (for fixed-size or recursive strategies) helps recover information that would otherwise be split across a boundary, at the cost of some duplicated content in the index.
