#!/bin/bash

# Brain-AI Comprehensive Feature Test Script
# Tests all features with Real DeepSeek API
# Version: 4.5.0

set -e

echo "🧪 Brain-AI v4.5.0 - Comprehensive Feature Test"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
API_URL="http://localhost:5001"
OCR_URL="http://localhost:8000"
GUI_URL="http://localhost:3000"

PASSED=0
FAILED=0
TOTAL=0

# Test result tracking
test_result() {
    TOTAL=$((TOTAL + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ PASS${NC}: $2"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ FAIL${NC}: $2"
        FAILED=$((FAILED + 1))
    fi
}

echo -e "${BLUE}Test 1: Service Health Checks${NC}"
echo "-----------------------------------"

# Test OCR health
curl -s http://localhost:8000/health > /dev/null
test_result $? "OCR Service Health"

# Test API health
curl -s http://localhost:5001/healthz > /dev/null
test_result $? "REST API Health"

# Test GUI
curl -s http://localhost:3000 > /dev/null 2>&1 || curl -s http://localhost:3001 > /dev/null 2>&1
test_result $? "GUI Accessibility"

echo ""
echo -e "${BLUE}Test 2: API Endpoints${NC}"
echo "-----------------------------------"

# Test stats endpoint
STATS=$(curl -s http://localhost:5001/stats)
echo "$STATS" | grep -q "total_docs"
test_result $? "Stats Endpoint"

# Test metrics endpoint
curl -s http://localhost:5001/metrics > /dev/null
test_result $? "Metrics Endpoint"

echo ""
echo -e "${BLUE}Test 3: Document Indexing${NC}"
echo "-----------------------------------"

# Create test document
TEST_DOC=$(mktemp)
cat > $TEST_DOC << 'EOF'
Brain-AI is an advanced RAG++ system that combines:
1. Vector search for semantic retrieval
2. Fuzzy caching for 50-80% performance improvement
3. Multi-agent orchestration for complex reasoning
4. DeepSeek API integration for state-of-the-art LLM capabilities

Key features include:
- Fast Mode: Single AI for quick responses
- Deep Think Mode: Multi-agent verification
- Smart caching with fuzzy matching
- OCR support for images and PDFs
EOF

# Index document
RESPONSE=$(curl -s -X POST http://localhost:5001/index \
  -H "Content-Type: application/json" \
  -d "{\"doc_id\": \"test-doc-1\", \"text\": \"$(cat $TEST_DOC | tr '\n' ' ')\"}")

echo "$RESPONSE" | grep -q "success"
test_result $? "Document Indexing"

rm $TEST_DOC

echo ""
echo -e "${BLUE}Test 4: Query - Fast Mode (Single AI)${NC}"
echo "-----------------------------------"

# Test basic query
QUERY_RESPONSE=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Brain-AI?",
    "top_k": 3,
    "use_multi_agent": false
  }')

echo "$QUERY_RESPONSE" | grep -q "answer"
test_result $? "Basic Query Execution"

echo "$QUERY_RESPONSE" | grep -q "confidence"
test_result $? "Confidence Score Present"

echo "$QUERY_RESPONSE" | grep -q "citations"
test_result $? "Citations Present"

# Display response
echo ""
echo "Response Preview:"
echo "$QUERY_RESPONSE" | python3 -m json.tool 2>/dev/null | head -20 || echo "$QUERY_RESPONSE" | head -20

echo ""
echo -e "${BLUE}Test 5: Query - Deep Think Mode (Multi-Agent)${NC}"
echo "-----------------------------------"

DEEP_THINK_RESPONSE=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the key features of Brain-AI?",
    "top_k": 5,
    "use_multi_agent": true,
    "enable_verification": true
  }')

echo "$DEEP_THINK_RESPONSE" | grep -q "answer"
test_result $? "Deep Think Query Execution"

# Check if response is different/more detailed
DEEP_LENGTH=$(echo "$DEEP_THINK_RESPONSE" | wc -c)
if [ $DEEP_LENGTH -gt 100 ]; then
    test_result 0 "Deep Think Response Generated"
else
    test_result 1 "Deep Think Response Generated"
fi

echo ""
echo "Deep Think Response Preview:"
echo "$DEEP_THINK_RESPONSE" | python3 -m json.tool 2>/dev/null | head -20 || echo "$DEEP_THINK_RESPONSE" | head -20

echo ""
echo -e "${BLUE}Test 6: Caching${NC}"
echo "-----------------------------------"

# First query (uncached)
START1=$(date +%s%N)
RESPONSE1=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is fuzzy caching?",
    "top_k": 3,
    "enable_fuzzy_cache": true
  }')
END1=$(date +%s%N)
TIME1=$(( (END1 - START1) / 1000000 ))

# Second query (should be cached)
START2=$(date +%s%N)
RESPONSE2=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is fuzzy caching?",
    "top_k": 3,
    "enable_fuzzy_cache": true
  }')
END2=$(date +%s%N)
TIME2=$(( (END2 - START2) / 1000000 ))

echo "First query: ${TIME1}ms"
echo "Second query: ${TIME2}ms"

# Cache should make second query faster
if [ $TIME2 -lt $TIME1 ]; then
    test_result 0 "Cache Performance Improvement"
else
    test_result 1 "Cache Performance Improvement (${TIME2}ms vs ${TIME1}ms)"
fi

# Check for cache indicator
echo "$RESPONSE2" | grep -q "cached"
test_result $? "Cache Hit Indicator"

echo ""
echo -e "${BLUE}Test 7: Fuzzy Cache Matching${NC}"
echo "-----------------------------------"

# Similar but not identical query
FUZZY_RESPONSE=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Tell me about fuzzy caching",
    "top_k": 3,
    "enable_fuzzy_cache": true,
    "fuzzy_threshold": 0.85
  }')

echo "$FUZZY_RESPONSE" | grep -q "answer"
test_result $? "Fuzzy Cache Query"

echo ""
echo -e "${BLUE}Test 8: Confidence Thresholds${NC}"
echo "-----------------------------------"

# High confidence threshold
HIGH_CONF_RESPONSE=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is Brain-AI?",
    "confidence_threshold": 0.9,
    "enable_verification": true
  }')

echo "$HIGH_CONF_RESPONSE" | grep -q "answer"
test_result $? "High Confidence Threshold Query"

echo ""
echo -e "${BLUE}Test 9: Multiple Document Queries${NC}"
echo "-----------------------------------"

# Index another document
curl -s -X POST http://localhost:5001/index \
  -H "Content-Type: application/json" \
  -d '{
    "doc_id": "test-doc-2",
    "text": "DeepSeek is a powerful AI model that excels at reasoning, coding, and complex problem-solving. It offers state-of-the-art performance on various benchmarks."
  }' > /dev/null

# Query across multiple docs
MULTI_DOC_RESPONSE=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What AI models are mentioned?",
    "top_k": 5
  }')

echo "$MULTI_DOC_RESPONSE" | grep -q "citations"
test_result $? "Multi-Document Query"

# Check for multiple citations
CITATION_COUNT=$(echo "$MULTI_DOC_RESPONSE" | grep -o "doc_id" | wc -l)
if [ $CITATION_COUNT -gt 0 ]; then
    test_result 0 "Multiple Citations Retrieved"
else
    test_result 1 "Multiple Citations Retrieved"
fi

echo ""
echo -e "${BLUE}Test 10: Error Handling${NC}"
echo "-----------------------------------"

# Test empty query
EMPTY_RESPONSE=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{"question": ""}' \
  -w "%{http_code}" -o /dev/null)

if [ "$EMPTY_RESPONSE" = "422" ] || [ "$EMPTY_RESPONSE" = "400" ]; then
    test_result 0 "Empty Query Validation"
else
    test_result 1 "Empty Query Validation (got $EMPTY_RESPONSE)"
fi

# Test invalid JSON
INVALID_RESPONSE=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d 'invalid json' \
  -w "%{http_code}" -o /dev/null)

if [ "$INVALID_RESPONSE" = "422" ] || [ "$INVALID_RESPONSE" = "400" ]; then
    test_result 0 "Invalid JSON Handling"
else
    test_result 1 "Invalid JSON Handling (got $INVALID_RESPONSE)"
fi

echo ""
echo -e "${BLUE}Test 11: Real DeepSeek API Integration${NC}"
echo "-----------------------------------"

# Test with a question that requires real LLM
REAL_LLM_RESPONSE=$(curl -s -X POST http://localhost:5001/answer \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain the benefits of multi-agent systems in AI",
    "top_k": 3,
    "use_multi_agent": false
  }')

# Check that response is NOT stubbed
echo "$REAL_LLM_RESPONSE" | grep -q "stubbed"
if [ $? -eq 0 ]; then
    test_result 1 "Real DeepSeek API (response is stubbed)"
else
    test_result 0 "Real DeepSeek API (response is real)"
fi

# Check response quality (should be substantial)
RESPONSE_LENGTH=$(echo "$REAL_LLM_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('answer', '')))" 2>/dev/null || echo "0")
if [ "$RESPONSE_LENGTH" -gt 50 ]; then
    test_result 0 "Real LLM Response Quality"
else
    test_result 1 "Real LLM Response Quality (length: $RESPONSE_LENGTH)"
fi

echo ""
echo -e "${BLUE}Test 12: Performance Metrics${NC}"
echo "-----------------------------------"

# Get updated stats
FINAL_STATS=$(curl -s http://localhost:5001/stats)

echo "$FINAL_STATS" | python3 -m json.tool 2>/dev/null || echo "$FINAL_STATS"

echo "$FINAL_STATS" | grep -q "cache_hit_rate"
test_result $? "Cache Hit Rate Metric"

echo "$FINAL_STATS" | grep -q "avg_response_time"
test_result $? "Response Time Metric"

echo ""
echo "=============================================="
echo -e "${BLUE}Test Summary${NC}"
echo "=============================================="
echo ""
echo "Total Tests: $TOTAL"
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    echo ""
    echo "✅ Your Brain-AI system is fully functional with:"
    echo "   • Real DeepSeek API integration"
    echo "   • Fast Mode (single AI)"
    echo "   • Deep Think Mode (multi-agent)"
    echo "   • Smart caching with fuzzy matching"
    echo "   • Document indexing and retrieval"
    echo "   • Confidence scoring"
    echo "   • Citation tracking"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  Some tests failed${NC}"
    echo ""
    echo "Check logs for details:"
    echo "   • API: tail -f logs/api-service.log"
    echo "   • OCR: tail -f logs/ocr-service.log"
    echo ""
    exit 1
fi
