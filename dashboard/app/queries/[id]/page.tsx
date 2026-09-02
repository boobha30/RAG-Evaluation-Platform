"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { fetchLog } from "@/lib/api";
import { useApi } from "@/lib/useApi";
import { DataState } from "@/components/DataState";
import { StatTile, fmtMs, fmtPct } from "@/components/StatTile";
import { MetricBadge } from "@/components/MetricBadge";
import { ChunkList } from "@/components/ChunkList";

export default function QueryDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const { data: log, loading, error } = useApi(() => fetchLog(id), [id]);

  return (
    <div className="flex flex-col gap-6">
      <Link href="/queries" className="secondary text-sm hover:underline w-fit">
        ← Back to live queries
      </Link>

      <DataState loading={loading} error={error}>
        {log && (
          <>
            <div>
              <h1 className="text-xl font-semibold">{log.query}</h1>
              <p className="muted text-xs mt-1">
                {new Date(log.created_at).toLocaleString()}
              </p>
            </div>

            <section className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <StatTile label="Faithfulness" value={fmtPct(log.faithfulness)} />
              <StatTile label="Relevance" value={fmtPct(log.relevance)} />
              <StatTile label="Latency" value={fmtMs(log.latency_ms)} />
              <StatTile
                label="Tokens (prompt / completion)"
                value={`${log.prompt_tokens ?? "—"} / ${log.completion_tokens ?? "—"}`}
              />
            </section>

            {log.hallucinated && (
              <div className="card p-4" style={{ borderColor: "var(--status-critical)" }}>
                <MetricBadge label="Hallucination detected" tone="critical" />
                {log.unsupported_claims.length > 0 && (
                  <ul className="mt-2 text-sm secondary list-disc pl-5">
                    {log.unsupported_claims.map((claim, i) => (
                      <li key={i}>{claim}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}

            <section className="grid md:grid-cols-2 gap-4">
              <div className="card p-4">
                <h2 className="text-sm font-medium mb-3">
                  Retrieved chunks ({log.retrieved_chunks.length})
                </h2>
                <div className="max-h-[520px] overflow-y-auto pr-1">
                  <ChunkList chunks={log.retrieved_chunks} />
                </div>
              </div>

              <div className="card p-4">
                <h2 className="text-sm font-medium mb-3">Generated answer</h2>
                <p className="text-sm whitespace-pre-wrap">{log.answer}</p>
              </div>
            </section>
          </>
        )}
      </DataState>
    </div>
  );
}
