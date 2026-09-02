"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { fetchEvalRun } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { DataState } from "@/components/DataState";
import { StatTile, fmtMs, fmtNum, fmtPct, fmtUsd } from "@/components/StatTile";
import { MetricBadge, faithfulnessTone } from "@/components/MetricBadge";

export default function RunDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const { data: run, loading, error } = useApi(() => fetchEvalRun(id), [id]);

  return (
    <div className="flex flex-col gap-6">
      <Link href="/runs" className="secondary text-sm hover:underline w-fit">
        ← Back to eval runs
      </Link>

      <DataState loading={loading} error={error}>
        {run && (
          <>
            <div>
              <h1 className="text-xl font-semibold">{run.name || run.config_name}</h1>
              <p className="muted text-xs mt-1">
                config={run.config_name} · hybrid={String(run.use_hybrid)} · reranker=
                {String(run.use_reranker)} · {new Date(run.created_at).toLocaleString()}
              </p>
            </div>

            <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <StatTile label="Precision@k" value={fmtNum(run.avg_precision)} />
              <StatTile label="Recall@k" value={fmtNum(run.avg_recall)} />
              <StatTile label="MRR" value={fmtNum(run.avg_mrr)} />
              <StatTile label="Faithfulness" value={fmtPct(run.avg_faithfulness)} />
              <StatTile label="Hallucination rate" value={fmtPct(run.hallucination_rate)} />
              <StatTile label="Answer relevance" value={fmtPct(run.avg_relevance)} />
              <StatTile label="Avg latency" value={fmtMs(run.avg_latency_ms)} />
              <StatTile label="Total cost" value={fmtUsd(run.total_cost_usd)} />
            </section>

            <div className="card overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left muted text-xs uppercase" style={{ borderBottom: "1px solid var(--border)" }}>
                    <th className="px-4 py-3 font-medium">Question</th>
                    <th className="px-4 py-3 font-medium">Precision</th>
                    <th className="px-4 py-3 font-medium">Recall</th>
                    <th className="px-4 py-3 font-medium">MRR</th>
                    <th className="px-4 py-3 font-medium">Faithfulness</th>
                  </tr>
                </thead>
                <tbody>
                  {run.logs.map((log) => (
                    <tr
                      key={log.id}
                      style={{ borderBottom: "1px solid var(--border)" }}
                      className="hover:bg-[var(--page)] transition-colors"
                    >
                      <td className="px-4 py-3">
                        <Link href={`/queries/${log.id}`} className="hover:underline">
                          {log.query.length > 70 ? `${log.query.slice(0, 70)}…` : log.query}
                        </Link>
                      </td>
                      <td className="px-4 py-3 secondary">{fmtNum(log.precision)}</td>
                      <td className="px-4 py-3 secondary">{fmtNum(log.recall)}</td>
                      <td className="px-4 py-3 secondary">{fmtNum(log.mrr)}</td>
                      <td className="px-4 py-3">
                        {log.faithfulness === null ? (
                          <span className="muted">—</span>
                        ) : (
                          <MetricBadge label={fmtPct(log.faithfulness)} tone={faithfulnessTone(log.faithfulness)} />
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </DataState>
    </div>
  );
}
