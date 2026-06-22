# Architecture: mcp-shellcheck v0.1.3

**Design Philosophy:** Simple adapter with robust error handling, async-aware, and future-extensible.

---

## Overview

`mcp-shellcheck` is a Model Context Protocol (MCP) server that wraps the ShellCheck CLI tool, providing shell script linting as a service for AI agents (Claude Desktop, Claude Code, Cursor, VS Code, OpenCode).

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
│ ShellCheck  │ (binary, v0.11.0 recommended)
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
**After (v0.1.2):** Robust `json.loads()`

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

### 4. Single-File Server (Not Modular)

**Decision:** Single `shellcheck_mcp_server.py` file, not split across modules.

**Rationale:**
- Server is small enough (~500 lines) that module overhead hurts more than it helps
- Easy to deploy -- copy one file
- No package needed for basic use
- Can modularize if complexity grows

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
- Configurable via `LOG_LEVEL` env var

---

## Data Flow

```
MCP Request (JSON)
        │
        ▼
call_tool("shellcheck", {script_content="...", shell="bash", severity="warning"})
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
        ├── build argv: ["shellcheck", "-s", "bash", "-f", "json", "-S", "warning", "-"]
        ├── subprocess.run(input=script_content, capture_output=True, timeout=30)
        ├── json.loads(stdout) ──if parse fail─→ error response
        └── return {success, message, results, exit_code}
        │
        ▼
json.dumps(result, indent=2) wrapped in TextContent
        │
        ▼
JSON response to MCP client
```

---

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SHELLCHECK_CMD` | `"shellcheck"` | Override shellcheck binary path |
| `LOG_LEVEL` | `"INFO"` | Logging level (DEBUG, INFO, WARNING, ERROR) |

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
| `create_server()` | MCP server setup, tool definitions, error boundaries |
| `main()` / `main_sync()` | Entry points with arg parsing |

---

## Tool Schema

### shellcheck

| Parameter | Type | Required | Default | Flag |
|-----------|------|----------|---------|------|
| `file_path` | string | no\* | -- | path arg |
| `script_content` | string | no\* | -- | stdin input |
| `shell` | string | no | `"bash"` | `-s` |
| `check_sourced` | boolean | no | `false` | `-a` |
| `enable_all` | boolean | no | `false` | `-o all` |
| `exclude` | string | no | -- | `-e` |
| `include` | string | no | -- | `-i` |
| `severity` | string | no | -- | `-S` |

> **Resolved:** `include` is now fully wired from `call_tool` through to shellcheck.

### shellcheck_info

Returns: server version, shellcheck version, supported shells, max script size.

---

## Error Handling Strategy

| Error Type | Handling |
|------------|----------|
| Validation | Return error response before subprocess |
| Timeout | Catch `subprocess.TimeoutExpired`, return error |
| Binary not found | Catch `FileNotFoundError`, return helpful message |
| JSON parse error | Log warning, return error response |
| Unexpected exception | Log stack trace, return generic error |

**Philosophy:** Never crash the server. Always return JSON error response.

---

## Performance Considerations

- **Timeouts:** 30 seconds per shellcheck call
- **Concurrency:** Thread pool allows concurrent requests (GIL-limited but fine for I/O)
- **Memory:** Script content piped to subprocess stdin; 10MB limit prevents abuse
- **JSON load:** Entire ShellCheck output loaded into memory (`json.loads`). Tested to 10K issues (~2.8MB JSON)

---

## Testing

### Unit Tests (35 tests)
- Input validation (all edge cases)
- Command building (flags, JSON format, severity, check_sourced, enable_all)
- JSON parsing (large output, unicode, malformed, control chars, escape roundtrips)
- Error handling (timeout, not found, invalid JSON)
- Async wrapper (thread pool delegation)

### Integration Tests
- Real shellcheck on simple scripts
- Real shellcheck on 6,000-line generated scripts
- Full roundtrip: result dict -> json.dumps -> json.loads

---

## Evolution History

### v0.1.0 (Original)
- Single-threaded, blocking
- Text output parsing (fragile)
- No input validation
- No logging
- No tests

### v0.1.2 (Async + Robustness)
- Async-compatible via thread pool
- JSON output parsing (robust)
- Comprehensive input validation
- Structured logging
- 22 passing tests
- Decent documentation

### v0.1.3 (Current)
- `oneOf` removed from inputSchema (Anthropic API 400 fix)
- ShellCheck flags corrected (`-S`->`-a`, `-a`->`-o all`, added `severity`->`-S`)
- `include` parameter now fully wired from `call_tool`
- 35 passing tests (22 original + 13 stress: JSON large output + escape roundtrips)
- shellcheck upgraded from system 0.8.0 to `shellcheck-py` 0.11.0
- First external contributor (@iav) merged 2 bugfix PRs
- Python 3.10 pinned via `.python-version`
- `mcp>=1.0.0,<2` pin to avoid SDK v2 breaking change (targets 2026-07-27)

---

## Future Work

1. **SDK v2 migration** (2026-07-27): stateful to stateless refactor
2. **Progress feedback:** Stream results for large scripts
3. **Caching:** File mtime + content hash eviction

---

## References

- [MCP Specification](https://github.com/modelcontextprotocol/specification)
- [ShellCheck Manual](https://www.shellcheck.net/)
