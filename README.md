# ShellCheck MCP Server

A Model Context Protocol (MCP) server that provides shell script linting via ShellCheck. Allows AI agents to analyze shell scripts for common errors, stylistic issues, and potential bugs.

## Features

- **File-based analysis**: Check shell scripts by file path
- **Inline script checking**: Analyze raw shell script content directly
- **Multiple shell support**: bash, sh, dash, ksh, ash
- **Configurable checks**: Exclude specific warnings, set severity levels
- **Structured output**: JSON-formatted results for easy parsing
- **OpenCode integration**: Ready to use with OpenCode agents

## Requirements

- Python 3.10+
- [ShellCheck](https://www.shellcheck.net/) installed on the system

### Installing ShellCheck

```bash
# Ubuntu/Debian
sudo apt-get install shellcheck

# macOS
brew install shellcheck

# Fedora/RHEL
sudo dnf install ShellCheck

# Arch Linux
sudo pacman -S shellcheck

# From source
git clone https://github.com/koalaman/shellcheck.git
cd shellcheck
cabal build
sudo cabal install
```

## Installation

### Option 1: Clone and Install

```bash
cd /home/ev3lynx/Project/local-mcp-server
git clone https://github.com/your-repo/mcp-shellcheck.git
cd mcp-shellcheck
pip install -e .
```

### Option 2: Direct Python Execution

```bash
pip install mcp
python3 shellcheck_mcp_server.py
```

### Option 3: Build Locally

```bash
# Clone and build
git clone https://github.com/ev3lynx727/mcp-shellcheck.git
cd mcp-shellcheck
uv build

# Install locally
uv pip install -e . --system

# Or run directly
uv run --with mcp python3 shellcheck_mcp_server.py
```

### Option 4: From GitHub Release

After creating a GitHub release, you can use uvx directly from the wheel file:

```bash
uvx --from https://github.com/Ev3lynx727/mcp-shellcheck/releases/download/v0.1.0/mcp_shellcheck-0.1.0-py3-none-any.whl shellcheck-mcp-server
```

Note: Replace the version number in the URL with your desired version.

## OpenCode Configuration

### Recommended: Using uv run

Add or update the shellcheck MCP server configuration:

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
        "/home/ev3lynx/Project/local-mcp-server/mcp-shellcheck/shellcheck_mcp_server.py"
      ],
      "enabled": true,
      "timeout": 60000
    }
  }
}
```

### Alternative: Direct Python (requires mcp installed)

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

### Agent Tool Configuration

The tool `shellcheck_shellcheck` is already enabled in these agents:
- `builder-pro`
- `deep-research`
- `lint`
- `docker-config`
- `analyze`

## Usage

### As an MCP Server

Once configured, the following tools are available:

#### `shellcheck` Tool

Check a shell script file or content for issues.

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | No* | Path to the shell script file |
| `script_content` | string | No* | Raw shell script content |
| `shell` | string | No | Shell type: bash, sh, dash, ksh, ash (default: bash) |
| `check_sourced` | boolean | No | Enable checks for sourced files (default: false) |
| `enable_all` | boolean | No | Enable all optional checks (default: false) |
| `exclude` | string | No | Comma-separated codes to exclude (e.g., "SC1090,SC2148") |
| `severity` | string | No | Minimum severity: error, warning, info, style |

*Either `file_path` or `script_content` must be provided.

#### `shellcheck_info` Tool

Get ShellCheck version and server information.

**Parameters:** None

### Direct CLI Usage

```bash
# Check a file
shellcheck /path/to/script.sh

# Check stdin
cat script.sh | shellcheck -s bash -

# With specific options
shellcheck -e SC1090,SC2148 -s bash script.sh
```

## Examples

### Example 1: Check a File

```bash
# Input
{
  "file_path": "/path/to/deploy.sh"
}

# Output
{
  "success": false,
  "message": "Found 3 issue(s)",
  "results": [
    {
      "line": 15,
      "column": 10,
      "code": "SC2086",
      "message": "Double quote to prevent globbing",
      "severity": "warning",
      "raw": "path/to/script.sh:15:10: warning: Double quote to prevent globbing..."
    }
  ],
  "exit_code": 1
}
```

### Example 2: Check Script Content

```bash
# Input
{
  "script_content": "#!/bin/bash\ncat `ls *.txt`",
  "shell": "bash"
}

# Output
{
  "success": false,
  "message": "Found 2 issue(s)",
  "results": [
    {
      "line": 2,
      "column": 5,
      "code": "SC2010",
      "message": "Don't read ls output with backticks",
      "severity": "warning"
    }
  ],
  "exit_code": 1
}
```

### Example 3: Exclude Specific Warnings

```bash
# Input
{
  "file_path": "/path/to/script.sh",
  "exclude": "SC1090,SC2148"
}
```

### Example 4: Check with Severity Filter

```bash
# Input
{
  "file_path": "/path/to/script.sh",
  "severity": "error"
}
```

## Common ShellCheck Error Codes

| Code | Description | Severity |
|------|-------------|----------|
| SC1090 | Can't follow non-constant source | info |
| SC1091 | Can't follow sourced file | info |
| SC2148 | Tips depend on target shell and yours is unknown | warning |
| SC2086 | Double quote to prevent globbing | warning |
| SC2164 | Use cd with \|\| exit | warning |
| SC2006 | Use $(...) instead of legacy backticks | style |
| SC2029 | Note that, unlike in BASH, a variable cannot contain a newline | warning |
| SC2230 | Which is redundant | info |
| SC2068 | Double quote array subscript | warning |
| SC2196 | Several way to test global flag | info |
| SC2001 | See if you can use ${var//search/replace} | style |
| SC2162 | read without -r will mangle backslashes | warning |
| SC2129 | Style: Consider using { cmd1; cmd2; } >> file | style |

## MCP Client Configuration Examples

### Claude Desktop

```json
{
  "mcpServers": {
    "shellcheck": {
      "command": "python3",
      "args": ["/home/ev3lynx/Project/local-mcp-server/mcp-shellcheck/shellcheck_mcp_server.py"]
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

### VS Code with Copilot

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "shellcheck": {
      "command": "python3",
      "args": ["/home/ev3lynx/Project/local-mcp-server/mcp-shellcheck/shellcheck_mcp_server.py"]
    }
  }
}
```

## Troubleshooting

### "ShellCheck not found"

Install ShellCheck on your system. See the Requirements section.

### "mcp package not installed"

```bash
pip install mcp
# or
uvx shellcheck-mcp-server
```

### MCP Server Not Connecting

1. Verify ShellCheck is installed: `shellcheck --version`
2. Test the server manually: `python3 shellcheck_mcp_server.py`
3. Check the MCP client logs for connection errors

### Timeout Errors

Increase the timeout in your MCP configuration:

```jsonc
{
  "mcp": {
    "shellcheck": {
      "timeout": 120000
    }
  }
}
```

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Lint Code

```bash
ruff check .
```

## File Structure

```
mcp-shellcheck/
├── shellcheck_mcp_server.py  # Main MCP server script
├── requirements.txt           # Python dependencies
├── pyproject.toml            # Package configuration
├── README.md                 # This documentation
├── CONFIG_EXAMPLES.md        # Configuration examples
└── tests/                    # Test files (optional)
```

## Publishing to PyPI

### Prerequisites

1. Create a PyPI account at https://pypi.org
2. Create an API token at https://pypi.org/manage/account/

### Option 1: Manual Publishing

```bash
# Build the package
uv build

# Publish to PyPI
uv publish

# Or test first with Test PyPI
uv publish --test
```

### Option 2: GitHub Actions (Recommended)

1. Create a GitHub repository
2. Add your PyPI token as a secret:
   - Go to Settings → Secrets and variables → Actions
   - Add `PYPI_API_TOKEN` with your PyPI token
3. Create a release on GitHub or manually trigger the workflow

### Option 3: Local Publishing with Token

```bash
# Set up token
uv publish --token your-api-token
```

## License

MIT License

## Credits

- [ShellCheck](https://www.shellcheck.net/) - The underlying shell script linting tool
  - Original author: [Viktor Eriksson](https://github.com/koalaman)
  - Source: https://github.com/koalaman/shellcheck
- [MCP SDK](https://github.com/modelcontextprotocol/python-sdk) - Python SDK for MCP
