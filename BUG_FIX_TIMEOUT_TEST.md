# Bug Fix: OCR Integration Test Timeout Duration

**Date:** November 4, 2024  
**Status:** ✅ FIXED  
**Test:** `test_service_timeout` in `test_ocr_integration.cpp`

## Problem Description

The `test_service_timeout` test is designed to verify that timeout handling works correctly by deliberately triggering a timeout condition. However, the test was using `std::chrono::seconds(1)` (1 second timeout), which was too long to reliably trigger a timeout.

### Why This Was a Problem

1. **Test Purpose Defeated:** A 1-second timeout gives a local OCR service plenty of time to respond successfully
2. **Unreliable Test:** The test might pass or fail randomly depending on service response time
3. **False Positive:** If the service responds within 1 second, the test incorrectly fails with "Timeout was expected but request succeeded"

## Root Cause

The `OCRConfig` structure has multiple timeout fields:
- `timeout` - Overall request timeout (type: `std::chrono::seconds`)
- `connect_timeout` - TCP connection timeout (type: `std::chrono::milliseconds`)
- `read_timeout` - Read operation timeout (type: `std::chrono::milliseconds`)

The test was incorrectly using the coarse-grained `timeout` field (seconds) instead of the fine-grained millisecond fields.

## Solution

Changed the test to use millisecond-precision timeout fields with extremely short values:

```cpp
// BEFORE (incorrect):
config.timeout = std::chrono::seconds(1);  // Too long!

// AFTER (correct):
config.connect_timeout = std::chrono::milliseconds(1);  // 1ms connect timeout
config.read_timeout = std::chrono::milliseconds(1);     // 1ms read timeout
```

## Why This Fix Works

1. **Reliably Triggers Timeout:** Even the fastest local service cannot complete a health check in 1ms
2. **Tests Timeout Logic:** Now actually tests the timeout exception handling path
3. **Predictable Behavior:** Test will consistently behave the same way across different environments

## Testing

### Compilation
```bash
cd brain-ai/build
make brain_ai_ocr_integration_tests -j12
```
✅ **Result:** Compiles successfully

### Execution
```bash
cd brain-ai/build
ctest --output-on-failure -R OCRIntegrationTests
```
✅ **Result:** Test passes (100% success rate)

## Code Changes

**File:** `brain-ai/tests/integration/test_ocr_integration.cpp`  
**Lines:** 388-413

```diff
 // Test 9: Service timeout handling
 bool test_service_timeout() {
     // This test uses a very short timeout to trigger timeout handling
     OCRConfig config;
     config.service_url = OCR_SERVICE_URL;
-    config.timeout = std::chrono::seconds(1);  // 1s timeout (OCRConfig.timeout is std::chrono::seconds)
+    // Use extremely short millisecond-level timeouts to reliably trigger timeout condition
+    config.connect_timeout = std::chrono::milliseconds(1);  // 1ms connect timeout
+    config.read_timeout = std::chrono::milliseconds(1);     // 1ms read timeout
     
     try {
         OCRClient client(config);
         
-        // Service might not be available or timeout is too short
-        // Either way, we're testing the timeout mechanism
+        // With 1ms timeouts, this should trigger a timeout exception
+        // even for a local service
         client.check_health();
```

## Impact

- **No Breaking Changes:** Only test code affected
- **Improved Test Reliability:** Test now correctly validates timeout handling
- **Better Test Coverage:** Actually exercises the timeout exception path

## Related Configuration

For reference, the `OCRConfig` structure (`brain-ai/include/document/ocr_client.hpp`):

```cpp
struct OCRConfig {
    std::string service_url = "http://deepseek-ocr:8000";
    std::chrono::seconds timeout{30};                   // Overall request timeout
    std::chrono::milliseconds connect_timeout{1000};    // TCP connect timeout
    std::chrono::milliseconds read_timeout{5000};       // Read timeout
    std::chrono::milliseconds write_timeout{5000};      // Write timeout
    // ... other fields
};
```

## Lessons Learned

1. **Choose Appropriate Timeout Precision:** Use milliseconds for tests that need to trigger quickly
2. **Test What You Intend:** Timeout tests should use timeouts short enough to actually trigger
3. **Document Test Intent:** Clear comments help future developers understand the test's purpose

## Verification

✅ Code compiles without errors  
✅ Test passes consistently  
✅ All other OCR integration tests still pass  
✅ No regression in test suite (6/6 tests passing)

---

**Bug Status:** RESOLVED ✅

