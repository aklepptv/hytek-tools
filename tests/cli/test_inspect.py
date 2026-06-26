"""Unit tests for the inspect CLI command."""

from pathlib import Path

from hytek_tools.cli.main import main

SAMPLE_HY3 = """\
D0header
D1swimmer1
D1swimmer2
D3event1
E0result1
"""


def test_inspect_command(tmp_path: Path, capsys) -> None:
    path = tmp_path / "meet.hy3"
    path.write_text(SAMPLE_HY3, encoding="latin-1")

    exit_code = main(["inspect", str(path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ("Record counts\n" "\n" "D0 1\n" "D1 2\n" "D3 1\n" "E0 1\n")
    assert captured.err == ""


def test_inspect_missing_file(tmp_path: Path, capsys) -> None:
    path = tmp_path / "missing.hy3"

    exit_code = main(["inspect", str(path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert f"error: file not found: {path}" in captured.err
