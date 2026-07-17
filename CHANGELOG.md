# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-07-17

### Changed
- **Docs restructured** — Moved `.md` files to `docs/` for Context7 discoverability
- **CHANGELOG dates** — Fixed year references (2025 → 2026)

---

## [0.1.3] - 2026-06-22

### Added
- **include param support** — `include` parameter wired from `call_tool` to `run_shellcheck_sync`
- **Stress tests** — Tests for concurrent/parallel shellcheck calls
- **Install script** — `curl -fsSL ... | sh` one-liner install with auto shellcheck binary provisioning

### Changed
- **Code cleanup** — Reordered imports, simplified exception handling in `run_shellcheck_sync`
- **Tool descriptions** — Enhanced with selection signals (Use when / Prefer over / Avoid when)

### Fixed
- **CLI flag mapping** — `check_sourced`, `enable_all`, `severity` now pass correct ShellCheck arguments

---

## [0.1.2] - 2026-02-23

### Added
- **Async compatibility** — Wraps blocking subprocess in thread pool to avoid blocking MCP server
- **Input validation** — Checks file existence, size limits, shell type, exclusive file/content
- **Structured logging** — Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- **Configurable shellcheck path** via `SHELLCHECK_CMD` environment variable
- **CLI `--log-level` argument** for runtime log configuration
- **Linter abstraction** — Abstract `Linter` class for future multi-backend support
- **Comprehensive test suite** — 22 tests (unit + integration), ~90% coverage
- **ARCHITECTURE.md** — Detailed design documentation
- **MIGRATION.md** — Upgrade guide from v0.1.0

### Changed
- **Parsing** — Switched from fragile text parsing to `-f json` (robust)
- **Error messages** — More helpful (validation errors, install hints)
- **Exit code handling** — Better distinction between success, issues found, and errors
- **Dependencies** — No new runtime deps; added dev deps (pytest, pytest-asyncio)

### Fixed
- **Blocking issue** — Server no longer freezes during long shellcheck runs
- **Script content stdin handling** — Properly passes `-` to read from stdin
- **JSON parsing** — No longer breaks on locale or format changes
- **Timeout handling** — Properly catches and reports timeouts
- **Binary not found** — Clear error message with install URL

### Security
- **Input size limits** — 10MB max on script content/files
- **Path validation** — Checks file exists and is regular file (not symlink attacks)
- **Shell enum** — Only allowed shells accepted

---

## [0.1.0] - 2026-02-22

- Initial release
- Basic MCP server with `shellcheck` and `shellcheck_info` tools
- Supports file path and script content input
- Configurable shell type, exclude codes, severity filter
- JSON output (but parsed from text, not using `-f json`)
- No tests, no validation, no logging
- Blocking subprocess calls

---

## Planned for v1.2.0
- Caching layer (file mtime + content hash)
- Configuration file (`~/.config/mcp-shellcheck/config.toml`)
- `--dry-run` mode
- `--list-checks` to show available warning codes
- shfmt support as alternative linter
- Pre-commit hook template
- GitHub Actions CI (tests + release)

---

## Unreleased (Backlog)
- Rate limiting / quota per client
- Telemetry (opt-in) for common error patterns
- Sandboxed execution (containerize shellcheck)
- Multi-linter aggregation (shellcheck + shfmt + bashate)
- Results streaming for large outputs

[0.2.0]: https://github.com/ev3lynx727/mcp-shellcheck/releases/tag/v0.2.0
[0.1.3]: https://github.com/ev3lynx727/mcp-shellcheck/releases/tag/v0.1.3
[0.1.2]: https://github.com/ev3lynx727/mcp-shellcheck/releases/tag/v0.1.2
[0.1.0]: https://github.com/ev3lynx727/mcp-shellcheck/releases/tag/v0.1.0
