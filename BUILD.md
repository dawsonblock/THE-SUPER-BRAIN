# Build Instructions

Complete guide for building Brain-AI RAG++ system on different platforms.

## Prerequisites

### All Platforms
- CMake 3.22+
- C++17 compatible compiler (GCC 9+, Clang 10+, MSVC 2019+)
- Python 3.12+
- Node.js 18+ (for GUI)

### Ubuntu/Debian
```bash
sudo apt-get update
sudo apt-get install -y build-essential cmake ninja-build ccache \
    libssl-dev python3-dev python3-pip git curl
```

### macOS
```bash
brew install cmake ninja ccache openssl python@3.12 node
```

### Optional but Recommended
- `ccache` - Speeds up rebuilds significantly
- `ninja` - Faster than make for large projects

## Building the C++ Core

### Quick Build (Recommended)
```bash
cd brain-ai
./build.sh
```

Options:
- `--clean` - Clean build directory before building
- `--debug` - Build with debug symbols
- `--no-tests` - Skip running tests
- `--demo` - Run demo after building

### Manual Build
```bash
cd brain-ai
mkdir -p build && cd build

# Configure
cmake -DCMAKE_BUILD_TYPE=Release \
      -DBUILD_TESTS=ON \
      -DBUILD_PYTHON_BINDINGS=ON \
      -GNinja ..

# Build (use all CPU cores)
ninja -j$(nproc || sysctl -n hw.ncpu)

# Test
ctest --output-on-failure

# Install (optional)
sudo ninja install
```

### Build Options
- `BUILD_TESTS` - Build test suite (default: ON)
- `BUILD_GRPC_SERVICE` - Build gRPC service (default: ON, requires Protobuf)
- `BUILD_PYTHON_BINDINGS` - Build Python bindings (default: ON)
- `USE_SANITIZERS` - Enable address/undefined sanitizers (default: ON in Debug)

### macOS-Specific Notes
The build script automatically detects macOS and:
- Uses `sysctl -n hw.ncpu` instead of `nproc`
- Detects Homebrew OpenSSL path
- Exports `OPENSSL_ROOT_DIR` for CMake

If OpenSSL is not found:
```bash
export OPENSSL_ROOT_DIR=$(brew --prefix openssl@3)
```

## Python Bindings

### Installing Python Module
```bash
cd brain-ai/python
pip install -e .
```

This builds the C++ extension and installs it as a Python package.

### Verifying Installation
```python
import brain_ai_core
print("✓ Python bindings loaded successfully")
```

## REST Service

### Installing Dependencies
```bash
cd brain-ai-rest-service
pip install -r requirements.txt
```

### Running the Service
```bash
# Development mode
uvicorn app.app_v2:app --host 0.0.0.0 --port 5001 --reload

# Production mode
uvicorn app.app_v2:app --host 0.0.0.0 --port 5001 --workers 4
```

### Environment Variables
```bash
export SAFE_MODE=0                # Enable full features
export LLM_STUB=0                 # Use real LLM (requires DEEPSEEK_API_KEY)
export DEEPSEEK_API_KEY=your_key  # DeepSeek API key
export API_KEY=your_secret        # API key for write operations
```

## Frontend GUI

### Installing Dependencies
```bash
cd brain-ai-gui
npm install
```

### Development Server
```bash
npm run dev
```

Visit http://localhost:3000

### Production Build
```bash
npm run build
npm run preview
```

## Docker Build

### Using Docker Compose (Recommended)
```bash
# Enable BuildKit for faster builds
export DOCKER_BUILDKIT=1

# Build and start all services
docker-compose up --build

# Build specific service
docker-compose build rest
```

### Manual Docker Build
```bash
# REST service
docker build -f Dockerfile.rest -t brain-ai-rest:latest .

# Run
docker run -p 5001:5001 -p 9090:9090 brain-ai-rest:latest
```

## Troubleshooting

### CMake Can't Find OpenSSL (macOS)
```bash
export OPENSSL_ROOT_DIR=$(brew --prefix openssl@3)
cmake -DCMAKE_BUILD_TYPE=Release ..
```

### Python Module Not Found
```bash
# Make sure C++ core is built first
cd brain-ai && ./build.sh

# Check build output
ls -la build/python/brain_ai_core*.so

# Install in development mode
cd python && pip install -e .
```

### ccache Not Working
```bash
# Verify ccache is installed
which ccache

# Clear cache if needed
ccache -C
```

### Slow Build Times
- Use Ninja instead of Make: `-GNinja`
- Enable ccache: automatically detected in CMake
- Use parallel builds: `ninja -j$(nproc)`
- Consider using Docker BuildKit caching

### Tests Failing
```bash
# Run specific test
cd brain-ai/build
./tests/brain_ai_tests

# Verbose output
ctest --output-on-failure --verbose
```

## Performance Tips

### C++ Build
1. **Use ccache**: Speeds up incremental builds by 10-50x
2. **Use Ninja**: 20-30% faster than Make
3. **Parallel builds**: Use all CPU cores with `-j$(nproc)`
4. **Release builds**: Add `-DCMAKE_BUILD_TYPE=Release` for optimizations

### Docker Build
1. **Enable BuildKit**: `export DOCKER_BUILDKIT=1`
2. **Use cache mounts**: Already configured in Dockerfiles
3. **Multi-stage builds**: Reduces final image size
4. **Layer caching**: Keep frequently changing files at the end

### Python
1. **Pip cache**: Use `--mount=type=cache,target=/root/.cache/pip` in Docker
2. **Wheel caching**: Speeds up repeated installs
3. **Pre-built wheels**: Install from PyPI when available

## CI/CD

### GitHub Actions
The CI pipeline automatically:
- Runs linters on all code
- Builds C++ on Ubuntu and macOS
- Runs all tests
- Builds Docker images
- Uploads coverage reports

### Pre-commit Hooks
Install pre-commit hooks for automatic code quality checks:
```bash
pip install pre-commit
pre-commit install

# Run manually
pre-commit run --all-files
```

## Additional Resources

- [README.md](README.md) - Project overview
- [docs/](docs/) - Additional documentation
- [QUICK_START.md](QUICK_START.md) - Quick start guide
- [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) - Production deployment

## Need Help?

Check existing documentation or open an issue on GitHub.

