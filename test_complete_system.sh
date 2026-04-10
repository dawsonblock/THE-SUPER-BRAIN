#!/bin/bash
# Integration test script — tests running services (requires live backend and OCR stub).
# Canonical routes only. Run from repo root after starting services with ./start_dev.sh.

set -e

BASE_URL="${BASE_URL:-http://localhost:5001}"
OCR_URL="${OCR_URL:-http://localhost:6001/ocr}"
API_KEY="${API_KEY:-devkey}"
FAILED=0
PASSED=0

GREEN='[0;32m'
RED='[0;31m'
NC='[0m'

pass() { echo -e "${GREEN}PASS${NC}: $1"; PASSED=$((PASSED+1)); }
fail() { echo -e "${RED}FAIL${NC}: $1"; FAILED=$((FAILED+1)); }

echo "==============================="
echo " Brain-AI Integration Tests"
echo "==============================="

# 1. Health
info=$(curl -sf "$BASE_URL/healthz") && pass "/healthz" || fail "/healthz"

# 2. Readiness
curl -sf "$BASE_URL/readyz" >/dev/null && pass "/readyz" || fail "/readyz"

# 3. Metrics
curl -sf "$BASE_URL/metrics" | grep -q "http_requests_total" && pass "/metrics" || fail "/metrics"

# 4. Index
curl -sf -X POST "$BASE_URL/index" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '''{'doc_id':'t1','text':'Hydrogen is the lightest element.'}''' \
  | grep -q '''"ok":true''' && pass "/index" || fail "/index"

# 5. Answer
curl -sf -X POST "$BASE_URL/answer" \
  -H "Content-Type: application/json" \
  -d '''{'query':'What is the lightest element?'}''' \
  | grep -q '''"answer"''' && pass "/answer" || fail "/answer"

# 6. Facts stats
curl -sf "$BASE_URL/facts/stats" | grep -q '''"count"''' && pass "/facts/stats" || fail "/facts/stats"

echo ""
echo "Results: PASSED=$PASSED FAILED=$FAILED"
[ "$FAILED" -eq 0 ] || exit 1
echo "All tests passed."
