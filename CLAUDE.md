# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A RAG (retrieval-augmented generation) system built to be *measured*: hybrid
(dense + BM25) retrieval with reciprocal rank fusion, cross-encoder
reranking, and an automated evaluation harness (retrieval metrics +
LLM-judged faithfulness/hallucination + answer relevance) that logs every
query to Postgres/SQLite, surfaced in a Next.js dashboard.

Two independent apps in one repo: `app/` (Python/FastAPI backend) and
`dashboard/` (Next.js frontend). The dashboard has its own
[dashboard/CLAUDE.md](dashboard/CLAUDE.md) (currently an `@AGENTS.md`
include) — read it when working there. It points at
[dashboard/AGENTS.md](dashboard/AGENTS.md), which warns that the installed
Next.js version (16.x) may differ from training-data assumptions and to
check `node_modules/next/dist/docs/` before writing dashboard code.

## Commands

### Backend setup

```bash
python3.10 -m venv .venv          # must be 3.10 — faiss/torch wheels need it, not system python
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # set OPENAI_API_KEY
python scripts/build_index.py      # builds FAISS + BM25 index from data/raw/ (required before serving)
uvicorn app.main:app --reload
```

`DATABASE_URL` defaults to a local SQLite file (`data/eval/eval.db`), so
zero extra setup is needed to run. `docker compose up postgres` starts a
Postgres instance for the full experience.

### Tests

```bash
pytest tests/ -v                       # all tests — no API key or network required
pytest tests/test_retriever.py -v      # single file
pytest tests/test_retriever.py::test_name -v   # single test
```

### Evaluation runs

```bash
python scripts/run_eval.py --config dense
python scripts/run_eval.py --config hybrid
python scripts/run_eval.py --config hybrid_rerank
```

Each batch-runs the 27-question labeled QA set (`data/eval/qa_set.json`)
through a pipeline configuration and logs results to the same `query_logs`
table used by live `/query` calls, so the dashboard can compare them.
Requires `OPENAI_API_KEY` (used for generation and the LLM judge).

### Dashboard

```bash
cd dashboard
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL, defaults to localhost:8000
npm install
npm run dev             # dev server
npm run build            # production build
npm run lint              # eslint
npx tsc --noEmit           # typecheck
```

### Docker

```bash
docker compose up --build
```

Starts Postgres, the FastAPI backend (index built at image-build time from
`data/raw/`), and the dashboard. Requires `OPENAI_API_KEY` in the shell
environment (passed through in `docker-compose.yml`).

## Architecture

**Pipeline**: `app/ingestion.py` (semantic chunking) → `app/embeddings.py`
(SBERT) → `app/vector_store.py` (FAISS) + `app/bm25_index.py` (BM25) →
`app/retriever.py` (Reciprocal Rank Fusion of the two, then
`app/reranker.py` cross-encoder) → `app/generation.py` (OpenAI) →
`app/eval/` (metrics, judge, relevance) → `app/db.py` / `app/models.py`
(SQLAlchemy, Postgres or SQLite) → `app/main.py` (FastAPI) → `dashboard/`
(Next.js).

**Hybrid retrieval + reranking** (`app/retriever.py`): dense embedding
search and BM25 keyword search are run independently, merged with
Reciprocal Rank Fusion (`reciprocal_rank_fusion`), then the fused top-N
candidates are reranked with a `ms-marco-MiniLM` cross-encoder that scores
query+passage jointly. Dense search alone misses exact keyword matches
(rare terms, product codes); BM25 alone misses paraphrases — that's why
both run and get fused rather than picking one. Toggle both independently
per-request via `use_hybrid` / `use_reranker` on `/query`, or via
`--config dense|hybrid|hybrid_rerank` in `scripts/run_eval.py`.

**Evaluation harness** (`app/eval/`): `pipeline.py` is the shared scoring +
DB-logging path used by *both* the live `/query` endpoint and
`scripts/run_eval.py` batch runs — they write to the same `query_logs`
table, distinguished by `run_id` (null for live traffic, set for a batch
eval run). This is why `/logs` filters on `run_id.is_(None)` in
`app/main.py`. Metrics computed: retrieval precision@k/recall@k/MRR
(`retrieval_metrics.py`) against the labeled QA set, LLM-as-judge
faithfulness/hallucination (`judge.py`), answer-relevance via
question/answer embedding cosine similarity (`relevance.py`), and token
cost (`cost.py`). Live-query judging is gated by
`request.evaluate and settings.evaluate_live_queries` since LLM-judging
every live query is expensive.

**Config** (`app/config.py`): all tunables (chunk size, RRF's `rrf_k`,
`fusion_candidate_k`, reranker top-n, models, `DATABASE_URL`) are a single
`Settings` object read from `.env` — check here before threading a new
constant through by hand.

**Startup**: `app/main.py` lifespan calls `init_db()` then loads
`Retriever.from_disk()`; if no index exists yet (`build_index.py` hasn't
run), `retriever` stays `None` and `/query` returns 503 rather than
crashing at startup.

## CI/CD

`Jenkinsfile` runs `pytest` and dashboard lint/typecheck/build on every
commit, then builds both Docker images. ECR-push/ECS-deploy stages exist
only as commented-out documentation of the intended AWS path — they are
not wired to run automatically (no AWS credentials, would provision
billable resources).
