#!/bin/bash
#
# Local Development Startup Script for Brain-AI
# Launches the canonical REST API (app.app_v2) in dev/stub mode.
#
# The C++ core (brain_ai_core) is OPTIONAL acceleration.
# If the native module is not built, the service falls back to an
# in-memory vector index automatically.
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
error() { echo -e "${RED}✗${NC} $1"; exit 1; }
step()  { echo -e "${BLUE}==>${NC} $1"; }

echo "╔════════════════════════════════════════════════════╗"
echo "║   Brain-AI Local Development Environment           ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# ── Install Python deps (once) ────────────────────────────────────────────────
step "Checking Python dependencies..."
cd brain-ai-rest-service
if ! python3 -c "import fastapi" 2>/dev/null; then
    pip3 install -r requirements.txt -q
    info "Python dependencies installed"
else
    info "Python dependencies already present"
fi
cd ..

# ── Data dirs ─────────────────────────────────────────────────────────────────
mkdir -p data logs
info "Data directories ready"

# ── Start REST API ────────────────────────────────────────────────────────────
step "Starting REST API (canonical: app.app_v2)..."
cd brain-ai-rest-service

export PYTHONUNBUFFERED=1
export SAFE_MODE=1
export LLM_STUB=1
export EMBEDDINGS_BACKEND=cpu
export API_KEY="${API_KEY:-devkey}"
export REQUIRE_API_KEY_FOR_WRITES=1
export OCR_URL="${OCR_URL:-http://localhost:6001/ocr}"
export METRICS_ENABLED=1

uvicorn app.app_v2:app \
    --host 0.0.0.0 \
    --port 5001 \
    --reload \
    --log-level info \
    > ../logs/rest-api.log 2>&1 &

REST_PID=$!
cd ..
info "REST API starting (PID: $REST_PID) — logs: logs/rest-api.log"

# ── Wait for readiness ────────────────────────────────────────────────────────
step "Waiting for REST API..."
for i in $(seq 1 30); do
    if curl -s http://localhost:5001/healthz > /dev/null 2>&1; then
        info "REST API is ready!"
        break
    fi
    [ "$i" -eq 30 ] && error "REST API failed to start within 30 s"
    sleep 1
done

# ── (Optional) GUI dev server ─────────────────────────────────────────────────
if [ -d brain-ai-gui ] && command -v npm >/dev/null 2>&1; then
    step "Starting GUI dev server..."
    cd brain-ai-gui
    [ ! -d node_modules ] && npm install
    npm run dev > ../logs/gui-dev.log 2>&1 &
    GUI_PID=$!
    cd ..
    info "GUI dev server starting (PID: $GUI_PID) — logs: logs/gui-dev.log"
else
    GUI_PID=""
    warn "GUI skipped (no npm or brain-ai-gui directory)"
fi

echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║          🚀 Development Environment Ready          ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "  Services:"
echo "    • REST API : http://localhost:5001"
[ -n "$GUI_PID" ] && echo "    • GUI      : http://localhost:3000"
echo "    • Metrics  : http://localhost:5001/metrics"
echo ""
echo "  Dev mode: SAFE_MODE=1  LLM_STUB=1  API_KEY=${API_KEY:-devkey}"
echo "  OCR URL : ${OCR_URL:-http://localhost:6001/ocr}"
echo ""
echo "  Logs:"
echo "    tail -f logs/rest-api.log"
echo ""
echo "  Press Ctrl+C to stop"
echo ""

# Convenience stop script
cat > stop_dev.sh << EOF
#!/bin/bash
kill ${REST_PID} ${GUI_PID} 2>/dev/null && echo "Services stopped" || echo "Nothing to stop"
EOF
chmod +x stop_dev.sh

trap "echo ''; echo 'Shutting down...'; kill ${REST_PID} ${GUI_PID} 2>/dev/null; exit 0" INT TERM
wait ${REST_PID} ${GUI_PID}
