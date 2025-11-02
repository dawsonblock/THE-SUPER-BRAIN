# Migration Guide: app.py → app_v2.py (RAG++ v3.0)

## Overview

The new `app_v2.py` includes all RAG++ features:
- Multi-agent correction
- Evidence gating
- Cross-encoder reranking
- Facts store caching
- Enhanced metrics

## Quick Migration

### Option 1: Switch Import (Recommended)

Update your startup command:

```bash
# Old
uvicorn app.app:app --host 0.0.0.0 --port 5001

# New (RAG++ v3.0)
uvicorn app.app_v2:app --host 0.0.0.0 --port 5001
```

Or use the provided startup script:
```bash
./scripts/start_production.sh
```

### Option 2: Symlink (Temporary)

For backward compatibility during testing:

```bash
cd brain-ai-rest-service/app
mv app.py app_legacy.py
ln -s app_v2.py app.py
```

## API Changes

### Breaking Changes

#### 1. `/query` endpoint removed

**Old**:
```bash
POST /query
{
  "query": "What is X?",
  "top_k": 5
}
```

**New**: Use `/answer` instead
```bash
POST /answer
{
  "query": "What is X?"
}
```

#### 2. Response format changed

**Old** (`/query`):
```json
{
  "answer": "The answer",
  "hits": [{"doc_id": "d1", "score": 0.9, "text": "..."}],
  "model": "deepseek-chat",
  "latency_ms": 500
}
```

**New** (`/answer`):
```json
{
  "answer": "The answer with citations [d1]",
  "citations": ["d1"],
  "confidence": 0.85,
  "latency_ms": 1234,
  "from_cache": false
}
```

### New Endpoints

#### 1. `/answer` - RAG++ Query (replaces `/query`)
```bash
POST /answer
Content-Type: application/json

{
  "query": "Your question?"
}
```

Response includes:
- `answer`: Answer text with inline citations
- `citations`: List of document IDs cited
- `confidence`: Confidence score [0.0, 1.0]
- `latency_ms`: End-to-end latency
- `from_cache`: Whether served from facts store

#### 2. `/facts` - List Canonical Facts
```bash
GET /facts?limit=100
X-API-Key: your-key
```

### Unchanged Endpoints

These endpoints work the same in both versions:

- ✅ `GET /healthz` - Health check
- ✅ `GET /readyz` - Readiness check
- ✅ `GET /metrics` - Prometheus metrics (enhanced in v2)
- ✅ `POST /index` - Index documents
- ✅ `POST /admin/kill` - Emergency shutdown
- ✅ `DELETE /admin/kill` - Re-enable

## Configuration Changes

### New Environment Variables

```bash
# Multi-agent correction
export N_SOLVERS=3
export MULTI_AGENT_ENABLED=true

# Evidence gating
export EVIDENCE_TAU=0.70

# Retrieval & reranking
export TOP_K_RETRIEVAL=50
export TOP_K_FINAL=10

# LLM models
export REASONING_MODEL=deepseek-r1
export SOLVER_MODEL=deepseek-chat

# Facts store
export FACTS_DB_PATH=./data/facts.db
```

### Unchanged Variables

These continue to work:
- `DEEPSEEK_API_KEY`
- `API_KEY`
- `SAFE_MODE`
- `LLM_STUB`
- `EMBEDDINGS_BACKEND`
- `RATE_LIMIT_RPM`
- All other existing variables

## Client Code Updates

### Python Client

**Before**:
```python
import requests

response = requests.post(
    "http://localhost:5001/query",
    json={"query": "What is X?", "top_k": 5}
)
data = response.json()
answer = data["answer"]
hits = data["hits"]
```

**After**:
```python
import requests

response = requests.post(
    "http://localhost:5001/answer",
    json={"query": "What is X?"}
)
data = response.json()
answer = data["answer"]
citations = data["citations"]
confidence = data["confidence"]

# Check if answer is a refusal
if answer.startswith("Insufficient evidence"):
    print(f"System refused to answer (confidence: {confidence})")
```

### JavaScript Client

**Before**:
```javascript
const response = await fetch('http://localhost:5001/query', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query: 'What is X?', top_k: 5})
});
const data = await response.json();
console.log(data.answer);
```

**After**:
```javascript
const response = await fetch('http://localhost:5001/answer', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({query: 'What is X?'})
});
const data = await response.json();
console.log(data.answer, 'Citations:', data.citations, 'Confidence:', data.confidence);
```

### cURL

**Before**:
```bash
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{"query":"What is X?","top_k":5}'
```

**After**:
```bash
curl -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"What is X?"}'
```

## Testing the Migration

### 1. Start with stub mode (safe testing)

```bash
export SAFE_MODE=1
export LLM_STUB=1
uvicorn app.app_v2:app --host 0.0.0.0 --port 5001
```

### 2. Run smoke tests

```bash
./scripts/smoke_test.sh
```

### 3. Compare responses

```bash
# Index test document
curl -X POST http://localhost:5001/index \
  -H "X-API-Key: devkey" \
  -H "Content-Type: application/json" \
  -d '{"doc_id":"test1","text":"The sky is blue because of Rayleigh scattering."}'

# Query
curl -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"Why is the sky blue?"}'
```

### 4. Enable production mode

```bash
export SAFE_MODE=0
export LLM_STUB=0
export DEEPSEEK_API_KEY="sk-..."
```

### 5. Run evaluation

```bash
cd eval
python run_eval.py --api-url http://localhost:5001/answer
```

## Rollback Plan

If you need to revert to the old version:

### Option 1: Change startup command
```bash
uvicorn app.app:app --host 0.0.0.0 --port 5001
```

### Option 2: Remove symlink
```bash
cd brain-ai-rest-service/app
rm app.py
mv app_legacy.py app.py
```

## Feature Comparison

| Feature | Old (app.py) | New (app_v2.py) |
|---------|--------------|-----------------|
| Vector retrieval | ✅ | ✅ |
| Embeddings | ✅ | ✅ |
| LLM integration | ✅ | ✅ Enhanced |
| **Multi-agent** | ❌ | ✅ NEW |
| **Evidence gating** | ❌ | ✅ NEW |
| **Reranking** | ❌ | ✅ NEW |
| **Facts store** | ❌ | ✅ NEW |
| **Citations** | ❌ | ✅ NEW |
| **Confidence scores** | ❌ | ✅ NEW |
| **Verification tools** | ❌ | ✅ NEW |
| Enhanced metrics | ❌ | ✅ NEW |
| CORS | ✅ | ✅ Enhanced |
| API keys | ✅ | ✅ |
| Rate limiting | ✅ | ✅ |

## Performance Impact

Expected changes in v2:

| Metric | Old | New | Notes |
|--------|-----|-----|-------|
| Latency (P50) | ~500ms | ~800ms | Multi-agent overhead |
| Latency (P95) | ~1000ms | ~1500ms | Worth it for quality |
| Throughput | ~100 qps | ~60 qps | Still plenty |
| Quality | Base | +15-20% | Better groundedness |
| Refusal rate | ~5% | ~15-25% | Safer, more honest |

## Troubleshooting

### Issue: "ImportError: cannot import name 'AnswerResponse'"

**Solution**: Update schemas.py (already done in upgrade)

### Issue: "ModuleNotFoundError: No module named 'agents'"

**Solution**: Ensure all new modules are in `app/` directory:
- `app/prompts.py`
- `app/reranker.py`
- `app/agents.py`
- `app/verification.py`
- `app/facts_store.py`

### Issue: High refusal rate in testing

**Solution**: Lower evidence threshold temporarily
```bash
export EVIDENCE_TAU=0.50
```

### Issue: Slow responses

**Solution**: Reduce multi-agent solvers
```bash
export N_SOLVERS=1
```

## Support

- Full documentation: `UPGRADE_GUIDE.md`
- Quick reference: `QUICK_REFERENCE_RAG_PLUS_PLUS.md`
- Implementation details: `IMPLEMENTATION_COMPLETE.md`

---

**Migration Checklist**:

- [ ] Read this migration guide
- [ ] Update startup command to use `app_v2`
- [ ] Set new environment variables
- [ ] Update client code to use `/answer` endpoint
- [ ] Update response parsing (add `citations`, `confidence`)
- [ ] Run smoke tests
- [ ] Run evaluation harness
- [ ] Monitor metrics for 24h
- [ ] Remove old `app.py` (optional)

---

**Version**: 3.0.0  
**Migration difficulty**: Low  
**Estimated time**: 30-60 minutes

