import os
import sys
from importlib import reload
from pathlib import Path

# Ensure brain-ai-rest-service is on the path when tests are run from repo root
_SERVICE_ROOT = Path(__file__).resolve().parent.parent
if str(_SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(_SERVICE_ROOT))

from fastapi.testclient import TestClient


def build_client(tmp_path: Path) -> TestClient:
    os.environ["SAFE_MODE"] = "1"
    os.environ["LLM_STUB"] = "1"
    os.environ["EMBEDDINGS_BACKEND"] = "cpu"
    os.environ["API_KEY"] = "test-key"
    os.environ["REQUIRE_API_KEY_FOR_WRITES"] = "1"
    os.environ["INDEX_SNAPSHOT"] = str(tmp_path / "index.json")
    os.environ["KILL_PATH"] = str(tmp_path / "switch")

    # Import canonical runtime (app.app is a shim that forwards here)
    import app.app_v2 as app_module

    reload(app_module)
    return TestClient(app_module.app)


def test_health_ready(tmp_path):
    client = build_client(tmp_path)
    assert client.get("/healthz").status_code == 200
    assert client.get("/readyz").status_code == 200


def test_index_requires_api_key(tmp_path):
    client = build_client(tmp_path)
    payload = {"doc_id": "doc-1", "text": "Example offline document."}
    response = client.post("/index", json=payload)
    assert response.status_code == 401

    response = client.post("/index", json=payload, headers={"X-API-Key": "test-key"})
    assert response.status_code == 200


def test_kill_switch_returns_503(tmp_path):
    client = build_client(tmp_path)
    switch_path = Path(os.environ["KILL_PATH"])
    switch_path.touch()

    # Middleware returns a real 503 JSON response
    response = client.get("/readyz")
    assert response.status_code == 503
    body = response.json()
    assert body.get("status") == 503 or body.get("ready") is False or "detail" in body

    # Any request through the middleware also returns 503
    response = client.post("/answer", json={"query": "test"})
    assert response.status_code == 503

    switch_path.unlink()
    response = client.get("/readyz")
    assert response.status_code == 200
