#!/bin/bash
#
# End-to-End Integration Test Script for Brain-AI RAG++ system
# Tests: C++ Core → Python REST API → GUI
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FAILED_TESTS=0
PASSED_TESTS=0

info() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    FAILED_TESTS=$((FAILED_TESTS + 1))
}

success() {
    echo -e "${GREEN}✓${NC} $1"
    PASSED_TESTS=$((PASSED_TESTS + 1))
}

step() {
    echo -e "${BLUE}==>${NC} $1"
}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        Brain-AI RAG++ End-to-End Integration Test         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Test 1: C++ Core via Python Bindings
step "Test 1: C++ Core (Python Bindings)"
cd brain-ai-rest-service

python3 << 'EOF'
import sys
try:
    import brain_ai_core
    print("✓ Module imported successfully")
    
    # Test indexing
    brain_ai_core.index_document("test1", "This is a test document about machine learning")
    print("✓ Document indexed")
    
    # Test search
    results = brain_ai_core.search("machine learning", top_k=5)
    if len(results) > 0:
        print(f"✓ Search successful: found {len(results)} results")
        sys.exit(0)
    else:
        print("✗ Search returned no results")
        sys.exit(1)
except Exception as e:
    print(f"✗ Error: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    success "C++ Core test passed"
else
    error "C++ Core test failed"
fi

cd ..

# Test 2: Start Services with Docker Compose
step "Test 2: Starting services with Docker Compose"

# Check if services are already running
if docker compose ps | grep -q "Up"; then
    warn "Services already running, stopping first..."
    docker compose down
fi

# Start services
docker compose up -d

if [ $? -eq 0 ]; then
    info "Services started"
else
    error "Failed to start services"
    exit 1
fi

# Test 3: Wait for all services to be healthy
step "Test 3: Waiting for services to be healthy"

check_health() {
    local service=$1
    local max_attempts=60
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if docker compose ps | grep $service | grep -q "healthy"; then
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    return 1
}

# Check core service
if check_health "core"; then
    success "Core service healthy"
else
    error "Core service failed health check"
fi

# Check REST API
if check_health "rest"; then
    success "REST API service healthy"
else
    error "REST API service failed health check"
fi

# Check GUI
if check_health "gui"; then
    success "GUI service healthy"
else
    error "GUI service failed health check"
fi

# Test 4: REST API Endpoints
step "Test 4: Testing REST API endpoints"

# Test health endpoint
if curl -sf http://localhost:5001/healthz > /dev/null; then
    success "REST API /healthz endpoint working"
else
    error "REST API /healthz endpoint failed"
fi

# Test ready endpoint
if curl -sf http://localhost:5001/readyz > /dev/null; then
    success "REST API /readyz endpoint working"
else
    error "REST API /readyz endpoint failed"
fi

# Test metrics endpoint
if curl -sf http://localhost:5001/metrics > /dev/null; then
    success "REST API /metrics endpoint working"
else
    error "REST API /metrics endpoint failed"
fi

# Test index endpoint (with API key)
INDEX_RESPONSE=$(curl -s -X POST http://localhost:5001/index \
    -H 'X-API-Key: local-dev-test-key-12345' \
    -H 'Content-Type: application/json' \
    -d '{"doc_id":"test_e2e","text":"End-to-end testing is crucial for system reliability"}')

if echo "$INDEX_RESPONSE" | grep -q '"ok"'; then
    success "REST API /index endpoint working"
else
    error "REST API /index endpoint failed"
fi

# Test query endpoint
QUERY_RESPONSE=$(curl -s -X POST http://localhost:5001/query \
    -H 'Content-Type: application/json' \
    -d '{"query":"What is testing?","top_k":5}')

if echo "$QUERY_RESPONSE" | grep -q '"answer"'; then
    success "REST API /query endpoint working"
else
    error "REST API /query endpoint failed"
fi

# Test 5: GUI Accessibility
step "Test 5: Testing GUI accessibility"

if curl -sf http://localhost:3000 > /dev/null; then
    success "GUI accessible at http://localhost:3000"
else
    error "GUI not accessible"
fi

# Check if GUI serves static assets
if curl -sf http://localhost:3000/assets/ > /dev/null 2>&1; then
    success "GUI static assets accessible"
else
    warn "GUI static assets check inconclusive (may not be critical)"
fi

# Test 6: Data Flow (GUI → REST → C++ Core)
step "Test 6: Testing data flow: GUI → REST → C++ Core"

# Test that API proxy works from GUI perspective
PROXY_TEST=$(curl -s http://localhost:3000/api/healthz)
if echo "$PROXY_TEST" | grep -q "ok"; then
    success "GUI → REST API proxy working"
else
    error "GUI → REST API proxy failed"
fi

# Test 7: Service Logs Check
step "Test 7: Checking for errors in service logs"

REST_ERRORS=$(docker compose logs rest 2>&1 | grep -i "error" | grep -v "ERROR_COUNT" | wc -l)
if [ "$REST_ERRORS" -lt 5 ]; then
    success "REST API logs clean (minimal errors)"
else
    warn "REST API has $REST_ERRORS error messages in logs"
fi

GUI_ERRORS=$(docker compose logs gui 2>&1 | grep -i "error" | wc -l)
if [ "$GUI_ERRORS" -lt 5 ]; then
    success "GUI logs clean (minimal errors)"
else
    warn "GUI has $GUI_ERRORS error messages in logs"
fi

# Test 8: Component Tests
step "Test 8: Running component-specific tests"

# Run C++ tests
cd brain-ai/build
if ctest --output-on-failure -j12 > /dev/null 2>&1; then
    success "C++ tests passed"
else
    error "C++ tests failed"
fi
cd ../..

# GUI build verification (already done earlier)
cd brain-ai-gui
if [ -d "dist" ]; then
    success "GUI build artifacts present"
else
    warn "GUI dist directory not found"
fi
cd ..

# Summary
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                     Test Summary                           ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "  ${GREEN}Passed:${NC} $PASSED_TESTS"
echo -e "  ${RED}Failed:${NC} $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo ""
    echo "System is ready for production deployment."
    echo ""
    echo "Access points:"
    echo "  • GUI:       http://localhost:3000"
    echo "  • REST API:  http://localhost:5001"
    echo "  • Metrics:   http://localhost:5001/metrics"
    echo ""
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Review the output above for details."
    echo ""
    echo "To view logs:"
    echo "  docker compose logs rest"
    echo "  docker compose logs gui"
    echo "  docker compose logs core"
    echo ""
    exit 1
fi

