"""Unit tests for the audit CLI command."""

import csv
from pathlib import Path

from hytek_tools.cli.main import main


def test_audit_command(capsys) -> None:
    root = Path(__file__).resolve().parents[2]
    cl2_path = (
        root
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-Souderton Dolphins-MA-001.cl2"
    )
    roster_path = root / "sample" / "roster.csv"

    exit_code = main(
        [
            "audit",
            "--cl2",
            str(cl2_path),
            "--roster",
            str(roster_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Identity Audit" in captured.out
    assert "Nathan Kleppinger" in captured.out
    assert "✓ Identity matches" in captured.out
    assert captured.err == ""


def test_audit_command_writes_csv(tmp_path: Path, capsys) -> None:
    root = Path(__file__).resolve().parents[2]
    cl2_path = root / "sample" / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    roster_path = root / "sample" / "roster.csv"
    csv_path = tmp_path / "audit.csv"

    exit_code = main(
        [
            "audit",
            "--cl2",
            str(cl2_path),
            "--roster",
            str(roster_path),
            "--csv",
            str(csv_path),
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert csv_path.is_file()
    assert "Identity differences:" in captured.out
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))
    assert rows[0][0] == "last_name"
    assert len(rows) > 1
    assert captured.err == ""


def test_audit_missing_cl2_file(tmp_path: Path, capsys) -> None:
    cl2_path = tmp_path / "missing.cl2"
    roster_path = tmp_path / "roster.csv"
    roster_path.write_text("Birthday,Gender,ID Card #\n", encoding="utf-8")

    exit_code = main(
        [
            "audit",
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
