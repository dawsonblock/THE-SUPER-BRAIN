"""
Smoke test using TestClient — no server required.
Canonical runtime: app.app_v2
"""

import os
import sys
from pathlib import Path

# Ensure brain-ai-rest-service is importable from repo root
_service_root = Path(__file__).resolve().parent / "brain-ai-rest-service"
if str(_service_root) not in sys.path:
    sys.path.insert(0, str(_service_root))

os.environ.setdefault("SAFE_MODE", "1")
os.environ.setdefault("LLM_STUB", "1")
os.environ.setdefault("EMBEDDINGS_BACKEND", "cpu")
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("REQUIRE_API_KEY_FOR_WRITES", "0")
os.environ.setdefault("METRICS_ENABLED", "1")

from fastapi.testclient import TestClient
from app.app_v2 import app

client = TestClient(app)


def test_health_check():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_readiness_check():
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["ready"] is True


def test_metrics():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"http_requests_total" in r.content


def test_index_document():
    r = client.post("/index", json={
        "doc_id": "rope1",
        "text": "Rope memory stores bits by threading wires through magnetic cores."
    }, headers={"X-API-Key": "test-key"})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_index_second_document():
    r = client.post("/index", json={
        "doc_id": "rope2",
        "text": "Apollo Guidance Computer used rope memory for its software storage."
    }, headers={"X-API-Key": "test-key"})
    assert r.status_code == 200


def test_query_with_context():
    r = client.post("/answer", json={"query": "How did rope memory work?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "confidence" in data
    assert "citations" in data
    assert "latency_ms" in data


def test_query_without_context():
    r = client.post("/answer", json={"query": "What is the capital of Mars?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert data["confidence"] >= 0.0


def test_facts_endpoint():
    r = client.get("/facts", headers={"X-API-Key": "test-key"})
    assert r.status_code in [200, 401]


def test_facts_stats():
    r = client.get("/facts/stats")
    assert r.status_code == 200
    data = r.json()
    assert "count" in data
    assert "avg_confidence" in data
    assert "total_accesses" in data

