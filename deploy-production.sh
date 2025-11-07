#!/bin/bash

# Brain-AI Production Deployment Script
# Version: 4.5.0

set -e  # Exit on error

echo "🚀 Brain-AI v4.5.0 - Production Deployment"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_PORT_OCR=8000
PRODUCTION_PORT_API=5001
PRODUCTION_PORT_GUI=80
PRODUCTION_HOST="0.0.0.0"

# Check if running as root for port 80
if [ "$PRODUCTION_PORT_GUI" -lt 1024 ] && [ "$EUID" -ne 0 ]; then 
   echo -e "${RED}Error: Port $PRODUCTION_PORT_GUI requires root privileges${NC}"
   echo "Run with: sudo ./deploy-production.sh"
   exit 1
fi

echo -e "${BLUE}Step 1: Checking Prerequisites${NC}"
echo "-----------------------------------"

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found${NC}"

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Node.js found${NC}"

# Check required Python packages
echo "Checking Python packages..."
python3 -c "import fastapi" 2>/dev/null || { echo -e "${RED}❌ FastAPI not installed${NC}"; exit 1; }
python3 -c "import uvicorn" 2>/dev/null || { echo -e "${RED}❌ Uvicorn not installed${NC}"; exit 1; }
echo -e "${GREEN}✅ Python packages OK${NC}"
echo ""

echo -e "${BLUE}Step 2: Building Production Assets${NC}"
echo "-----------------------------------"

# Build GUI
echo "Building React GUI..."
cd brain-ai-gui
npm run build
echo -e "${GREEN}✅ GUI built successfully${NC}"
cd ..
echo ""

echo -e "${BLUE}Step 3: Stopping Existing Services${NC}"
echo "-----------------------------------"
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "uvicorn.*5001" 2>/dev/null || true
pkill -f "serve.*dist" 2>/dev/null || true
echo -e "${GREEN}✅ Old services stopped${NC}"
echo ""

echo -e "${BLUE}Step 4: Starting Production Services${NC}"
echo "-----------------------------------"

# Start OCR Service
echo "Starting OCR Service on port $PRODUCTION_PORT_OCR..."
cd brain-ai/deepseek-ocr-service
DEEPSEEK_OCR_MOCK_MODE=true \
  python3 -m uvicorn app.main:app \
  --host $PRODUCTION_HOST \
  --port $PRODUCTION_PORT_OCR \
  --workers 2 \
  > /var/log/brain-ai-ocr.log 2>&1 &
OCR_PID=$!
echo -e "${GREEN}✅ OCR Service started (PID: $OCR_PID)${NC}"
cd ../..

# Wait for OCR to be ready
sleep 3

# Start REST API
echo "Starting REST API on port $PRODUCTION_PORT_API..."
cd brain-ai-rest-service
REQUIRE_API_KEY_FOR_WRITES=false \
  SAFE_MODE=false \
  LLM_STUB=false \
  python3 -m uvicorn app.app:app \
  --host $PRODUCTION_HOST \
  --port $PRODUCTION_PORT_API \
  --workers 4 \
  > /var/log/brain-ai-api.log 2>&1 &
API_PID=$!
echo -e "${GREEN}✅ REST API started (PID: $API_PID)${NC}"
cd ..

# Wait for API to be ready
sleep 3

# Start GUI (using serve for production)
echo "Starting GUI on port $PRODUCTION_PORT_GUI..."
if ! command -v serve &> /dev/null; then
    echo "Installing serve..."
    npm install -g serve
fi

cd brain-ai-gui
serve -s dist -l $PRODUCTION_PORT_GUI > /var/log/brain-ai-gui.log 2>&1 &
GUI_PID=$!
echo -e "${GREEN}✅ GUI started (PID: $GUI_PID)${NC}"
cd ..

echo ""
echo -e "${BLUE}Step 5: Health Checks${NC}"
echo "-----------------------------------"

# Wait for services to fully start
sleep 5

# Check OCR
echo -n "Checking OCR Service... "
if curl -s http://localhost:$PRODUCTION_PORT_OCR/health > /dev/null; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Check API
echo -n "Checking REST API... "
if curl -s http://localhost:$PRODUCTION_PORT_API/healthz > /dev/null; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

# Check GUI
echo -n "Checking GUI... "
if curl -s http://localhost:$PRODUCTION_PORT_GUI > /dev/null; then
    echo -e "${GREEN}✅ Healthy${NC}"
else
    echo -e "${RED}❌ Failed${NC}"
fi

echo ""
echo -e "${BLUE}Step 6: Saving Process IDs${NC}"
echo "-----------------------------------"
cat > brain-ai.pids << EOF
OCR_PID=$OCR_PID
API_PID=$API_PID
GUI_PID=$GUI_PID
EOF
echo -e "${GREEN}✅ PIDs saved to brain-ai.pids${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}🎉 Production Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "📊 Service URLs:"
echo "   • GUI:     http://localhost:$PRODUCTION_PORT_GUI"
echo "   • API:     http://localhost:$PRODUCTION_PORT_API"
echo "   • API Docs: http://localhost:$PRODUCTION_PORT_API/docs"
echo "   • OCR:     http://localhost:$PRODUCTION_PORT_OCR"
echo ""
echo "📝 Logs:"
echo "   • OCR: /var/log/brain-ai-ocr.log"
echo "   • API: /var/log/brain-ai-api.log"
echo "   • GUI: /var/log/brain-ai-gui.log"
echo ""
echo "🛑 To stop services:"
echo "   ./stop-production.sh"
echo ""
echo "📊 To view logs:"
echo "   tail -f /var/log/brain-ai-*.log"
echo ""
