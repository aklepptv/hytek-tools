"""Unit tests for the compare CLI command."""

from pathlib import Path

from hytek_tools.cli.main import main


def test_compare_command(capsys) -> None:
    root = Path(__file__).resolve().parents[2]
    cl2_path = root / "sample" / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    roster_path = root / "sample" / "roster.csv"

    exit_code = main(
        [
            "compare",
            "--cl2",
            str(cl2_path),
            "--roster",
            str(roster_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Comparison Report" in captured.out
    assert "Swimmers: 258" in captured.out
    assert "TeamUnify ID Missing in CL2 (100)" in captured.out
    assert "Missing ID in TeamUnify Roster (1)" in captured.out
    assert "No Match (157)" in captured.out
    assert captured.err == ""


def test_compare_debug_command(capsys) -> None:
    root = Path(__file__).resolve().parents[2]
    cl2_path = root / "sample" / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    roster_path = root / "sample" / "roster.csv"

    exit_code = main(
        [
            "compare",
            "--debug",
            "--cl2",
            str(cl2_path),
            "--roster",
            str(roster_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Compare Debug" in captured.out
    assert "Unique swimmers compared: 258" in captured.out
    assert "Swimmer 20" in captured.out
    assert "Comparison Report" in captured.out
    assert "Exact Match (0)" in captured.out
    assert captured.err == ""


def test_compare_missing_cl2_file(tmp_path: Path, capsys) -> None:
    roster_path = tmp_path / "roster.csv"
    roster_path.write_text("Birthday,Gender,ID Card #\n", encoding="utf-8")
    cl2_path = tmp_path / "missing.cl2"

    exit_code = main(
        [
            "compare",
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


def test_compare_missing_roster_file(tmp_path: Path, capsys) -> None:
    cl2_path = tmp_path / "meet.cl2"
    cl2_path.write_text("A01test\n", encoding="latin-1")
    roster_path = tmp_path / "missing.csv"

    exit_code = main(
        [
            "compare",
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
