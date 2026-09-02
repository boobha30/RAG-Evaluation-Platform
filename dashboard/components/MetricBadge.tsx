import clsx from "clsx";

/** Status colors are reserved for state — never reused as a categorical series color. */
export function MetricBadge({
  label,
  tone,
}: {
  label: string;
  tone: "good" | "warning" | "critical" | "neutral";
}) {
  const color = {
    good: "var(--status-good)",
    warning: "var(--status-warning)",
    critical: "var(--status-critical)",
    neutral: "var(--text-muted)",
  }[tone];

  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium"
      )}
      style={{ border: `1px solid ${color}`, color }}
    >
      <span
        className="inline-block w-1.5 h-1.5 rounded-full"
        style={{ background: color }}
      />
      {label}
    </span>
  );
}

export function faithfulnessTone(v: number | null): "good" | "warning" | "critical" | "neutral" {
  if (v === null) return "neutral";
  if (v >= 0.8) return "good";
  if (v >= 0.5) return "warning";
  return "critical";
}
