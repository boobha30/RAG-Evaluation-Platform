import type { SourceChunk } from "@/lib/types";

export function ChunkList({ chunks }: { chunks: SourceChunk[] }) {
  return (
    <div className="flex flex-col gap-2">
      {chunks.map((chunk, i) => (
        <div
          key={i}
          className="text-sm p-3 rounded-lg"
          style={{ background: "var(--page)", border: "1px solid var(--border)" }}
        >
          <div className="flex items-center justify-between muted text-xs mb-1.5">
            <span className="font-medium secondary">{chunk.source}</span>
            <span>
              {chunk.rerank_score !== null && chunk.rerank_score !== undefined
                ? `rerank ${chunk.rerank_score.toFixed(3)}`
                : chunk.fused_score !== null && chunk.fused_score !== undefined
                  ? `fused ${chunk.fused_score.toFixed(4)}`
                  : chunk.score !== null && chunk.score !== undefined
                    ? `score ${chunk.score.toFixed(3)}`
                    : ""}
            </span>
          </div>
          {chunk.text}
        </div>
      ))}
    </div>
  );
}
