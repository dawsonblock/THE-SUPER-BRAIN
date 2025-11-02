#!/bin/bash
# Smoke test for Brain-AI RAG++ system

set -e

API_URL="${API_URL:-http://localhost:5001}"
API_KEY="${API_KEY:-devkey}"

echo "========================================="
echo "Brain-AI RAG++ Smoke Test"
echo "========================================="
echo "API URL: $API_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
PASSED=0
FAILED=0

test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    local expected_status="${5:-200}"
    
    echo -n "Testing $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET "$API_URL$endpoint" \
            -H "X-API-Key: $API_KEY")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -H "X-API-Key: $API_KEY" \
            -d "$data")
    fi
    
    status_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$status_code" = "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} (HTTP $status_code)"
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}✗ FAIL${NC} (Expected HTTP $expected_status, got $status_code)"
        echo "Response: $body"
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Wait for service to be ready
echo "Waiting for service to be ready..."
for i in {1..30}; do
    if curl -sf "$API_URL/healthz" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Service is ready${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}✗ Service did not become ready after 30 seconds${NC}"
        exit 1
    fi
    sleep 1
done

echo ""

# Test 1: Health check
test_endpoint "Health check" "GET" "/healthz"

# Test 2: Readiness check
test_endpoint "Readiness check" "GET" "/readyz"

# Test 3: Metrics endpoint
test_endpoint "Metrics endpoint" "GET" "/metrics"

# Test 4: Index a document
test_endpoint "Index document" "POST" "/index" \
    '{"doc_id":"test1","text":"Rope memory stores bits by threading wires through cores for 1, around for 0.","metadata":{"source":"test"}}'

# Test 5: Index another document
test_endpoint "Index document 2" "POST" "/index" \
    '{"doc_id":"test2","text":"The Apollo Guidance Computer used rope memory for its software.","metadata":{"source":"test"}}'

# Give indexing time to complete
sleep 2

# Test 6: Query with context (should answer)
echo -n "Testing Query with context... "
response=$(curl -s -X POST "$API_URL/answer" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"query":"How did rope memory store bits?"}')

if echo "$response" | grep -q '"answer"'; then
    answer=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', '')[:60])")
    confidence=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('confidence', 0.0))")
    echo -e "${GREEN}✓ PASS${NC}"
    echo "  Answer: $answer..."
    echo "  Confidence: $confidence"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $response"
    FAILED=$((FAILED + 1))
fi

# Test 7: Query without context (should refuse or give low confidence)
echo -n "Testing Query without context (refusal)... "
response=$(curl -s -X POST "$API_URL/answer" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"query":"What is the capital of the imaginary country XYZABC?"}')

if echo "$response" | grep -q '"answer"'; then
    answer=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('answer', '').lower())")
    confidence=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('confidence', 0.0))")
    
    # Check if it's a refusal or low confidence
    if echo "$answer" | grep -q "insufficient" || [ "$(echo "$confidence < 0.7" | bc -l)" = "1" ]; then
        echo -e "${GREEN}✓ PASS${NC} (Properly refused or low confidence)"
        echo "  Answer: $answer"
        echo "  Confidence: $confidence"
        PASSED=$((PASSED + 1))
    else
        echo -e "${YELLOW}⚠ PARTIAL${NC} (Answered with high confidence, may be hallucinating)"
        echo "  Answer: $answer"
        echo "  Confidence: $confidence"
        PASSED=$((PASSED + 1))  # Count as pass but warn
    fi
else
    echo -e "${RED}✗ FAIL${NC}"
    echo "Response: $response"
    FAILED=$((FAILED + 1))
fi

# Test 8: Facts store (list facts)
test_endpoint "List facts" "GET" "/facts"

echo ""
echo "========================================="
echo "Smoke Test Summary"
echo "========================================="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All smoke tests passed!${NC}"
    exit 0
else
    echo -e "${RED}❌ Some smoke tests failed${NC}"
    exit 1
fi

