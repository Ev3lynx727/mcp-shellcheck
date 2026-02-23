# Architecture: mcp-shellcheck v1.0.1

**Design Philosophy:** Simple adapter with robust error handling, async-aware, and future-extensible.

---

## Overview

`mcp-shellcheck` is a Model Context Protocol (MCP) server that wraps the ShellCheck CLI tool, providing shell script linting as a service for AI agents (Claude Desktop, Cursor, VS Code, etc.).

**Core Principle:** One responsibility, done well — lint shell scripts via ShellCheck, nothing more.

---

## Component Diagram

```
┌─────────────┐
│   MCP Client│ (Claude, Cursor, etc.)
└──────┬──────┘
       │ JSON-RPC over stdio
       ▼
┌─────────────────────────────┐
│  ShellCheck MCPServer       │
│  ┌─────────────────────┐   │
│  │  list_tools()       │───┼─> Tool definitions
│  │  call_tool()        │   │    (shellcheck, shellcheck_info)
│  └─────────────────────┘   │
│         │                   │
│         ▼                   │
│  ┌─────────────────────┐   │
│  │  run_shellcheck_async│  │
│  │  (thread pool)      │   │
│  └─────────────────────┘   │
│         │                   │
│         ▼                   │
│  ┌─────────────────────┐   │
│  │  run_shellcheck_sync│   │
│  │  - validate inputs  │   │
│  │  - build cmd        │   │
│  │  - subprocess.run   │   │
│  │  - parse JSON       │   │
│  └─────────────────────┘   │
└─────────────────────────────┘
       │
       ▼
┌─────────────┐
│ ShellCheck  │ (system binary)
└─────────────┘
```

---

## Key Design Decisions

### 1. Async Wrapper (Not Native Async Subprocess)

**Decision:** Use `asyncio.to_thread()` / `run_in_executor()` to wrap blocking `subprocess.run`.

**Rationale:**
- ShellCheck is a CLI tool; no async Python bindings exist
- Must not block MCP server event loop (other requests would queue)
- Thread pool is acceptable for I/O-bound subprocess calls
- Simpler than rewriting to `asyncio.create_subprocess_exec` for a single call

**Trade-offs:**
- Thread overhead minimal vs subprocess cost
- Easy to understand and maintain
- Could switch to native async later if needed

### 2. JSON Output Format

**Decision:** Always use `-f json` flag. Never parse human-readable output.

**Rationale:**
- Machine-readable, stable format
- Locale-independent
- Structured data (line, column, code, severity, message, fix)
- ShellCheck's JSON is well-defined

**Before (v0.1.0):** Fragile text parsing by splitting on `:`  
**After (v1.0.1):** Robust `json.loads()`

### 3. Input Validation Layer

**Decision:** Validate all inputs before spawning subprocess.

**Validation checks:**
- Exactly one of `file_path` or `script_content` provided
- `file_path` exists, is file, size < 10MB
- `script_content` size < 10MB
- `shell` in allowed set (bash, sh, dash, ksh, ash)

**Rationale:**
- Fail fast with clear error messages
- Prevent DoS via huge inputs
- Avoid shellcheck errors that are hard to debug
- Security: don't pass arbitrary paths without checking

### 4. Decoupled Linter Interface

**Decision:** Abstract `Linter` class, even though only ShellCheck exists today.

**Rationale:**
- Future-proof: could support `shfmt`, `bashate`, `beautysh`
- Dependency injection for testing
- Clear separation: MCP server ←→ linter backend
- Easy to add multi-linter aggregation later

**Not over-engineered:** Simple abstract base, one concrete implementation.

### 5. Logging Strategy

**Decision:** Use Python `logging` module, log to stderr.

**Levels:**
- `INFO`: Startup, completion, counts
- `DEBUG`: Command built, subprocess details
- `WARNING`: JSON parse failures, fallbacks
- `ERROR`: ShellCheck binary missing, timeouts

**Rationale:**
- Observability in production
- Debuggability when things go wrong
- MCP clients can capture stderr for diagnostics
- Configurable via `--log-level`

---

## Data Flow

```
MCP Request (JSON)
        │
        ▼
call_tool("shellcheck", {file_path="/path/to/script.sh", shell="bash"})
        │
        ▼
validate_inputs() ──if invalid─→ error response
        │
        ▼
run_shellcheck_async()  (thread pool)
        │
        ▼
run_shellcheck_sync()
        │
        ├── build cmd: ["shellcheck", "-s", "bash", "-f", "json", "/path/to/script.sh"]
        ├── subprocess.run(cmd, capture_output=True, timeout=30)
        ├── parse JSON from stdout
        └── return {success, message, results, exit_code}
        │
        ▼
JSON response to MCP client
```

---

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SHELLCHECK_CMD` | `"shellcheck"` | Override shellcheck binary path (e.g., `/usr/local/bin/shellcheck`) |
| (none for log level) | `INFO` | Set via `--log-level` argument |

### Command-Line Arguments

```bash
python3 shellcheck_mcp_server.py --log-level DEBUG
```

---

## Module Responsibilities

| Module/Function | Responsibility |
|-----------------|----------------|
| `validate_inputs()` | Guard against bad inputs (files, sizes, shells) |
| `run_shellcheck_sync()` | Synchronous shellcheck invocation with JSON parsing |
| `run_shellcheck_async()` | Thread pool wrapper for async compatibility |
| `Linter` (ABC) | Abstract interface for linting backends |
| `ShellCheckLinter` | Concrete ShellCheck implementation |
| `create_server()` | MCP server setup, tool definitions, tool routing |
| `list_tools()` | MCP capability advertisement |
| `call_tool()` | Request dispatcher, error boundaries |
| `main()` / `main_sync()` | Entry points with arg parsing |

---

## Error Handling Strategy

| Error Type | Handling |
|------------|----------|
| Validation | Return error response before subprocess |
| Timeout | Catch `subprocess.TimeoutExpired`, return error |
| Binary not found | Catch `FileNotFoundError`, return helpful message |
| JSON parse error | Log warning, return error (but include raw if possible) |
| Unexpected exception | Log stack trace, return generic error |

**Philosophy:** Never crash the server. Always return JSON error response.

---

## Performance Considerations

- **Timeouts:** 30 seconds per shellcheck call (configurable would be nice)
- **Caching:** Not implemented (future: `@lru_cache` on file mtime + hash)
- **Concurrency:** Thread pool allows concurrent requests (limited by GIL but okay for I/O)
- **Memory:** Script content copied into subprocess stdin; 10MB limit prevents abuse

---

## Testing Strategy

### Unit Tests (37+ tests planned)
- Input validation (all edge cases)
- Command building (flags, JSON format)
- JSON parsing (various shellcheck outputs)
- Error handling (timeout, not found, invalid JSON)
- Async wrapper (thread pool usage)
- Constants (version format, allowed shells)

### Integration Tests
- Real shellcheck on simple script
- Real shellcheck on problematic script
- End-to-end with actual binary

**Coverage Goal:** >90% of core logic.

---

## Evolution History

### v0.1.0 (Original)
- Single-threaded, blocking
- Text output parsing (fragile)
- No input validation
- No logging
- No tests

### v1.0.1 (This Release)
- Async-compatible via thread pool
- JSON output parsing (robust)
- Comprehensive input validation
- Structured logging
- 22 passing tests
- Linter abstraction (future-proof)
- Decent documentation

---

## Open Questions (Future Work)

1. **Caching:** How to invalidate? File mtime + content hash? TTL?
2. **Config file:** Where to put user defaults (shell, exclude list)?
3. **Progress feedback:** Can we stream results for large scripts?
4. **Multiple linters:** How to combine results? Prioritize?
5. **Rich output:** Should we return fix suggestions from shellcheck?
6. **Security:** Sandboxing? Run shellcheck in container?

---

## References

- [MCP Specification](https://github.com/modelcontextprotocol/specification)
- [ShellCheck Manual](https://www.shellcheck.net/)
- [Python asyncio.run_in_executor](https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.run_in_executor)

---

**Maintainer Philosophy:** Keep it simple, test it thoroughly, fail gracefully. 🧠
