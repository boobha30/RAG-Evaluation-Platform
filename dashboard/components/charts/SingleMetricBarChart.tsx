"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function SingleMetricBarChart({
  data,
  valueFormatter,
}: {
  data: { name: string; value: number }[];
  valueFormatter: (v: number) => string;
}) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} barCategoryGap="30%">
        <CartesianGrid vertical={false} stroke="var(--gridline)" />
        <XAxis
          dataKey="name"
          tick={{ fill: "var(--text-muted)", fontSize: 12 }}
          axisLine={{ stroke: "var(--baseline)" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "var(--text-muted)", fontSize: 12 }}
          axisLine={false}
          tickLine={false}
          width={44}
        />
        <Tooltip
          contentStyle={{
            background: "var(--surface)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            fontSize: 12,
            color: "var(--text-primary)",
          }}
          formatter={(value) => (typeof value === "number" ? valueFormatter(value) : value)}
        />
        <Bar dataKey="value" fill="var(--series-blue)" radius={[4, 4, 0, 0]} maxBarSize={36} />
      </BarChart>
    </ResponsiveContainer>
  );
}
