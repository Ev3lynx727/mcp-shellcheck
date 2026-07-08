# ShellCheck MCP Server

[![Tests](https://github.com/Ev3lynx727/mcp-shellcheck/actions/workflows/tests.yml/badge.svg)](https://github.com/Ev3lynx727/mcp-shellcheck/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/mcp-shellcheck)](https://pypi.org/project/mcp-shellcheck/)
[![License](https://img.shields.io/badge/license-MIT-blue)](./LICENSE)

A Model Context Protocol (MCP) server that provides shell script linting via ShellCheck. Allows AI agents to analyze shell scripts for common errors, stylistic issues, and potential bugs.

## MCP Server Profile

```json
{
  "name": "mcp-shellcheck",
  "description": "A Model Context Protocol (MCP) server that provides shell script linting via ShellCheck for AI coding assistants",
  "tools": [
    {
      "name": "shellcheck",
      "description": "Run ShellCheck on a shell script to find bugs, stylistic issues, and potential errors",
      "inputSchema": {
        "type": "object",
        "properties": {
          "file_path": { "type": "string", "description": "Path to the shell script file to check" },
          "script_content": { "type": "string", "description": "Raw shell script content to check" },
          "shell": { "type": "string", "description": "Shell type to check", "enum": ["bash", "sh", "dash", "ksh", "ash"] },
          "check_sourced": { "type": "boolean", "description": "Enable checks for sourced files" },
          "enable_all": { "type": "boolean", "description": "Enable all optional checks" },
          "exclude": { "type": "string", "description": "Comma-separated list of warning codes to exclude" },
          "severity": { "type": "string", "description": "Minimum severity to report", "enum": ["error", "warning", "info", "style"] }
        }
      }
    },
    {
      "name": "shellcheck_info",
      "description": "Get information about the ShellCheck version and server capabilities",
      "inputSchema": {
        "type": "object",
        "properties": {}
      }
    }
  ]
}
```

## Quick Install

```bash
# Run via uvx from PyPI
uvx --from mcp-shellcheck shellcheck-mcp-server

# Run via uvx from GitHub release
uvx --from https://github.com/Ev3lynx727/mcp-shellcheck/releases/download/v0.1.3/mcp_shellcheck-0.1.3-py3-none-any.whl shellcheck-mcp-server

# One-liner install (install.sh)
curl -fsSL https://raw.githubusercontent.com/Ev3lynx727/mcp-shellcheck/main/install.sh | sh

# Install from PyPI
pip install mcp-shellcheck

# Clone and dev install
git clone https://github.com/Ev3lynx727/mcp-shellcheck.git
cd mcp-shellcheck && pip install -e .
```

## Features

- **File-based analysis**: Check shell scripts by file path
- **Inline script checking**: Analyze raw shell script content directly
- **Multiple shell support**: bash, sh, dash, ksh, ash
- **Configurable checks**: Exclude specific warnings, set severity levels
- **Structured output**: JSON-formatted results for easy parsing
- **OpenCode integration**: Ready to use with OpenCode agents
- **Production-ready**: Async, tested, validated, logged

## Requirements

- Python 3.10+
- [ShellCheck](https://www.shellcheck.net/) installed on the system

### Installing ShellCheck

**Recommended (always latest):**

```bash
pip install shellcheck-py
```

The `shellcheck-py` package provides a pre-built shellcheck v0.11.0 binary on your PATH with no system dependencies.

**System package managers (may ship older versions):**

```bash
# Ubuntu/Debian
sudo apt-get install shellcheck

# macOS
brew install shellcheck

# Fedora/RHEL
sudo dnf install ShellCheck

# Arch Linux
sudo pacman -S shellcheck
```

## Tools

### `shellcheck`

Run ShellCheck on a shell script to find bugs, stylistic issues, and potential errors.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | No* | Path to the shell script file |
| `script_content` | string | No* | Raw shell script content |
| `shell` | string | No | Shell type: bash, sh, dash, ksh, ash (default: bash) |
| `check_sourced` | boolean | No | Enable checks for sourced files (default: false) |
| `enable_all` | boolean | No | Enable all optional checks (default: false) |
| `exclude` | string | No | Comma-separated codes to exclude (e.g., "SC1090,SC2148") |
| `include` | string | No | Comma-separated codes to include (e.g., "SC2086,SC2164") |
| `severity` | string | No | Minimum severity: error, warning, info, style |

*Either `file_path` or `script_content` must be provided.

**Common error codes:**

| Code | Description | Severity |
|------|-------------|----------|
| SC1090 | Can't follow non-constant source | info |
| SC2086 | Double quote to prevent globbing | warning |
| SC2164 | Use cd with \|\| exit | warning |
| SC2006 | Use $(...) instead of legacy backticks | style |

### `shellcheck_info`

Get ShellCheck version and server capabilities.

**Parameters:** None

## Configuration

### OpenCode

```jsonc
{
  "mcp": {
    "shellcheck": {
      "type": "local",
      "command": [
        "uv",
        "run",
        "--with", "mcp",
        "python3",
        "/path/to/mcp-shellcheck/shellcheck_mcp_server.py"
      ],
      "enabled": true,
      "timeout": 60000
    }
  }
}
```

### OpenCode (uvx from GitHub release)

```jsonc
{
  "mcp": {
    "shellcheck": {
      "type": "local",
      "command": [
        "uvx",
        "--from", "https://github.com/Ev3lynx727/mcp-shellcheck/releases/download/v0.1.3/mcp_shellcheck-0.1.3-py3-none-any.whl",
        "shellcheck-mcp-server"
      ],
      "enabled": true,
      "timeout": 60000
    }
  }
}
```

### Claude Desktop

```json
{
  "mcpServers": {
    "shellcheck": {
      "command": "python3",
      "args": ["/path/to/mcp-shellcheck/shellcheck_mcp_server.py"]
    }
  }
}
```

### Cursor

```json
{
  "mcpServers": {
    "shellcheck": {
      "command": "uvx",
      "args": ["shellcheck-mcp-server"]
    }
  }
}
```

### VS Code (Copilot)

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "shellcheck": {
      "command": "python3",
      "args": ["/path/to/mcp-shellcheck/shellcheck_mcp_server.py"]
    }
  }
}
```

## Examples

### Check a File

```json
// Input
{ "file_path": "/path/to/deploy.sh" }

// Output
{
  "success": false,
  "message": "Found 3 issue(s)",
  "results": [
    {
      "line": 15,
      "column": 10,
      "code": "SC2086",
      "message": "Double quote to prevent globbing",
      "severity": "warning"
    }
  ],
  "exit_code": 1
}
```

### Check Script Content

```json
// Input
{ "script_content": "#!/bin/bash\ncat `ls *.txt`", "shell": "bash" }
```

### Exclude Specific Warnings

```json
{ "file_path": "/path/to/script.sh", "exclude": "SC1090,SC2148" }
```

### Filter by Severity

```json
{ "file_path": "/path/to/script.sh", "severity": "error" }
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| ShellCheck not found | Install via `pip install shellcheck-py` or system package manager |
| MCP package not installed | `pip install mcp` |
| Server not connecting | Verify `shellcheck --version`, test with `python3 shellcheck_mcp_server.py` |
| Timeout errors | Increase timeout: `"timeout": 120000` in MCP config |

## Development

```bash
pip install -e ".[dev]"
pytest
ruff check .
```

See [CHANGELOG.md](./CHANGELOG.md) for release history and [ARCHITECTURE.md](docs/ARCHITECTURE.md) for design docs.

## License

MIT
