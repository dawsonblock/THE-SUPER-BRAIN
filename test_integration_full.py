#!/usr/bin/env python3
"""
Full integration test for all new additions.
"""

import sys
import os

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brain-ai', 'build'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brain-ai-rest-service'))

# Set environment
os.environ['SAFE_MODE'] = '1'
os.environ['LLM_STUB'] = '1'
os.environ['API_KEY'] = 'test-key'
os.environ['REQUIRE_API_KEY_FOR_WRITES'] = '0'

from fastapi.testclient import TestClient
from app.app_v2 import app

client = TestClient(app)

print("=" * 60)
print("COMPREHENSIVE INTEGRATION TEST")
print("=" * 60)

test_results = []

def test(name, fn):
    global test_results
    try:
        fn()
        test_results.append((name, True, None))
        print(f"✓ {name}")
    except AssertionError as e:
        test_results.append((name, False, str(e)))
        print(f"✗ {name}: {e}")
    except Exception as e:
        test_results.append((name, False, f"Error: {e}"))
        print(f"✗ {name}: {e}")

print("\nRunning tests...")
print("-" * 60)

# Test 1: Health checks
def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] == True

test("Health check", test_health)

def test_ready():
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["ready"] == True

test("Readiness check", test_ready)

# Test 2: Document indexing
def test_index1():
    r = client.post("/index", json={
        "doc_id": "int_test_1",
        "text": "Rope memory stores bits by threading wires through magnetic cores."
    })
    assert r.status_code == 200
    assert r.json()["ok"] == True

test("Index document 1", test_index1)

def test_index2():
    r = client.post("/index", json={
        "doc_id": "int_test_2",
        "text": "Apollo Guidance Computer used rope memory for software storage."
    })
    assert r.status_code == 200

test("Index document 2", test_index2)

# Test 3: Query answering
def test_query():
    r = client.post("/answer", json={"query": "How did rope memory work?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "confidence" in data
    assert "latency_ms" in data
    assert "citations" in data
    assert data["confidence"] >= 0.0

test("Query with context", test_query)

# Test 4: Refusal handling
def test_refusal():
    r = client.post("/answer", json={
        "query": "What is the capital of the imaginary country XYZABC?"
    })
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data

test("Query without context", test_refusal)

# Test 5: Metrics
def test_metrics():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"http_requests_total" in r.content

test("Metrics endpoint", test_metrics)

# Test 6: Facts endpoint
def test_facts():
    r = client.get("/facts", headers={"X-API-Key": "test-key"})
    assert r.status_code in [200, 401]

test("Facts endpoint", test_facts)

# Summary
print("\n" + "=" * 60)
print("TEST SUMMARY")
print("=" * 60)

passed = sum(1 for _, result, _ in test_results if result)
failed = sum(1 for _, result, _ in test_results if not result)
total = len(test_results)

print(f"Total: {total}")
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Pass rate: {(passed/total*100):.1f}%")

if failed > 0:
    print("\nFailed tests:")
    for name, result, error in test_results:
        if not result:
            print(f"  - {name}: {error}")

print("\n" + "=" * 60)
if failed == 0:
    print("✅ ALL INTEGRATION TESTS PASSED")
    print("=" * 60)
    sys.exit(0)
else:
    print(f"⚠ {failed} TEST(S) FAILED")
    print("=" * 60)
    sys.exit(1)

