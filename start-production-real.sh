#!/bin/bash

# Brain-AI Production Start with Real DeepSeek API
# Version: 4.5.0

set -e

echo "🚀 Starting Brain-AI v4.5.0 with Real DeepSeek API"
echo "=================================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Load production environment
if [ -f .env.production.real ]; then
    export $(cat .env.production.real | grep -v '^#' | xargs)
    echo -e "${GREEN}✅ Loaded production environment${NC}"
else
    echo -e "${YELLOW}⚠️  .env.production.real not found, using defaults${NC}"
fi

# Verify API key
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "❌ Error: DEEPSEEK_API_KEY not set"
    exit 1
fi
echo -e "${GREEN}✅ DeepSeek API key configured${NC}"

# Stop any existing services
echo ""
echo -e "${BLUE}Stopping existing services...${NC}"
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "uvicorn.*5001" 2>/dev/null || true
pkill -f "vite.*3000" 2>/dev/null || true
sleep 2

# Create log directory
mkdir -p logs
echo -e "${GREEN}✅ Log directory ready${NC}"

echo ""
echo -e "${BLUE}Starting services with REAL DeepSeek API...${NC}"
echo ""

# Start OCR Service (with real API)
echo "Starting OCR Service..."
cd brain-ai/deepseek-ocr-service
DEEPSEEK_OCR_MOCK_MODE=false \
  DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY \
  python3 -m uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 2 \
  > ../../logs/ocr-service.log 2>&1 &
OCR_PID=$!
echo -e "${GREEN}✅ OCR Service started (PID: $OCR_PID)${NC}"
cd ../..

# Wait for OCR
sleep 3

# Start REST API (with real LLM)
echo "Starting REST API..."
cd brain-ai-rest-service
SAFE_MODE=false \
  LLM_STUB=false \
  DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY \
  DEEPSEEK_MODEL=deepseek-chat \
  REQUIRE_API_KEY_FOR_WRITES=false \
  python3 -m uvicorn app.app:app \
  --host 0.0.0.0 \
  --port 5001 \
  --workers 2 \
  > ../logs/api-service.log 2>&1 &
API_PID=$!
echo -e "${GREEN}✅ REST API started (PID: $API_PID)${NC}"
cd ..

# Wait for API
sleep 3

# Start GUI
echo "Starting GUI..."
cd brain-ai-gui
VITE_API_URL=http://localhost:5001 \
  npm run dev > ../logs/gui-service.log 2>&1 &
GUI_PID=$!
echo -e "${GREEN}✅ GUI started (PID: $GUI_PID)${NC}"
cd ..

# Save PIDs
cat > brain-ai-production.pids << EOF
OCR_PID=$OCR_PID
API_PID=$API_PID
GUI_PID=$GUI_PID
EOF

echo ""
echo -e "${BLUE}Waiting for services to be ready...${NC}"
sleep 5

# Health checks
echo ""
echo -e "${BLUE}Running health checks...${NC}"

# Check OCR
echo -n "OCR Service: "
if curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Not responding${NC}"
fi

# Check API
echo -n "REST API: "
if curl -s http://localhost:5001/healthz > /dev/null; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Not responding${NC}"
fi

# Check GUI
echo -n "GUI: "
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Healthy${NC}"
elif curl -s http://localhost:3001 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Healthy (port 3001)${NC}"
else
    echo -e "${YELLOW}⚠️  Not responding yet (may take a moment)${NC}"
fi

echo ""
echo "=================================================="
echo -e "${GREEN}🎉 Brain-AI Production Started!${NC}"
echo "=================================================="
echo ""
echo "📊 Service URLs:"
echo "   • GUI:     http://localhost:3000 (or 3001)"
echo "   • API:     http://localhost:5001"
echo "   • API Docs: http://localhost:5001/docs"
echo "   • OCR:     http://localhost:8000"
echo ""
echo "📝 Logs:"
echo "   • OCR: tail -f logs/ocr-service.log"
echo "   • API: tail -f logs/api-service.log"
echo "   • GUI: tail -f logs/gui-service.log"
echo ""
echo "🔑 Using Real DeepSeek API:"
echo "   • Model: deepseek-chat"
echo "   • API Key: ${DEEPSEEK_API_KEY:0:10}...${DEEPSEEK_API_KEY: -4}"
echo ""
echo "🛑 To stop:"
echo "   ./stop-production.sh"
echo ""
echo "✨ Ready to test all features!"
echo ""
