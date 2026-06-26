"""Unit tests for the swimmers CLI command."""

from pathlib import Path

from hytek_tools.cli.main import main


def test_swimmers_command(capsys) -> None:
    cl2_path = (
        Path(__file__).resolve().parents[2]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )

    exit_code = main(["swimmers", str(cl2_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Swimmer Summary" in captured.out
    assert "Total D01 records: 640" in captured.out
    assert "Unique swimmers: 258" in captured.out
    assert "Additional event entries: 382" in captured.out
    assert "Swimmers missing TeamUnify IDs: 110" in captured.out
    assert "Duplicate identities (0)" in captured.out
    assert captured.err == ""


def test_swimmers_missing_file(tmp_path: Path, capsys) -> None:
    path = tmp_path / "missing.cl2"

    exit_code = main(["swimmers", str(path)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert f"error: file not found: {path}" in captured.err
