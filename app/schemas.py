from datetime import datetime

from pydantic import BaseModel, ConfigDict


class QueryRequest(BaseModel):
    query: str
    top_k: int | None = None
    use_hybrid: bool | None = None
    use_reranker: bool | None = None
    evaluate: bool = True


class SourceChunk(BaseModel):
    source: str
    text: str
    score: float | None = None
    fused_score: float | None = None
    rerank_score: float | None = None


class QueryMetricsOut(BaseModel):
    faithfulness: float | None = None
    hallucinated: bool | None = None
    unsupported_claims: list[str] = []
    relevance: float | None = None
    latency_ms: float | None = None
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]
    metrics: QueryMetricsOut


class QueryLogOut(BaseModel):
    id: int
    run_id: int | None
    query: str
    answer: str
    retrieved_sources: list[str]
    retrieved_chunks: list[dict]
    precision: float | None
    recall: float | None
    mrr: float | None
    faithfulness: float | None
    hallucinated: bool | None
    unsupported_claims: list[str]
    relevance: float | None
    latency_ms: float | None
    prompt_tokens: int | None
    completion_tokens: int | None
    cost_usd: float | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvalRunOut(BaseModel):
    id: int
    name: str
    config_name: str
    use_hybrid: bool
    use_reranker: bool
    created_at: datetime
    num_queries: int
    avg_precision: float | None
    avg_recall: float | None
    avg_mrr: float | None
    avg_faithfulness: float | None
    hallucination_rate: float | None
    avg_relevance: float | None
    avg_latency_ms: float | None
    total_cost_usd: float | None


class EvalRunDetailOut(EvalRunOut):
    logs: list[QueryLogOut]
