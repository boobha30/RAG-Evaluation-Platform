from dataclasses import dataclass

from app.config import settings
from app.db import get_session
from app.embeddings import get_embedder
from app.eval.cost import estimate_cost_usd
from app.eval.judge import judge_faithfulness
from app.eval.relevance import answer_relevance
from app.eval.retrieval_metrics import precision_at_k, recall_at_k, reciprocal_rank
from app.generation import GenerationResult
from app.models import QueryLog


@dataclass
class QueryMetrics:
    precision: float | None
    recall: float | None
    mrr: float | None
    faithfulness: float | None
    hallucinated: bool | None
    unsupported_claims: list[str]
    relevance: float | None
    latency_ms: float | None
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


def score_and_log_query(
    query: str,
    contexts: list[dict],
    generation: GenerationResult,
    *,
    latency_ms: float | None = None,
    relevant_sources: set[str] | None = None,
    run_id: int | None = None,
    include_faithfulness: bool = True,
) -> QueryMetrics:
    """Compute retrieval + generation quality metrics for one query and
    persist a QueryLog row. Used by both the live /query endpoint and the
    batch eval script (scripts/run_eval.py), so a single code path defines
    what "quality" means everywhere in the app.

    Faithfulness/hallucination judging calls the OpenAI API and is treated
    as best-effort: if it fails (no API key, network error, etc.) the query
    is still logged with those fields left null rather than failing the
    whole request.
    """
    precision = recall = mrr_score = None
    if relevant_sources is not None:
        precision = precision_at_k(contexts, relevant_sources, len(contexts))
        recall = recall_at_k(contexts, relevant_sources, len(contexts))
        mrr_score = reciprocal_rank(contexts, relevant_sources)

    relevance = None
    try:
        relevance = answer_relevance(query, generation.answer, get_embedder())
    except Exception:
        pass

    faithfulness = hallucinated = None
    unsupported_claims: list[str] = []
    if include_faithfulness and contexts:
        try:
            result = judge_faithfulness(query, contexts, generation.answer)
            faithfulness = result.faithfulness_score
            hallucinated = result.hallucinated
            unsupported_claims = result.unsupported_claims
        except Exception:
            pass

    cost_usd = estimate_cost_usd(
        settings.generation_model, generation.prompt_tokens, generation.completion_tokens
    )

    session = get_session()
    try:
        log = QueryLog(
            run_id=run_id,
            query=query,
            answer=generation.answer,
            retrieved_sources=[c["source"] for c in contexts],
            retrieved_chunks=[
                {
                    "source": c["source"],
                    "text": c["text"],
                    "score": c.get("score"),
                    "fused_score": c.get("fused_score"),
                    "rerank_score": c.get("rerank_score"),
                }
                for c in contexts
            ],
            precision=precision,
            recall=recall,
            mrr=mrr_score,
            faithfulness=faithfulness,
            hallucinated=hallucinated,
            unsupported_claims=unsupported_claims,
            relevance=relevance,
            latency_ms=latency_ms,
            prompt_tokens=generation.prompt_tokens,
            completion_tokens=generation.completion_tokens,
            cost_usd=cost_usd,
        )
        session.add(log)
        session.commit()
    finally:
        session.close()

    return QueryMetrics(
        precision=precision,
        recall=recall,
        mrr=mrr_score,
        faithfulness=faithfulness,
        hallucinated=hallucinated,
        unsupported_claims=unsupported_claims,
        relevance=relevance,
        latency_ms=latency_ms,
        prompt_tokens=generation.prompt_tokens,
        completion_tokens=generation.completion_tokens,
        cost_usd=cost_usd,
    )
