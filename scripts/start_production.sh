#!/bin/bash
# Production startup script for Brain-AI RAG++

set -e

echo "========================================="
echo "Brain-AI RAG++ Production Startup"
echo "========================================="

# Check required environment variables
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo "ERROR: DEEPSEEK_API_KEY environment variable not set"
    echo "Please set it before starting:"
    echo "  export DEEPSEEK_API_KEY=your-api-key"
    exit 1
fi

# Set defaults
export SAFE_MODE="${SAFE_MODE:-0}"
export LLM_STUB="${LLM_STUB:-0}"
export EVIDENCE_TAU="${EVIDENCE_TAU:-0.70}"
export N_SOLVERS="${N_SOLVERS:-3}"
export MULTI_AGENT_ENABLED="${MULTI_AGENT_ENABLED:-true}"
export REASONING_MODEL="${REASONING_MODEL:-deepseek-r1}"
export CHAT_MODEL="${CHAT_MODEL:-deepseek-chat}"
export SOLVER_MODEL="${SOLVER_MODEL:-deepseek-chat}"
export API_KEY="${API_KEY:-$(openssl rand -hex 32)}"

echo "Configuration:"
echo "  SAFE_MODE: $SAFE_MODE"
echo "  LLM_STUB: $LLM_STUB"
echo "  EVIDENCE_TAU: $EVIDENCE_TAU"
echo "  N_SOLVERS: $N_SOLVERS"
echo "  MULTI_AGENT_ENABLED: $MULTI_AGENT_ENABLED"
echo "  REASONING_MODEL: $REASONING_MODEL"
echo "  CHAT_MODEL: $CHAT_MODEL"
echo "  API_KEY: [REDACTED]"
echo ""

# Create data directory
mkdir -p data

# Build C++ core
echo "Building C++ core..."
cd brain-ai
if [ ! -d "build" ]; then
    mkdir build
fi
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_PYTHON_BINDINGS=ON ..
make -j$(nproc)

# Run tests (optional, comment out for faster startup)
echo "Running C++ tests..."
ctest --output-on-failure || {
    echo "WARNING: Some tests failed. Continuing anyway..."
}

cd ../..

# Import Python module (check if it works)
echo "Checking Python bindings..."
python3 -c "import sys; sys.path.insert(0, 'brain-ai/build'); import brain_ai_py; print('✓ brain_ai_py imported')" || {
    echo "ERROR: Failed to import brain_ai_py"
    exit 1
}

# Start REST service
echo "Starting REST service..."
cd brain-ai-rest-service

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Add C++ build directory to Python path
export PYTHONPATH="$PWD/../brain-ai/build:$PYTHONPATH"

echo ""
echo "========================================="
echo "Starting FastAPI server on port 5001"
echo "Metrics available on port 9090"
echo "========================================="
echo ""

# Start uvicorn
exec uvicorn app.app_v2:app \
    --host 0.0.0.0 \
    --port 5001 \
    --log-level info \
    --access-log

