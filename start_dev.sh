#!/bin/bash
#
# Local Development Startup Script for Brain-AI RAG++ system
# Builds C++ core, starts REST API, and starts GUI dev server
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() {
    echo -e "${GREEN}✓${NC} $1"
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

step() {
    echo -e "${BLUE}==>${NC} $1"
}

echo "╔════════════════════════════════════════════════════════════╗"
echo "║     Brain-AI RAG++ Local Development Environment          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    warn ".env file not found, creating from env.example..."
    if [ -f env.example ]; then
        cp env.example .env
        info ".env file created - update with your API keys if needed"
    else
        error "env.example not found"
    fi
fi

# Load environment
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    info "Environment variables loaded from .env"
fi

# Step 1: Build C++ Core
step "Building C++ Core with Python bindings..."
cd brain-ai

if [ ! -d "build" ]; then
    mkdir -p build
fi

cd build

cmake -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_PYTHON_BINDINGS=ON \
      -DBUILD_TESTS=ON \
      -DBUILD_GRPC_SERVICE=OFF \
      -DUSE_SANITIZERS=OFF \
      ..

NUM_CPUS=$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)
make -j${NUM_CPUS}

if [ $? -ne 0 ]; then
    error "C++ build failed"
fi

info "C++ core built successfully"

# Step 2: Run tests quickly
step "Running C++ tests..."
if ! ctest --output-on-failure -j${NUM_CPUS}; then
    warn "Some tests failed, but continuing..."
else
    info "All C++ tests passed"
fi

cd ../..

# Step 3: Copy Python module to REST service
step "Copying Python module to REST service..."
if [ -f "brain-ai/build/python/brain_ai_core.cpython-312-darwin.so" ]; then
    cp brain-ai/build/python/brain_ai_core.cpython-312-darwin.so brain-ai-rest-service/
    info "Python module copied"
elif [ -f "brain-ai/build/python/brain_ai_core.so" ]; then
    cp brain-ai/build/python/brain_ai_core.so brain-ai-rest-service/brain_ai_core.cpython-312-darwin.so
    info "Python module copied"
else
    error "Python module not found in build directory"
fi

# Step 4: Install Python dependencies
step "Installing Python dependencies..."
cd brain-ai-rest-service
if ! pip3 list | grep -q fastapi; then
    pip3 install -r requirements.txt -q
    info "Python dependencies installed"
else
    info "Python dependencies already installed"
fi
cd ..

# Step 5: Install GUI dependencies
step "Installing GUI dependencies..."
cd brain-ai-gui
if [ ! -d "node_modules" ]; then
    npm install
    info "GUI dependencies installed"
else
    info "GUI dependencies already installed"
fi
cd ..

# Step 6: Create data directories
mkdir -p data
info "Data directories ready"

# Step 7: Start services
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                 Starting Services                          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Start REST API in background
step "Starting REST API..."
cd brain-ai-rest-service

# Export environment variables for the service
export PYTHONUNBUFFERED=1
export SAFE_MODE="${SAFE_MODE:-1}"
export LLM_STUB="${LLM_STUB:-1}"
export API_KEY="${API_KEY:-local-dev-test-key-12345}"

uvicorn app:app \
    --host 0.0.0.0 \
    --port 5001 \
    --reload \
    --log-level info \
    > ../logs/rest-api.log 2>&1 &

REST_PID=$!
cd ..

info "REST API started (PID: $REST_PID, logs: logs/rest-api.log)"

# Wait for REST API to be ready
step "Waiting for REST API to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:5001/healthz > /dev/null 2>&1; then
        info "REST API is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        error "REST API failed to start"
    fi
    sleep 1
done

# Start GUI dev server in background
step "Starting GUI dev server..."
cd brain-ai-gui

npm run dev > ../logs/gui-dev.log 2>&1 &
GUI_PID=$!
cd ..

info "GUI dev server started (PID: $GUI_PID, logs: logs/gui-dev.log)"

# Wait for GUI to be ready
step "Waiting for GUI to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:3000 > /dev/null 2>&1; then
        info "GUI is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        warn "GUI may still be starting..."
    fi
    sleep 1
done

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║          🚀 Development Environment Ready! 🚀              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "  ${GREEN}Services Running:${NC}"
echo "    • REST API:  http://localhost:5001"
echo "    • GUI:       http://localhost:3000"
echo "    • Metrics:   http://localhost:5001/metrics"
echo ""
echo "  ${BLUE}API Info:${NC}"
echo "    • Mode: SAFE_MODE=1, LLM_STUB=1 (no real API calls)"
echo "    • API Key: ${API_KEY}"
echo "    • Health: curl http://localhost:5001/healthz"
echo ""
echo "  ${YELLOW}Process IDs:${NC}"
echo "    • REST API: $REST_PID"
echo "    • GUI:      $GUI_PID"
echo ""
echo "  ${YELLOW}Logs:${NC}"
echo "    • REST API: tail -f logs/rest-api.log"
echo "    • GUI:      tail -f logs/gui-dev.log"
echo ""
echo "  ${RED}To Stop:${NC}"
echo "    • kill $REST_PID $GUI_PID"
echo "    • or press Ctrl+C"
echo ""

# Create stop script for convenience
cat > stop_dev.sh << EOF
#!/bin/bash
echo "Stopping development services..."
kill $REST_PID $GUI_PID 2>/dev/null
echo "Services stopped"
EOF
chmod +x stop_dev.sh

info "Created stop_dev.sh for easy shutdown"

# Keep script running and handle Ctrl+C
trap "echo ''; echo 'Shutting down...'; kill $REST_PID $GUI_PID 2>/dev/null; exit 0" INT TERM

echo "Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $REST_PID $GUI_PID

