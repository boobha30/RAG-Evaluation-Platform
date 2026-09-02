"use client";

import { useRef, useState } from "react";
import { postQuery } from "@/lib/api";
import type { QueryResponse } from "@/lib/types";
import { ChunkList } from "@/components/ChunkList";
import { MetricBadge, faithfulnessTone } from "@/components/MetricBadge";
import { fmtMs, fmtPct } from "@/components/StatTile";

interface Turn {
  id: number;
  question: string;
  status: "loading" | "done" | "error";
  response?: QueryResponse;
  error?: string;
}

export default function AskPage() {
  const [input, setInput] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [useHybrid, setUseHybrid] = useState(true);
  const [useReranker, setUseReranker] = useState(true);
  const [showSettings, setShowSettings] = useState(false);
  const nextId = useRef(0);

  async function ask(question: string) {
    if (!question.trim()) return;
    const id = nextId.current++;
    setTurns((t) => [...t, { id, question, status: "loading" }]);
    setInput("");

    try {
      const response = await postQuery({
        query: question,
        use_hybrid: useHybrid,
        use_reranker: useReranker,
      });
      setTurns((t) =>
        t.map((turn) => (turn.id === id ? { ...turn, status: "done", response } : turn))
      );
    } catch (err) {
      setTurns((t) =>
        t.map((turn) =>
          turn.id === id
            ? { ...turn, status: "error", error: err instanceof Error ? err.message : String(err) }
            : turn
        )
      );
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold">Ask</h1>
          <p className="secondary text-sm mt-1">
            Query the RAG pipeline directly. Every answer here is scored and
            logged the same way as an eval run.
          </p>
        </div>
        <button
          onClick={() => setShowSettings((s) => !s)}
          className="text-xs secondary px-3 py-1.5 rounded-md hover:text-[var(--text-primary)] whitespace-nowrap"
          style={{ border: "1px solid var(--border)" }}
        >
          {showSettings ? "Hide settings" : "Settings"}
        </button>
      </div>

      {showSettings && (
        <div className="card p-4 flex flex-wrap gap-6 text-sm">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={useHybrid}
              onChange={(e) => setUseHybrid(e.target.checked)}
            />
            Hybrid retrieval (dense + BM25)
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={useReranker}
              onChange={(e) => setUseReranker(e.target.checked)}
            />
            Cross-encoder reranking
          </label>
        </div>
      )}

      <div className="flex flex-col gap-4">
        {turns.length === 0 && (
          <div className="card p-8 text-center muted text-sm">
            Ask a question about the documents in <code>data/raw/</code> to see
            retrieval + generation + evaluation run end to end.
          </div>
        )}

        {turns.map((turn) => (
          <div key={turn.id} className="flex flex-col gap-3">
            <div className="self-end max-w-[80%] card px-4 py-2.5 text-sm" style={{ background: "var(--page)" }}>
              {turn.question}
            </div>

            {turn.status === "loading" && (
              <div className="muted text-sm px-1">Thinking…</div>
            )}

            {turn.status === "error" && (
              <div className="card p-4 text-sm" style={{ borderColor: "var(--status-critical)" }}>
                <span style={{ color: "var(--status-critical)" }}>{turn.error}</span>
              </div>
            )}

            {turn.status === "done" && turn.response && (
              <div className="card p-4 flex flex-col gap-4">
                <p className="text-sm whitespace-pre-wrap">{turn.response.answer}</p>

                <div className="flex flex-wrap items-center gap-2">
                  {turn.response.metrics.faithfulness !== null && (
                    <MetricBadge
                      label={`faithfulness ${fmtPct(turn.response.metrics.faithfulness)}`}
                      tone={faithfulnessTone(turn.response.metrics.faithfulness)}
                    />
                  )}
                  {turn.response.metrics.hallucinated && (
                    <MetricBadge label="hallucinated" tone="critical" />
                  )}
                  {turn.response.metrics.relevance !== null && (
                    <MetricBadge label={`relevance ${fmtPct(turn.response.metrics.relevance)}`} tone="neutral" />
                  )}
                  <MetricBadge label={fmtMs(turn.response.metrics.latency_ms)} tone="neutral" />
                </div>

                {turn.response.metrics.unsupported_claims.length > 0 && (
                  <ul className="text-sm secondary list-disc pl-5">
                    {turn.response.metrics.unsupported_claims.map((claim, i) => (
                      <li key={i}>{claim}</li>
                    ))}
                  </ul>
                )}

                <details>
                  <summary className="text-xs secondary cursor-pointer">
                    {turn.response.sources.length} retrieved chunks
                  </summary>
                  <div className="mt-3">
                    <ChunkList chunks={turn.response.sources} />
                  </div>
                </details>
              </div>
            )}
          </div>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          ask(input);
        }}
        className="sticky bottom-6 flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about the ingested documents…"
          className="flex-1 card px-4 py-2.5 text-sm outline-none"
        />
        <button
          type="submit"
          disabled={!input.trim()}
          className="px-4 py-2.5 rounded-xl text-sm font-medium disabled:opacity-40"
          style={{ background: "var(--series-blue)", color: "white" }}
        >
          Ask
        </button>
      </form>
    </div>
  );
}
