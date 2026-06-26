"""Unit tests for the diff-cl2 CLI command."""

from pathlib import Path

from hytek_tools.cli.main import main
from hytek_tools.writers.cl2 import fix_cl2_teamunify_ids


def test_diff_cl2_command(tmp_path: Path, capsys) -> None:
    root = Path(__file__).resolve().parents[2]
    original_path = (
        root / "sample" / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )
    roster_path = root / "sample" / "roster.csv"
    modified_path = tmp_path / "fixed.cl2"
    fix_cl2_teamunify_ids(original_path, roster_path, modified_path)

    exit_code = main(
        [
            "diff-cl2",
            "--original",
            str(original_path),
            "--new",
            str(modified_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "CL2 Binary Diff" in captured.out
    assert "Changed records: 270" in captured.out
    assert "Unchanged records: 1101" in captured.out
    assert "Changed record" in captured.out
    assert "Record type: D01" in captured.out
    assert "Byte offset:" in captured.out
    assert "Original bytes:" in captured.out
    assert "New bytes:" in captured.out
    assert "ASCII original:" in captured.out
    assert "ASCII new:" in captured.out
    assert captured.err == ""


def test_diff_cl2_identical_files(tmp_path: Path, capsys) -> None:
    cl2_path = tmp_path / "meet.cl2"
    cl2_path.write_bytes(b"A01Meet\n")

    exit_code = main(
        [
            "diff-cl2",
            "--original",
            str(cl2_path),
            "--new",
            str(cl2_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Changed records: 0" in captured.out
    assert "Unchanged records: 1" in captured.out
    assert captured.err == ""


def test_diff_cl2_missing_original_file(tmp_path: Path, capsys) -> None:
    original_path = tmp_path / "missing.cl2"
    new_path = tmp_path / "new.cl2"
    new_path.write_bytes(b"A01Meet\n")

    exit_code = main(
        [
            "diff-cl2",
            "--original",
            str(original_path),
            "--new",
            str(new_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert f"error: file not found: {original_path}" in captured.err
