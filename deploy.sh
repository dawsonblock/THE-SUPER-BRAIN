#!/bin/bash
# Brain-AI Production Deployment Script v4.5.0

set -e  # Exit on error

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Brain-AI Deployment Script v4.5.0${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Configuration
DEPLOYMENT_MODE="${1:-production}"  # production, staging, development
SKIP_TESTS="${SKIP_TESTS:-false}"
SKIP_BUILD="${SKIP_BUILD:-false}"

echo -e "${YELLOW}Deployment Mode: ${DEPLOYMENT_MODE}${NC}"
echo ""

# Pre-flight checks
echo -e "${YELLOW}Running pre-flight checks...${NC}"

# Check required tools
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: docker is required${NC}"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Error: docker-compose is required${NC}"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${RED}Error: jq is required${NC}"; exit 1; }

echo -e "${GREEN}✓ All required tools present${NC}"

# Check environment file
if [ "$DEPLOYMENT_MODE" = "production" ]; then
    if [ ! -f ".env.production" ]; then
        echo -e "${RED}Error: .env.production not found${NC}"
        exit 1
    fi
    ENV_FILE=".env.production"
else
    ENV_FILE=".env"
fi

echo -e "${GREEN}✓ Environment file: ${ENV_FILE}${NC}"

# Build C++ core
if [ "$SKIP_BUILD" != "true" ]; then
    echo ""
    echo -e "${YELLOW}Building C++ core...${NC}"
    cd brain-ai
    ./build.sh --no-tests
    cd ..
    echo -e "${GREEN}✓ C++ core built${NC}"
fi

# Run tests
if [ "$SKIP_TESTS" != "true" ]; then
    echo ""
    echo -e "${YELLOW}Running tests...${NC}"
    
    # C++ tests
    echo "Running C++ tests..."
    cd brain-ai/build
    if ctest --output-on-failure; then
        echo -e "${GREEN}✓ C++ tests passed${NC}"
    else
        echo -e "${RED}✗ C++ tests failed${NC}"
        exit 1
    fi
    cd ../..
    
    # Smoke tests
    echo "Running smoke tests..."
    if ./test_smoke.sh; then
        echo -e "${GREEN}✓ Smoke tests passed${NC}"
    else
        echo -e "${RED}✗ Smoke tests failed${NC}"
        exit 1
    fi
fi

# Build Docker images
echo ""
echo -e "${YELLOW}Building Docker images...${NC}"

if [ "$DEPLOYMENT_MODE" = "production" ]; then
    docker-compose build --no-cache
else
    docker-compose build
fi

echo -e "${GREEN}✓ Docker images built${NC}"

# Stop existing services
echo ""
echo -e "${YELLOW}Stopping existing services...${NC}"
docker-compose down
echo -e "${GREEN}✓ Services stopped${NC}"

# Start services
echo ""
echo -e "${YELLOW}Starting services...${NC}"

if [ "$DEPLOYMENT_MODE" = "production" ]; then
    docker-compose --env-file "$ENV_FILE" up -d
else
    docker-compose up -d
fi

echo -e "${GREEN}✓ Services started${NC}"

# Wait for services to be ready
echo ""
echo -e "${YELLOW}Waiting for services to be ready...${NC}"

MAX_WAIT=60
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s -f http://localhost:5001/healthz > /dev/null 2>&1; then
        echo -e "${GREEN}✓ REST service is healthy${NC}"
        break
    fi
    echo -n "."
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ $WAIT_COUNT -ge $MAX_WAIT ]; then
    echo -e "${RED}✗ Services failed to start${NC}"
    docker-compose logs
    exit 1
fi

# Verify deployment
echo ""
echo -e "${YELLOW}Verifying deployment...${NC}"

# Check OCR service
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ OCR service is healthy${NC}"
else
    echo -e "${RED}✗ OCR service is not responding${NC}"
    exit 1
fi

# Check REST service
if curl -s -f http://localhost:5001/healthz > /dev/null 2>&1; then
    echo -e "${GREEN}✓ REST service is healthy${NC}"
else
    echo -e "${RED}✗ REST service is not responding${NC}"
    exit 1
fi

# Display service status
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✅ Deployment Successful!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Services:"
echo "  OCR Service:  http://localhost:8000"
echo "  REST API:     http://localhost:5001"
echo "  GUI:          http://localhost:3000"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop services:"
echo "  docker-compose down"
echo ""
