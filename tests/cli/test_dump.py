"""Unit tests for the dump CLI command."""

from pathlib import Path

from hytek_tools.cli.main import main

SAMPLE_HY3 = """\
D0header
D1swimmer1
D3event1
"""


def test_dump_command(tmp_path: Path, capsys) -> None:
    path = tmp_path / "meet.hy3"
    path.write_text(SAMPLE_HY3, encoding="latin-1")

    exit_code = main(["dump", str(path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    assert "Record 1\n" in captured.out
    assert "  Record type: D0\n" in captured.out
    assert "  Raw text: D0header\n" in captured.out
    assert "Record 3\n" in captured.out
    assert "  Raw text: D3event1\n" in captured.out


def test_dump_missing_file(tmp_path: Path, capsys) -> None:
    path = tmp_path / "missing.hy3"

    exit_code = main(["dump", str(path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert f"error: file not found: {path}" in captured.err
