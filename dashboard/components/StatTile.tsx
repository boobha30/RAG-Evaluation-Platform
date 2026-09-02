export function StatTile({
  label,
  value,
  sub,
}: {
  label: string;
  value: string;
  sub?: string;
}) {
  return (
    <div className="card p-4">
      <div className="muted text-xs uppercase tracking-wide">{label}</div>
      <div
        className="text-2xl mt-1"
        style={{ fontVariantNumeric: "proportional-nums" }}
      >
        {value}
      </div>
      {sub && <div className="secondary text-xs mt-1">{sub}</div>}
    </div>
  );
}

export function fmtPct(v: number | null | undefined): string {
  return v === null || v === undefined ? "—" : `${(v * 100).toFixed(0)}%`;
}

export function fmtNum(v: number | null | undefined, digits = 2): string {
  return v === null || v === undefined ? "—" : v.toFixed(digits);
}

export function fmtMs(v: number | null | undefined): string {
  return v === null || v === undefined ? "—" : `${Math.round(v)} ms`;
}

export function fmtUsd(v: number | null | undefined): string {
  return v === null || v === undefined ? "—" : `$${v.toFixed(4)}`;
}
