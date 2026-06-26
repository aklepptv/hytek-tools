"""Unit tests for the trace CLI command."""

from pathlib import Path

from hytek_tools.cli.main import main


def test_trace_command(capsys) -> None:
    cl2_path = (
        Path(__file__).resolve().parents[2]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )

    exit_code = main(
        [
            "trace",
            "--cl2",
            str(cl2_path),
            "--name",
            "Nathan Kleppinger",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "CL2 Identity Trace" in captured.out
    assert "Records found: 5" in captured.out
    assert "Record type: D01" in captured.out
    assert "Byte offset:" in captured.out
    assert "Raw record:" in captured.out
    assert "Identity Field Occurrences" in captured.out
    assert "Differences" in captured.out
    assert "birth_date:" in captured.out
    assert captured.err == ""


def test_trace_missing_cl2_file(tmp_path: Path, capsys) -> None:
    cl2_path = tmp_path / "missing.cl2"

    exit_code = main(
        [
            "trace",
            "--cl2",
            str(cl2_path),
            "--name",
            "Nathan Kleppinger",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert f"error: file not found: {cl2_path}" in captured.err


def test_trace_invalid_name_query(tmp_path: Path, capsys) -> None:
    cl2_path = tmp_path / "meet.cl2"
    cl2_path.write_text("A01Meet\n", encoding="latin-1")

    exit_code = main(
        [
            "trace",
            "--cl2",
            str(cl2_path),
            "--name",
            "Nathan",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 1
    assert captured.out == ""
    assert "error: name query must include first and last name" in captured.err
