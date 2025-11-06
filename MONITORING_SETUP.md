# Brain-AI Monitoring & Alerting Setup

**Version**: 4.5.0  
**Last Updated**: November 6, 2025

## 📊 Metrics Collection

### Prometheus Setup

#### 1. Install Prometheus
```bash
# macOS
brew install prometheus

# Ubuntu
sudo apt-get install prometheus

# Docker
docker run -d -p 9090:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

#### 2. Configure Scraping
Create `prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'brain-ai-rest'
    static_configs:
      - targets: ['localhost:5001']
    metrics_path: '/metrics'
  
  - job_name: 'brain-ai-ocr'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

### Key Metrics

#### REST API Metrics
- `query_latency_seconds` - Query processing time
- `index_operations_total` - Total index operations
- `active_requests` - Current active requests
- `memory_usage_bytes` - Memory consumption
- `error_rate` - Error rate percentage

#### OCR Service Metrics
- `ocr_processing_time_seconds` - OCR processing latency
- `ocr_requests_total` - Total OCR requests
- `ocr_requests_success` - Successful requests
- `ocr_model_loaded` - Model load status

## 🚨 Alerting Rules

### Prometheus Alerts
Create `alerts.yml`:
```yaml
groups:
  - name: brain-ai-alerts
    rules:
      # Critical: Service Down
      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
      
      # Critical: High Error Rate
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Error rate > 5%"
      
      # Warning: High Latency
      - alert: HighLatency
        expr: histogram_quantile(0.95, query_latency_seconds) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "p95 latency > 500ms"
      
      # Warning: High Memory
      - alert: HighMemory
        expr: memory_usage_bytes > 0.9 * memory_limit_bytes
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Memory usage > 90%"
```

## 📈 Grafana Dashboards

### Install Grafana
```bash
# macOS
brew install grafana

# Ubuntu
sudo apt-get install grafana

# Docker
docker run -d -p 3001:3000 grafana/grafana
```

### Dashboard Panels

#### 1. Query Performance
- Query latency (p50, p95, p99)
- Queries per second
- Error rate

#### 2. System Health
- CPU usage
- Memory usage
- Disk I/O
- Network traffic

#### 3. OCR Performance
- OCR processing time
- OCR throughput
- Success rate

#### 4. Index Operations
- Index size
- Documents indexed
- Index operations/sec

### Sample Dashboard JSON
```json
{
  "dashboard": {
    "title": "Brain-AI Monitoring",
    "panels": [
      {
        "title": "Query Latency",
        "targets": [{
          "expr": "histogram_quantile(0.95, query_latency_seconds)"
        }]
      },
      {
        "title": "Requests/sec",
        "targets": [{
          "expr": "rate(requests_total[1m])"
        }]
      }
    ]
  }
}
```

## 📝 Logging Setup

### Structured Logging

#### Configure Log Format
```python
# Python services
import logging
import json

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
```

### Log Aggregation (ELK Stack)

#### 1. Elasticsearch
```bash
docker run -d -p 9200:9200 \
  -e "discovery.type=single-node" \
  elasticsearch:8.11.0
```

#### 2. Logstash
```bash
# logstash.conf
input {
  file {
    path => "/var/log/brain-ai/*.log"
    type => "brain-ai"
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
  }
}
```

#### 3. Kibana
```bash
docker run -d -p 5601:5601 \
  -e "ELASTICSEARCH_HOSTS=http://localhost:9200" \
  kibana:8.11.0
```

## 🔔 Alert Channels

### Slack Integration
```yaml
# alertmanager.yml
receivers:
  - name: 'slack'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts'
        title: 'Brain-AI Alert'
        text: '{{ .CommonAnnotations.summary }}'
```

### Email Alerts
```yaml
receivers:
  - name: 'email'
    email_configs:
      - to: 'ops@example.com'
        from: 'alerts@example.com'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'alerts@example.com'
        auth_password: 'password'
```

### PagerDuty
```yaml
receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_SERVICE_KEY'
```

## 📊 SLO/SLA Definitions

### Service Level Objectives

#### Availability
- **Target**: 99.9% uptime
- **Measurement**: `up` metric
- **Alert**: < 99.9% over 30 days

#### Latency
- **Target**: p95 < 100ms
- **Measurement**: `query_latency_seconds`
- **Alert**: p95 > 100ms for 10 minutes

#### Error Rate
- **Target**: < 1% errors
- **Measurement**: `errors_total / requests_total`
- **Alert**: > 1% for 5 minutes

## 🔍 Health Check Endpoints

### REST API
```bash
# Liveness
curl http://localhost:5001/healthz
# Response: {"ok": true, "version": "4.5.0"}

# Readiness
curl http://localhost:5001/readyz
# Response: {"ready": true, "checks": {...}}

# Metrics
curl http://localhost:5001/metrics
```

### OCR Service
```bash
# Health
curl http://localhost:8000/health
# Response: {"status": "healthy", "model_loaded": true}

# Metrics
curl http://localhost:8000/metrics
```

## �� Monitoring Checklist

- [ ] Prometheus installed and configured
- [ ] Grafana dashboards created
- [ ] Alert rules defined
- [ ] Alert channels configured
- [ ] Log aggregation setup
- [ ] SLO/SLA defined
- [ ] On-call rotation established
- [ ] Runbooks created
- [ ] Escalation procedures documented

## 🎯 Quick Start

```bash
# 1. Start Prometheus
prometheus --config.file=prometheus.yml

# 2. Start Grafana
grafana-server

# 3. Access dashboards
open http://localhost:3001  # Grafana
open http://localhost:9090  # Prometheus

# 4. Import Brain-AI dashboard
# Use dashboard JSON from above
```

**Monitoring Status**: ⬜ Configured ⬜ Active ⬜ Tested
