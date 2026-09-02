<<<<<<< HEAD
# RAG Evaluation Platform

A retrieval-augmented generation (RAG) system built specifically to be
*measured*: hybrid retrieval, cross-encoder reranking, and an automated
evaluation harness (retrieval metrics + LLM-judged faithfulness/hallucination
+ answer relevance) that logs every query to Postgres, surfaced in a Next.js
dashboard for explainability — why did this answer succeed or fail, given
what was actually retrieved?

## Architecture

```mermaid
flowchart LR
    subgraph Ingestion
        A[data/raw/*.txt,.md,.pdf] --> B[Semantic chunking]
        B --> C[SBERT embeddings]
        C --> D[(FAISS index)]
        B --> E[(BM25 index)]
    end

    subgraph "Query time"
        Q[Query] --> F[Dense search]
        Q --> G[BM25 search]
        F --> H[Reciprocal Rank Fusion]
        G --> H
        H --> I[Cross-encoder reranker]
        I --> J[LLM generation]
        J --> K[Answer + sources]
    end

    subgraph "Evaluation"
        K --> L[Retrieval metrics<br/>precision / recall / MRR]
        K --> M[LLM-as-judge<br/>faithfulness / hallucination]
        K --> N[Embedding similarity<br/>answer relevance]
        L --> O[(Postgres)]
        M --> O
        N --> O
    end

    O --> P[Next.js dashboard]

    D -.-> F
    E -.-> G
```

**Pipeline**: `app/ingestion.py` (semantic chunking) → `app/embeddings.py` →
`app/vector_store.py` (FAISS) + `app/bm25_index.py` (BM25) →
`app/retriever.py` (Reciprocal Rank Fusion + `app/reranker.py` cross-encoder)
→ `app/generation.py` → `app/eval/` (metrics, judge, relevance) →
`app/db.py` / `app/models.py` (Postgres) → `app/main.py` (FastAPI) →
`dashboard/` (Next.js).

## Why hybrid retrieval + reranking

Dense (embedding) retrieval finds semantically similar text but can miss
exact keyword matches (rare terms, product codes, acronyms). BM25 keyword
search covers exactly that gap but misses paraphrases. This project runs
both and merges them with **Reciprocal Rank Fusion** (`app/retriever.py:reciprocal_rank_fusion`),
then reranks the fused top candidates with a `ms-marco-MiniLM` cross-encoder
that scores the query and passage jointly — a much stronger relevance signal
than a bi-encoder, at a cost that's affordable *only* on a small shortlist.

## Why an evaluation harness, not eyeballing

Automated metrics, logged for every query:

- **Retrieval**: precision@k, recall@k, MRR against a 27-question labeled QA
  set (`data/eval/qa_set.json`) hand-built from the project's own docs corpus.
- **Faithfulness / hallucination**: LLM-as-judge (`app/eval/judge.py`) checks
  whether the answer's claims are actually supported by the retrieved
  context — not just fluent, but grounded.
- **Answer relevance**: cosine similarity between question and answer
  embeddings (`app/eval/relevance.py`) — catches faithful-but-off-topic answers.
- **Cost/latency**: token usage and wall-clock time per query.

Every live `/query` call and every batch `scripts/run_eval.py` run is logged
to the same `query_logs` table, so the dashboard can show live traffic and
controlled eval-run comparisons side by side.

## Results: dense-only vs hybrid vs hybrid+reranked

Produced by running the same 27-question QA set through
`scripts/run_eval.py` against three pipeline configurations, on the same
FAISS/BM25 index:

| Config | Precision@4 | Recall@4 | MRR | Faithfulness | Hallucination rate | Relevance | Avg latency |
|---|---|---|---|---|---|---|---|
| dense | 0.741 | 1.000 | 0.975 | 0.711 | 7.4% | 0.771 | 12.6s |
| hybrid | 0.778 | 1.000 | 0.975 | 0.735 | 7.4% | 0.764 | 10.1s |
| hybrid_rerank | 0.759 | 1.000 | **1.000** | **0.769** | **0.0%** | **0.778** | 9.4s |

**Hallucination rate dropped from 7.4% to 0%** going from dense-only to the
full hybrid+rerank pipeline, faithfulness climbed 71.1% → 76.9%, and MRR
reached a perfect 1.000 — the reranker consistently puts the single most
relevant chunk first, even in the (rare) cases hybrid retrieval didn't.
Precision@4 wasn't perfectly monotonic (0.741 → 0.778 → 0.759): with a
27-question set, index-level noise can outweigh a small ranking change on
individual borderline questions — recall@k is already saturated at 1.000
throughout, meaning the relevant document was always somewhere in the top 4,
so the real differentiator between configs here is faithfulness and
hallucination rate, not what got retrieved but *how well the model used it*.

Run against a **free, fully local model** (no OpenAI billing) — see
[Free/local generation](#freelocal-generation-no-api-key-needed) below — on
generation quality alone a hosted model would likely score higher across the
board; the *relative* improvement from hybrid+rerank is the point being
measured here, not the absolute numbers. Reproduce with:

```bash
python scripts/run_eval.py --config dense
python scripts/run_eval.py --config hybrid
python scripts/run_eval.py --config hybrid_rerank
```

or view them interactively in the dashboard's Eval Runs page.

## Project layout

```
app/
  ingestion.py        semantic chunking
  embeddings.py        SBERT embeddings
  vector_store.py      FAISS index build/search
  bm25_index.py         BM25 index build/search
  reranker.py           cross-encoder reranker
  retriever.py          hybrid retrieval + RRF fusion
  generation.py          OpenAI generation
  db.py / models.py       SQLAlchemy (Postgres/SQLite)
  eval/
    retrieval_metrics.py  precision@k / recall@k / MRR
    relevance.py           answer-question embedding similarity
    judge.py                 LLM-as-judge faithfulness/hallucination
    cost.py                    token cost estimation
    pipeline.py                shared scoring + DB logging, used by both
                                 /query and scripts/run_eval.py
  main.py               FastAPI app: /query, /logs, /eval/runs
scripts/
  build_index.py        build FAISS + BM25 index from data/raw/
  run_eval.py            batch-run the QA set through a config, log to DB
data/
  raw/                  source documents
  eval/qa_set.json        27 labeled Q&A pairs
tests/                  pytest: chunking, RRF fusion, retrieval metrics
dashboard/              Next.js app: overview, live queries, eval runs
Dockerfile / dashboard/Dockerfile / docker-compose.yml
Jenkinsfile
```

## Setup

### Backend

```bash
python3.10 -m venv .venv          # this project needs 3.10 for faiss/torch wheels
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env               # set OPENAI_API_KEY
python scripts/build_index.py      # builds FAISS + BM25 index from data/raw/
uvicorn app.main:app --reload
```

By default `DATABASE_URL` points at a local SQLite file
(`data/eval/eval.db`) so the app runs with zero setup. Point it at Postgres
(`postgresql+psycopg2://rag:rag@localhost:5432/rag_eval`) for the full
experience — `docker compose up postgres` starts one.

SQLite is fine for a single writer, but this project logs *every* live
query and batch eval run to the same file, so `app/db.py` enables WAL mode
+ a busy timeout on the sqlite engine — without it, running
`scripts/run_eval.py` in the background while also hitting `/query` (e.g.
from the dashboard's Ask page) can throw `attempt to write a readonly
database` as two processes race for the file lock. Postgres doesn't have
this problem at all.

### Free/local generation (no API key needed)

`GENERATION_MODEL`/`JUDGE_MODEL` and the OpenAI client's `base_url` are
both configurable (`app/config.py`'s `openai_base_url`), so any
OpenAI-compatible server works — including [Ollama](https://ollama.com),
which is free and runs entirely on your machine:

```bash
brew install ollama
ollama pull llama3.2:3b
```

```bash
# .env
# OPENAI_API_KEY=            # leave unset
OPENAI_BASE_URL=http://localhost:11434/v1
GENERATION_MODEL=llama3.2:3b
JUDGE_MODEL=llama3.2:3b
```

`app/eval/cost.py` reports `$0` cost automatically whenever
`OPENAI_BASE_URL` is set, since OpenAI's per-token pricing doesn't apply to
a self-hosted model. The [results above](#results-dense-only-vs-hybrid-vs-hybridreranked)
were produced this way — a 3B local model is noticeably slower (~10-15s per
query on a laptop CPU vs. sub-second for a hosted API) and lower quality
than `gpt-4o-mini`, but it's enough to demonstrate the pipeline and measure
the *relative* effect of hybrid retrieval and reranking without spending
anything. Swap back to `OPENAI_API_KEY` + `gpt-4o-mini` any time for faster,
higher-quality answers.

### Evaluation

```bash
python scripts/run_eval.py --config dense
python scripts/run_eval.py --config hybrid
python scripts/run_eval.py --config hybrid_rerank
```

### Dashboard

```bash
cd dashboard
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL, defaults to localhost:8000
npm install
npm run dev
```

### Tests

```bash
pytest tests/ -v
```

22 tests covering semantic chunking boundary behavior, RRF fusion math, and
retrieval metrics — no API key or network required.

### Docker

```bash
docker compose up --build
```

Starts Postgres, the FastAPI backend (index built at image-build time from
`data/raw/`), and the dashboard. Set `OPENAI_API_KEY` in your shell
environment before running (it's passed through in `docker-compose.yml`).

> Docker was not available in the environment this project was built in, so
> `docker compose build`/`up` have not been run end-to-end here — verify
> locally before relying on it. The Dockerfiles and compose config follow
> standard multi-stage patterns (Python slim base pinned to 3.10, Next.js
> `output: "standalone"`) and were reviewed but not executed.

### CI/CD and cloud deployment

`Jenkinsfile` runs backend tests (pytest) and dashboard lint/typecheck/build
on every commit, then builds both Docker images. The ECR-push and
ECS-deploy stages are included as commented-out documentation of the
intended AWS path — they need real AWS credentials and provision billable
resources, so they're not wired to run automatically. To go live: bind AWS
credentials in Jenkins, uncomment those stages, and point them at an ECR
repo and ECS cluster (or swap for App Runner / Elastic Beanstalk for a
lighter footprint).

## What has been verified

Everything in this checkout has been run, not just written:

- `pytest tests/` — 22/22 passing (chunking, RRF fusion, retrieval metrics).
- `scripts/build_index.py` — builds a 52-chunk FAISS + BM25 index from the
  corpus in `data/raw/` (the original sample doc plus five added topical
  docs, needed for a meaningful 27-question QA set).
- Hybrid retrieval + reranking end-to-end (`Retriever.retrieve`): confirmed
  it fuses dense + BM25 candidates and reranks them to the most relevant
  chunk for a held-out query.
- FastAPI app: `init_db()` creates the schema on startup, `/health`,
  `/logs`, `/eval/runs`, `/eval/runs/{id}` all verified against a live
  server and real database rows, response shapes matching the dashboard's
  TypeScript types exactly.
- Dashboard: `npx tsc --noEmit`, `npx eslint .`, and `next build` all pass
  cleanly; `next start` was run against the live FastAPI backend and every
  route (`/`, `/ask`, `/queries`, `/queries/[id]`, `/runs`, `/runs/[id]`)
  returned 200 and round-tripped real API data.
- **The full pipeline end to end, including real LLM calls**: all three
  `scripts/run_eval.py` configs (dense/hybrid/hybrid_rerank) ran to
  completion against a local Ollama model, producing the
  [results table above](#results-dense-only-vs-hybrid-vs-hybridreranked)
  from real generation and real LLM-as-judge faithfulness scoring — not
  placeholder numbers. Live `/query` calls through the Ask page were also
  exercised against the same local model.

What has **not** been run: anything against the real OpenAI API (the
`gpt-4o-mini` numbers would likely differ, probably favorably, from the
local-model numbers above — the account available during development had
no billing quota), and `docker compose build`/`up` (Docker was not
installed in this environment).
=======
# RAG-Evaluation-Platform
>>>>>>> 86f678698444548f7dd25764aa4ff54051030516
