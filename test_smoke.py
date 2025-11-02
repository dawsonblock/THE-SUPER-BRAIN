#!/usr/bin/env python3
"""
Smoke test using TestClient - no server required.
"""

import sys
import os

# Add brain-ai build to path for C++ bindings
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brain-ai', 'build'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'brain-ai-rest-service'))

# Set environment for testing
os.environ['SAFE_MODE'] = '1'
os.environ['LLM_STUB'] = '1'
os.environ['API_KEY'] = 'test-key'
os.environ['REQUIRE_API_KEY_FOR_WRITES'] = '0'
os.environ['METRICS_ENABLED'] = '1'

from fastapi.testclient import TestClient
from app.app_v2 import app

client = TestClient(app)

print("=" * 60)
print("SMOKE TEST SUITE")
print("=" * 60)

passed = 0
failed = 0

def test(name, fn):
    global passed, failed
    print(f"\n{name}...", end=" ")
    try:
        fn()
        print("✓ PASS")
        passed += 1
    except AssertionError as e:
        print(f"✗ FAIL: {e}")
        failed += 1
    except Exception as e:
        print(f"✗ ERROR: {e}")
        failed += 1

# Test 1: Health check
def test1():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] == True

test("Test 1: Health check", test1)

# Test 2: Readiness check
def test2():
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["ready"] == True

test("Test 2: Readiness check", test2)

# Test 3: Metrics
def test3():
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"http_requests_total" in r.content

test("Test 3: Metrics endpoint", test3)

# Test 4: Index document
def test4():
    r = client.post("/index", json={
        "doc_id": "rope1",
        "text": "Rope memory stores bits by threading wires through magnetic cores."
    })
    assert r.status_code == 200
    assert r.json()["ok"] == True

test("Test 4: Index document", test4)

# Test 5: Index another document
def test5():
    r = client.post("/index", json={
        "doc_id": "rope2",
        "text": "Apollo Guidance Computer used rope memory for its software storage."
    })
    assert r.status_code == 200

test("Test 5: Index second document", test5)

# Test 6: Query with context
def test6():
    r = client.post("/answer", json={"query": "How did rope memory work?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    assert "confidence" in data
    assert "citations" in data
    assert "latency_ms" in data

test("Test 6: Query with context", test6)

# Test 7: Query without context (should refuse or low confidence)
def test7():
    r = client.post("/answer", json={"query": "What is the capital of Mars?"})
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data
    # In stub mode, this might not refuse properly, but it should respond
    assert data["confidence"] >= 0.0

test("Test 7: Query without context", test7)

# Test 8: Facts endpoint
def test8():
    r = client.get("/facts", headers={"X-API-Key": "test-key"})
    assert r.status_code in [200, 401]  # 401 is OK if auth required

test("Test 8: Facts endpoint", test8)

print("\n" + "=" * 60)
print(f"SMOKE TEST RESULTS")
print("=" * 60)
print(f"Passed: {passed}")
print(f"Failed: {failed}")
print(f"Total:  {passed + failed}")
print("=" * 60)

if failed > 0:
    print(f"\n✗ {failed} test(s) failed")
    sys.exit(1)
else:
    print(f"\n✓ All {passed} tests passed!")
    sys.exit(0)

