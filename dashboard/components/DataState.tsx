export function DataState({
  loading,
  error,
  empty,
  children,
}: {
  loading: boolean;
  error: string | null;
  empty?: boolean;
  children: React.ReactNode;
}) {
  if (loading) {
    return <div className="muted text-sm py-12 text-center">Loading…</div>;
  }
  if (error) {
    return (
      <div className="card p-4 text-sm" style={{ color: "var(--status-critical)" }}>
        Could not reach the API at {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}.
        <div className="muted mt-1">{error}</div>
      </div>
    );
  }
  if (empty) {
    return (
      <div className="muted text-sm py-12 text-center">
        No data yet — run some queries or an eval run to see results here.
      </div>
    );
  }
  return <>{children}</>;
}
