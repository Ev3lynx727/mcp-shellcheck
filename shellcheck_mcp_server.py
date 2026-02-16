#!/usr/bin/env python3
"""
ShellCheck MCP Server

A Model Context Protocol (MCP) server that provides shell script linting
via ShellCheck. Allows AI agents to analyze shell scripts for common errors,
stylistic issues, and potential bugs.

Usage:
    python3 shellcheck_mcp_server.py

Or with uvx:
    uvx shellcheck-mcp-server
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
except ImportError:
    print("Error: mcp package not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)


class McpError(Exception):
    """Custom MCP Error exception."""

    pass


APP_NAME = "shellcheck-mcp-server"
APP_VERSION = "0.1.0"


def run_shellcheck(
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
    Run shellcheck on a file or script content.

    Args:
        file_path: Path to the shell script file
        script_content: Raw shell script content to check
        shell: Shell type (bash, sh, dash, etc.)
        check_sourced: Enable checks for sourced files
        enable_all: Enable all optional checks
        exclude: Comma-separated list of warning codes to exclude
        include: Comma-separated list of enabled checks
        severity: Minimum severity level (error, warning, info, style)

    Returns:
        Dictionary with results or error information
    """
    cmd = ["shellcheck"]

    if shell:
        cmd.extend(["-s", shell])

    if check_sourced:
        cmd.append("-S")

    if enable_all:
        cmd.append("-a")

    if exclude:
        cmd.extend(["-e", exclude])

    if include:
        cmd.extend(["-i", include])

    if severity:
        cmd.extend(["-f", "json"])

    if file_path:
        cmd.append(file_path)
    elif script_content:
        cmd.extend(["-s", shell or "bash"])
    else:
        return {
            "success": False,
            "error": "Either file_path or script_content must be provided",
            "results": [],
        }

    try:
        if script_content:
            result = subprocess.run(
                cmd,
                input=script_content,
                capture_output=True,
                text=True,
                timeout=30,
            )
        else:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
            )

        output = result.stdout + result.stderr

        if not output.strip():
            return {
                "success": True,
                "message": "No issues found",
                "results": [],
                "exit_code": result.returncode,
            }

        parsed_results = _parse_shellcheck_output(output)

        return {
            "success": result.returncode == 0,
            "message": f"Found {len(parsed_results)} issue(s)",
            "results": parsed_results,
            "exit_code": result.returncode,
            "raw_output": output,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "ShellCheck timed out after 30 seconds",
            "results": [],
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "ShellCheck not found. Please install: https://shellcheck.net",
            "results": [],
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
        }


def _parse_shellcheck_output(output: str) -> list[dict[str, Any]]:
    """
    Parse shellcheck output into structured results.
    Tries JSON first, falls back to text parsing.
    """
    results = []

    for line in output.strip().split("\n"):
        if not line.strip():
            continue

        parts = line.split(":", 3)
        if len(parts) >= 3:
            try:
                line_num = int(parts[1].strip())
            except ValueError:
                line_num = 0

            column = 0
            message = ""
            code = ""

            if len(parts) >= 4:
                message = parts[3].strip() if parts[3] else ""
                code_parts = parts[2].strip().split()
                if code_parts:
                    code = code_parts[0]
                    if len(code_parts) > 1:
                        try:
                            column = int(code_parts[1].strip("^"))
                        except ValueError:
                            pass

            severity = "warning"
            if code.startswith("SC"):
                if code.startswith("SC1"):
                    severity = "info"
                elif code.startswith("SC2"):
                    severity = "warning"
                elif code.startswith("SC10"):
                    severity = "info"
                elif code.startswith("SC20"):
                    severity = "style"

            results.append(
                {
                    "line": line_num,
                    "column": column,
                    "code": code,
                    "message": message,
                    "severity": severity,
                    "raw": line,
                }
            )

    return results


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

Use exclude parameter to suppress specific warnings (e.g., "SC1090,SC2148").""",
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
                            "description": "Shell type to check (bash, sh, dash, ksh, ash)",
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
                description="Get information about the ShellCheck version and capabilities",
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
            result = run_shellcheck(
                file_path=arguments.get("file_path") if arguments else None,
                script_content=arguments.get("script_content") if arguments else None,
                shell=arguments.get("shell", "bash") if arguments else "bash",
                check_sourced=arguments.get("check_sourced", False) if arguments else False,
                enable_all=arguments.get("enable_all", False) if arguments else False,
                exclude=arguments.get("exclude") if arguments else None,
                severity=arguments.get("severity") if arguments else None,
            )
            return [TextContent(type="text", text=json.dumps(result, indent=2))]

        elif name == "shellcheck_info":
            try:
                result = subprocess.run(
                    ["shellcheck", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                version_info = result.stdout.strip() or result.stderr.strip()
            except Exception as e:
                version_info = f"ShellCheck not available: {e}"

            return [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "server": APP_NAME,
                            "version": APP_VERSION,
                            "shellcheck": version_info,
                            "supported_shells": ["bash", "sh", "dash", "ksh", "ash"],
                        },
                        indent=2,
                    ),
                )
            ]

        else:
            raise McpError(f"Unknown tool: {name}")

    return server


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="ShellCheck MCP Server")
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} {APP_VERSION}",
    )
    args = parser.parse_args()

    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main_sync():
    """Synchronous entry point for CLI."""
    import asyncio

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Server stopped", file=sys.stderr)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main_sync()
