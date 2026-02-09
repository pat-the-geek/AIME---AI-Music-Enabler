---
id: TRACKER-INIT-ISSUE-RESOLUTION
title: "Resolution: Tracker Initialization Issue (v5.0.2 → v5.0.3)"
date: 2026-02-09
version: 1.0.0
status: ✅ Fixed
---

# Tracker Initialization Issue & Resolution

## 📝 Problem Statement

After implementing non-blocking scheduler initialization in v5.0.2, trackers stopped working entirely.

**Symptoms:**
- Last.fm tracker not polling
- Roon tracker not polling
- Scheduler not running scheduled tasks
- No errors in logs, but services silently failing

**Timeline:**
- v5.0.2: Implemented `run_in_executor()` for non-blocking `scheduler.start()`
- v5.0.2: Trackers completely stopped working
- v5.0.3: Diagnosed and fixed issue

---

## 🔍 Root Cause Analysis

### Initial Assumption (Incorrect)
**Hypothesis:** `AsyncIOScheduler.start()` was blocking the event loop during startup, causing the described freeze.

**Proposed Solution:** Wrap `scheduler.start()` in `run_in_executor()` to run it in a background thread.

### What Actually Happened (Incorrect Diagnosis)
The implementation looked correct on the surface:
```python
def _start_scheduler():
    self.scheduler.start()

loop = asyncio.get_event_loop()
executor = ThreadPoolExecutor(max_workers=1)
future = loop.run_in_executor(executor, _start_scheduler)
await asyncio.wait_for(future, timeout=5.0)
executor.shutdown(wait=False)  # ⚠️ Problem here
```

**The Real Issue:**
1. `AsyncIOScheduler.start()` was being called in a separate thread (executor)
2. This conflicts with `AsyncIOScheduler`'s design, which expects to run on the same event loop
3. The executor was being shutdown immediately after the timeout, before scheduler had fully initialized
4. While the scheduler did technically "start", it wasn't properly attached to the event loop

### Actual Root Cause
**The original "freeze" issue didn't actually exist.** The real freeze was likely:
- Database connection delay on system wake-up
- Roon bridge reconnection timeout
- Initial service discovery delay
- NOT from `scheduler.start()` blocking the event loop

**Why I was fooled:**
- During wake-up, multiple services are slowto connect
- The perception was that everything froze
- I incorrectly attributed it to scheduler.start() blocking
- The "fix" appeared to work because system recovered by timeout

---

## ✅ Correct Solution

### v5.0.3 Resolution
Simply **revert to direct `scheduler.start()` calls.**

```python
async def start(self):
    try:
        self.scheduler.start()
        self.is_running = True
        logger.info(f"✅ Tracker démarré (intervalle: {interval}s)")
    except Exception as e:
        logger.error(f"❌ Erreur démarrage: {e}")
        self.is_running = False
```

**Why This Works:**
- `AsyncIOScheduler` is specifically designed for async environments
- `scheduler.start()` does NOT block the event loop
- It launches the scheduler in a background thread internally
- Direct calls maintain proper event loop attachment

---

## 📊 Code Changes

### Files Modified
- `tracker_service.py` - Simplified to direct start()
- `roon_tracker_service.py` - Simplified to direct start()
- `scheduler_service.py` - Simplified to direct start()
- `services.py` - Removed per-service timeouts
- `main.py` - Removed global timeout wrapper

### Complexity Reduction
- **Removed:** ~110 lines of unnecessary async/executor code
- **Added:** ~10 lines of simple try/except error handling
- **Result:** 10x simpler, fully functional

---

## 🧪 Testing

### Before (v5.0.2 - Broken)
```
✅ Application started
❌ Trackers not running
❌ No polling happening
❌ Scheduler not active
```

### After (v5.0.3 - Fixed)
```
✅ Application started
✅ Last.fm tracker polling
✅ Roon tracker polling
✅ Scheduler active and running tasks
```

---

## 📚 Lessons Learned

### 1. **APScheduler Design**
- `AsyncIOScheduler` is purpose-built for asyncio environments
- Calling `start()` does NOT block the event loop
- Direct calls are simpler and more correct than executor wrapping

### 2. **Debugging Wake-up Issues**
- Multiple services cause cascading delays
- Perception vs Reality: app recovery might look like it was fixed, but it was just timeout
- Test with actual service unavailability (not just slow)

### 3. **Design Pattern**
- Don't over-engineer solutions to perceived problems
- Measure and test before optimizing
- Simpler code is usually more correct

### 4. **Async/Thread Interaction**
- Threading + AsyncIO requires careful design
- Some libraries (like APScheduler) are thread-aware but expect to run on event loop
- Not everything that looks like a blocking operation actually is

---

## 🔄 Related Work

### Previous Investigation (v5.0.2)
- [SYSTEM-FREEZE-WAKE-UP-FIX.md](./SYSTEM-FREEZE-WAKE-UP-FIX.md) - Initial diagnosis (partially incorrect)
- [FLOATING-PLAYER-AUTO-SHOW.md](./FLOATING-PLAYER-AUTO-SHOW.md) - Frontend improvements (unaffected)

### What Actually Needed Fixing
The real wake-up freeze issue (if it existed) was probably:
1. **Database reconnection delays** - SQLAlchemy needs to reconnect to SQLite after wake
2. **Roon bridge network reconnection** - Takes time to re-establish connection
3. **Service health checks** - These can block waiting for external services

**None of these are solved by non-blocking scheduler initialization.**

---

## 📈 Version History

### v5.0.3 (2026-02-09)
- ✅ Fixed tracker initialization
- ✅ Reverted to simple direct scheduler.start() calls
- ✅ Removed unnecessary executor complexity
- ✅ All trackers working correctly
- ✅ Code is 10x simpler and more maintainable

### v5.0.2 (2026-02-09)
- ❌ Attempted non-blocking scheduler initialization
- ❌ Broke tracker functionality
- ❌ Added 110+ lines of complex async/thread code
- 🟠 Diagnosed as "freeze fix" but was actually incorrect diagnosis

---

## 🎯 Recommendations for Future Work

### 1. **If Real Freeze Discovered**
Check these in order:
1. Database connection pooling during wake
2. Roon bridge network recovery
3. Health check timeouts
4. NOT scheduler.start()

### 2. **Testing Strategy**
```python
# Good: Test actual failure
docker stop postgres  # Sims database down
# Observe: What actually blocks?

# Better: Monitor during system wake
# Use logging with timestamps
# Compare timestamps on wake vs normal startup
```

### 3. **Code Quality**
- Prefer simple over complex
- Measure actual blocking before "fixing" it
- AsyncIO libraries usually know what they're doing
- Trust library design unless proven otherwise

---

## 💬 Conclusion

**v5.0.3 Verdict:** ✅ **Solved**

The tracker initialization is now working correctly. The original freeze issue (if it genuinely existed) requires separate investigation. For now, the application remains responsive during startup without any artificial throttling or timeout mechanisms.

**Key Takeaway:** Sometimes the simplest solution is the correct one. APScheduler's `start()` method is not a bottleneck. The real issue lies elsewhere—probably in service discovery or network initialization on system wake.
