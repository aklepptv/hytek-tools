"""Unit tests for the fix-cl2 CLI command."""

from pathlib import Path

from hytek_tools.cli.main import main


def test_fix_cl2_command(tmp_path: Path, capsys) -> None:
    root = Path(__file__).resolve().parents[2]
    cl2_path = root / "sample" / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    roster_path = root / "sample" / "roster.csv"
    output_path = tmp_path / "MeetResults-fixed.cl2"

    exit_code = main(
        [
            "fix-cl2",
            "--cl2",
            str(cl2_path),
            "--roster",
            str(roster_path),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.is_file()
    assert "Fix CL2 Summary" in captured.out
    assert "IDs written: 270" in captured.out
    assert "Records unchanged: 370" in captured.out
    assert captured.err == ""


def test_fix_cl2_missing_cl2_file(tmp_path: Path, capsys) -> None:
    roster_path = tmp_path / "roster.csv"
    roster_path.write_text("Birthday,Gender,ID Card #\n", encoding="utf-8")
    cl2_path = tmp_path / "missing.cl2"
    output_path = tmp_path / "fixed.cl2"

    exit_code = main(
        [
            "fix-cl2",
            "--cl2",
            str(cl2_path),
            "--roster",
            str(roster_path),
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert f"error: file not found: {cl2_path}" in captured.err
