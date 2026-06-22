import json
import subprocess
from unittest.mock import patch, MagicMock
from shellcheck_mcp_server import run_shellcheck_sync, SHELLCHECK_CMD, MAX_SCRIPT_SIZE


def test_json_parse_large_output():
    """Stress test: ShellCheck JSON output with thousands of issues."""
    large_warnings = [
        {
            "file": "script.sh",
            "line": i,
            "column": 1,
            "level": "warning",
            "code": 2086,
            "message": "Double quote to prevent globbing and word splitting." * 5,
        }
        for i in range(10_000)
    ]
    large_json = json.dumps(large_warnings)

    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(
            stdout=large_json,
            stderr="",
            returncode=1,
        )
        result = run_shellcheck_sync(cmd="sc", script_content="x")

    assert result["success"] is False
    assert result["message"] == "Found 10000 issue(s)"
    assert len(result["results"]) == 10_000
    print(f"  Parsed 10,000 issues OK ({len(large_json)} bytes of JSON)")


def test_json_parse_single_massive_issue():
    """Stress test: single issue with enormous message text."""
    massive_issue = [
        {
            "file": "script.sh",
            "line": 1,
            "column": 1,
            "level": "error",
            "code": 9999,
            "message": "A" * 500_000,
        }
    ]
    massive_json = json.dumps(massive_issue)

    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(
            stdout=massive_json,
            stderr="",
            returncode=1,
        )
        result = run_shellcheck_sync(cmd="sc", script_content="x")

    assert result["success"] is False
    assert len(result["results"]) == 1
    assert len(result["results"][0]["message"]) == 500_000
    print(f"  Single 500KB message parsed OK ({len(massive_json)} bytes)")


def test_json_parse_unicode_issues():
    """Stress test: Unicode in script content and JSON output."""
    unicode_issues = [
        {
            "file": "脚本.sh",
            "line": i,
            "column": 1,
            "level": "warning",
            "code": 1000 + i,
            "message": f"خطأ في السطر {i}: สคริปต์นี้มีปัญหา",
        }
        for i in range(500)
    ]
    unicode_json = json.dumps(unicode_issues, ensure_ascii=False)

    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(
            stdout=unicode_json,
            stderr="",
            returncode=1,
        )
        result = run_shellcheck_sync(cmd="sc", script_content="x")

    assert result["success"] is False
    assert len(result["results"]) == 500
    assert "脚本" in result["results"][0]["file"]
    print(f"  Unicode (Arabic/Chinese/Thai) 500 issues parsed OK")


def test_json_parse_empty_array():
    """Edge case: empty JSON array (no issues)."""
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(
            stdout="[]",
            stderr="",
            returncode=0,
        )
        result = run_shellcheck_sync(cmd="sc", script_content="x")

    assert result["success"] is True
    assert result["message"] == "No issues found"
    assert len(result["results"]) == 0
    print("  Empty array [] parsed OK")


def test_json_parse_malformed():
    """Edge case: malformed JSON from shellcheck."""
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(
            stdout="{this is not json!!!",
            stderr="",
            returncode=1,
        )
        result = run_shellcheck_sync(cmd="sc", script_content="x")

    assert result["success"] is False
    assert "error" in result
    assert "Failed to parse" in result["error"]
    print("  Malformed JSON handled OK")


def test_json_parse_null_bytes():
    """Edge case: null bytes in JSON output."""
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(
            stdout='[\n  {"line": 1, "message": "null\x00byte"}\n]',
            stderr="",
            returncode=1,
        )
        result = run_shellcheck_sync(cmd="sc", script_content="x")

    assert result["success"] is False
    print(f"  Null bytes in JSON: success={result['success']}")


def test_real_large_script():
    """Integration: check a large generated script against real shellcheck."""
    lines = []
    for i in range(2000):
        lines.append(f'x{i}=$(echo "hello" | grep "test")')
        lines.append(f'if [ -z "$x{i}" ]; then')
        lines.append(f'    echo "processing {i}"')
        lines.append(f'fi')

    script = "\n".join(lines)
    result = run_shellcheck_sync(
        cmd=SHELLCHECK_CMD,
        script_content=script,
        shell="bash",
    )

    assert "results" in result
    assert "success" in result
    print(f"  Real large script ({len(lines)} lines, {len(script)} bytes): "
          f"{len(result['results'])} issues found")


if __name__ == "__main__":
    test_json_parse_large_output()
    test_json_parse_single_massive_issue()
    test_json_parse_unicode_issues()
    test_json_parse_empty_array()
    test_json_parse_malformed()
    test_json_parse_null_bytes()
    test_real_large_script()
    print("\nAll stress tests passed!")
