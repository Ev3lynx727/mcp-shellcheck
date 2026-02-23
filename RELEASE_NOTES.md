# What's Changed

## v0.1.2 - Stability Refactor

### Critical fixes:
- **Async-safe** — Wraps blocking subprocess in thread pool to avoid blocking MCP server
- **Robust parsing** — Uses ShellCheck `-f json` output instead of fragile text parsing
- **Input validation** — File existence, size limits, shell type validation
- **Fix stdin handling** — Properly passes `-` for script_content
- **Proper error boundaries** — timeout, not found, JSON parse errors

### Quality improvements:
- **Structured logging** — DEBUG/INFO/WARNING/ERROR with `--log-level` flag
- **Configurable shellcheck path** via `SHELLCHECK_CMD` environment variable
- **Linter abstraction** — Abstract `Linter` class for future multi-backend support
- **Comprehensive tests** — 22 tests, ~90% coverage

### Documentation:
- Added **ARCHITECTURE.md** with design docs and data flow
- Added **MIGRATION.md** guide (v0.1.0 → v0.1.2)
- Added **CHANGELOG.md** following Keep a Changelog
- Updated **README.md** with badges and v0.1.2 highlights

### Tech debt addressed:
- Fixed AsyncGhost (blocking async)
- Fixed ParsingVulnerability (text → JSON)
- Added InputVoid validation
- Added VisibilityThin (logging)
- Added Testability gap (tests)

**Full Changelog**: https://github.com/Ev3lynx727/mcp-shellcheck/compare/v0.1.0...v0.1.2