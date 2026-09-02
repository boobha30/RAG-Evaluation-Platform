"use client";

import Link from "next/link";
import { fetchEvalRuns } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { DataState } from "@/components/DataState";
import { fmtMs, fmtNum, fmtPct } from "@/components/StatTile";

export default function RunsPage() {
  const { data, loading, error } = useApi(fetchEvalRuns, []);
  const runs = data ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Eval Runs</h1>
        <p className="secondary text-sm mt-1">
          Batch runs of the labeled QA set through a pipeline configuration.
          Produced with <code>scripts/run_eval.py --config &lt;name&gt;</code>.
        </p>
      </div>

      <DataState loading={loading} error={error} empty={runs.length === 0}>
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left muted text-xs uppercase" style={{ borderBottom: "1px solid var(--border)" }}>
                <th className="px-4 py-3 font-medium">Run</th>
                <th className="px-4 py-3 font-medium">Config</th>
                <th className="px-4 py-3 font-medium">Precision</th>
                <th className="px-4 py-3 font-medium">Recall</th>
                <th className="px-4 py-3 font-medium">MRR</th>
                <th className="px-4 py-3 font-medium">Faithfulness</th>
                <th className="px-4 py-3 font-medium">Hallucination</th>
                <th className="px-4 py-3 font-medium">Latency</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr
                  key={run.id}
                  style={{ borderBottom: "1px solid var(--border)" }}
                  className="hover:bg-[var(--page)] transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link href={`/runs/${run.id}`} className="hover:underline font-medium">
                      {run.name || run.config_name}
                    </Link>
                    <div className="muted text-xs">{run.num_queries} queries</div>
                  </td>
                  <td className="px-4 py-3 secondary">{run.config_name}</td>
                  <td className="px-4 py-3 secondary">{fmtNum(run.avg_precision)}</td>
                  <td className="px-4 py-3 secondary">{fmtNum(run.avg_recall)}</td>
                  <td className="px-4 py-3 secondary">{fmtNum(run.avg_mrr)}</td>
                  <td className="px-4 py-3 secondary">{fmtPct(run.avg_faithfulness)}</td>
                  <td className="px-4 py-3 secondary">{fmtPct(run.hallucination_rate)}</td>
                  <td className="px-4 py-3 secondary">{fmtMs(run.avg_latency_ms)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataState>
    </div>
  );
}
