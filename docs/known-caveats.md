# Known Caveats & Technical Debt

This document tracks known limitations, potential issues, and technical debt in the codebase.

---

## Table of Contents

1. [Middleware In-Memory State (LangGraph Persistence)](#1-middleware-in-memory-state-langgraph-persistence)

---

## 1. Middleware In-Memory State (LangGraph Persistence)

**Status:** Acceptable for single-session CLI use
**Risk:** Medium (if adding server mode or crash recovery)
**File:** `ax_advanced_class/src/middleware/tool_validation_middleware.py`

### Problem

The `ToolValidationMiddleware` uses an in-memory dict to track file reads:

```python
self._read_files: dict[str, float] = {}  # IN-MEMORY ONLY
```

This field is used for:
- **Read-before-write/edit check**: Ensures files are read before being modified
- **Stale read detection**: Detects if a file was modified externally since last read

### Current Behavior

| Scenario | Result |
|----------|--------|
| Read → Edit (same session) | ✅ Works |
| Read → Interrupt → Resume → Edit | ✅ Works |
| Read → **Process restart** → Edit | ❌ Fails with "must read first" |

**Why interrupts are safe:** Tracking happens AFTER `interrupt()` points in the code flow, so no double-execution bug.

### When This Becomes a Problem

- Long-running server with restarts/deployments
- Serverless functions (Lambda, Cloud Functions)
- Multi-process architecture
- Crash recovery scenarios

### Future Solutions

| Option | Approach | Tradeoff |
|--------|----------|----------|
| **1. LangGraph State** | Move to graph state schema | Requires schema changes |
| **2. File-Based** | Save to JSON or external file per thread_id | Manual save/load |
| **3. Rebuild from History** | Scan messages on startup | Complex parsing |
| **4. Skip on Resume** | Disable check if resumed | Loses safety guarantee |

### Action Items

- [ ] No action needed for single-session CLI
- [ ] Implement Option 1 if adding server mode
- [ ] Implement Option 2 or 3 if adding crash recovery

### References

- [LangGraph Persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/)
- [LangGraph Human-in-the-Loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/)

---

*Last updated: 2025-01-20*
