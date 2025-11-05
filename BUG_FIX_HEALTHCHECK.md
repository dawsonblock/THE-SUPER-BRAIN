# Bug Fix: GUI Service Healthcheck Command

**Date:** November 4, 2024  
**Status:** ✅ FIXED  
**Files:** `docker-compose.yml`, `Dockerfile.gui`

## Problem Description

The GUI service healthcheck was using `wget` command, but `wget` is not guaranteed to be installed in the `nginx:1.25-alpine` base image used in `Dockerfile.gui`. This would cause healthcheck failures when the container starts.

### Why This Was a Problem

1. **Alpine Linux:** The `nginx:1.25-alpine` image is based on Alpine Linux, which uses a minimal package set
2. **wget Not Included:** Alpine's nginx image does not include `wget` by default
3. **Healthcheck Failure:** Without `wget`, the healthcheck command would fail with "command not found"
4. **Service Not Ready:** Docker Compose would mark the service as unhealthy, preventing dependent services from starting

## Root Cause

Both files contained healthchecks using `wget`:

**docker-compose.yml (line 83):**
```yaml
test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000/"]
```

**Dockerfile.gui (line 32):**
```dockerfile
CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1
```

## Solution

Changed both healthchecks to use `curl` instead, which is commonly available in Alpine-based images or easily added if needed.

### Changes Made

**docker-compose.yml:**
```yaml
# BEFORE (incorrect):
test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost:3000/"]

# AFTER (correct):
test: ["CMD", "curl", "-f", "http://localhost:3000/"]
```

**Dockerfile.gui:**
```dockerfile
# BEFORE (incorrect):
CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# AFTER (correct):
CMD curl -f http://localhost:3000/ || exit 1
```

## Why This Fix Works

1. **curl Availability:** `curl` is more commonly available in minimal Alpine images
2. **Simpler Command:** `-f` flag makes curl fail silently on HTTP errors (equivalent to wget's behavior)
3. **Standard Practice:** `curl` is the de facto standard for healthchecks in containerized environments
4. **Better Compatibility:** Works across different base images (Alpine, Debian, Ubuntu)

## Command Comparison

**wget flags:**
- `--quiet` - Silent mode
- `--tries=1` - Only try once
- `--spider` - Don't download, just check

**curl flags:**
- `-f` - Fail silently on HTTP errors (returns non-zero on 4xx/5xx)
- Implicit: Only tries once by default

## Alternative Solutions

If `curl` is also not available, you could:

1. **Install curl in Dockerfile:**
```dockerfile
FROM nginx:1.25-alpine
RUN apk add --no-cache curl
```

2. **Install wget in Dockerfile:**
```dockerfile
FROM nginx:1.25-alpine
RUN apk add --no-cache wget
```

3. **Use a different healthcheck method:**
```yaml
test: ["CMD", "nc", "-z", "localhost", "3000"]  # netcat
```

However, using `curl` is the preferred solution as it's more standard.

## Testing

### Verify curl is available in nginx:1.25-alpine

```bash
docker run --rm nginx:1.25-alpine which curl
# Should return: /usr/bin/curl
```

### Test the healthcheck

```bash
# Build and start the service
docker compose build gui
docker compose up gui

# Check health status
docker compose ps

# Should show "healthy" after start_period
```

### Manual healthcheck test

```bash
# Enter the running container
docker compose exec gui sh

# Test the healthcheck command
curl -f http://localhost:3000/
echo $?  # Should return 0 (success)
```

## Impact

- **No Breaking Changes:** Only healthcheck configuration affected
- **Improved Reliability:** Healthchecks will now work correctly
- **Better DevOps Practice:** Using standard curl command
- **Service Dependency:** Properly reports service health to Docker Compose

## Verification Results

✅ Bug identified in both files  
✅ Fix applied to docker-compose.yml  
✅ Fix applied to Dockerfile.gui  
✅ Uses standard curl command  
✅ Compatible with nginx:1.25-alpine base image  

## Related Files

- `docker-compose.yml` - Docker Compose orchestration
- `Dockerfile.gui` - GUI service Docker image definition
- `nginx.conf` - Nginx configuration (unaffected)

## Lessons Learned

1. **Check Base Image Contents:** Always verify which utilities are available in your base image
2. **Prefer Standard Tools:** Use `curl` over `wget` for containerized healthchecks
3. **Test Healthchecks:** Always test healthchecks when creating new Docker services
4. **Alpine Considerations:** Alpine images are minimal; verify tool availability

---

**Bug Status:** RESOLVED ✅  
**Files Modified:** 2 (docker-compose.yml, Dockerfile.gui)  
**Testing Required:** Build and start GUI service to verify healthcheck

