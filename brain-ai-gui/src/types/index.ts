export interface QueryRequest {
  query: string;
}

export interface QueryResponse {
  answer: string;
  citations: string[];
  confidence: number;
  latency_ms: number;
  from_cache?: boolean;
  verification?: {
    verified: boolean;
    details?: string;
  };
}

export interface IndexRequest {
  doc_id: string;
  text: string;
  metadata?: Record<string, unknown>;
}

export interface IndexResponse {
  ok: boolean;
  doc_id: string;
  chunks: number;
}

export interface HealthResponse {
  ok: boolean;
  version: string;
  pybind_available: boolean;
  documents: number;
  facts: {
    total_facts: number;
    avg_confidence: number;
    total_accesses: number;
  };
}

export interface Fact {
  question: string;
  answer: string;
  citations: string[];
  confidence: number;
  timestamp: number;
  from_cache?: boolean;
}

export interface SystemMetrics {
  query_count: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  refusal_count: number;
  refusal_rate: number;
  avg_confidence: number;
  cache_hits: number;
  cache_hit_rate: number;
}

export type QueryMode = 'fast' | 'balanced' | 'accuracy';

export interface Config {
  mode: QueryMode;
  evidence_threshold: number;
  n_solvers: number;
  top_k_retrieval: number;
}

export interface AgentOutput {
  solver_id: number;
  answer: string;
  citations: string[];
  confidence: number;
  temperature: number;
}

export interface MultiAgentResponse extends QueryResponse {
  agents?: AgentOutput[];
  selected_agent?: number;
}

