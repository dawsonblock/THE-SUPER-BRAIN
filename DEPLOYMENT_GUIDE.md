# Brain-AI RAG++ Deployment Guide

## Overview

This guide covers deployment strategies for the Brain-AI RAG++ system in local development, staging, and production environments.

## Architecture

The system consists of four main services:

1. **Core** - C++ core library with vector search (internal, no exposed ports)
2. **REST** - FastAPI REST service (port 5001)
3. **GUI** - React/TypeScript frontend with Nginx (port 3000)
4. **OCR** - DeepSeek-OCR service (port 6001, optional)

## Pre-Deployment Checklist

### 1. Environment Configuration

- [ ] Copy `env.example` to `.env` (local) or `.env.production` (production)
- [ ] Set `DEEPSEEK_API_KEY` (required for production)
- [ ] Set `API_KEY` (generate secure key for production)
- [ ] Configure `CORS_ORIGINS` with your frontend domains
- [ ] Set appropriate rate limits (`RATE_LIMIT_RPM`)
- [ ] Review and adjust timeout values
- [ ] Set `SAFE_MODE=0` and `LLM_STUB=0` for production

### 2. Security Verification

- [ ] API keys are strong and unique (not defaults)
- [ ] `REQUIRE_API_KEY_FOR_WRITES=1` is set
- [ ] CORS origins are restricted to known domains
- [ ] Rate limiting is enabled
- [ ] Environment files are in `.gitignore`
- [ ] No sensitive data in Docker images

### 3. Build Verification

- [ ] C++ core builds successfully (`cd brain-ai && ./build.sh`)
- [ ] All C++ tests pass (`cd brain-ai/build && ctest`)
- [ ] Python module loads (`python3 -c "import brain_ai_core"`)
- [ ] GUI builds (`cd brain-ai-gui && npm run build`)
- [ ] Docker images build (`docker compose build`)

### 4. Performance Testing

- [ ] Load test REST API endpoints
- [ ] Verify p95 latency < 500ms for queries
- [ ] Check memory usage under load
- [ ] Verify index persistence works
- [ ] Test failover scenarios

## Deployment Options

### Local Development

**Use Case:** Development, testing, debugging

**Command:**
```bash
./start_dev.sh
```

**Features:**
- Hot reload for REST API and GUI
- SAFE_MODE enabled (no real API calls)
- Logs to `logs/` directory
- Easy to stop with `Ctrl+C` or `./stop_dev.sh`

**Access:**
- GUI: http://localhost:3000
- REST API: http://localhost:5001
- Metrics: http://localhost:5001/metrics

---

### Docker Compose (Local/Staging)

**Use Case:** Local testing, staging environments, demo deployments

**Command:**
```bash
# Start all services
docker compose up --build -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

**Features:**
- All services containerized
- Automatic health checks
- Data persistence via volumes
- Easy to tear down and restart

**Verification:**
```bash
# Check service health
docker compose ps

# Test end-to-end
./test_e2e_full.sh
```

---

### Production Deployment (Single Server)

**Use Case:** Small-scale production, single server

**Command:**
```bash
./start_production.sh
```

**Features:**
- Validates API keys before starting
- Runs C++ tests before deployment
- Production-optimized build
- Process monitoring
- Persistent data storage

**Post-Deployment Checks:**
```bash
# Health check
curl -H "X-API-Key: YOUR_API_KEY" http://localhost:5001/healthz

# Metrics
curl http://localhost:5001/metrics

# Test query
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{"query":"test","top_k":5}'
```

---

### Production Deployment (Docker Production)

**Use Case:** Production with container orchestration

**Steps:**

1. **Build Production Images:**
```bash
docker compose -f docker-compose.yml build
```

2. **Tag Images:**
```bash
docker tag brain-ai-core:latest your-registry/brain-ai-core:v1.0.0
docker tag brain-ai-rest:latest your-registry/brain-ai-rest:v1.0.0
docker tag brain-ai-gui:latest your-registry/brain-ai-gui:v1.0.0
```

3. **Push to Registry:**
```bash
docker push your-registry/brain-ai-core:v1.0.0
docker push your-registry/brain-ai-rest:v1.0.0
docker push your-registry/brain-ai-gui:v1.0.0
```

4. **Deploy on Production Server:**
```bash
# On production server
docker compose -f docker-compose.yml pull
docker compose -f docker-compose.yml up -d

# Or with specific env file
docker compose --env-file .env.production up -d
```

---

## Health Monitoring

### Health Check Endpoints

**REST API:**
- `/healthz` - Basic health (no auth required)
- `/readyz` - Readiness check (checks dependencies)
- `/metrics` - Prometheus metrics

**Example Health Check Script:**
```bash
#!/bin/bash
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/healthz)
if [ $response = "200" ]; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy (HTTP $response)"
    exit 1
fi
```

### Monitoring Metrics

Key metrics to monitor (available at `/metrics`):

- `http_requests_total` - Total HTTP requests
- `request_latency_seconds` - Request latency distribution
- `query_latency_seconds` - Query-specific latency
- `indexed_documents_total` - Number of indexed documents
- `index_size_bytes` - Current index size
- `error_count_total` - Error counts by component

### Log Locations

**Docker Compose:**
```bash
docker compose logs rest    # REST API logs
docker compose logs gui     # GUI logs
docker compose logs core    # Core service logs
```

**Local Development:**
```bash
tail -f logs/rest-api.log
tail -f logs/gui-dev.log
```

**Production:**
```bash
# If using systemd
journalctl -u brain-ai-rest -f

# Or check application logs
tail -f /var/log/brain-ai/rest.log
```

---

## Troubleshooting

### Service Won't Start

1. **Check port availability:**
```bash
lsof -i :5001  # REST API
lsof -i :3000  # GUI
```

2. **Check Docker service status:**
```bash
docker compose ps
docker compose logs rest
```

3. **Verify environment variables:**
```bash
docker compose config
```

### API Key Issues

**Symptom:** 401/403 errors

**Solution:**
```bash
# Verify API key is set
echo $API_KEY

# Test with explicit key
curl -H "X-API-Key: your-key-here" http://localhost:5001/readyz
```

### CORS Errors

**Symptom:** Browser console shows CORS errors

**Solution:**
1. Update `CORS_ORIGINS` in `.env`:
```
CORS_ORIGINS=http://localhost:3000,https://your-domain.com
```

2. Restart REST service:
```bash
docker compose restart rest
```

### Out of Memory

**Symptom:** Service crashes or becomes unresponsive

**Solution:**
1. Check index size:
```bash
curl http://localhost:5001/healthz | jq '.documents'
```

2. Increase Docker memory limits in `docker-compose.yml`:
```yaml
services:
  rest:
    deploy:
      resources:
        limits:
          memory: 4G
```

3. Clear and rebuild index if needed

### Slow Query Performance

**Diagnostics:**
```bash
# Check query latency
curl http://localhost:5001/metrics | grep query_latency

# Check index size
curl http://localhost:5001/metrics | grep index_size
```

**Solutions:**
- Reduce `TOP_K_RETRIEVAL` in config
- Increase `ef_search` parameter for accuracy/speed tradeoff
- Add more CPU resources
- Consider index sharding for large datasets

---

## Rollback Procedures

### Docker Rollback

```bash
# Stop current deployment
docker compose down

# Pull previous version
docker pull your-registry/brain-ai-rest:v0.9.0

# Update docker-compose.yml with previous version tag

# Start previous version
docker compose up -d
```

### Local Deployment Rollback

```bash
# Stop current service
kill $(cat /var/run/brain-ai-rest.pid)

# Checkout previous version
git checkout v0.9.0

# Rebuild
cd brain-ai && ./build.sh

# Restart
./start_production.sh
```

---

## Backup and Recovery

### Data Backup

**Index Data:**
```bash
# Backup index and metadata
cp data/index.json data/index.json.backup
cp data/index.json.metadata.json data/index.json.metadata.json.backup

# Or use the API
curl -X POST http://localhost:5001/api/v1/system/backup \
  -H "X-API-Key: YOUR_KEY"
```

**Database Backup:**
```bash
# Backup facts database
cp data/facts.db data/facts.db.backup
```

### Recovery

```bash
# Restore from backup
cp data/index.json.backup data/index.json
cp data/index.json.metadata.json.backup data/index.json.metadata.json

# Restart service
docker compose restart rest
```

---

## Security Best Practices

1. **Never commit** `.env` or `.env.production` to version control
2. **Rotate API keys** regularly (monthly recommended)
3. **Use HTTPS** in production with valid certificates
4. **Restrict CORS** to known frontend domains only
5. **Enable rate limiting** to prevent abuse
6. **Monitor logs** for suspicious activity
7. **Keep dependencies updated** regularly
8. **Use secrets management** (e.g., AWS Secrets Manager, HashiCorp Vault)

---

## Performance Tuning

### C++ Core

- Adjust `ef_search` parameter (default: 50, range: 10-500)
- Increase `M` parameter for better recall (default: 16)
- Use `march=native` for optimized builds

### REST API

- Increase worker count for high traffic: `--workers 4`
- Adjust `uvicorn` timeout values
- Enable HTTP/2 for better performance
- Use caching for frequent queries

### GUI

- Enable gzip compression in nginx
- Set appropriate cache headers for static assets
- Use CDN for asset delivery
- Minify and bundle assets

---

## Support and Monitoring

### Key Metrics Dashboard

Monitor these metrics in production:

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Query Latency (p95) | < 500ms | > 1000ms |
| Error Rate | < 1% | > 5% |
| Memory Usage | < 2GB | > 3GB |
| CPU Usage | < 50% | > 80% |
| Index Size | < 1GB | > 5GB |
| Request Rate | Variable | > 1000/min |

### Alerting

Set up alerts for:
- Service down (health check fails)
- High error rate (> 5%)
- High latency (p95 > 1s)
- Memory usage (> 80%)
- Disk space (> 90%)

---

## Maintenance Schedule

**Daily:**
- Check service health
- Review error logs
- Monitor metrics dashboard

**Weekly:**
- Review performance metrics
- Check disk space usage
- Backup index data
- Review security logs

**Monthly:**
- Rotate API keys
- Update dependencies
- Review and optimize queries
- Capacity planning review

**Quarterly:**
- Full system audit
- Penetration testing
- Disaster recovery drill
- Performance benchmark tests

---

## Contact and Support

For issues during deployment:
1. Check this guide's troubleshooting section
2. Review service logs
3. Check GitHub issues
4. Contact support (if applicable)

**Emergency Contacts:**
- On-call engineer: [Contact info]
- System administrator: [Contact info]
- Security team: [Contact info]

