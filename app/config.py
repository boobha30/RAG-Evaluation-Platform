from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    openai_api_key: str = ""
    # Point this at any OpenAI-compatible endpoint (e.g. Ollama's
    # http://localhost:11434/v1) to use a local/free model instead of
    # OpenAI's hosted API. Leave blank to use OpenAI directly.
    openai_base_url: str = ""
    embedding_model: str = "all-MiniLM-L6-v2"
    generation_model: str = "gpt-4o-mini"
    judge_model: str = "gpt-4o-mini"

    raw_docs_dir: Path = BASE_DIR / "data" / "raw"
    index_dir: Path = BASE_DIR / "data" / "index"
    eval_dir: Path = BASE_DIR / "data" / "eval"

    chunk_max_chars: int = 1000
    chunk_similarity_threshold: float = 0.5

    top_k: int = 4

    # Hybrid retrieval + reranking (Phase 2)
    use_hybrid: bool = True
    use_reranker: bool = True
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_top_n: int = 20
    rrf_k: int = 60
    # how many candidates each of dense/BM25 contribute before fusion
    fusion_candidate_k: int = 20

    # Evaluation harness (Phase 3)
    database_url: str = "sqlite:///./data/eval/eval.db"
    evaluate_live_queries: bool = True

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env")


settings = Settings()
