# DeepSeek-OCR Service

FastAPI-based OCR service for the Brain-AI document processing pipeline.

## Canonical Contract

| | |
|---|---|
| **Port** | `6001` |
| **Route** | `POST /ocr` |
| **Response keys** | `status`, `text`, `latency_ms` |

## Features

- **OCR Text Extraction**: Extract text from PDFs and images
- **Health Monitoring**: Built-in health check and statistics endpoints
- **Docker Support**: Easy deployment with Docker Compose

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start service
docker-compose up --build -d

# Check health
curl http://localhost:6001/health

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run service (port 6001)
uvicorn app:app --host 0.0.0.0 --port 6001
```

## API Endpoints

### Health Check
```
GET /health
```
Response: `{"status": "healthy", "timestamp": "..."}`

### OCR (canonical)
```
POST /ocr
Content-Type: multipart/form-data
```
Parameters:
- `file`: Document file (required)

Response:
```json
{
  "status": "ok",
  "text": "Extracted text content...",
  "latency_ms": 312
}
```

### Statistics
```
GET /stats
```

## Usage Examples

### Using curl

```bash
# Canonical OCR endpoint
curl -X POST http://localhost:6001/ocr \
  -F "file=@document.pdf"
```

### Using Python

```python
import requests

url = "http://localhost:6001/ocr"

with open("document.pdf", "rb") as f:
    response = requests.post(url, files={"file": f})
    result = response.json()

print(result["text"])    # extracted text
print(result["status"])  # "ok"
print(result["latency_ms"])
```

## Configuration

### Environment Variables

- `LOG_LEVEL`: Logging level (default: info)

## Monitoring

```bash
# Health check
curl http://localhost:6001/health

# Detailed status
curl http://localhost:6001/status
```

## Development

### Mock Implementation

This is currently a **mock implementation** that simulates OCR processing.
For production use, replace the mock functions in `app.py` with actual
DeepSeek OCR model integration.

## Troubleshooting

### Service won't start

```bash
# Check port availability
lsof -i :6001

# Check logs
docker-compose logs ocr-service

# Rebuild container
docker-compose up --build --force-recreate
```

## License

Part of the Brain-AI project.
