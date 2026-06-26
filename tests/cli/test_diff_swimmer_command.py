"""Unit tests for the diff-swimmer CLI command."""

from pathlib import Path

from hytek_tools.cli.main import main
from hytek_tools.writers.cl2 import fix_cl2_middle_initials


def test_diff_swimmer_command(tmp_path: Path, capsys) -> None:
    root = Path(__file__).resolve().parents[2]
    before_path = root / "sample" / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    roster_path = root / "sample" / "roster.csv"
    after_path = tmp_path / "MeetResults-mi-fixed.cl2"
    fix_cl2_middle_initials(before_path, roster_path, after_path)

    exit_code = main(
        [
            "diff-swimmer",
            "--before",
            str(before_path),
            "--after",
            str(after_path),
            "--name",
            "Nathan Kleppinger",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "CL2 Swimmer D01 Diff" in captured.out
    assert "D01 records before: 3" in captured.out
    assert "D01 records after: 3" in captured.out
    assert "All modified records identical: yes" in captured.out
    assert "middle_initial: (none) -> T" in captured.out
    assert "Changed bytes:" in captured.out
    assert "Identical modification pattern" in captured.out
    assert captured.err == ""


def test_diff_swimmer_identical_files(capsys) -> None:
    cl2_path = (
        Path(__file__).resolve().parents[2]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )

    exit_code = main(
        [
            "diff-swimmer",
            "--before",
            str(cl2_path),
            "--after",
            str(cl2_path),
            "--name",
            "Nathan Kleppinger",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Unchanged records: 3" in captured.out
    assert "Modified records: 0" in captured.out
    assert captured.err == ""


def test_diff_swimmer_missing_before_file(tmp_path: Path, capsys) -> None:
    before_path = tmp_path / "missing.cl2"
    after_path = tmp_path / "after.cl2"
    after_path.write_bytes(b"A01Meet\n")

    exit_code = main(
        [
            "diff-swimmer",
            "--before",
            str(before_path),
            "--after",
            str(after_path),
            "--name",
            "Nathan Kleppinger",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert f"error: file not found: {before_path}" in captured.err


def test_diff_swimmer_invalid_name_query(tmp_path: Path, capsys) -> None:
    cl2_path = tmp_path / "meet.cl2"
    cl2_path.write_text("A01Meet\n", encoding="latin-1")

    exit_code = main(
        [
            "diff-swimmer",
            "--before",
            str(cl2_path),
            "--after",
            str(cl2_path),
            "--name",
            "Nathan",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "error: name query must include first and last name" in captured.err
