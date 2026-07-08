# Configuration Examples

This document contains example configurations for various MCP clients.

## Usage Notes

Before using these examples:

- Replace `/path/to/mcp-shellcheck` with your actual clone path
- Ensure `shellcheck` is installed: `pip install shellcheck-py` (v0.11.0) or system package
- Requires Python >=3.10 and `mcp>=1.0.0,<2`

---

## OpenCode

Add to `~/.config/opencode/opencode.jsonc`:

### Recommended: uvx with local path

```jsonc
{
  "mcp": {
    "shellcheck": {
      "type": "local",
      "command": [
        "uvx",
        "--from",
        "/path/to/mcp-shellcheck",
        "shellcheck-mcp-server"
      ],
      "enabled": true,
      "timeout": 60000
    }
  }
}
```

### Direct Python (requires mcp installed)

```jsonc
{
  "mcp": {
    "shellcheck": {
      "type": "local",
      "command": [
        "python3",
        "/path/to/mcp-shellcheck/shellcheck_mcp_server.py"
      ],
      "enabled": true,
      "timeout": 60000
    }
  }
}
```

---

## Claude Desktop

### macOS

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

### Linux

Add to `~/.config/Claude/claude_desktop_config.json`:

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

---

## Cursor

### macOS

Add to `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`:

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

---

## VS Code with Copilot Chat

Create or update `.vscode/mcp.json` in your project:

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

---

## Cline (VS Code Extension)

Add to `~/.cline/mcp_settings.json`:

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

---

## LM Studio

Add to your LM Studio MCP settings:

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

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `SHELLCHECK_CMD` | `"shellcheck"` | Override shellcheck binary path |

```jsonc
{
  "mcp": {
    "shellcheck": {
      "type": "local",
      "command": ["python3", "/path/to/mcp-shellcheck/shellcheck_mcp_server.py"],
      "environment": {
        "SHELLCHECK_CMD": "/path/to/shellcheck"
      }
    }
  }
}
```

---

## Tool Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file_path` | string | No* | — | Path to script file |
| `script_content` | string | No* | — | Raw script text |
| `shell` | string | No | `"bash"` | One of: bash, sh, dash, ksh, ash |
| `check_sourced` | boolean | No | `false` | `-a` — include warnings from sourced files |
| `enable_all` | boolean | No | `false` | `-o all` — enable all optional checks |
| `exclude` | string | No | — | Comma-separated codes to exclude (e.g., "SC1090,SC2148") |
| `include` | string | No | — | Comma-separated codes to include |
| `severity` | string | No | — | Minimum severity: error, warning, info, style |

*Either `file_path` or `script_content` must be provided, but not both.

### Example tool call

```json
{
  "file_path": "/path/to/script.sh",
  "shell": "bash",
  "exclude": "SC1090,SC2148",
  "severity": "warning",
  "enable_all": true
}
```
