# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.2] - 2025-02-23

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

## [0.1.0] - 2025-02-22

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
