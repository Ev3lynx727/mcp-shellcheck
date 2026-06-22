# CE: mcp-shellcheck — Context Engineer Handoff

## Identity

MCP server that wraps ShellCheck to provide shell script linting to AI agents via the Model Context Protocol. Accepts file paths or raw script content, returns structured JSON results.

`mcp-shellcheck` v0.1.3 — MIT, Python >=3.10, dependency: `mcp>=1.0.0`.

## Architecture

```
mcp-shellcheck/
├── shellcheck_mcp_server.py     # Single-file server: entry, logic, schema, all in one
├── pyproject.toml               # Package config, deps, scripts entry point
├── requirements.txt             # Pin file (mcp>=1.0.0)
├── README.md                    # User-facing docs
├── CONFIG_EXAMPLES.md           # MCP client config templates
├── CE.md                        # This file
├── .python-version              # uv pin: Python 3.10
├── .venv/                       # Local dev venv (uv sync)
└── tests/
    ├── test_shellcheck_mcp_server.py  # 22 unit/integration tests
    ├── test_stress_json.py            # 7 JSON stress tests
    └── test_stress_escape.py          # 6 escape/stress tests
```

## Pipeline

```
MCP client (tool: shellcheck)
  -> call_tool handler (shellcheck_mcp_server.py:388)
  -> validate_inputs() (shell: type, path: exists/size, content: size)
  -> run_shellcheck_sync() via run_in_executor (thread pool, non-blocking)
     -> build shellcheck argv (flags: -s, -a, -o all, -S, -e, -f json)
     -> subprocess.run(input=script_content, timeout=30)
     -> json.loads(stdout) -> parse results
  -> return TextContent(json.dumps(result, indent=2))

Errors: JSONDecodeError -> graceful "Failed to parse" response
        TimeoutExpired -> "timed out after 30 seconds"
        FileNotFoundError -> "ShellCheck not found" with install hint
        generic Exception -> "Unexpected error" + stack trace
```

## Key Types

```
Result dict {
  success: bool          # shellcheck exit code 0 = success
  message: str           # "N issue(s)" or "No issues found"
  results: list[dict]    # parsed shellcheck JSON issues
  exit_code: int         # raw shellcheck exit code
  error?: str            # present only on failure paths
}

Input params (via MCP tool call):
  file_path?       str  # path to script file
  script_content?  str  # raw script text
  shell            str  # bash|sh|dash|ksh|ash (default: bash)
  check_sourced   bool  # -a flag (default: false)
  enable_all      bool  # -o all flag (default: false)
  exclude?         str  # comma-separated SC codes to exclude
  severity?        str  # error|warning|info|style
```

## Critical Constraints

- **shellcheck binary**: Resolved via `SHELLCHECK_CMD` env var, falls back to PATH. Must be installed separately (`pip install shellcheck-py` or system package). v0.11.0 recommended.
- **Python MCP SDK `mcp>=1.0.0,<2`**: Currently at v1.28.0 (v1.26.0 local). v2.0.0a2 in alpha, stable target 2026-07-27. v2 is stateless request/response (breaking: stateful→stateless). Upper bound `<2` is required — 84% of PyPI dependents lack it and will break on v2 stable drop. See [python-sdk v2 migration](https://github.com/modelcontextprotocol/python-sdk/blob/main/docs/migration.md).
- **input_schema**: NO `oneOf`/`allOf`/`anyOf` at top level — Anthropic API rejects them. Use runtime `validate_inputs()` instead.
- **CLI flags mapping**: `check_sourced` → `-a`, `enable_all` → `-o all`, `severity` → `-S <level>` — these were swapped in v0.1.2, fixed in v0.1.3.
- **`include` param**: Wired in `run_shellcheck_sync` signature but NOT passed from `call_tool` handler — won't work until wired.
- **uvx entry**: `uvx --from /home/ev3lynx/mcp-shellcheck shellcheck-mcp-server` for local dev; not on PyPI yet.
- **10MB max script size**: Enforced in `validate_inputs()` on both file and content paths.
- **30-second subprocess timeout**: Hardcoded in `subprocess.run(timeout=30)`.

## CLI

Not a standalone CLI tool — runs as an MCP server. The entry point `shellcheck-mcp-server` starts stdio MCP server. No CLI flags at server level. Direct shellcheck CLI usage documented in README for debugging.

## Current State

- v0.1.3 — stable, tested, two bugs fixed (oneOf schema, CLI flags)
- Tests: 35 total (22 unit/integration + 7 JSON stress + 6 escape stress), all passing
- Server deployed via `uvx --from <local>` in opencode.jsonc
- `include` param now fully wired from `call_tool`
- Package NOT published to PyPI — only available via GitHub clone or local install
- shellcheck binary upgraded from system 0.8.0 to pip 0.11.0

## Files to Edit

| File | Purpose |
|------|---------|
| `shellcheck_mcp_server.py` | Everything — single file server, no split modules |
| `pyproject.toml` | Version bumps, dependency changes, optional extras |
| `tests/test_shellcheck_mcp_server.py` | Main test suite (22 tests) |
| `tests/test_stress_json.py` | JSON parsing stress tests |
| `tests/test_stress_escape.py` | Escape/roundtrip stress tests |
| `README.md` | User-facing docs, config examples, install instructions |

## Recent Changes

- v0.1.3: Dropped `oneOf` from inputSchema (Anthropic API compat) — PR #2
- v0.1.3: Fixed shellcheck CLI flags (`-S`→`-a`, `-a`→`-o all`, added `severity`→`-S`) — PR #3
- v0.1.3: Added 13 stress tests (JSON large output + escape roundtrip)
- v0.1.3: Upgraded shellcheck from system 0.8.0 to pip 0.11.0
- v0.1.3: Standardized dev on Python 3.10, `.python-version` pin added

## Important Files

- `~/.config/opencode/opencode.jsonc` — MCP server config block for shellcheck
- `~/.local/bin/shellcheck` — pip-installed v0.11.0 binary
- `~/.npm/_npx/` — 3.1GB npx cache (needs cleaning, not related to this project)
