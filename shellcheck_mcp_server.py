#!/usr/bin/env python3
"""
ShellCheck MCP Server — Refactored

A Model Context Protocol (MCP) server that provides shell script linting
via ShellCheck. Allows AI agents to analyze shell scripts for common errors,
stylistic issues, and potential bugs.

Architecture improvements (v1.0.1):
- Async-compatible: non-blocking subprocess calls
- JSON output parsing: robust, locale-independent
- Input validation: file existence, size limits, shell type
- Structured logging: debug, info, error levels
- Configurable shellcheck path via SHELLCHECK_CMD env
- Proper error boundaries and graceful degradation
"""

import argparse
import asyncio
import json
import logging
import os
import subprocess
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)


# ============================================
# Logging Configuration
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr)],
)
logger = logging.getLogger(__name__)


# ============================================
# Configuration & Constants
# ============================================

APP_NAME = "shellcheck-mcp-server"
APP_VERSION = "0.1.2"

# Configurable via environment
SHELLCHECK_CMD = os.getenv("SHELLCHECK_CMD", "shellcheck")
MAX_SCRIPT_SIZE = 10_000_000  # 10MB
ALLOWED_SHELLS = {"bash", "sh", "dash", "ksh", "ash"}


class McpError(Exception):
    """Custom MCP Error exception."""

    pass


@dataclass
class ValidationError:
    """Validation error details."""

    field: str
    message: str


def validate_inputs(
    file_path: Optional[str],
    script_content: Optional[str],
    shell: str,
) -> Optional[ValidationError]:
    """
    Validate input parameters before running shellcheck.

    Returns ValidationError if invalid, None if valid.
    """
    # Either file_path or script_content required (handled by caller, but double-check)
    if not file_path and not script_content:
        return ValidationError("", "Either file_path or script_content must be provided")

    # Can't have both
    if file_path and script_content:
        return ValidationError("file_path/script_content", "Cannot specify both")

    # Validate file_path if present
    if file_path:
        path = Path(file_path)
        if not path.exists():
            return ValidationError("file_path", f"File not found: {file_path}")
        if not path.is_file():
            return ValidationError("file_path", f"Path is not a file: {file_path}")
        if path.stat().st_size > MAX_SCRIPT_SIZE:
            return ValidationError(
                "file_path",
                f"File too large (max {MAX_SCRIPT_SIZE:,} bytes, got {path.stat().st_size:,})",
            )

    # Validate script_content size
    if script_content and len(script_content) > MAX_SCRIPT_SIZE:
        return ValidationError(
            "script_content",
            f"Script content too large (max {MAX_SCRIPT_SIZE:,} bytes, got {len(script_content):,})",
        )

    # Validate shell type
    if shell not in ALLOWED_SHELLS:
        return ValidationError(
            "shell",
            f"Unsupported shell: {shell}. Must be one of: {', '.join(sorted(ALLOWED_SHELLS))}",
        )

    return None


# ============================================
# Core Linter Interface (Future-proofing)
# ============================================

class Linter(ABC):
    """Abstract linter interface for future multi-linter support."""

    @abstractmethod
    def lint(self, content: str, **kwargs) -> dict[str, Any]:
        """Run linting and return structured results."""
        pass


class ShellCheckLinter(Linter):
    """Concrete ShellCheck linter implementation."""

    def __init__(self, cmd: str = SHELLCHECK_CMD):
        self.cmd = cmd

    def lint(self, content: str, **kwargs) -> dict[str, Any]:
        """Run shellcheck synchronously."""
        return run_shellcheck_sync(cmd=self.cmd, script_content=content, **kwargs)


# ============================================
# ShellCheck Runner (Synchronous)
# ============================================

def run_shellcheck_sync(
    *,
    cmd: str,
    file_path: Optional[str] = None,
    script_content: Optional[str] = None,
    shell: str = "bash",
    check_sourced: bool = False,
    enable_all: bool = False,
    exclude: Optional[str] = None,
    include: Optional[str] = None,
    severity: Optional[str] = None,
) -> dict[str, Any]:
    """
    Run shellcheck synchronously. Used by async wrapper.

    Args:
        cmd: Path to shellcheck binary
        file_path: Path to shell script file
        script_content: Raw shell script content
        shell: Shell type (bash, sh, dash, ksh, ash)
        check_sourced: Enable checks for sourced files
        enable_all: Enable all optional checks
        exclude: Comma-separated warning codes to exclude
        include: Comma-separated enabled checks
        severity: Minimum severity level

    Returns:
        Dictionary with results or error information
    """
    # Build command
    shellcheck_cmd = [cmd]

    if shell:
        shellcheck_cmd.extend(["-s", shell])

    if check_sourced:
        shellcheck_cmd.append("-S")

    if enable_all:
        shellcheck_cmd.append("-a")

    if exclude:
        shellcheck_cmd.extend(["-e", exclude])

    if include:
        shellcheck_cmd.extend(["-i", include])

    # Always use JSON output for robust parsing
    shellcheck_cmd.extend(["-f", "json"])

    if file_path:
        shellcheck_cmd.append(file_path)
    elif script_content:
        # Tell shellcheck to read from stdin
        shellcheck_cmd.append("-")
    else:
        # Should be caught by validation, but defensive
        return {
            "success": False,
            "error": "Either file_path or script_content must be provided",
            "results": [],
        }

    logger.debug("Running shellcheck: cmd=%s, file=%s, content_len=%d",
                shellcheck_cmd, file_path, len(script_content) if script_content else 0)

    try:
        # Run subprocess
        if script_content:
            result = subprocess.run(
                shellcheck_cmd,
                input=script_content,
                capture_output=True,
                text=True,
                timeout=30,
            )
        else:
            result = subprocess.run(
                shellcheck_cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

        # Parse JSON output
        if result.stdout.strip():
            try:
                parsed_results = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                logger.warning("Failed to parse shellcheck JSON output: %s", e)
                logger.debug("Raw output: %s", result.stdout[:500])
                return {
                    "success": False,
                    "error": f"Failed to parse shellcheck output: {e}",
                    "results": [],
                    "exit_code": result.returncode,
                }
        else:
            parsed_results = []

        # Determine success (shellcheck returns 0 for no issues, 1 for issues found)
        success = result.returncode == 0

        logger.info(
            "Shellcheck completed: exit_code=%d, issues=%d, success=%s",
            result.returncode,
            len(parsed_results),
            success,
        )

        return {
            "success": success,
            "message": f"Found {len(parsed_results)} issue(s)" if parsed_results else "No issues found",
            "results": parsed_results,
            "exit_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        logger.error("Shellcheck timed out after 30 seconds")
        return {
            "success": False,
            "error": "ShellCheck timed out after 30 seconds",
            "results": [],
        }
    except FileNotFoundError:
        logger.error("ShellCheck binary not found: %s", cmd)
        return {
            "success": False,
            "error": f"ShellCheck not found at '{cmd}'. Install from https://shellcheck.net",
            "results": [],
        }
    except Exception as e:
        logger.exception("Unexpected error running shellcheck")
        return {
            "success": False,
            "error": str(e),
            "results": [],
        }


# ============================================
# Async Wrapper
# ============================================

async def run_shellcheck_async(**kwargs) -> dict[str, Any]:
    """
    Async wrapper around run_shellcheck_sync.

    Uses thread pool to avoid blocking the MCP server event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: run_shellcheck_sync(**kwargs))


# ============================================
# MCP Server Setup
# ============================================

def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server(APP_NAME)

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="shellcheck",
                description="""Run ShellCheck on a shell script to find bugs, stylistic issues, and potential errors.

Supported shells: bash, sh, dash, ksh, ash

The tool returns structured JSON with issue details including line, column, code, message, and severity.

Common error codes:
- SC1090: Can't follow non-constant source
- SC2148: Tips depend on target shell and yours is unknown
- SC2086: Double quote to prevent globbing
- SC2164: Use cd with || exit
- SC2006: Use $(...) instead of legacy backticks
- SC2029: Note that, unlike in BASH, a variable cannot contain a newline
- SC2230: Which is redundant
- SC2068: Double quote array subscript
- SC2196: Several way to test global flag
- SC2001: See if you can use ${var//search/replace}
- SC2162: read without -r will mangle backslashes
- SC2129: Style: Consider using { cmd1; cmd2; } >> file instead of individual redirects

Use exclude parameter to suppress specific warnings (e.g., "SC1090,SC2148").
Use severity parameter to filter by minimum severity (error, warning, info, style).""",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the shell script file to check",
                        },
                        "script_content": {
                            "type": "string",
                            "description": "Raw shell script content to check (alternative to file_path)",
                        },
                        "shell": {
                            "type": "string",
                            "description": "Shell type to check",
                            "enum": ["bash", "sh", "dash", "ksh", "ash"],
                            "default": "bash",
                        },
                        "check_sourced": {
                            "type": "boolean",
                            "description": "Enable checks for sourced files",
                            "default": False,
                        },
                        "enable_all": {
                            "type": "boolean",
                            "description": "Enable all optional checks",
                            "default": False,
                        },
                        "exclude": {
                            "type": "string",
                            "description": "Comma-separated list of warning codes to exclude (e.g., 'SC1090,SC2148')",
                        },
                        "severity": {
                            "type": "string",
                            "description": "Minimum severity to report",
                            "enum": ["error", "warning", "info", "style"],
                        },
                    },
                    "oneOf": [
                        {"required": ["file_path"]},
                        {"required": ["script_content"]},
                    ],
                },
            ),
            Tool(
                name="shellcheck_info",
                description="Get information about the ShellCheck version and server capabilities",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict | None) -> list[TextContent]:
        """Handle tool calls."""
        if name == "shellcheck":
            # Validate inputs
            file_path = arguments.get("file_path") if arguments else None
            script_content = arguments.get("script_content") if arguments else None
            shell = arguments.get("shell", "bash") if arguments else "bash"

            validation_error = validate_inputs(file_path, script_content, shell)
            if validation_error:
                error_response = {
                    "success": False,
                    "error": f"Validation error ({validation_error.field}): {validation_error.message}",
                    "results": [],
                }
                return [TextContent(type="text", text=json.dumps(error_response, indent=2))]

            # Run shellcheck asynchronously
            result = await run_shellcheck_async(
                cmd=SHELLCHECK_CMD,
                file_path=file_path,
                script_content=script_content,
                shell=shell,
                check_sourced=arguments.get("check_sourced", False) if arguments else False,
                enable_all=arguments.get("enable_all", False) if arguments else False,
                exclude=arguments.get("exclude") if arguments else None,
                severity=arguments.get("severity") if arguments else None,
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "shellcheck_info":
            try:
                result = subprocess.run(
                    [SHELLCHECK_CMD, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                version_info = result.stdout.strip() or result.stderr.strip()
            except Exception as e:
                logger.error("Failed to get shellcheck version: %s", e)
                version_info = f"ShellCheck not available: {e}"

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "server": APP_NAME,
                            "version": APP_VERSION,
                            "shellcheck": version_info,
                            "shellcheck_cmd": SHELLCHECK_CMD,
                            "supported_shells": sorted(list(ALLOWED_SHELLS)),
                            "max_script_size": MAX_SCRIPT_SIZE,
                        },
                        indent=2,
                    ),
                )
            ]

        else:
            raise McpError(f"Unknown tool: {name}")

    return server


# ============================================
# Main Entry Points
# ============================================

async def main():
    """Main entry point for MCP server."""
    parser = argparse.ArgumentParser(description="ShellCheck MCP Server")
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} {APP_VERSION}",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level",
    )
    args = parser.parse_args()

    # Set log level from argument
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info("Starting %s v%s (shellcheck cmd: %s)", APP_NAME, APP_VERSION, SHELLCHECK_CMD)

    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main_sync():
    """Synchronous entry point for CLI."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception("Fatal error")
        sys.exit(1)


if __name__ == "__main__":
    main_sync()
