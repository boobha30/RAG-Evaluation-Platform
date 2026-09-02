"""Batch-run the labeled QA set through a chosen retrieval configuration and
log per-query + aggregate metrics to the database.

Usage:
    python scripts/run_eval.py --config dense
    python scripts/run_eval.py --config hybrid
    python scripts/run_eval.py --config hybrid_rerank --run-name "post-rerank"

Running this for each config against the same index is what produces the
before/after numbers (e.g. "faithfulness 71% -> 89% after adding reranking")
referenced in the README.
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.db import get_session, init_db
from app.eval.pipeline import score_and_log_query
from app.generation import generate_answer
from app.models import EvalRun
from app.retriever import Retriever

CONFIGS = {
    "dense": {"use_hybrid": False, "use_reranker": False},
    "hybrid": {"use_hybrid": True, "use_reranker": False},
    "hybrid_rerank": {"use_hybrid": True, "use_reranker": True},
}


def load_qa_set() -> list[dict]:
    path = settings.eval_dir / "qa_set.json"
    return json.loads(path.read_text())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", choices=sorted(CONFIGS), required=True)
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--top-k", type=int, default=settings.top_k)
    parser.add_argument(
        "--no-judge",
        action="store_true",
        help="Skip the LLM-as-judge faithfulness call (still needs OPENAI_API_KEY for generation).",
    )
    args = parser.parse_args()

    init_db()

    retrieval_opts = CONFIGS[args.config]
    qa_set = load_qa_set()
    print(f"Loaded {len(qa_set)} QA pairs. Config={args.config} top_k={args.top_k}")

    retriever = Retriever.from_disk()

    session = get_session()
    run = EvalRun(
        name=args.run_name or args.config,
        config_name=args.config,
        use_hybrid=retrieval_opts["use_hybrid"],
        use_reranker=retrieval_opts["use_reranker"],
    )
    session.add(run)
    session.commit()
    run_id = run.id
    session.close()

    all_metrics = []
    for i, item in enumerate(qa_set, start=1):
        question = item["question"]
        relevant_sources = set(item["relevant_sources"])

        start = time.perf_counter()
        contexts = retriever.retrieve(question, top_k=args.top_k, **retrieval_opts)
        generation = generate_answer(question, contexts) if contexts else None
        latency_ms = (time.perf_counter() - start) * 1000

        if generation is None:
            print(f"  [{i}/{len(qa_set)}] {question!r} -> no context retrieved, skipping")
            continue

        metrics = score_and_log_query(
            question,
            contexts,
            generation,
            latency_ms=latency_ms,
            relevant_sources=relevant_sources,
            run_id=run_id,
            include_faithfulness=not args.no_judge,
        )
        all_metrics.append(metrics)
        print(
            f"  [{i}/{len(qa_set)}] precision={metrics.precision:.2f} "
            f"recall={metrics.recall:.2f} mrr={metrics.mrr:.2f} "
            f"faithfulness={metrics.faithfulness} relevance={metrics.relevance:.2f} "
            f"latency={metrics.latency_ms:.0f}ms"
        )

    def _avg(values):
        clean = [v for v in values if v is not None]
        return sum(clean) / len(clean) if clean else None

    print("\n=== Aggregate results ===")
    print(f"Run: {run.name} (id={run_id}, config={args.config})")
    print(f"Queries evaluated: {len(all_metrics)}")
    print(f"Precision@k: {_avg([m.precision for m in all_metrics]):.3f}")
    print(f"Recall@k:    {_avg([m.recall for m in all_metrics]):.3f}")
    print(f"MRR:         {_avg([m.mrr for m in all_metrics]):.3f}")
    faithfulness_avg = _avg([m.faithfulness for m in all_metrics])
    print(f"Faithfulness: {faithfulness_avg:.3f}" if faithfulness_avg is not None else "Faithfulness: n/a")
    hallucination_rate = _avg([1.0 if m.hallucinated else 0.0 for m in all_metrics if m.hallucinated is not None])
    print(f"Hallucination rate: {hallucination_rate:.3f}" if hallucination_rate is not None else "Hallucination rate: n/a")
    print(f"Answer relevance: {_avg([m.relevance for m in all_metrics]):.3f}")
    print(f"Avg latency: {_avg([m.latency_ms for m in all_metrics]):.0f}ms")
    print(f"Total cost: ${sum(m.cost_usd for m in all_metrics):.4f}")


if __name__ == "__main__":
    main()
