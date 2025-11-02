"""Prometheus metrics definitions with bounded label cardinality."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, CollectorRegistry, generate_latest


REGISTRY = CollectorRegistry()

# HTTP surface metrics
HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=("route", "status"),
    registry=REGISTRY,
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Latency per HTTP route",
    labelnames=("route",),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

# Domain metrics
INDEXED_DOCUMENTS = Counter(
    "index_docs_total",
    "Number of documents indexed",
    registry=REGISTRY,
)

QUERY_LATENCY = Histogram(
    "query_latency_seconds",
    "Latency of query operations by stage",
    labelnames=("stage",),
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0),
    registry=REGISTRY,
)

# RAG++ specific metrics
RERANK_LATENCY = Histogram(
    "rerank_latency_seconds",
    "Cross-encoder reranking latency",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5),
    registry=REGISTRY,
)

DEEPSEEK_CALLS = Counter(
    "deepseek_calls_total",
    "DeepSeek API calls",
    labelnames=("model", "status"),
    registry=REGISTRY,
)

DEEPSEEK_LATENCY = Histogram(
    "deepseek_latency_seconds",
    "DeepSeek API call latency",
    labelnames=("model",),
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 30.0),
    registry=REGISTRY,
)

REFUSAL_COUNT = Counter(
    "refusals_total",
    "Number of times system refused to answer due to insufficient evidence",
    registry=REGISTRY,
)

FACTS_HITS = Counter(
    "facts_cache_hits_total",
    "Number of answers served from facts store cache",
    registry=REGISTRY,
)

FACTS_SIZE = Gauge(
    "facts_store_size",
    "Number of facts in canonical store",
    registry=REGISTRY,
)

MULTI_AGENT_CANDIDATES = Histogram(
    "multi_agent_candidates",
    "Number of candidate answers generated",
    buckets=(1, 2, 3, 4, 5, 6, 8, 10),
    registry=REGISTRY,
)

ANSWER_CONFIDENCE = Histogram(
    "answer_confidence",
    "Distribution of answer confidence scores",
    buckets=(0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 1.0),
    registry=REGISTRY,
)

OCR_CALLS = Counter(
    "ocr_calls_total",
    "OCR requests made",
    registry=REGISTRY,
)

ERROR_COUNT = Counter(
    "errors_total",
    "Count of errors by component",
    labelnames=("component",),
    registry=REGISTRY,
)

INDEX_SIZE = Gauge(
    "index_size_total",
    "Documents stored in index",
    registry=REGISTRY,
)


def collect_metrics() -> bytes:
    """Render metrics in Prometheus exposition format."""
    return generate_latest(REGISTRY)


__all__ = [
    "HTTP_REQUESTS",
    "REQUEST_LATENCY",
    "INDEXED_DOCUMENTS",
    "QUERY_LATENCY",
    "RERANK_LATENCY",
    "DEEPSEEK_CALLS",
    "DEEPSEEK_LATENCY",
    "REFUSAL_COUNT",
    "FACTS_HITS",
    "FACTS_SIZE",
    "MULTI_AGENT_CANDIDATES",
    "ANSWER_CONFIDENCE",
    "OCR_CALLS",
    "ERROR_COUNT",
    "INDEX_SIZE",
    "collect_metrics",
    "REGISTRY",
]
