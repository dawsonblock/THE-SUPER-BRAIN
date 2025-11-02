"""
Upgraded FastAPI application with RAG++ features:
- Real C++ core via pybind11
- Multi-agent correction
- Evidence gating
- Reranking
- Facts store
- Comprehensive metrics
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware

from .agents import multi_agent_query
from .config import settings
from .core_bridge import bridge
from .embeddings import embed_text
from .facts_store import get_facts_store
from .logging_utils import configure_logging
from .metrics import (
    ERROR_COUNT,
    HTTP_REQUESTS,
    INDEXED_DOCUMENTS,
    INDEX_SIZE,
    QUERY_LATENCY,
    REQUEST_LATENCY,
    collect_metrics,
)
from .prompts import apply_evidence_gate, enforce_json, make_messages
from .rate_limiter import RateLimiter
from .reranker import cross_encode_rerank, ensure_chunk_format
from .schemas import AnswerResponse, IndexPayload, QueryPayload
from .verification import verify_answer

LOGGER = logging.getLogger(__name__)

app = FastAPI(
    title="Brain-AI RAG++ REST API",
    version="3.0.0",
    description="Production RAG system with multi-agent correction and evidence gating",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

rate_limiter = RateLimiter(settings.rate_limit_rpm)

# Metrics counters
REFUSAL_COUNT = ERROR_COUNT.labels(component="refusal")
RERANK_LATENCY = QUERY_LATENCY.labels(stage="rerank")
FACTS_HITS = ERROR_COUNT.labels(component="facts_hit")


def _client_ip(request: Request) -> str:
    """Extract client IP from request."""
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _require_api_key(request: Request) -> None:
    """Validate API key if required."""
    import secrets
    
    if not settings.require_api_key_for_writes:
        return
    
    expected = settings.api_key
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured",
        )
    
    candidate = request.headers.get("X-API-Key")
    if not candidate:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            candidate = auth[7:]
    
    if not candidate:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing API key")
    
    if not secrets.compare_digest(candidate, expected):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Invalid API key")


def _check_kill_switch() -> None:
    """Check if kill switch is engaged."""
    if Path(settings.kill_switch_path).exists():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Kill switch engaged")


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize application on startup."""
    configure_logging()
    LOGGER.info(
        "Brain-AI RAG++ starting: safe_mode=%s, pybind=%s, multi_agent=%s",
        settings.safe_mode,
        bridge.available,
        os.getenv("MULTI_AGENT_ENABLED", "true"),
    )
    Path(settings.kill_switch_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Initialize facts store
    facts = get_facts_store()
    stats = facts.get_stats()
    LOGGER.info("Facts store loaded: %d facts, avg_confidence=%.3f",
               stats.get("total_facts", 0), stats.get("avg_confidence", 0.0))


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    """Observability and security middleware."""
    route = request.url.path
    start = time.perf_counter()
    client = _client_ip(request)
    
    status_code = status.HTTP_200_OK
    try:
        rate_limiter.check(client)
        _check_kill_switch()
        
        if request.method in {"POST", "PUT", "PATCH"}:
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > settings.max_doc_bytes:
                raise HTTPException(
                    status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    "Payload too large",
                )
        
        response = await call_next(request)
        status_code = response.status_code
        return response
    except HTTPException as exc:
        status_code = exc.status_code
        raise
    except Exception as exc:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        ERROR_COUNT.labels(component="server").inc()
        LOGGER.exception("Unhandled error")
        raise
    finally:
        duration = time.perf_counter() - start
        HTTP_REQUESTS.labels(route=route, status=str(status_code)).inc()
        REQUEST_LATENCY.labels(route=route).observe(duration)
        LOGGER.info(
            "request complete",
            extra={
                "route": route,
                "lat_ms": int(duration * 1000),
                "status_code": status_code,
                "client_ip": client,
            },
        )


@app.get("/healthz")
async def healthz() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "ok": True,
        "version": "3.0.0",
        "pybind_available": bridge.available,
        "documents": bridge.size(),
        "facts": get_facts_store().get_stats(),
    }


@app.get("/readyz")
async def readyz() -> Dict[str, Any]:
    """Readiness check endpoint."""
    _check_kill_switch()
    return {
        "ready": True,
        "requires_api_key": settings.require_api_key_for_writes,
    }


@app.get("/metrics")
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    if not settings.metrics_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Metrics disabled")
    payload = collect_metrics()
    return Response(payload, media_type="text/plain; version=0.0.4")


@app.post("/index")
async def index_document(payload: IndexPayload, request: Request) -> Dict[str, bool]:
    """
    Index a document in the vector store.
    
    Requires API key if REQUIRE_API_KEY_FOR_WRITES is enabled.
    """
    _require_api_key(request)
    start = time.perf_counter()
    
    # Generate embedding
    embedding = embed_text(payload.text)
    
    # Index in C++ core
    bridge.index_document(payload.doc_id, payload.text, embedding)
    
    # Update metrics
    INDEXED_DOCUMENTS.inc()
    INDEX_SIZE.set(bridge.size())
    
    # Save snapshot (best-effort)
    try:
        bridge.save_index(settings.index_snapshot_path)
    except Exception as exc:
        LOGGER.warning("Index snapshot save failed: %s", exc)
    
    duration_ms = int((time.perf_counter() - start) * 1000)
    LOGGER.info(
        "indexed document",
        extra={
            "route": "/index",
            "lat_ms": duration_ms,
            "doc_id": payload.doc_id,
        },
    )
    
    return {"ok": True}


@app.post("/answer", response_model=AnswerResponse)
async def answer_query(payload: QueryPayload, request: Request) -> Dict[str, Any]:
    """
    Answer a query using RAG++ pipeline:
    1. Check facts store for cached answer
    2. Retrieve candidates from vector store
    3. Rerank with cross-encoder
    4. Multi-agent correction (generate multiple candidates)
    5. Judge best candidate
    6. Evidence gating (refuse if confidence < tau)
    7. Verification (optional, for math/code tasks)
    8. Promote to facts store if high quality
    """
    start = time.perf_counter()
    query = payload.query
    
    # Get evidence threshold
    tau = float(os.getenv("EVIDENCE_TAU", "0.70"))
    
    # Step 1: Check facts store
    facts = get_facts_store()
    cached = facts.lookup(query)
    if cached:
        FACTS_HITS.inc()
        cached["latency_ms"] = int((time.perf_counter() - start) * 1000)
        LOGGER.info("Returning cached answer from facts store")
        return cached
    
    # Step 2: Retrieve from vector store
    embedding = embed_text(query)
    top_k_retrieval = int(os.getenv("TOP_K_RETRIEVAL", "50"))
    raw_hits = bridge.search(query, top_k_retrieval, embedding)
    
    # Enrich with text
    enriched_hits: List[Dict[str, Any]] = []
    for doc_id, score in raw_hits:
        text = bridge.document_text(doc_id) or "(text unavailable)"
        enriched_hits.append({
            "id": doc_id,
            "doc_id": doc_id,
            "text": text,
            "content": text,
            "score": score,
        })
    
    if not enriched_hits:
        REFUSAL_COUNT.inc()
        return {
            "answer": "No relevant context found.",
            "citations": [],
            "confidence": 0.0,
            "latency_ms": int((time.perf_counter() - start) * 1000),
        }
    
    # Step 3: Rerank with cross-encoder
    rerank_start = time.perf_counter()
    top_k_final = int(os.getenv("TOP_K_FINAL", "10"))
    reranked = cross_encode_rerank(query, enriched_hits, top_k=top_k_final)
    reranked = ensure_chunk_format(reranked)
    RERANK_LATENCY.observe(time.perf_counter() - rerank_start)
    
    # Step 4-5: Multi-agent correction (solve + judge)
    n_solvers = int(os.getenv("N_SOLVERS", "3"))
    result = multi_agent_query(
        query=query,
        ctx=reranked,
        tau=tau,
        n_solvers=n_solvers,
    )
    
    # Step 6: Evidence gating (already applied in judge, but double-check)
    result = apply_evidence_gate(result, tau)
    
    # Step 7: Verification (optional)
    if os.getenv("ENABLE_VERIFICATION", "false").lower() == "true":
        verification = verify_answer(result["answer"], query)
        result["verification"] = verification
    
    # Step 8: Promote to facts store if high quality
    if result.get("confidence", 0.0) >= 0.85 and len(result.get("citations", [])) >= 2:
        facts.upsert(
            question=query,
            answer=result["answer"],
            citations=result["citations"],
            confidence=result["confidence"],
        )
    
    # Track refusals
    if result["answer"].startswith("Insufficient evidence"):
        REFUSAL_COUNT.inc()
    
    # Add latency
    result["latency_ms"] = int((time.perf_counter() - start) * 1000)
    
    QUERY_LATENCY.labels(stage="total").observe(time.perf_counter() - start)
    
    return result


@app.get("/facts")
async def list_facts(request: Request, limit: int = 100) -> Dict[str, Any]:
    """List facts from the canonical store."""
    _require_api_key(request)
    facts = get_facts_store()
    facts_list = facts.list_facts(limit=limit)
    return {
        "facts": facts_list,
        "count": len(facts_list),
        "stats": facts.get_stats(),
    }


@app.post("/admin/kill")
async def trigger_kill_switch(request: Request) -> Dict[str, object]:
    """Engage kill switch to stop serving requests."""
    _require_api_key(request)
    Path(settings.kill_switch_path).touch()
    return {"ok": True, "path": settings.kill_switch_path}


@app.delete("/admin/kill")
async def clear_kill_switch(request: Request) -> Dict[str, object]:
    """Disengage kill switch."""
    _require_api_key(request)
    try:
        os.remove(settings.kill_switch_path)
    except FileNotFoundError:
        pass
    return {"ok": True}


def create_app() -> FastAPI:
    """Factory function for creating the app."""
    return app


__all__ = ["app", "create_app"]

