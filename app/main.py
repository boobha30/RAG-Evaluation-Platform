import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import APIError

from app.config import settings
from app.db import get_session, init_db
from app.eval.pipeline import score_and_log_query
from app.generation import generate_answer
from app.models import EvalRun, QueryLog
from app.retriever import Retriever
from app.schemas import (
    EvalRunDetailOut,
    EvalRunOut,
    QueryLogOut,
    QueryRequest,
    QueryResponse,
)

retriever: Retriever | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global retriever
    init_db()
    try:
        retriever = Retriever.from_disk()
    except FileNotFoundError:
        retriever = None
    yield


app = FastAPI(title="RAG Evaluation Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # portfolio project: dashboard runs on a different localhost port
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "index_loaded": retriever is not None}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    if retriever is None:
        raise HTTPException(
            status_code=503,
            detail="No index loaded. Run scripts/build_index.py first.",
        )
    if not settings.openai_api_key and not settings.openai_base_url:
        raise HTTPException(
            status_code=503,
            detail="OPENAI_API_KEY is not configured. Set it in .env.",
        )

    start = time.perf_counter()
    contexts = retriever.retrieve(
        request.query,
        top_k=request.top_k,
        use_hybrid=request.use_hybrid,
        use_reranker=request.use_reranker,
    )
    if not contexts:
        raise HTTPException(status_code=404, detail="No relevant context found.")

    try:
        generation = generate_answer(request.query, contexts)
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {e.message}")
    latency_ms = (time.perf_counter() - start) * 1000

    metrics = score_and_log_query(
        request.query,
        contexts,
        generation,
        latency_ms=latency_ms,
        include_faithfulness=request.evaluate and settings.evaluate_live_queries,
    )

    return QueryResponse(
        answer=generation.answer,
        sources=contexts,
        metrics=metrics.__dict__,
    )


@app.get("/logs", response_model=list[QueryLogOut])
def list_logs(limit: int = 50, offset: int = 0):
    session = get_session()
    try:
        rows = (
            session.query(QueryLog)
            .filter(QueryLog.run_id.is_(None))
            .order_by(QueryLog.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return rows
    finally:
        session.close()


@app.get("/logs/{log_id}", response_model=QueryLogOut)
def get_log(log_id: int):
    session = get_session()
    try:
        row = session.get(QueryLog, log_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Query log not found.")
        return row
    finally:
        session.close()


def _run_to_out(run: EvalRun, cls=EvalRunOut, **extra) -> dict:
    logs = run.logs
    n = len(logs)

    def _avg(values):
        clean = [v for v in values if v is not None]
        return sum(clean) / len(clean) if clean else None

    hallucinated_flags = [l.hallucinated for l in logs if l.hallucinated is not None]
    hallucination_rate = (
        sum(1 for h in hallucinated_flags if h) / len(hallucinated_flags)
        if hallucinated_flags
        else None
    )

    return cls(
        id=run.id,
        name=run.name,
        config_name=run.config_name,
        use_hybrid=run.use_hybrid,
        use_reranker=run.use_reranker,
        created_at=run.created_at,
        num_queries=n,
        avg_precision=_avg([l.precision for l in logs]),
        avg_recall=_avg([l.recall for l in logs]),
        avg_mrr=_avg([l.mrr for l in logs]),
        avg_faithfulness=_avg([l.faithfulness for l in logs]),
        hallucination_rate=hallucination_rate,
        avg_relevance=_avg([l.relevance for l in logs]),
        avg_latency_ms=_avg([l.latency_ms for l in logs]),
        total_cost_usd=sum((l.cost_usd or 0.0) for l in logs),
        **extra,
    )


@app.get("/eval/runs", response_model=list[EvalRunOut])
def list_eval_runs():
    session = get_session()
    try:
        runs = session.query(EvalRun).order_by(EvalRun.created_at.desc()).all()
        return [_run_to_out(r) for r in runs]
    finally:
        session.close()


@app.get("/eval/runs/{run_id}", response_model=EvalRunDetailOut)
def get_eval_run(run_id: int):
    session = get_session()
    try:
        run = session.get(EvalRun, run_id)
        if run is None:
            raise HTTPException(status_code=404, detail="Eval run not found.")
        return _run_to_out(run, cls=EvalRunDetailOut, logs=run.logs)
    finally:
        session.close()
