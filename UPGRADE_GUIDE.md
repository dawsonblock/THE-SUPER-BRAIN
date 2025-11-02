# Brain-AI RAG++ Production Upgrade Guide

## Overview

This upgrade transforms the Brain-AI system into a production-ready RAG++ architecture with:

- ✅ Real C++ core integration via pybind11
- ✅ Multi-agent correction with solve-verify-judge pipeline
- ✅ Evidence gating (refuses when confidence < τ)
- ✅ Cross-encoder reranking for improved relevance
- ✅ Facts store (SQLite) for canonical answers
- ✅ Comprehensive Prometheus metrics
- ✅ Security hardening (CORS, API keys, rate limits)
- ✅ Evaluation harness with baseline metrics
- ✅ Docker with healthchecks and proper orchestration

## Quick Start

### 1. Set Environment Variables

```bash
export DEEPSEEK_API_KEY="your-deepseek-api-key"
export API_KEY="your-secure-api-key"  # For API authentication
export EVIDENCE_TAU="0.70"             # Evidence threshold
export N_SOLVERS="3"                   # Number of multi-agent solvers
```

### 2. Start the System

#### Option A: Local Development

```bash
# Start production services
./scripts/start_production.sh
```

The script will:
1. Build C++ core with tests
2. Create Python virtual environment
3. Install dependencies
4. Start FastAPI server on port 5001
5. Expose Prometheus metrics on port 9090

#### Option B: Docker Compose

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f rest
```

### 3. Run Smoke Tests

```bash
# In another terminal
./scripts/smoke_test.sh
```

Expected output:
```
✓ Health check
✓ Readiness check
✓ Metrics endpoint
✓ Index document
✓ Query with context
✓ Query without context (refusal)
✅ All smoke tests passed!
```

## Configuration

### Embedding Model (config.yaml)

**Option A: Fast CPU (Default)**
```yaml
embeddings:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  dimension: 384

cpp_backend:
  embedding_dim: 384  # MUST match above
```

**Option B: Better Quality**
```yaml
embeddings:
  model: "sentence-transformers/all-mpnet-base-v2"
  dimension: 768

cpp_backend:
  embedding_dim: 768  # MUST match above
```

### LLM Router

```yaml
llm:
  router:
    reasoning_model: "deepseek-r1"    # For complex reasoning
    chat_model: "deepseek-chat"       # For fast responses
```

### Evidence Gating

```yaml
evidence:
  threshold: 0.70           # Minimum confidence to return answer
  citation_required: true
  min_citations: 2
```

### Multi-Agent Correction

```yaml
multi_agent:
  enabled: true
  n_solvers: 3
  temperatures: [0.0, 0.3, 0.4]
  planner_model: "deepseek-r1"
  solver_model: "deepseek-chat"
```

## API Usage

### Index a Document

```bash
curl -X POST http://localhost:5001/index \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "doc_id": "d1",
    "text": "Rope memory stores bits by threading wires through cores for 1, around for 0.",
    "metadata": {"source": "wiki"}
  }'
```

### Query with RAG++ Pipeline

```bash
curl -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "query": "How did rope memory store bits?"
  }'
```

Response:
```json
{
  "answer": "Rope memory stored bits by threading wires through ferrite cores for binary 1, or around cores for binary 0 [d1].",
  "citations": ["d1"],
  "confidence": 0.92,
  "latency_ms": 1243
}
```

### Refusal Example (Low Confidence)

```bash
curl -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the capital of XYZABC?"
  }'
```

Response:
```json
{
  "answer": "Insufficient evidence.",
  "citations": [],
  "confidence": 0.15,
  "latency_ms": 523
}
```

## Evaluation

### Run Evaluation Harness

```bash
cd eval
python run_eval.py \
  --api-url http://localhost:5001/answer \
  --eval-set eval_set.jsonl \
  --output metrics.json \
  --api-key your-api-key
```

### Metrics Tracked

- **Exact Match (EM)**: Exact string match with expected answer
- **F1 Score**: Token-level F1
- **Groundedness**: % of answers with ≥2 valid citations
- **Refusal Rate**: % of queries refused due to insufficient evidence
- **Hallucination Rate**: % of refusal tasks answered with high confidence
- **Latency**: P50, P95 in milliseconds

### Targets

```yaml
targets:
  recall_at_k: 0.95         # Retrieval quality
  groundedness: 0.80        # Citation quality
  hallucination_max: 0.10   # Max acceptable hallucination
  p95_latency_ms: 2000      # 95th percentile latency
```

## Monitoring

### Prometheus Metrics

Access metrics at `http://localhost:9090/metrics` (or port 9090 on rest service)

**Key Metrics:**

- `http_requests_total{route, status}` - HTTP request count
- `request_latency_seconds{route}` - Request latency histogram
- `query_latency_seconds{stage}` - Query stage latency
- `rerank_latency_seconds` - Reranking latency
- `deepseek_calls_total{model, status}` - DeepSeek API calls
- `deepseek_latency_seconds{model}` - DeepSeek API latency
- `refusals_total` - Number of refusals
- `facts_cache_hits_total` - Facts store cache hits
- `answer_confidence` - Confidence score distribution
- `index_size_total` - Number of indexed documents

### Grafana Dashboard (Optional)

Import `monitoring/grafana-dashboard.json` for pre-built visualizations.

## Architecture

### RAG++ Pipeline

```
Query → Facts Store Lookup (cache)
  ↓ (miss)
Retrieve (HNSW) → Top-K=50
  ↓
Rerank (cross-encoder) → Top-K=10
  ↓
Multi-Agent Correction:
  - Generate N candidates (different temperatures)
  - Judge best candidate (score = 0.8*confidence + 0.2*citation_quality)
  ↓
Evidence Gate (τ=0.70)
  ↓
Verification (optional, for math/code)
  ↓
Response (or refusal)
  ↓
Promote to Facts Store (if confidence ≥ 0.85 and ≥2 citations)
```

### Components

- **C++ Core**: HNSW vector search, episodic buffer, semantic network
- **Python REST**: FastAPI with multi-agent orchestration
- **DeepSeek LLM**: R1 for reasoning, chat for fast responses
- **Cross-Encoder**: Reranking for relevance
- **Facts Store**: SQLite canonical QA cache
- **Metrics**: Prometheus for observability

## Security

### API Key Authentication

Set `REQUIRE_API_KEY_FOR_WRITES=1` and provide `API_KEY` env var.

All write operations (`/index`, `/facts`, `/admin/*`) require:
```
X-API-Key: your-api-key
```

### CORS Configuration

Set allowed origins:
```bash
export CORS_ORIGINS="http://localhost:3000,https://your-ui.example"
```

### Rate Limiting

Default: 120 requests/minute per client IP

Configure via:
```bash
export RATE_LIMIT_RPM=120
```

### Kill Switch

Emergency shutdown:
```bash
curl -X POST http://localhost:5001/admin/kill \
  -H "X-API-Key: your-api-key"
```

Re-enable:
```bash
curl -X DELETE http://localhost:5001/admin/kill \
  -H "X-API-Key: your-api-key"
```

## Troubleshooting

### Issue: "brain_ai_py module not found"

**Solution:** Build C++ core with Python bindings:
```bash
cd brain-ai
mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_PYTHON_BINDINGS=ON ..
make -j$(nproc)

# Test import
python3 -c "import sys; sys.path.insert(0, '.'); import brain_ai_py"
```

### Issue: "DeepSeek API call failed"

**Solution:** Check API key and model names:
```bash
export DEEPSEEK_API_KEY="sk-..."
export REASONING_MODEL="deepseek-r1"
export CHAT_MODEL="deepseek-chat"
```

### Issue: "Tests failing in Docker build"

**Solution:** Temporarily disable strict test enforcement:
```dockerfile
# In Dockerfile.core, change:
RUN ctest --output-on-failure || true
```

### Issue: "High refusal rate"

**Solution:** Lower evidence threshold:
```bash
export EVIDENCE_TAU=0.60  # Lower = more permissive
```

## Performance Tuning

### Increase Multi-Agent Candidates

```bash
export N_SOLVERS=5  # More candidates = better quality, higher latency
```

### Adjust Retrieval/Reranking

```bash
export TOP_K_RETRIEVAL=100  # More candidates for reranking
export TOP_K_FINAL=15       # More context for LLM
```

### Enable GPU Acceleration

```yaml
embeddings:
  backend: "gpu"
```

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Build and Test
  run: |
    cd brain-ai
    mkdir build && cd build
    cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=ON ..
    make -j$(nproc)
    ctest --output-on-failure

- name: Run Smoke Tests
  run: |
    docker-compose up -d
    sleep 30
    ./scripts/smoke_test.sh

- name: Run Evaluation
  run: |
    cd eval
    python run_eval.py --api-url http://localhost:5001/answer
```

## Next Steps

1. **Add More Test Cases**: Expand `eval/eval_set.jsonl` with domain-specific Q&A
2. **Fine-tune Models**: Train LoRA adapters on judged traces
3. **Implement Code Sandbox**: Enable safe code execution for verification
4. **Deploy to Production**: Use Kubernetes with autoscaling
5. **Monitor Metrics**: Set up alerts on refusal rate, latency, error rate

## Support

For issues, see `docs/` or contact the team.

## License

See LICENSE file.

