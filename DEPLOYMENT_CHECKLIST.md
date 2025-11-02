# Brain-AI RAG++ v3.0 - Deployment Checklist

## Pre-Deployment Verification

### ✅ Code Complete (All Done)

- [x] Config coherence (`config.yaml`)
- [x] Pybind11 bindings functional
- [x] Prompts module (`app/prompts.py`)
- [x] Reranker module (`app/reranker.py`)
- [x] Enhanced LLM client (`app/llm_deepseek.py`)
- [x] Multi-agent correction (`app/agents.py`)
- [x] Verification tools (`app/verification.py`)
- [x] Facts store (`app/facts_store.py`)
- [x] Upgraded REST API (`app/app_v2.py`)
- [x] Enhanced metrics (`app/metrics.py`)
- [x] Security hardening (CORS, API keys)
- [x] Docker configuration updated
- [x] CI/test enforcement
- [x] Evaluation harness (`eval/`)
- [x] Startup scripts (`scripts/`)
- [x] Documentation complete

### Environment Setup

- [ ] Set `DEEPSEEK_API_KEY`
- [ ] Generate secure `API_KEY`
- [ ] Set `EVIDENCE_TAU` (default 0.70)
- [ ] Set `N_SOLVERS` (default 3)
- [ ] Configure `CORS_ORIGINS`
- [ ] Review and set other env vars from `env.example`

### Build & Test

- [ ] Build C++ core:
  ```bash
  cd brain-ai && mkdir -p build && cd build
  cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_PYTHON_BINDINGS=ON ..
  make -j$(nproc)
  ```

- [ ] Run C++ tests:
  ```bash
  ctest --output-on-failure
  ```

- [ ] Verify Python bindings:
  ```bash
  python3 -c "import sys; sys.path.insert(0, '.'); import brain_ai_py; print('OK')"
  ```

- [ ] Install Python dependencies:
  ```bash
  cd ../../brain-ai-rest-service
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
  ```

- [ ] Run unit tests:
  ```bash
  cd ../tests
  python test_rag_plus_plus.py
  ```

### Local Smoke Test

- [ ] Start services:
  ```bash
  ./scripts/start_production.sh
  ```

- [ ] Wait for startup (30s)

- [ ] Run smoke tests:
  ```bash
  ./scripts/smoke_test.sh
  ```

- [ ] Verify all tests pass

### Metrics & Monitoring

- [ ] Access metrics endpoint:
  ```bash
  curl http://localhost:9090/metrics
  ```

- [ ] Verify Prometheus scraping works

- [ ] Check key metrics are present:
  - `refusals_total`
  - `facts_cache_hits_total`
  - `deepseek_calls_total`
  - `query_latency_seconds`
  - `answer_confidence`

### Security Verification

- [ ] API key authentication works:
  ```bash
  # Should fail without key
  curl -X POST http://localhost:5001/index \
    -H "Content-Type: application/json" \
    -d '{"doc_id":"test","text":"test"}'
  
  # Should succeed with key
  curl -X POST http://localhost:5001/index \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"doc_id":"test","text":"test"}'
  ```

- [ ] CORS headers present:
  ```bash
  curl -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: POST" \
    -X OPTIONS http://localhost:5001/answer -v
  ```

- [ ] Rate limiting works (send 121 requests in 1 minute)

- [ ] Kill switch works:
  ```bash
  curl -X POST http://localhost:5001/admin/kill \
    -H "X-API-Key: $API_KEY"
  
  # Verify service refuses requests
  curl http://localhost:5001/healthz
  
  # Re-enable
  curl -X DELETE http://localhost:5001/admin/kill \
    -H "X-API-Key: $API_KEY"
  ```

### Functional Testing

- [ ] Index test documents:
  ```bash
  curl -X POST http://localhost:5001/index \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"doc_id":"d1","text":"Rope memory stores bits by threading wires through cores."}'
  ```

- [ ] Query with context (should answer):
  ```bash
  curl -X POST http://localhost:5001/answer \
    -H "Content-Type: application/json" \
    -d '{"query":"How did rope memory work?"}'
  ```

- [ ] Query without context (should refuse):
  ```bash
  curl -X POST http://localhost:5001/answer \
    -H "Content-Type: application/json" \
    -d '{"query":"What is XYZABC?"}'
  ```

- [ ] Verify response format:
  - Contains `answer`, `citations`, `confidence`
  - Confidence is float between 0 and 1
  - Citations are array of strings

### Evaluation Baseline

- [ ] Run evaluation harness:
  ```bash
  cd eval
  python run_eval.py \
    --api-url http://localhost:5001/answer \
    --eval-set eval_set.jsonl \
    --output metrics.json
  ```

- [ ] Review metrics.json:
  - Groundedness ≥ 0.80?
  - Hallucination ≤ 0.10?
  - P95 latency ≤ 2000ms?

- [ ] Document baseline metrics for future comparison

### Docker Verification

- [ ] Build images:
  ```bash
  docker-compose build
  ```

- [ ] Start containers:
  ```bash
  docker-compose up -d
  ```

- [ ] Check health:
  ```bash
  docker-compose ps
  docker-compose logs rest | tail -20
  ```

- [ ] Run smoke tests against Docker:
  ```bash
  API_URL=http://localhost:5001 ./scripts/smoke_test.sh
  ```

- [ ] Stop containers:
  ```bash
  docker-compose down
  ```

## Staging Deployment

### Infrastructure

- [ ] Provision compute resources (CPU: 4 cores, RAM: 8GB min)
- [ ] Set up PostgreSQL/MySQL for facts store (optional, SQLite OK for staging)
- [ ] Configure Prometheus server
- [ ] Configure log aggregation (optional)
- [ ] Set up DNS/domain name
- [ ] Configure TLS/SSL certificates

### Deployment

- [ ] Push Docker images to registry
- [ ] Deploy to staging environment
- [ ] Configure environment variables
- [ ] Start services
- [ ] Verify health checks pass
- [ ] Run smoke tests
- [ ] Run evaluation harness

### Monitoring Setup

- [ ] Configure Prometheus scraping
- [ ] Set up Grafana dashboards (optional)
- [ ] Configure alerts:
  - High error rate (>5%)
  - High refusal rate (>40%)
  - High latency (P95 > 5s)
  - Low cache hit rate (<5%)

### Load Testing

- [ ] Run load test with 10 concurrent users
- [ ] Monitor metrics during load test
- [ ] Verify no crashes or errors
- [ ] Check P95 latency stays under target

## Production Deployment

### Pre-Production

- [ ] Staging has been stable for 48+ hours
- [ ] All metrics meet targets
- [ ] Security audit complete
- [ ] Load testing passed
- [ ] Rollback plan documented

### Production Cutover

- [ ] Schedule maintenance window
- [ ] Notify users of migration
- [ ] Deploy production environment
- [ ] Configure production DNS
- [ ] Enable monitoring and alerts
- [ ] Run smoke tests
- [ ] Monitor for 1 hour

### Post-Deployment

- [ ] Verify all endpoints responding
- [ ] Check metrics dashboard
- [ ] Review logs for errors
- [ ] Test from client applications
- [ ] Send test queries
- [ ] Monitor for 24 hours

### Rollback (If Needed)

If issues arise:

- [ ] Switch DNS back to old version
- [ ] Or: Update uvicorn command to use old `app.app`
- [ ] Notify users
- [ ] Investigate issues
- [ ] Plan fix and re-deploy

## Continuous Operations

### Daily

- [ ] Check error logs
- [ ] Review refusal rate trend
- [ ] Check DeepSeek API usage
- [ ] Verify cache hit rate growing

### Weekly

- [ ] Run evaluation harness
- [ ] Review performance metrics
- [ ] Check facts store growth
- [ ] Update eval_set.jsonl with new examples

### Monthly

- [ ] Review and update documentation
- [ ] Analyze user query patterns
- [ ] Fine-tune evidence threshold if needed
- [ ] Consider model upgrades

## Success Criteria

### Minimum Requirements

- ✅ All smoke tests pass
- ✅ Groundedness ≥ 0.80
- ✅ Hallucination ≤ 0.10
- ✅ P95 latency ≤ 2000ms
- ✅ Error rate < 1%
- ✅ Uptime ≥ 99.5%

### Stretch Goals

- Groundedness ≥ 0.90
- P95 latency ≤ 1500ms
- Cache hit rate ≥ 15%
- User satisfaction > 4/5

## Emergency Contacts

- **On-call Engineer**: [Your contact]
- **DeepSeek Support**: [Support channel]
- **Infrastructure Team**: [Contact info]

## References

- Quick Start: `UPGRADE_GUIDE.md`
- Migration: `brain-ai-rest-service/MIGRATION_TO_V2.md`
- Quick Reference: `QUICK_REFERENCE_RAG_PLUS_PLUS.md`
- Implementation: `IMPLEMENTATION_COMPLETE.md`

---

**Version**: 3.0.0  
**Last Updated**: November 1, 2025  
**Status**: Ready for Deployment ✅

