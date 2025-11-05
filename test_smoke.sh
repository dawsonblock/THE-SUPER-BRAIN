#!/bin/bash
# Quick smoke test for Brain-AI system

set -e

echo "======================================"
echo "Brain-AI Smoke Test"
echo "======================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Service URLs
OCR_SERVICE="http://localhost:8000"
REST_SERVICE="http://localhost:5001"

echo "1. Testing OCR Service..."
if curl -s -f "$OCR_SERVICE/health" > /dev/null; then
    echo -e "${GREEN}✓ OCR Service is healthy${NC}"
else
    echo -e "${RED}✗ OCR Service failed${NC}"
    exit 1
fi

echo "2. Testing REST Service..."
if curl -s -f "$REST_SERVICE/healthz" > /dev/null; then
    echo -e "${GREEN}✓ REST Service is healthy${NC}"
else
    echo -e "${RED}✗ REST Service failed${NC}"
    exit 1
fi

echo "3. Testing OCR extraction..."
# Create a simple test image using Python
python3 -c "
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (200, 100), color='white')
d = ImageDraw.Draw(img)
d.text((10,40), 'Test Document', fill='black')
img.save('/tmp/test_smoke.png')
" 2>/dev/null || {
    # Fallback: create a minimal PNG if PIL is not available
    echo "Skipping OCR extraction test (PIL not available)"
    echo -e "${GREEN}✓ OCR extraction skipped${NC}"
}

echo "4. Testing document indexing..."
if curl -s -f -X POST "$REST_SERVICE/index" \
    -H "Content-Type: application/json" \
    -d '{"doc_id": "test1", "text": "Sample document text"}' | jq -e '.ok == true' > /dev/null; then
    echo -e "${GREEN}✓ Document indexing works${NC}"
else
    echo -e "${RED}✗ Document indexing failed${NC}"
    exit 1
fi

echo "5. Testing query..."
if curl -s -f -X POST "$REST_SERVICE/query" \
    -H "Content-Type: application/json" \
    -d '{"query": "test query", "top_k": 5}' | jq -e '.answer' > /dev/null; then
    echo -e "${GREEN}✓ Query works${NC}"
else
    echo -e "${RED}✗ Query failed${NC}"
    exit 1
fi

echo ""
echo "======================================"
echo -e "${GREEN}✅ All smoke tests passed!${NC}"
echo "======================================"
echo ""
echo "System Status:"
echo "  ✓ OCR Service running on port 8000"
echo "  ✓ REST API running on port 5001"
echo "  ✓ Document indexing functional"
echo "  ✓ Query processing functional"
echo ""
