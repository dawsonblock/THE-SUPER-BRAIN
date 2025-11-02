# Brain-AI RAG++ Quick Reference

## 🚀 Quick Start

```bash
# 1. Set API key
export DEEPSEEK_API_KEY="sk-..."
export API_KEY="your-secure-key"

# 2. Start system
./scripts/start_production.sh

# 3. Run smoke tests (in another terminal)
./scripts/smoke_test.sh
```

## 📝 Common Commands

### Index Documents
```bash
curl -X POST http://localhost:5001/index \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"doc_id":"d1","text":"Your document text here"}'
```

### Query (Answer)
```bash
curl -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{"query":"Your question?"}'
```

### Check Health
```bash
curl http://localhost:5001/healthz
```

### View Metrics
```bash
curl http://localhost:9090/metrics
```

### List Facts
```bash
curl http://localhost:5001/facts \
  -H "X-API-Key: $API_KEY"
```

## 🔧 Configuration

### Environment Variables (Most Important)

| Variable | Default | Description |
|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | *required* | DeepSeek API key |
| `EVIDENCE_TAU` | `0.70` | Confidence threshold |
| `N_SOLVERS` | `3` | Multi-agent solver count |
| `TOP_K_RETRIEVAL` | `50` | Initial retrieval count |
| `TOP_K_FINAL` | `10` | After reranking |
| `MULTI_AGENT_ENABLED` | `true` | Enable multi-agent |

### Config File (config.yaml)

```yaml
# Option A: Fast CPU
embeddings:
  model: "sentence-transformers/all-MiniLM-L6-v2"
  dimension: 384

cpp_backend:
  embedding_dim: 384  # MUST MATCH

# Option B: Better quality
embeddings:
  model: "sentence-transformers/all-mpnet-base-v2"
  dimension: 768

cpp_backend:
  embedding_dim: 768  # MUST MATCH
```

## 🔍 Monitoring

### Key Metrics

```bash
# Refusal rate
curl -s localhost:9090/metrics | grep refusals_total

# Facts cache hit rate
curl -s localhost:9090/metrics | grep facts_cache_hits

# Query latency P95
curl -s localhost:9090/metrics | grep query_latency_seconds

# DeepSeek API calls
curl -s localhost:9090/metrics | grep deepseek_calls_total
```

## 🧪 Testing

### Run Evaluation
```bash
cd eval
python run_eval.py \
  --api-url http://localhost:5001/answer \
  --api-key $API_KEY
```

### Smoke Tests
```bash
./scripts/smoke_test.sh
```

## 🐛 Troubleshooting

### Issue: Can't import brain_ai_py
```bash
cd brain-ai/build
python3 -c "import brain_ai_py"  # Should work
export PYTHONPATH="$(pwd):$PYTHONPATH"
```

### Issue: High refusal rate
```bash
export EVIDENCE_TAU=0.60  # Lower threshold
```

### Issue: Slow responses
```bash
export N_SOLVERS=1  # Reduce multi-agent
export TOP_K_RETRIEVAL=20  # Fewer candidates
```

### Issue: DeepSeek API errors
```bash
# Check API key
echo $DEEPSEEK_API_KEY

# Check rate limits
curl -s localhost:9090/metrics | grep deepseek_calls
```

## 🔒 Security

### Emergency Shutdown
```bash
curl -X POST http://localhost:5001/admin/kill \
  -H "X-API-Key: $API_KEY"
```

### Re-enable
```bash
curl -X DELETE http://localhost:5001/admin/kill \
  -H "X-API-Key: $API_KEY"
```

## 📊 Response Format

### Successful Answer
```json
{
  "answer": "The answer with citations [d1] [d3]",
  "citations": ["d1", "d3"],
  "confidence": 0.85,
  "latency_ms": 1234
}
```

### Refusal (Low Confidence)
```json
{
  "answer": "Insufficient evidence.",
  "citations": [],
  "confidence": 0.42,
  "latency_ms": 523
}
```

## 🏗️ Architecture Flow

```
Query
  → Facts Store (cache lookup)
  → HNSW Retrieval (top-50)
  → Cross-Encoder Rerank (top-10)
  → Multi-Agent (3 solvers)
  → Judge (best candidate)
  → Evidence Gate (τ=0.70)
  → Response (or refusal)
  → Promote to Facts Store (if confidence≥0.85)
```

## 📁 Important Files

| File | Purpose |
|------|---------|
| `config.yaml` | Main configuration |
| `env.example` | Environment template |
| `brain-ai-rest-service/app/app_v2.py` | REST API |
| `brain-ai-rest-service/app/agents.py` | Multi-agent logic |
| `brain-ai-rest-service/app/prompts.py` | Prompt engineering |
| `eval/run_eval.py` | Evaluation harness |
| `scripts/start_production.sh` | Startup |
| `scripts/smoke_test.sh` | Smoke tests |

## 🎯 KPIs

| Metric | Target | How to Check |
|--------|--------|--------------|
| Groundedness | ≥80% | Run eval harness |
| Hallucination | ≤10% | Run eval harness |
| P95 Latency | ≤2s | `curl metrics \| grep p95` |
| Cache Hit Rate | Growing | `grep facts_cache_hits metrics` |

## 📞 Support

- Documentation: `UPGRADE_GUIDE.md`
- Implementation: `IMPLEMENTATION_COMPLETE.md`
- Issues: See `docs/` directory

---

**Version**: 3.0.0  
**Last Updated**: November 1, 2025

