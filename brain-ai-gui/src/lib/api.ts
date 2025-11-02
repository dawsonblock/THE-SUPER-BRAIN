import axios from 'axios';
import type {
  QueryRequest,
  QueryResponse,
  IndexRequest,
  IndexResponse,
  HealthResponse,
  Fact,
} from '@/types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add API key from localStorage if available
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('brain_ai_api_key');
  if (apiKey) {
    config.headers['X-API-Key'] = apiKey;
  }
  return config;
});

export const apiClient = {
  // Health & Status
  async getHealth(): Promise<HealthResponse> {
    const { data } = await api.get<HealthResponse>('/healthz');
    return data;
  },

  async getReadiness(): Promise<{ ready: boolean }> {
    const { data } = await api.get<{ ready: boolean }>('/readyz');
    return data;
  },

  async getMetrics(): Promise<string> {
    const { data } = await api.get<string>('/metrics');
    return data;
  },

  // Query & Answer
  async query(request: QueryRequest): Promise<QueryResponse> {
    const { data } = await api.post<QueryResponse>('/answer', request);
    return data;
  },

  // Document Indexing
  async indexDocument(request: IndexRequest): Promise<IndexResponse> {
    const { data } = await api.post<IndexResponse>('/index', request);
    return data;
  },

  // Facts Store
  async getFacts(): Promise<Fact[]> {
    const { data } = await api.get<{ facts: Fact[] }>('/facts');
    return data.facts || [];
  },

  async getFactsStats(): Promise<{
    count: number;
    avg_confidence: number;
    total_accesses: number;
  }> {
    const { data } = await api.get<{
      count: number;
      avg_confidence: number;
      total_accesses: number;
    }>('/facts/stats');
    return data;
  },

  // Admin
  async triggerKillSwitch(): Promise<{ ok: boolean }> {
    const { data } = await api.post<{ ok: boolean }>('/admin/kill');
    return data;
  },

  async clearCache(): Promise<{ ok: boolean }> {
    const { data } = await api.post<{ ok: boolean }>('/admin/clear-cache');
    return data;
  },
};

export default apiClient;

