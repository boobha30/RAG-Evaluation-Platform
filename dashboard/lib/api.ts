import type { EvalRun, EvalRunDetail, QueryLog, QueryRequest, QueryResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function apiFetch<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`${path} -> ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export async function postQuery(request: QueryRequest): Promise<QueryResponse> {
  const res = await fetch(`${API_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(request),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || `/query -> ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export function fetchLogs(limit = 50): Promise<QueryLog[]> {
  return apiFetch(`/logs?limit=${limit}`);
}

export function fetchLog(id: number): Promise<QueryLog> {
  return apiFetch(`/logs/${id}`);
}

export function fetchEvalRuns(): Promise<EvalRun[]> {
  return apiFetch(`/eval/runs`);
}

export function fetchEvalRun(id: number): Promise<EvalRunDetail> {
  return apiFetch(`/eval/runs/${id}`);
}

export { API_URL };
