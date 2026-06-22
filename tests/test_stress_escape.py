import json
from unittest.mock import patch, MagicMock
from shellcheck_mcp_server import run_shellcheck_sync, SHELLCHECK_CMD


def test_script_with_backslashes():
    script = "echo \"hello\\\"world\"\npath=C:\\Users\\test\nregex=\"^foo\\bar$\"\nescaped=\\\\\n"
    result = run_shellcheck_sync(cmd=SHELLCHECK_CMD, script_content=script, shell="bash")
    serialized = json.dumps(result)
    parsed = json.loads(serialized)
    assert parsed["success"] is True or parsed["success"] is False
    print(f"  Backslashes: OK ({len(result['results'])} issues)")


def test_script_with_quotes():
    script = '#!/bin/bash\necho "double quotes with single inside"\necho '"'"'single quotes with double inside'"'"'\necho `backticks with "quotes"`\nprintf "%s\\n" "$var"\n'
    result = run_shellcheck_sync(cmd=SHELLCHECK_CMD, script_content=script, shell="bash")
    serialized = json.dumps(result)
    parsed = json.loads(serialized)
    assert "success" in parsed
    print(f"  Quotes: OK ({len(result['results'])} issues)")


def test_script_with_special_chars():
    script = (
        "#!/bin/bash\n"
        "# Tab\tseparated\tvalues\n"
        'echo "line1"\n'
        "echo 'line2'\n"
        "echo $((1 + 2))\n"
        "echo ${VAR:-default}\n"
        "echo $(command sub)\n"
        '# Unicode: nino, nihongo, shalom\n'
        'echo "Stephane resume"\n'
    )
    result = run_shellcheck_sync(cmd=SHELLCHECK_CMD, script_content=script, shell="bash")
    serialized = json.dumps(result)
    parsed = json.loads(serialized)
    assert "success" in parsed
    print(f"  Special chars: OK ({len(result['results'])} issues)")


def test_json_response_roundtrip():
    script = "#!/bin/bash\ncat `ls *.txt`\nrm -rf $BUILD_DIR/*\neval $(curl -s $URL)\n"
    result = run_shellcheck_sync(cmd=SHELLCHECK_CMD, script_content=script, shell="bash")
    response_json = json.dumps(result, indent=2)
    assert isinstance(response_json, str)
    assert len(response_json) > 0
    parsed = json.loads(response_json)
    assert "success" in parsed
    assert "results" in parsed
    assert "message" in parsed
    for issue in parsed["results"]:
        assert isinstance(issue["message"], str)
    print(f"  Roundtrip: OK ({len(result['results'])} issues, {len(response_json)} bytes)")


def test_mock_control_chars_in_message():
    mock_issues = [
        {"line": 1, "column": 1, "level": "error", "code": 9999,
         "message": "Line with \n newline \t tab \r return"},
    ]
    mock_json = json.dumps(mock_issues)
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(stdout=mock_json, stderr="", returncode=1)
        result = run_shellcheck_sync(cmd="sc", script_content="x")

    response_json = json.dumps(result, indent=2)
    parsed = json.loads(response_json)
    msg = parsed["results"][0]["message"]
    assert "\n" in msg
    assert "\t" in msg
    print("  Control chars in message: OK")


def test_mock_backslash_apocalypse():
    payload = "\\\\ \\' \\\" \\n \\t \\u0041 \\x41 \\${} \\` \\!"
    mock_issues = [
        {"line": 1, "column": 1, "level": "warning", "code": 1111,
         "message": payload * 100},
    ]
    mock_json = json.dumps(mock_issues)
    with patch("subprocess.run") as mock:
        mock.return_value = MagicMock(stdout=mock_json, stderr="", returncode=1)
        result = run_shellcheck_sync(cmd="sc", script_content="x")

    response_json = json.dumps(result, indent=2)
    parsed = json.loads(response_json)
    recovered = parsed["results"][0]["message"]
    assert recovered == payload * 100
    print(f"  Backslash apocalypse ({len(recovered)} chars): roundtrip preserved")


if __name__ == "__main__":
    test_script_with_backslashes()
    test_script_with_quotes()
    test_script_with_special_chars()
    test_json_response_roundtrip()
    test_mock_control_chars_in_message()
    test_mock_backslash_apocalypse()
    print("\nAll escape tests passed!")
