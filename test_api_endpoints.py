"""
API endpoint tests using TestClient — no server required.
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
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("REQUIRE_API_KEY_FOR_WRITES", "0")
os.environ.setdefault("METRICS_ENABLED", "1")

from fastapi.testclient import TestClient
from app.app_v2 import app

client = TestClient(app)


def test_health_check():
    response = client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True


def test_readiness_check():
    response = client.get("/readyz")
    assert response.status_code == 200
    data = response.json()
    assert data["ready"] is True


def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"http_requests_total" in response.content


def test_index_document():
    response = client.post(
        "/index",
        json={
            "doc_id": "test1",
            "text": "The sky is blue because of Rayleigh scattering."
        }
    )
    assert response.status_code == 200, f"Index failed: {response.text}"
    assert response.json()["ok"] is True


def test_index_second_document():
    response = client.post(
        "/index",
        json={
            "doc_id": "test2",
            "text": "Water freezes at 0 degrees Celsius at standard pressure."
        }
    )
    assert response.status_code == 200


def test_answer_with_context():
    response = client.post("/answer", json={"query": "Why is the sky blue?"})
    assert response.status_code == 200, f"Query failed: {response.text}"
    data = response.json()
    assert "answer" in data
    assert "citations" in data
    assert "confidence" in data
    assert "latency_ms" in data


def test_answer_without_context():
    response = client.post(
        "/answer",
        json={"query": "What is the capital of the imaginary country XYZABC?"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["confidence"] >= 0.0


def test_facts_endpoint():
    response = client.get("/facts", headers={"X-API-Key": "test-key"})
    assert response.status_code in [200, 401]


def test_facts_stats():
    response = client.get("/facts/stats")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "avg_confidence" in data
    assert "total_accesses" in data

