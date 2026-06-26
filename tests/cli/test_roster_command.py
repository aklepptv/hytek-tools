"""Unit tests for the roster CLI command."""

from pathlib import Path

from hytek_tools.cli.main import main


def test_roster_command(capsys) -> None:
    roster_path = Path(__file__).resolve().parents[2] / "sample" / "roster.csv"

    exit_code = main(["roster", str(roster_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Roster Validation" in captured.out
    assert "Total swimmers: 127" in captured.out
    assert "Missing ID Cards (1)" in captured.out
    assert "GROFF, IZAAC  2013-10-24" in captured.out
    assert "Duplicate ID Cards (0)" in captured.out
    assert "Duplicate DOB + First + Last (0)" in captured.out
    assert "Invalid birthdays (0)" in captured.out
    assert captured.err == ""


def test_roster_missing_file(tmp_path: Path, capsys) -> None:
    path = tmp_path / "missing.csv"

    exit_code = main(["roster", str(path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert f"error: file not found: {path}" in captured.err
