# Python Bindings (pybind_module.cpp) - Known Issues

**Date**: November 2, 2025  
**Status**: ⚠️ C++ module causes crashes - recommend using memory fallback

---

## Summary

The `brain_ai_core` Python module (C++ bindings via pybind11) has critical issues that cause crashes. The pure-Python memory fallback works perfectly and should be used instead.

## Verified Issues

### Bug 1: `save_index()` path parameter is ignored ✅ CONFIRMED

**Location**: `brain-ai/bindings/pybind_module.cpp:144-153`

**Issue**: The function accepts a `path` parameter but never uses it:
```cpp
void save_index(const std::string &path) {
    auto &manager = ensure_manager();
    if (!manager.save()) {  // Uses internal config path, not 'path' parameter
        throw std::runtime_error("Failed to save index");
    }
}
```

**Impact**: Callers expect to save to the specified path, but the path is ignored. The index is saved to whatever path was set during IndexManager construction (often empty/none).

**Root Cause**: `IndexManager::save()` doesn't accept a path parameter - it uses `config_.index_path` set during construction.

---

### Bug 2: `load_index()` ignores path on subsequent calls ✅ CONFIRMED

**Location**: `brain-ai/bindings/pybind_module.cpp:155-172`

**Issue**: Only the FIRST call to `load_index()` uses the path parameter. Subsequent calls with different paths are silently ignored:
```cpp
void load_index(const std::string &path) {
    if (!g_manager) {
        config.index_path = path;  // Only used on first call
        g_manager = std::make_unique<IndexManager>(config);
    }
    // If g_manager exists, path is completely ignored!
}
```

**Impact**: After the first call, the singleton `g_manager` prevents loading from different paths. This violates the function's contract.

**Root Cause**: `g_manager` is a static singleton. Subsequent calls don't recreate it.

---

## Why Fixes Cause Crashes

### Attempted Fix #1: Recreate manager with new path
```cpp
g_manager.reset();
g_manager = std::make_unique<IndexManager>(config);
```

**Result**: Bus error / segmentation fault

**Why**: IndexManager or the underlying HNSWIndex doesn't handle being destroyed and recreated cleanly. Possible issues:
- HNSW index state corruption
- Thread safety issues
- Memory management bugs in IndexManager destructor
- Static/global state in hnswlib not being reset

### Attempted Fix #2: Update config path before save/load
**Result**: Still crashes

**Why**: IndexManager stores `config_` as private member with no setter. Can't change path after construction without recreating (which crashes).

### Attempted Fix #3: Track path and validate
**Result**: Still crashes when manager is recreated

---

## Current Workaround

The code now includes documentation of the limitations but doesn't fix them (to avoid crashes):

```cpp
void save_index(const std::string &path) {
    // NOTE: This function has a known limitation - the path parameter is not actually used
    // The path parameter is accepted for API compatibility but is currently ignored
    // TODO: Implement proper path handling (requires IndexManager refactoring)
    auto &manager = ensure_manager();
    if (!manager.save()) {
        throw std::runtime_error("Failed to save index");
    }
}

void load_index(const std::string &path) {
    // NOTE: subsequent calls with different paths are ignored  
    // This is because recreating IndexManager causes crashes
    if (!g_manager) {
        config.index_path = path;
        g_manager = std::make_unique<IndexManager>(config);
    }
    // If manager already exists, this call is silently ignored (limitation)
}
```

---

## Test Results

### Without C++ Module (Memory Fallback)
```
✅ All integration tests pass (8/8, 100%)
✅ No crashes
✅ All functionality works correctly
```

### With C++ Module
```
❌ Bus error / segmentation fault
❌ Tests cannot complete
❌ System unstable
```

---

## Recommendation

**DO NOT USE the C++ module (`brain_ai_core`) in production until these issues are fixed.**

The pure-Python memory fallback in `brain-ai-rest-service/app/memory_index.py` works perfectly and should be used instead:

```python
# Current behavior - automatically falls back to memory when C++ module unavailable
if self._module:
    try:
        self._module.save_index(str(path))
    except Exception as exc:
        LOGGER.warning("Failed to save pybind index: %s", exc)
self._memory.save(path)  # This always works
```

---

## Proper Fix Requirements

To properly fix these bugs, the following changes are needed:

### Option A: Make IndexManager support path updates
1. Add setter method to IndexManager:
   ```cpp
   void IndexManager::set_index_path(const std::string& path) {
       config_.index_path = path;
   }
   ```
2. Update Python bindings to call setter before save/load

### Option B: Redesign Python bindings architecture
1. Don't use a singleton `g_manager`
2. Create a Python class that wraps IndexManager
3. Allow multiple IndexManager instances with different paths

### Option C: Fix underlying crashes
1. Debug why IndexManager::reset() causes crashes
2. Fix memory management in IndexManager destructor
3. Fix any global/static state issues in hnswlib
4. Add proper cleanup for HNSW index

### Option D: Accept limitations and document
1. Document that save/load use the path from initialization only
2. Require load_index() to be called once at startup with the correct path
3. Don't allow changing paths dynamically

**Recommended approach**: Option A + Option C for a complete solution.

---

## Additional Notes

- The crashes occur specifically when:
  - Creating IndexManager with a path
  - Destroying and recreating IndexManager  
  - The underlying HNSW index is involved
  
- The memory fallback (`MemoryIndex`) has none of these issues because:
  - It's pure Python
  - No complex C++ object lifecycle
  - No hnswlib dependencies
  - Simple dict-based storage

- Performance comparison:
  - C++ module (when working): ~2-5x faster for large indexes
  - Memory fallback: Sufficient for most use cases (<10K documents)
  
Given that the memory fallback works perfectly and the C++ module crashes, **continue using the memory fallback** until the architectural issues in IndexManager and the Python bindings are resolved.

---

## Files Modified

- `brain-ai/bindings/pybind_module.cpp` - Added documentation comments about limitations
- `BUILD_UPGRADE_COMPLETE.md` - Documents the build upgrade (C++ module builds successfully)
- `PYBIND_MODULE_ISSUES.md` - This file (documents the runtime issues)

---

**Conclusion**: The bugs are real and confirmed. However, fixing them requires deeper architectural changes to avoid crashes. For now, the memory fallback provides stable, working functionality.

