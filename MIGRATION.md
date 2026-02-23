# Migration Guide: v0.1.0 → v0.1.2

**Upgrading?** Here's what changed and what you need to know.

---

## Summary

v0.1.2 is a **stability and reliability** refactor. It fixes critical issues with async blocking, parsing, and validation. **No breaking changes for end users** — the tool behaves better, not differently.

**You should upgrade** because:
- ✅ Won't block your MCP server anymore (async fix)
- ✅ More accurate results (JSON parsing, not text hacks)
- ✅ Better error messages (validation + logging)
- ✅ Tested (22 passing tests, >90% coverage)
- ✅ Future-proof (linter abstraction in place)

---

## What Changed (Under the Hood)

### 1. Async Compatibility Fixed
- **Before:** Blocking `subprocess.run()` in async MCP handler → entire server waited
- **After:** Thread pool wrapper → other requests can proceed while shellcheck runs

**Impact:** Better concurrency, no more frozen agents during long checks.

### 2. Robust JSON Parsing
- **Before:** Parsed human-readable output by splitting on `:` — locale- and version-dependent
- **After:** Use ShellCheck's `-f json` flag and `json.loads()` — stable, structured

**Impact:** More reliable results across shellcheck versions.

### 3. Input Validation
- **Before:** No checks — could pass non-existent files, huge scripts, invalid shells
- **After:** Validates file existence, size limits (<10MB), shell enum, not both file & content

**Impact:** Clearer errors, prevents accidental DoS.

### 4. Logging
- **Before:** Only `print()` to stderr
- **After:** Structured logging (`INFO`, `DEBUG`, `WARNING`, `ERROR`) with timestamp

**Impact:** Easier debugging in production.

### 5. Configuration via Environment
- **Before:** Shellcheck binary path hardcoded as `"shellcheck"`
- **After:** Can override with `SHELLCHECK_CMD` environment variable

**Impact:** Useful for custom installations or testing.

### 6. Code Quality
- **Before:** No tests (0% coverage)
- **After:** 22 tests covering validation, parsing, async wrapper, integration (≥90% coverage)

**Impact:** Confidence in future changes.

---

## User-Visible Changes

### Nothing to change in your MCP client config

Your existing configuration (in Claude Desktop, Cursor, VS Code) continues to work exactly as before.

**Example (unchanged):**
```json
{
  "mcpServers": {
    "shellcheck": {
      "command": "python3",
      "args": ["/path/to/shellcheck_mcp_server.py"]
    }
  }
}
```

### Optional: Set Log Level

If you want more detailed logs, you can now add `--log-level DEBUG`:

```json
{
  "mcpServers": {
    "shellcheck": {
      "command": "python3",
      "args": ["/path/to/shellcheck_mcp_server.py", "--log-level", "DEBUG"]
    }
  }
}
```

### Optional: Override ShellCheck Path

If your `shellcheck` is not in PATH, set `SHELLCHECK_CMD`:

```bash
export SHELLCHECK_CMD="/opt/homebrew/bin/shellcheck"
# Then start your MCP client
```

Or in your systemd service file if running as daemon.

---

## Breaking Changes? None.

The tool's **inputs and outputs are identical**:
- Same tool names (`shellcheck`, `shellcheck_info`)
- Same parameters (file_path, script_content, shell, exclude, severity, etc.)
- Same output format (JSON with success, message, results array)

You can upgrade the server binary without touching your MCP client config.

---

## Performance Notes

- **Speed:** Similar or slightly faster due to reduced overhead (no text parsing)
- **Memory:** Negligible increase (logging, thread pool)
- **Concurrency:** Much better — long checks won't block others

---

## Known Issues (Unchanged)

- ShellCheck must be installed separately (not bundled)
- No caching yet (every check re-runs shellcheck)
- No configuration file (all options via MCP params or env)

These are known and on the roadmap for v0.2.0.

---

## Rollback

If you encounter issues (unlikely), simply revert to v0.1.0:
```bash
# If installed via pip:
pip install mcp-shellcheck==0.1.0

# If running from source:
git checkout v0.1.0  # or your previous commit
```

---

## Need Help?

- **Issues:** https://github.com/Ev3lynx727/mcp-shellcheck/issues
- **Changelog:** See [CHANGELOG.md](CHANGELOG.md) for full details
- **Architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md) for design docs

---

**Bottom line:** Upgrade with confidence. The tool is now more robust, better tested, and async-safe. Nothing to change in your workflow. 🚀
