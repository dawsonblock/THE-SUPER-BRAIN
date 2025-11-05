# Brain-AI RAG++ System

> **Production-ready C++ cognitive architecture with vector search, multi-agent orchestration, and LLM integration**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](BUILD_DEBUG_SUMMARY.md)
[![Tests](https://img.shields.io/badge/tests-6%2F6%20passing-brightgreen.svg)](BUILD_DEBUG_SUMMARY.md)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](docker-compose.yml)
[![Version](https://img.shields.io/badge/version-4.3.0-blue.svg)](CHANGELOG.md)

---

## 🚀 Quick Start

Get the full system running in under 5 minutes:

```bash
# Option 1: Local Development (with hot reload)
./start_dev.sh
# Access: GUI at http://localhost:3000, API at http://localhost:5001

# Option 2: Docker Production
docker compose up --build
# Access: GUI at http://localhost:3000, API at http://localhost:5001

# Option 3: Run Tests
./test_e2e_full.sh
```

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Development](#development)
- [Deployment](#deployment)
- [Testing](#testing)
- [Performance](#performance)
- [Contributing](#contributing)
- [Documentation](#documentation)
- [License](#license)

---

## 🎯 Overview

Brain-AI RAG++ is a high-performance, production-ready Retrieval-Augmented Generation system that combines:

- **C++ Core Engine** - Lightning-fast vector search using HNSW algorithm
- **Python REST API** - FastAPI service with advanced RAG capabilities
- **React GUI** - Modern TypeScript interface for system control
- **Multi-Agent System** - Collaborative AI agents for improved accuracy
- **Document Processing** - OCR integration for document analysis
- **Production Features** - Monitoring, security, rate limiting, and more

### Why Brain-AI RAG++?

- ⚡ **Fast**: <10ms p50 query latency with C++ vector search
- 🧠 **Smart**: Multi-agent orchestration with verification
- 🛡️ **Safe**: Hallucination detection and evidence gating
- 📈 **Scalable**: Docker-ready with health monitoring
- 🔒 **Secure**: API key auth, CORS protection, rate limiting
- 📊 **Observable**: Prometheus metrics and structured logging

---

## ✨ Features

### Core Capabilities

- **Vector Search**: HNSW-based approximate nearest neighbor search
- **Semantic Indexing**: 384/768-dim embeddings with metadata
- **LLM Integration**: DeepSeek AI (R1, Chat, V3) with retry logic
- **Multi-Agent RAG**: 3+ solver agents with confidence voting
- **Re-ranking**: Cross-encoder for precision refinement
- **Facts Store**: SQLite-backed knowledge persistence
- **OCR Processing**: DeepSeek-OCR for document extraction

### Production Features

- **Health Monitoring**: `/healthz`, `/readyz`, `/metrics` endpoints
- **Rate Limiting**: Configurable per-client limits
- **Circuit Breaker**: Automatic failure recovery
- **Structured Logging**: JSON logs with context
- **API Security**: Key-based authentication
- **CORS Protection**: Configurable origin whitelist
- **Auto-persistence**: Index snapshots every N documents
- **Kill Switch**: Emergency shutdown capability

### User Interface

- **Chat Interface**: Real-time Q&A with streaming responses
- **Document Upload**: Batch indexing with progress tracking
- **Search Console**: Advanced search with filters
- **Metrics Dashboard**: Real-time performance monitoring
- **Admin Panel**: System control and configuration
- **Multi-Agent View**: Agent collaboration visualization

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Users / Clients                       │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌──────────────────┐           ┌──────────────────┐
│   GUI (React)    │           │   External API   │
│   Port 3000      │           │   Clients        │
│   - TypeScript   │           │   - curl, Postman│
│   - Nginx Proxy  │           │   - SDK clients  │
└────────┬─────────┘           └────────┬─────────┘
         │                              │
         └───────────────┬──────────────┘
                         │ /api/*
                         ▼
              ┌─────────────────────┐
              │   REST API (FastAPI)│
              │   Port 5001         │
              │   - Query endpoint  │
              │   - Index endpoint  │
              │   - Metrics endpoint│
              └──────────┬──────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│ C++ Core    │  │ LLM Service  │  │ OCR Service  │
│ brain_ai_   │  │ DeepSeek API │  │ Port 6001    │
│ core.so     │  │ - R1 Model   │  │ (Optional)   │
│             │  │ - Chat Model │  │              │
│ - HNSW      │  │ - V3 Model   │  │              │
│ - Indexing  │  └──────────────┘  └──────────────┘
│ - Search    │
└─────────────┘
```

### Technology Stack

**Backend:**
- C++17 with CMake
- Python 3.12 with FastAPI
- Pybind11 for bindings
- HNSW for vector search
- SQLite for persistence

**Frontend:**
- React 18 with TypeScript
- Vite for build tooling
- TailwindCSS for styling
- Axios for API calls
- React Query for state

**Infrastructure:**
- Docker & Docker Compose
- Nginx for GUI serving
- Prometheus metrics
- OpenSSL for security

---

## 📦 Installation

### Prerequisites

- **C++ Build Tools**: CMake 3.22+, C++17 compiler
- **Python**: 3.12+ with pip
- **Node.js**: 18+ with npm
- **Docker**: 20.10+ (optional, for containerized deployment)
- **OpenSSL**: 3.0+ (for security features)

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/C-AI-BRAIN-2.git
cd C-AI-BRAIN-2

# Install system dependencies (macOS)
brew install cmake python@3.12 node openssl

# Install system dependencies (Ubuntu)
sudo apt-get install build-essential cmake python3 python3-pip nodejs npm libssl-dev

# Set up environment
cp env.example .env
# Edit .env with your API keys (optional for dev mode)
```

### Development Setup

```bash
# Build C++ core
cd brain-ai
./build.sh
cd ..

# Install Python dependencies
cd brain-ai-rest-service
pip install -r requirements.txt
cd ..

# Install GUI dependencies
cd brain-ai-gui
npm install
cd ..

# Start everything
./start_dev.sh
```

### Docker Setup

```bash
# Build all services
docker compose build

# Start the system
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

---

## 🎮 Usage

### Basic Example

```bash
# Index a document
curl -X POST http://localhost:5001/index \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "doc_id": "doc1",
    "text": "Machine learning is a subset of artificial intelligence."
  }'

# Query the system
curl -X POST http://localhost:5001/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 5
  }'
```

### Python SDK Example

```python
import requests

# Configure
API_URL = "http://localhost:5001"
API_KEY = "your-api-key"

# Index documents
def index_document(doc_id: str, text: str):
    response = requests.post(
        f"{API_URL}/index",
        json={"doc_id": doc_id, "text": text},
        headers={"X-API-Key": API_KEY}
    )
    return response.json()

# Query
def query(question: str, top_k: int = 5):
    response = requests.post(
        f"{API_URL}/query",
        json={"query": question, "top_k": top_k}
    )
    return response.json()

# Usage
index_document("doc1", "Python is a programming language.")
result = query("What is Python?")
print(result["answer"])
```

### GUI Usage

1. Open http://localhost:3000
2. Enter API key in settings (if required)
3. Navigate to Upload tab to index documents
4. Use Chat tab to ask questions
5. View Metrics for system performance

---

## 📚 API Reference

### Core Endpoints

#### `POST /index` - Index Document
```json
Request:
{
  "doc_id": "unique-id",
  "text": "Document content here"
}

Response:
{
  "ok": true
}
```

#### `POST /query` or `POST /answer` - Query System
```json
Request:
{
  "query": "Your question here",
  "top_k": 5
}

Response:
{
  "answer": "Generated answer",
  "hits": [{"doc_id": "...", "score": 0.95, "text": "..."}],
  "model": "deepseek-chat",
  "latency_ms": 150
}
```

#### `GET /healthz` - Health Check
```json
Response:
{
  "ok": true,
  "safe_mode": false,
  "llm_stub": false,
  "pybind_available": true,
  "documents": 42
}
```

#### `GET /metrics` - Prometheus Metrics
```
Response: (text/plain)
# HELP query_latency_seconds Query latency
# TYPE query_latency_seconds histogram
query_latency_seconds_bucket{le="0.1"} 50
...
```

### Authentication

All write endpoints require API key:
```bash
curl -H "X-API-Key: your-key-here" ...
```

Or:
```bash
curl -H "Authorization: Bearer your-key-here" ...
```

---

## 🛠️ Development

### Project Structure

```
C-AI-BRAIN-2/
├── brain-ai/              # C++ core engine
│   ├── src/              # C++ source files
│   ├── include/          # C++ headers
│   ├── bindings/         # Python bindings (pybind11)
│   ├── tests/            # C++ tests
│   └── build.sh          # Build script
├── brain-ai-rest-service/ # Python REST API
│   ├── app/              # FastAPI application
│   ├── requirements.txt  # Python dependencies
│   └── config.yaml       # Configuration
├── brain-ai-gui/         # React GUI
│   ├── src/              # TypeScript source
│   ├── package.json      # Node dependencies
│   └── vite.config.ts    # Build config
├── docker-compose.yml    # Orchestration
├── start_dev.sh          # Local dev script
├── test_e2e_full.sh      # E2E tests
└── README.md             # This file
```

### Building from Source

```bash
# C++ Core
cd brain-ai
mkdir -p build && cd build
cmake -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_PYTHON_BINDINGS=ON \
      -DBUILD_TESTS=ON \
      ..
make -j$(nproc)
ctest --output-on-failure

# Python Module
cp build/python/brain_ai_core*.so ../brain-ai-rest-service/

# GUI
cd brain-ai-gui
npm run build
```

### Running Tests

```bash
# C++ tests
cd brain-ai/build
ctest --output-on-failure

# Python tests
cd brain-ai-rest-service
pytest tests/

# End-to-end
./test_e2e_full.sh
```

### Code Style

- **C++**: clang-format with Google style
- **Python**: black + flake8 + mypy
- **TypeScript**: prettier + eslint

```bash
# Format code
npm run format           # GUI
black .                  # Python
clang-format -i src/**   # C++
```

---

## 🚀 Deployment

### Production Checklist

- [ ] Set strong API keys in `.env.production`
- [ ] Configure CORS origins for your domain
- [ ] Set `SAFE_MODE=0` and `LLM_STUB=0`
- [ ] Enable HTTPS with valid certificates
- [ ] Set up monitoring and alerting
- [ ] Configure backup strategy
- [ ] Review rate limits
- [ ] Test disaster recovery

### Docker Production

```bash
# Build production images
docker compose build

# Start services
docker compose up -d

# Monitor
docker compose ps
docker compose logs -f rest

# Scale (if needed)
docker compose up -d --scale rest=3
```

### Kubernetes (Advanced)

```yaml
# Example k8s deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: brain-ai-rest
spec:
  replicas: 3
  selector:
    matchLabels:
      app: brain-ai-rest
  template:
    metadata:
      labels:
        app: brain-ai-rest
    spec:
      containers:
      - name: rest
        image: brain-ai-rest:latest
        ports:
        - containerPort: 5001
        env:
        - name: API_KEY
          valueFrom:
            secretKeyRef:
              name: brain-ai-secrets
              key: api-key
```

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for comprehensive deployment documentation.

---

## 🧪 Testing

### Test Coverage

- **C++ Core**: 6/6 test suites (100%)
- **REST API**: Integration tests
- **GUI**: Build verification
- **E2E**: Full stack testing

### Running Tests

```bash
# Quick test
./test_e2e_full.sh

# Detailed C++ tests
cd brain-ai/build
ctest --output-on-failure --verbose

# Python tests with coverage
cd brain-ai-rest-service
pytest --cov=app --cov-report=html

# Load testing
cd bench
python run_bench.py --queries 1000
```

---

## 📊 Performance

### Benchmarks

| Metric | Value | Notes |
|--------|-------|-------|
| Query Latency (p50) | <10ms | C++ core only |
| Query Latency (p95) | <100ms | With LLM (stub) |
| Index Speed | 1000 docs/s | Batch indexing |
| Memory Usage | <500MB | 10k documents |
| Throughput | 100 qps | Single instance |
| Startup Time | <30s | All services |

### Optimization Tips

1. **Increase `ef_search`** for better recall (default: 50)
2. **Use batch indexing** for large document sets
3. **Enable GPU** for embedding generation
4. **Tune HNSW parameters** (M=16, ef_construction=200)
5. **Use Redis** for distributed caching
6. **Scale horizontally** with load balancer

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Write tests for new features
- Update documentation
- Follow code style guidelines
- Add commit messages that explain *why*
- Keep PRs focused and small

### Reporting Issues

- Use GitHub Issues
- Include reproduction steps
- Provide system information
- Attach relevant logs

---

## 📖 Documentation

### Quick Links

- [Quick Start Guide](QUICK_START.md) - Get started in 5 minutes
- [Deployment Guide](DEPLOYMENT_GUIDE.md) - Production deployment
- [API Reference](QUICK_REFERENCE_RAG_PLUS_PLUS.md) - Complete API docs
- [Architecture Overview](PROJECT_OVERVIEW.md) - System design
- [Operations Guide](OPERATIONS.md) - Day-to-day operations
- [Security Guide](SECURITY.md) - Security best practices

### Recent Updates

- [GUI Full Functionality](GUI_FULL_FUNCTIONALITY_UPGRADE.md) - GUI upgrade details
- [Build Debug Summary](BUILD_DEBUG_SUMMARY.md) - Build verification
- [Bug Fixes](BUG_FIXES_SUMMARY.md) - Recent bug fixes
- [Production Build](PRODUCTION_BUILD_COMPLETE.md) - Production readiness

### Additional Resources

- [Changelog](CHANGELOG.md) - Version history
- [Upgrade Guide](UPGRADE_GUIDE.md) - Migration guides
- [FAQ](docs/) - Frequently asked questions
- [Blog Posts](docs/) - Tutorials and articles

---

## 🔧 Configuration

### Environment Variables

Key configuration options (see `env.example` for complete list):

```bash
# API Keys
DEEPSEEK_API_KEY=sk-your-key-here
API_KEY=your-secure-key

# Operating Mode
SAFE_MODE=0                    # 0=production, 1=safe mode
LLM_STUB=0                     # 0=real API, 1=stub

# Multi-Agent
N_SOLVERS=3                    # Number of solver agents
EVIDENCE_TAU=0.70              # Confidence threshold

# Performance
TOP_K_RETRIEVAL=50             # Initial retrieval count
TOP_K_FINAL=10                 # After reranking

# Security
CORS_ORIGINS=https://yourdomain.com
RATE_LIMIT_RPM=120             # Requests per minute
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **HNSW Algorithm**: [nmslib/hnswlib](https://github.com/nmslib/hnswlib)
- **DeepSeek AI**: LLM and OCR services
- **FastAPI**: Modern Python web framework
- **React**: UI library
- **Contributors**: All contributors who have helped

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/C-AI-BRAIN-2/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/C-AI-BRAIN-2/discussions)
- **Email**: support@example.com
- **Twitter**: [@YourHandle](https://twitter.com/yourhandle)

---

## 🎯 Roadmap

### v5.0 (Next Release)
- [ ] Multi-language support
- [ ] Advanced caching layer
- [ ] GraphQL API
- [ ] Mobile app
- [ ] Plugin system

### v4.4 (Current)
- [x] GUI full functionality
- [x] Production deployment ready
- [x] Comprehensive testing
- [x] Docker optimization

### v4.3 (Previous)
- [x] Enhanced indexing
- [x] Multi-agent orchestration
- [x] OCR integration
- [x] Monitoring & metrics

---

## 📈 Stats

![GitHub Stars](https://img.shields.io/github/stars/yourusername/C-AI-BRAIN-2?style=social)
![GitHub Forks](https://img.shields.io/github/forks/yourusername/C-AI-BRAIN-2?style=social)
![GitHub Issues](https://img.shields.io/github/issues/yourusername/C-AI-BRAIN-2)
![GitHub PRs](https://img.shields.io/github/issues-pr/yourusername/C-AI-BRAIN-2)

---

<div align="center">

**[⬆ Back to Top](#brain-ai-rag-system)**

Made with ❤️ by the Brain-AI Team

</div>
