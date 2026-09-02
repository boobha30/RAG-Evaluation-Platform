"use client";

import { fetchEvalRuns, fetchLogs } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { DataState } from "@/components/DataState";
import { StatTile, fmtMs, fmtPct, fmtUsd } from "@/components/StatTile";
import { MetricsComparisonChart } from "@/components/charts/MetricsComparisonChart";
import { SingleMetricBarChart } from "@/components/charts/SingleMetricBarChart";

export default function OverviewPage() {
  const runsState = useApi(fetchEvalRuns, []);
  const logsState = useApi(() => fetchLogs(200), []);

  const runs = runsState.data ?? [];
  const logs = logsState.data ?? [];
  const latestRun = runs[0];

  const latencyData = runs
    .slice()
    .reverse()
    .map((r) => ({ name: r.name || r.config_name, value: r.avg_latency_ms ?? 0 }));
  const costData = runs
    .slice()
    .reverse()
    .map((r) => ({ name: r.name || r.config_name, value: r.total_cost_usd ?? 0 }));

  return (
    <div className="flex flex-col gap-8">
      <div>
        <h1 className="text-xl font-semibold">Overview</h1>
        <p className="secondary text-sm mt-1">
          Explainability for RAG: retrieval + generation quality across pipeline
          configurations and live traffic.
        </p>
      </div>

      <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatTile label="Eval runs" value={String(runs.length)} />
        <StatTile label="Live queries logged" value={String(logs.length)} />
        <StatTile
          label="Latest faithfulness"
          value={fmtPct(latestRun?.avg_faithfulness ?? null)}
          sub={latestRun ? `run: ${latestRun.name || latestRun.config_name}` : undefined}
        />
        <StatTile
          label="Latest hallucination rate"
          value={fmtPct(latestRun?.hallucination_rate ?? null)}
        />
      </section>

      <section className="card p-4">
        <h2 className="text-sm font-medium mb-1">
          Retrieval &amp; generation quality by configuration
        </h2>
        <p className="muted text-xs mb-4">
          Each eval run is one pipeline configuration (dense-only, hybrid,
          hybrid+rerank) scored against the same labeled QA set.
        </p>
        <DataState loading={runsState.loading} error={runsState.error} empty={runs.length === 0}>
          <MetricsComparisonChart runs={runs} />
        </DataState>
      </section>

      <section className="grid sm:grid-cols-2 gap-4">
        <div className="card p-4">
          <h2 className="text-sm font-medium mb-4">Avg latency per run</h2>
          <DataState loading={runsState.loading} error={runsState.error} empty={runs.length === 0}>
            <SingleMetricBarChart data={latencyData} valueFormatter={(v) => fmtMs(v)} />
          </DataState>
        </div>
        <div className="card p-4">
          <h2 className="text-sm font-medium mb-4">Total cost per run</h2>
          <DataState loading={runsState.loading} error={runsState.error} empty={runs.length === 0}>
            <SingleMetricBarChart data={costData} valueFormatter={(v) => fmtUsd(v)} />
          </DataState>
        </div>
      </section>
    </div>
  );
}
