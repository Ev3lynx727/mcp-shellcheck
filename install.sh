#!/usr/bin/env bash
set -eu

REPO="Ev3lynx727/mcp-shellcheck"
VERSION="0.1.3"

echo "  Installing mcp-shellcheck v${VERSION} (${REPO})"

PYTHON=$(command -v python3 || command -v python)
if [ -z "$PYTHON" ]; then
  echo "Error: Python 3.10+ required" >&2
  exit 1
fi

echo "  Installing shellcheck CLI binary..."
$PYTHON -m pip install shellcheck-py -q

if ! command -v shellcheck &>/dev/null; then
  USER_BIN=$($PYTHON -m site --user-base 2>/dev/null)/bin
  if [ -x "$USER_BIN/shellcheck" ]; then
    export PATH="$USER_BIN:$PATH"
    echo "  Located at $USER_BIN/shellcheck"
    echo "  To make permanent, add to your shell rc:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
  else
    echo "  Warning: shellcheck binary not found." >&2
    echo "  Try: sudo apt install shellcheck  # Ubuntu/Debian" >&2
    echo "  Try: brew install shellcheck      # macOS" >&2
  fi
fi

echo "  Installing mcp-shellcheck..."
TMPDIR=$(mktemp -d)
cd "$TMPDIR" || exit 1
curl -fsSL "https://github.com/${REPO}/archive/main.tar.gz" | tar xz --strip=1
$PYTHON -m pip install -e . -q
cd / && rm -rf "$TMPDIR"

echo ""
echo "  Done. Add to your MCP client config:"
cat << JSON
{
  "mcpServers": {
    "shellcheck": {
      "type": "local",
      "command": ["$PYTHON", "-m", "shellcheck_mcp_server"],
      "enabled": true,
      "timeout": 60000
    }
  }
}
JSON
