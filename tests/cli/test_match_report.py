"""Unit tests for the match-report CLI command."""

from pathlib import Path

from hytek_tools.cli.main import main


def test_match_report_command(
    capsys,
) -> None:
    root = Path(__file__).resolve().parents[2]
    cl2_path = root / "sample" / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    roster_path = root / "sample" / "roster.csv"

    exit_code = main(
        [
            "match-report",
            "--cl2",
            str(cl2_path),
            "--roster",
            str(roster_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Match Report" in captured.out
    assert "Exact matches (100)" in captured.out
    assert "Missing ID Cards (1)" in captured.out
    assert "Unmatched swimmers (157)" in captured.out
    assert captured.err == ""


def test_match_report_missing_cl2_file(tmp_path: Path, capsys) -> None:
    roster_path = tmp_path / "roster.csv"
    roster_path.write_text("Birthday,Gender,ID Card #\n", encoding="utf-8")
    cl2_path = tmp_path / "missing.cl2"

    exit_code = main(
        [
            "match-report",
            "--cl2",
            str(cl2_path),
            "--roster",
            str(roster_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert f"error: file not found: {cl2_path}" in captured.err


def test_match_report_missing_roster_file(tmp_path: Path, capsys) -> None:
    cl2_path = tmp_path / "meet.cl2"
    cl2_path.write_text("A01test\n", encoding="latin-1")
    roster_path = tmp_path / "missing.csv"

    exit_code = main(
        [
            "match-report",
            "--cl2",
            str(cl2_path),
            "--roster",
            str(roster_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert f"error: file not found: {roster_path}" in captured.err
