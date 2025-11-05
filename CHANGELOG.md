# Changelog

All notable changes to the Brain-AI RAG++ project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.4.0] - 2024-11-04

### Added
- **GUI Full Functionality**: Complete React/TypeScript GUI with all features operational
- **Production Deployment Infrastructure**: Docker Compose with all services (core, REST, GUI, OCR)
- **Local Development Script**: `start_dev.sh` for one-command startup with hot reload
- **End-to-End Testing**: `test_e2e_full.sh` comprehensive integration test suite
- **Deployment Guide**: Complete deployment documentation for all scenarios
- **API Endpoint Alias**: `/answer` endpoint as alias to `/query` for GUI compatibility
- **Enhanced Documentation**: GitHub-ready README.md with badges and comprehensive guides

### Fixed
- **GUI Healthcheck**: Changed from `wget` to `curl` in `docker-compose.yml` and `Dockerfile.gui`
- **API Endpoint Mismatch**: Added `/answer` endpoint to match GUI expectations
- **OCR Test Timeout**: Fixed timeout test to use millisecond precision for reliable testing
- **Index Manager Contract**: Corrected return value in `load_from()` for empty state initialization
- **GUI Dependencies**: Added missing dependencies (lucide-react, clsx, tailwind-merge)
- **Build Configuration**: Added hnswlib include paths to brain_ai_demo target

### Changed
- **Docker Compose**: Added GUI service with nginx and proper health checks
- **Nginx Configuration**: Created production-ready nginx.conf with API proxy
- **Environment Configuration**: Enhanced .env with comprehensive local dev defaults
- **Quick Start Guide**: Updated with three deployment options and clear instructions

### Security
- **CORS Configuration**: Explicit CORS setup for localhost and production domains
- **API Key Management**: Improved key storage and validation
- **Rate Limiting**: Configured per-client rate limits (120 req/min)

## [4.3.0] - 2024-10-15

### Added
- **Enhanced Indexing**: IndexManager with save/load functionality and atomic operations
- **Multi-Agent Orchestration**: N-solver agents with confidence voting and verification
- **Document Processing Pipeline**: OCR integration with DeepSeek-OCR service
- **Advanced Re-ranking**: Cross-encoder for precision refinement
- **Facts Store**: SQLite-backed knowledge persistence with access tracking

### Fixed
- **IndexManager Deadlocks**: Resolved deadlocks in save_as() and load_from() methods
- **Data Loss Prevention**: Added state rollback on load failure
- **Metadata Handling**: Fixed silent failures and missing metadata file handling
- **Test Path Issues**: Corrected hardcoded absolute paths in test scripts

### Changed
- **Vector Search**: Optimized HNSW parameters (M=16, ef_construction=200)
- **Embedding Dimension**: Configurable 384/768-dim embeddings
- **Index Persistence**: Auto-save every N documents with atomic writes

## [4.2.0] - 2024-09-20

### Added
- **OCR Integration**: DeepSeek-OCR service for document text extraction
- **Document Validation**: Text quality validation and error handling
- **OCR Client**: Robust HTTP client with retry logic and timeouts
- **Integration Tests**: Comprehensive OCR integration test suite

### Fixed
- **OCR Service Timeout**: Proper handling of service timeouts and failures
- **HTTP Client**: Connection pooling and keep-alive configuration
- **Error Messages**: Improved error reporting and debugging information

## [4.1.0] - 2024-08-15

### Added
- **HNSW Vector Search**: High-performance approximate nearest neighbor search
- **Index Statistics**: Comprehensive metrics and health reporting
- **Search Parameters**: Configurable ef_search for precision/recall tradeoff
- **Metadata Storage**: JSON metadata support for documents

### Fixed
- **Memory Leaks**: Resolved memory management issues in C++ core
- **Thread Safety**: Added mutex protection for concurrent operations
- **Index Corruption**: Atomic operations for index persistence

## [4.0.1] - 2024-07-10

### Added
- **Production Monitoring**: Prometheus metrics integration
- **Health Checks**: Comprehensive health and readiness endpoints
- **Circuit Breaker**: Automatic failure recovery with configurable thresholds
- **Structured Logging**: JSON logs with context and correlation IDs

### Fixed
- **Resource Leaks**: Fixed file descriptor and memory leaks
- **Error Handling**: Improved exception handling and error recovery
- **Configuration**: Validated config on startup with clear error messages

### Security
- **API Key Authentication**: Required for write operations
- **Kill Switch**: Emergency shutdown mechanism
- **Input Validation**: Comprehensive request validation and sanitization

## [4.0.0] - 2024-06-01

### Added
- **C++ Core Engine**: High-performance C++ implementation with Python bindings
- **FastAPI REST Service**: Modern async Python web service
- **LLM Integration**: DeepSeek AI models (R1, Chat, V3)
- **React GUI Foundation**: Basic TypeScript/React interface
- **Docker Support**: Containerized deployment with Docker Compose
- **Evidence Gating**: Confidence-based answer filtering
- **Semantic Network**: Knowledge graph capabilities
- **Episodic Buffer**: Conversation context management
- **Hallucination Detection**: Safety mechanisms for LLM outputs

### Changed
- **Architecture**: Complete rewrite from Python-only to C++/Python hybrid
- **Performance**: 10x improvement in vector search latency
- **Scalability**: Support for 100k+ documents
- **API Design**: RESTful API with standard HTTP patterns

### Deprecated
- **Pure Python Backend**: Replaced with C++ core for performance
- **Old API Endpoints**: Migrated to new RESTful design

## [3.0.0] - 2024-03-15

### Added
- **Initial RAG Implementation**: Basic retrieval-augmented generation
- **Simple Vector Store**: In-memory vector storage
- **Basic LLM Integration**: Initial OpenAI integration
- **Command-Line Interface**: Basic CLI for testing

---

## Version History

- **v4.4.0** - GUI Full Functionality & Production Ready (Current)
- **v4.3.0** - Enhanced Indexing & Multi-Agent
- **v4.2.0** - OCR Integration
- **v4.1.0** - HNSW Vector Search
- **v4.0.1** - Production Monitoring
- **v4.0.0** - C++ Core Engine
- **v3.0.0** - Initial RAG System

---

## Upgrade Guides

- [v4.3 to v4.4](UPGRADE_GUIDE.md#v43-to-v44)
- [v4.2 to v4.3](UPGRADE_GUIDE.md#v42-to-v43)
- [v4.1 to v4.2](UPGRADE_GUIDE.md#v41-to-v42)
- [v4.0 to v4.1](UPGRADE_GUIDE.md#v40-to-v41)
- [v3.x to v4.0](UPGRADE_GUIDE.md#v3x-to-v40)

---

## Support

For questions about specific versions or upgrade paths, please see:
- [Documentation](docs/)
- [GitHub Issues](https://github.com/yourusername/C-AI-BRAIN-2/issues)
- [Upgrade Guide](UPGRADE_GUIDE.md)

