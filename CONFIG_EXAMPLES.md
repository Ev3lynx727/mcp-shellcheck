# Configuration Examples

This document contains example configurations for various MCP clients.

## OpenCode

### Basic Configuration

Add to `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "mcp": {
    "shellcheck": {
      "type": "local",
      "command": [
        "python3",
        "/home/ev3lynx/Project/local-mcp-server/mcp-shellcheck/shellcheck_mcp_server.py"
      ],
      "enabled": true,
      "timeout": 60000
    }
  }
}
```

### With uvx

```jsonc
{
  "mcp": {
    "shellcheck": {
      "type": "local",
      "command": ["uvx", "shellcheck-mcp-server"],
      "enabled": true,
      "timeout": 60000
    }
  }
}
```

## Claude Desktop

### macOS

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "shellcheck": {
      "command": "python3",
      "args": [
        "/home/ev3lynx/Project/local-mcp-server/mcp-shellcheck/shellcheck_mcp_server.py"
      ]
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
      "args": [
        "/home/ev3lynx/Project/local-mcp-server/mcp-shellcheck/shellcheck_mcp_server.py"
      ]
    }
  }
}
```

## Cursor

### macOS

Add to `~/Library/Application Support/Cursor/User/globalStorage/mcp.json`:

```json
{
  "mcpServers": {
    "shellcheck": {
      "command": "python3",
      "args": [
        "/home/ev3lynx/Project/local-mcp-server/mcp-shellcheck/shellcheck_mcp_server.py"
      ]
    }
  }
}
```

## VS Code with Copilot Chat

Create or update `.vscode/mcp.json` in your project:

```json
{
  "servers": {
    "shellcheck": {
      "command": "python3",
      "args": [
        "/home/ev3lynx/Project/local-mcp-server/mcp-shellcheck/shellcheck_mcp_server.py"
      ]
    }
  }
}
```

## Cline (VS Code Extension)

Add to `~/.cline/mcp_settings.json`:

```json
{
  "mcpServers": {
    "shellcheck": {
      "command": "python3",
      "args": [
        "/home/ev3lynx/Project/local-mcp-server/mcp-shellcheck/shellcheck_mcp_server.py"
      ]
    }
  }
}
```

## LM Studio

Add to your LM Studio MCP settings:

```json
{
  "mcpServers": {
    "shellcheck": {
      "command": "python3",
      "args": [
        "/home/ev3lynx/Project/local-mcp-server/mcp-shellcheck/shellcheck_mcp_server.py"
      ]
    }
  }
}
```

## Docker-based (Alternative)

If you prefer Docker-based isolation:

```jsonc
{
  "mcp": {
    "shellcheck": {
      "type": "local",
      "command": [
        "docker",
        "run",
        "--rm",
        "-i",
        "--network=none",
        "python:3.11-slim",
        "python3",
        "-c",
        "import sys; print(sys.stdin.read())"
      ],
      "enabled": true,
      "timeout": 60000
    }
  }
}
```

## Environment Variables

No environment variables are required. However, you can pass custom environment:

```jsonc
{
  "mcp": {
    "shellcheck": {
      "type": "local",
      "command": ["python3", "shellcheck_mcp_server.py"],
      "environment": {
        "SHELLCHECK_PATH": "/usr/local/bin/shellcheck"
      }
    }
  }
}
```

## Advanced: Custom ShellCheck Options

Pass custom ShellCheck options via the tool parameters:

```json
{
  "file_path": "/path/to/script.sh",
  "shell": "bash",
  "exclude": "SC1090,SC2148",
  "severity": "warning"
}
```
