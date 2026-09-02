export interface SourceChunk {
  source: string;
  text: string;
  score?: number | null;
  fused_score?: number | null;
  rerank_score?: number | null;
}

export interface QueryLog {
  id: number;
  run_id: number | null;
  query: string;
  answer: string;
  retrieved_sources: string[];
  retrieved_chunks: SourceChunk[];
  precision: number | null;
  recall: number | null;
  mrr: number | null;
  faithfulness: number | null;
  hallucinated: boolean | null;
  unsupported_claims: string[];
  relevance: number | null;
  latency_ms: number | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  cost_usd: number | null;
  created_at: string;
}

export interface EvalRun {
  id: number;
  name: string;
  config_name: string;
  use_hybrid: boolean;
  use_reranker: boolean;
  created_at: string;
  num_queries: number;
  avg_precision: number | null;
  avg_recall: number | null;
  avg_mrr: number | null;
  avg_faithfulness: number | null;
  hallucination_rate: number | null;
  avg_relevance: number | null;
  avg_latency_ms: number | null;
  total_cost_usd: number | null;
}

export interface EvalRunDetail extends EvalRun {
  logs: QueryLog[];
}

export interface QueryMetricsOut {
  faithfulness: number | null;
  hallucinated: boolean | null;
  unsupported_claims: string[];
  relevance: number | null;
  latency_ms: number | null;
  prompt_tokens: number | null;
  completion_tokens: number | null;
  cost_usd: number | null;
}

export interface QueryResponse {
  answer: string;
  sources: SourceChunk[];
  metrics: QueryMetricsOut;
}

export interface QueryRequest {
  query: string;
  top_k?: number | null;
  use_hybrid?: boolean | null;
  use_reranker?: boolean | null;
  evaluate?: boolean;
}
