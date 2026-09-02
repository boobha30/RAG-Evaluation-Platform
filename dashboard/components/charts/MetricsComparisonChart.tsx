"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { EvalRun } from "@/lib/types";

const METRICS: { key: keyof EvalRun; label: string; color: string }[] = [
  { key: "avg_precision", label: "Precision@k", color: "var(--series-blue)" },
  { key: "avg_recall", label: "Recall@k", color: "var(--series-green)" },
  { key: "avg_mrr", label: "MRR", color: "var(--series-magenta)" },
  { key: "avg_faithfulness", label: "Faithfulness", color: "var(--series-yellow)" },
  { key: "avg_relevance", label: "Relevance", color: "var(--series-aqua)" },
];

export function MetricsComparisonChart({ runs }: { runs: EvalRun[] }) {
  const data = runs
    .slice()
    .reverse()
    .map((r) => ({
      name: r.name || r.config_name,
      Precision: r.avg_precision,
      Recall: r.avg_recall,
      MRR: r.avg_mrr,
      Faithfulness: r.avg_faithfulness,
      Relevance: r.avg_relevance,
    }));

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data} barGap={2} barCategoryGap="20%">
        <CartesianGrid vertical={false} stroke="var(--gridline)" />
        <XAxis
          dataKey="name"
          tick={{ fill: "var(--text-muted)", fontSize: 12 }}
          axisLine={{ stroke: "var(--baseline)" }}
          tickLine={false}
        />
        <YAxis
          domain={[0, 1]}
          tick={{ fill: "var(--text-muted)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={32}
        />
        <Tooltip
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--text-primary)",
          }}
          formatter={(value) => (typeof value === "number" ? value.toFixed(3) : value)}
        />
        <Legend wrapperStyle={{ fontSize: 12, color: "var(--text-secondary)" }} />
        {METRICS.map((m) => (
          <Bar
            key={m.label}
            dataKey={m.label}
            fill={m.color}
            radius={[4, 4, 0, 0]}
            maxBarSize={28}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
