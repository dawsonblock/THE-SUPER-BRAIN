# Brain-AI Deployment Checklist

**Version**: 4.5.0  
**Last Updated**: November 6, 2025

## 🎯 Pre-Deployment

### System Requirements
- [ ] CPU: 8+ cores
- [ ] RAM: 16GB+ (32GB recommended)
- [ ] GPU: Optional (NVIDIA CUDA 11.8+ for OCR)
- [ ] Disk: 50GB+ free

### Build Verification
- [ ] C++ core builds: `cd brain-ai && ./build.sh`
- [ ] All tests pass: `cd brain-ai/build && ctest`
- [ ] Smoke tests pass: `./test_smoke.sh`

## 🔧 Configuration

### Production Environment Variables
```bash
DEEPSEEK_OCR_MOCK_MODE=false
DEEPSEEK_OCR_USE_VLLM=true
REQUIRE_API_KEY_FOR_WRITES=true
SAFE_MODE=false
DEEPSEEK_API_KEY=<your-key>
API_KEY=<production-key>
CORS_ORIGINS=https://yourdomain.com
```

### Security
- [ ] API keys generated and secured
- [ ] CORS origins configured
- [ ] Rate limiting enabled

## 🚀 Deployment

### Automated (Recommended)
```bash
./deploy.sh production
curl http://localhost:8000/health
curl http://localhost:5001/healthz
./test_smoke.sh
```

### Manual Steps
1. [ ] Build C++ core
2. [ ] Install Python dependencies
3. [ ] Build GUI
4. [ ] Start OCR service (port 8000)
5. [ ] Start REST API (port 5001)
6. [ ] Start GUI (port 3000)

## ✅ Post-Deployment

### Health Checks
- [ ] OCR service healthy
- [ ] REST API healthy
- [ ] GUI accessible
- [ ] Metrics available

### Functional Tests
- [ ] Document indexing works
- [ ] Query processing works
- [ ] OCR extraction works

### Performance
- [ ] Query p50 < 50ms
- [ ] Query p95 < 100ms
- [ ] CPU < 80%
- [ ] Memory < 80%

## 🔄 Rollback Plan
```bash
docker-compose down
git checkout v4.4.0
cp backup/index.bin data/
./deploy.sh production
```

**Deployed By**: _______________  
**Date**: _______________  
**Status**: ⬜ Success ⬜ Rollback
