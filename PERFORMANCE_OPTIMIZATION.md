# Brain-AI Performance Optimization Guide

**Version**: 4.5.0  
**Last Updated**: November 6, 2025

## 🎯 Current Performance Baseline

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Query Latency (p50) | 20ms | <50ms | ✅ Excellent |
| Query Latency (p95) | 50ms | <100ms | ✅ Excellent |
| Index Throughput | 200/s | >100/s | ✅ Good |
| Memory Usage | 350MB | <1GB | ✅ Excellent |
| Build Time | 30s | <2min | ✅ Excellent |

## 🚀 Quick Wins (Immediate Impact)

### 1. Enable Connection Pooling

**Impact**: 30-50% latency reduction  
**Effort**: Low

#### Python REST API
```python
# app/http_client.py
import httpx

class ConnectionPool:
    def __init__(self):
        self.client = httpx.AsyncClient(
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            ),
            timeout=httpx.Timeout(30.0)
        )
    
    async def get(self, url):
        return await self.client.get(url)
```

### 2. Implement Batch Processing Parallelization

**Impact**: 3-5x speedup for batch operations  
**Effort**: Medium

#### C++ OCR Client
```cpp
// src/document/ocr_client.cpp
#include <future>
#include <thread>

std::vector<OCRResult> OCRClient::process_batch(
    const std::vector<std::string>& filepaths
) {
    const size_t max_threads = std::thread::hardware_concurrency();
    std::vector<std::future<OCRResult>> futures;
    
    for (const auto& filepath : filepaths) {
        futures.push_back(std::async(
            std::launch::async,
            [this, filepath]() { return process_file(filepath); }
        ));
    }
    
    std::vector<OCRResult> results;
    for (auto& future : futures) {
        results.push_back(future.get());
    }
    return results;
}
```

### 3. Add Redis Caching

**Impact**: 80%+ cache hit rate, 10x faster for cached queries  
**Effort**: Medium

#### Setup Redis
```bash
# Install Redis
brew install redis  # macOS
sudo apt-get install redis  # Ubuntu

# Start Redis
redis-server
```

#### Python Integration
```python
# app/cache.py
import redis
import json

class RedisCache:
    def __init__(self, host='localhost', port=6379):
        self.redis = redis.Redis(host=host, port=port)
        self.ttl = 3600  # 1 hour
    
    def get_embedding(self, text):
        key = f"emb:{hash(text)}"
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)
        return None
    
    def set_embedding(self, text, embedding):
        key = f"emb:{hash(text)}"
        self.redis.setex(key, self.ttl, json.dumps(embedding))
```

## 🔧 Configuration Optimizations

### 1. HNSW Index Tuning

**Current**: Default parameters  
**Optimized**: Tuned for your workload

```python
# Adjust based on your needs:
# - M: Number of connections (16-48)
# - ef_construction: Build quality (100-400)
# - ef_search: Search quality (50-200)

manager = IndexManager(
    embedding_dim=384,
    M=32,  # Higher = better recall, more memory
    ef_construction=200,  # Higher = better index quality
    ef_search=100  # Higher = better recall, slower search
)
```

**Guidelines**:
- **Small dataset (<10K docs)**: M=16, ef=100
- **Medium dataset (10K-100K)**: M=32, ef=200
- **Large dataset (>100K)**: M=48, ef=400

### 2. Embedding Model Selection

**Current**: all-MiniLM-L6-v2 (384-dim)

| Model | Dimensions | Speed | Quality | Use Case |
|-------|------------|-------|---------|----------|
| all-MiniLM-L6-v2 | 384 | Fast | Good | General (current) |
| all-mpnet-base-v2 | 768 | Medium | Better | High quality |
| multi-qa-mpnet | 768 | Medium | Best | Q&A specific |

```bash
# Change model
export EMBEDDING_MODEL_NAME=sentence-transformers/all-mpnet-base-v2
```

### 3. OCR Service Optimization

#### Use vLLM Backend
```bash
# Faster inference
export DEEPSEEK_OCR_USE_VLLM=true
```

#### Adjust Resolution
```bash
# Lower resolution = faster processing
export DEEPSEEK_OCR_DEFAULT_RESOLUTION=small  # or tiny
```

## 💾 Memory Optimization

### 1. Reduce Model Memory

```python
# Use quantization
model = SentenceTransformer(
    'all-MiniLM-L6-v2',
    device='cpu'
).half()  # FP16 instead of FP32
```

### 2. Limit Cache Size

```python
# Reduce embedding cache
embedding_service = EmbeddingService(
    cache_size=500  # Down from 1000
)
```

### 3. Index Compression

```cpp
// Use smaller data types where possible
using embedding_t = float;  // Consider float16 for production
```

## 🌐 Network Optimization

### 1. Enable HTTP/2

```python
# uvicorn with HTTP/2
uvicorn app.app:app --http h2
```

### 2. Enable Compression

```python
# FastAPI middleware
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 3. CDN for Static Assets

```nginx
# nginx.conf
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

## 🔄 Database Optimization

### 1. Index Optimization

```sql
-- SQLite facts store
CREATE INDEX idx_question_hash ON facts(question_hash);
CREATE INDEX idx_confidence ON facts(confidence);
CREATE INDEX idx_access_count ON facts(access_count);
```

### 2. Query Optimization

```python
# Use prepared statements
cursor.execute(
    "SELECT * FROM facts WHERE question_hash = ?",
    (q_hash,)
)
```

### 3. Batch Operations

```python
# Batch inserts
cursor.executemany(
    "INSERT INTO facts VALUES (?, ?, ?)",
    batch_data
)
```

## 📊 Profiling & Benchmarking

### 1. Python Profiling

```bash
# Profile REST API
python -m cProfile -o profile.stats app.py

# Analyze
python -m pstats profile.stats
```

### 2. C++ Profiling

```bash
# Build with profiling
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo ..

# Profile with perf
perf record ./brain_ai_demo
perf report
```

### 3. Load Testing

```bash
# Install hey
go install github.com/rakyll/hey@latest

# Run load test
hey -n 10000 -c 100 \
  -m POST \
  -H "Content-Type: application/json" \
  -d '{"query":"test","top_k":5}' \
  http://localhost:5001/query
```

## 🎯 Optimization Roadmap

### Phase 1: Quick Wins (Week 1)
- [ ] Enable connection pooling
- [ ] Tune HNSW parameters
- [ ] Enable HTTP compression
- [ ] Add database indexes

**Expected Improvement**: 30-40% latency reduction

### Phase 2: Caching (Week 2-3)
- [ ] Setup Redis
- [ ] Implement embedding cache
- [ ] Implement query result cache
- [ ] Add cache warming

**Expected Improvement**: 50-80% for cached queries

### Phase 3: Parallelization (Week 4)
- [ ] Batch processing parallelization
- [ ] Multi-threaded indexing
- [ ] Async I/O operations

**Expected Improvement**: 3-5x for batch operations

### Phase 4: Advanced (Month 2)
- [ ] GPU acceleration for embeddings
- [ ] Distributed caching
- [ ] Load balancing
- [ ] Horizontal scaling

**Expected Improvement**: 10x+ at scale

## �� Performance Monitoring

### Key Metrics to Track

```python
# Add to metrics.py
OPTIMIZATION_METRICS = {
    'cache_hit_rate': Gauge('cache_hit_rate', 'Cache hit rate'),
    'batch_size': Histogram('batch_size', 'Batch operation size'),
    'connection_pool_usage': Gauge('pool_usage', 'Connection pool usage'),
}
```

### Performance Dashboard

Create Grafana dashboard with:
- Cache hit rate over time
- Latency percentiles (p50, p95, p99)
- Throughput (requests/sec)
- Resource utilization (CPU, memory, disk)

## ✅ Optimization Checklist

### Configuration
- [ ] HNSW parameters tuned
- [ ] Embedding model selected
- [ ] OCR resolution optimized
- [ ] Cache sizes configured

### Infrastructure
- [ ] Connection pooling enabled
- [ ] Redis installed and configured
- [ ] HTTP/2 enabled
- [ ] Compression enabled

### Code
- [ ] Batch processing parallelized
- [ ] Database queries optimized
- [ ] Async I/O implemented
- [ ] Memory usage optimized

### Monitoring
- [ ] Performance metrics tracked
- [ ] Profiling setup
- [ ] Load testing automated
- [ ] Alerts configured

## 🎓 Best Practices

1. **Measure First**: Always profile before optimizing
2. **Optimize Bottlenecks**: Focus on the slowest parts
3. **Test Impact**: Measure improvement after each change
4. **Monitor Production**: Track metrics in production
5. **Document Changes**: Keep optimization log

## 📝 Optimization Log Template

```markdown
### Optimization: [Name]
**Date**: [Date]
**Metric**: [What you're optimizing]
**Before**: [Baseline measurement]
**After**: [New measurement]
**Improvement**: [Percentage]
**Changes**: [What you changed]
**Risks**: [Any potential issues]
```

**Status**: ⬜ Baseline ⬜ Optimized ⬜ Validated
