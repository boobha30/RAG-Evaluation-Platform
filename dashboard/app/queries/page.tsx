"use client";

import Link from "next/link";
import { fetchLogs } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { DataState } from "@/components/DataState";
import { fmtMs, fmtPct } from "@/components/StatTile";
import { MetricBadge, faithfulnessTone } from "@/components/MetricBadge";

export default function QueriesPage() {
  const { data, loading, error } = useApi(() => fetchLogs(100), []);
  const logs = data ?? [];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-xl font-semibold">Live Queries</h1>
        <p className="secondary text-sm mt-1">
          Recent traffic through <code>/query</code>, scored as it happens.
        </p>
      </div>

      <DataState loading={loading} error={error} empty={logs.length === 0}>
        <div className="card overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left muted text-xs uppercase" style={{ borderBottom: "1px solid var(--border)" }}>
                <th className="px-4 py-3 font-medium">Query</th>
                <th className="px-4 py-3 font-medium">Faithfulness</th>
                <th className="px-4 py-3 font-medium">Relevance</th>
                <th className="px-4 py-3 font-medium">Latency</th>
                <th className="px-4 py-3 font-medium">Cost</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr
                  key={log.id}
                  style={{ borderBottom: "1px solid var(--border)" }}
                  className="hover:bg-[var(--page)] transition-colors"
                >
                  <td className="px-4 py-3">
                    <Link href={`/queries/${log.id}`} className="hover:underline">
                      {log.query.length > 70 ? `${log.query.slice(0, 70)}…` : log.query}
                    </Link>
                    {log.hallucinated && (
                      <span className="ml-2">
                        <MetricBadge label="hallucinated" tone="critical" />
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    {log.faithfulness === null ? (
                      <span className="muted">—</span>
                    ) : (
                      <MetricBadge label={fmtPct(log.faithfulness)} tone={faithfulnessTone(log.faithfulness)} />
                    )}
                  </td>
                  <td className="px-4 py-3 secondary">{fmtPct(log.relevance)}</td>
                  <td className="px-4 py-3 secondary">{fmtMs(log.latency_ms)}</td>
                  <td className="px-4 py-3 secondary">
                    {log.cost_usd === null ? "—" : `$${log.cost_usd.toFixed(4)}`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DataState>
    </div>
  );
}
