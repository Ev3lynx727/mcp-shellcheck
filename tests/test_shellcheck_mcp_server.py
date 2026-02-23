"""
Tests for mcp-shellcheck server.

Run with: pytest tests/
"""

import json
import subprocess
import pytest
from unittest.mock import patch, MagicMock

# Import the module under test
import sys
sys.path.insert(0, '/home/ev3lynx/mcp-shellcheck')
from shellcheck_mcp_server import (
    validate_inputs,
    run_shellcheck_sync,
    run_shellcheck_async,
    McpError,
    ValidationError,
    APP_NAME,
    APP_VERSION,
)


# ============================================
# Validation Tests
# ============================================

class TestValidateInputs:
    """Test input validation function."""

    def test_requires_either_file_or_content(self):
        """Validation fails when neither file_path nor script_content provided."""
        err = validate_inputs(None, None, "bash")
        assert err is not None
        assert "Either file_path or script_content must be provided" in err.message

    def test_cannot_have_both_file_and_content(self):
        """Validation fails when both file_path and script_content provided."""
        err = validate_inputs("/path/to/file.sh", "echo test", "bash")
        assert err is not None
        assert "Cannot specify both" in err.message

    def test_missing_file(self):
        """Validation fails when file does not exist."""
        err = validate_inputs("/nonexistent/file.sh", None, "bash")
        assert err is not None
        assert "File not found" in err.message

    def test_nonexistent_shell(self):
        """Validation fails for unsupported shell type."""
        err = validate_inputs(None, "echo test", "zsh")
        assert err is not None
        assert "Unsupported shell" in err.message
        assert "bash" in err.message

    def test_script_too_large(self):
        """Validation fails when script_content exceeds limit."""
        large_content = "x" * (10_000_000 + 1)
        err = validate_inputs(None, large_content, "bash")
        assert err is not None
        assert "too large" in err.message.lower()

    def test_valid_file(self, tmp_path):
        """Validation passes for existing file."""
        test_file = tmp_path / "test.sh"
        test_file.write_text("echo hello")
        err = validate_inputs(str(test_file), None, "bash")
        assert err is None

    def test_valid_content(self):
        """Validation passes for reasonable script content."""
        err = validate_inputs(None, "echo hello", "bash")
        assert err is None

    def test_all_shells_allowed(self):
        """All documented shells should be allowed."""
        for shell in ["bash", "sh", "dash", "ksh", "ash"]:
            err = validate_inputs(None, "echo test", shell)
            assert err is None, f"Shell {shell} should be allowed"


# ============================================
# ShellCheck Sync Runner Tests
# ============================================

class TestRunShellcheckSync:
    """Test the synchronous shellcheck runner."""

    @pytest.fixture
    def mock_subprocess(self):
        """Fixture to mock subprocess.run."""
        with patch('subprocess.run') as mock:
            yield mock

    def test_successful_check_returns_results(self, mock_subprocess):
        """Successful shellcheck returns parsed JSON results."""
        # Mock shellcheck output with typical JSON format
        mock_output = json.dumps([
            {
                "file": "test.sh",
                "line": 1,
                "column": 5,
                "level": "warning",
                "code": "SC2086",
                "message": "Double quote to prevent globbing"
            }
        ])

        mock_result = MagicMock()
        mock_result.stdout = mock_output
        mock_result.stderr = ""
        mock_result.returncode = 1  # ShellCheck returns 1 when issues found
        mock_subprocess.return_value = mock_result

        result = run_shellcheck_sync(
            cmd="shellcheck",
            script_content="cat `ls *.txt`",
            shell="bash"
        )

        assert result["success"] is False  # returncode 1 means issues found
        assert len(result["results"]) == 1
        assert result["results"][0]["code"] == "SC2086"
        assert "issue" in result["message"].lower()

    def test_no_issues_returns_success(self, mock_subprocess):
        """Clean script returns success with empty results."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        result = run_shellcheck_sync(
            cmd="shellcheck",
            script_content="echo 'hello world'",
            shell="bash"
        )

        assert result["success"] is True
        assert len(result["results"]) == 0
        assert "No issues found" in result["message"]

    def test_timeout_returns_error(self, mock_subprocess):
        """Subprocess timeout returns error."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired("shellcheck", 30)

        result = run_shellcheck_sync(
            cmd="shellcheck",
            script_content="echo test",
            shell="bash"
        )

        assert result["success"] is False
        assert "timed out" in result["error"].lower()

    def test_shellcheck_not_found(self, mock_subprocess):
        """FileNotFoundError returns helpful error."""
        mock_subprocess.side_effect = FileNotFoundError()

        result = run_shellcheck_sync(
            cmd="shellcheck",
            script_content="echo test",
            shell="bash"
        )

        assert result["success"] is False
        assert "not found" in result["error"].lower()

    def test_invalid_json_returns_error(self, mock_subprocess):
        """Non-JSON output returns error with details."""
        mock_result = MagicMock()
        mock_result.stdout = "Some invalid output: SC2086: test:1:5: warning: something"
        mock_result.stderr = ""
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        result = run_shellcheck_sync(
            cmd="shellcheck",
            script_content="bad script",
            shell="bash"
        )

        assert result["success"] is False
        assert "Failed to parse" in result["error"]

    def test_file_path_used_correctly(self, mock_subprocess):
        """When file_path provided, it's appended to command."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        run_shellcheck_sync(
            cmd="shellcheck",
            file_path="/path/to/script.sh",
            shell="bash"
        )

        # Check that file path was passed to subprocess
        called_cmd = mock_subprocess.call_args[0][0]
        assert "/path/to/script.sh" in called_cmd

    def test_script_content_passed_via_stdin(self, mock_subprocess):
        """When script_content provided, it's passed as stdin."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        run_shellcheck_sync(
            cmd="shellcheck",
            script_content="echo test",
            shell="bash"
        )

        # Check that input was passed
        call_kwargs = mock_subprocess.call_args[1]
        assert "input" in call_kwargs
        assert call_kwargs["input"] == "echo test"

    def test_exclude_flags_passed(self, mock_subprocess):
        """Exclude parameter converts to -e flag."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        run_shellcheck_sync(
            cmd="shellcheck",
            script_content="echo test",
            shell="bash",
            exclude="SC1090,SC2148"
        )

        called_cmd = mock_subprocess.call_args[0][0]
        assert "-e" in called_cmd
        assert "SC1090,SC2148" in called_cmd

    def test_json_format_always_used(self, mock_subprocess):
        """ShellCheck is always called with -f json."""
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        run_shellcheck_sync(
            cmd="shellcheck",
            script_content="echo test",
            shell="bash"
        )

        called_cmd = mock_subprocess.call_args[0][0]
        assert "-f" in called_cmd
        assert "json" in called_cmd


# ============================================
# Integration Tests (Optional - require actual shellcheck)
# ============================================

@pytest.mark.integration
class TestIntegration:
    """Integration tests with real shellcheck binary."""

    def test_real_shellcheck_simple(self):
        """Test with actual shellcheck if available."""
        # Simple valid script
        script = "#!/bin/bash\necho 'Hello, World!'"
        result = run_shellcheck_sync(
            cmd="shellcheck",
            script_content=script,
            shell="bash"
        )
        # Should succeed or at least not error about shellcheck binary
        assert "success" in result

    def test_real_shellcheck_with_issue(self):
        """Test with actual shellcheck on problematic script."""
        # Script with common issues: unquoted glob, backticks, etc.
        script = "#!/bin/bash\ncat *.txt"
        result = run_shellcheck_sync(
            cmd="shellcheck",
            script_content=script,
            shell="bash"
        )
        # Should find at least one issue (shellcheck is strict)
        assert len(result["results"]) > 0, f"Expected issues, got: {result}"
        # Check for any non-style severity issue (numeric codes: 2035, 2086, etc.)
        codes = [str(issue["code"]) for issue in result["results"]]
        # Accept any of common warnings (without SC prefix in JSON)
        expected_codes = {"2035", "2086", "2015", "2044"}
        assert any(code in expected_codes for code in codes), f"Codes: {codes}"


# ============================================
# Async Wrapper Tests
# ============================================

class TestAsyncWrapper:
    """Test the async wrapper."""

    @pytest.mark.asyncio
    async def test_async_wrapper_calls_sync(self):
        """Async wrapper should execute sync function in thread."""
        with patch('shellcheck_mcp_server.run_shellcheck_sync') as mock_sync:
            mock_sync.return_value = {"success": True, "results": []}

            result = await run_shellcheck_async(
                cmd="shellcheck",
                script_content="echo test",
                shell="bash"
            )

            assert result["success"] is True
            mock_sync.assert_called_once()


# ============================================
# Constants Tests
# ============================================

def test_version_format():
    """Version should be semantic (x.y.z)."""
    parts = APP_VERSION.split(".")
    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)

def test_all_allowed_shells_are_strings():
    """ALLOWED_SHELLS should be a set of strings."""
    from shellcheck_mcp_server import ALLOWED_SHELLS
    assert isinstance(ALLOWED_SHELLS, set)
    assert all(isinstance(s, str) for s in ALLOWED_SHELLS)
    assert len(ALLOWED_SHELLS) == 5  # bash, sh, dash, ksh, ash
