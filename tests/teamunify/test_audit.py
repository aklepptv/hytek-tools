"""Unit tests for TeamUnify identity audit."""

import csv
from pathlib import Path

import pytest

from hytek_tools.teamunify.audit import (
    build_identity_audit_report_from_files,
    format_identity_audit,
    write_identity_audit_csv,
)


@pytest.fixture
def roster_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sample" / "roster.csv"


@pytest.fixture
def full_meet_cl2_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )


@pytest.fixture
def souderton_cl2_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-Souderton Dolphins-MA-001.cl2"
    )


def test_identity_audit_nathan_kleppinger_matches(
    souderton_cl2_path: Path,
    roster_path: Path,
) -> None:
    report = build_identity_audit_report_from_files(souderton_cl2_path, roster_path)

    nathan = next(
        entry for entry in report.entries if entry.swimmer.last_name == "Kleppinger"
    )

    assert nathan.display_name == "Nathan Kleppinger"
    assert nathan.identity_matches is True
    assert "✓ Identity matches" in format_identity_audit(report)


def test_identity_audit_peyton_rafter_first_name_differs(
    full_meet_cl2_path: Path,
    roster_path: Path,
) -> None:
    report = build_identity_audit_report_from_files(full_meet_cl2_path, roster_path)

    peyton = next(
        entry
        for entry in report.entries
        if entry.swimmer.last_name == "Rafter" and entry.swimmer.first_name == "Peyton"
    )

    assert peyton.identity_matches is False
    first_name = next(
        difference
        for difference in peyton.differences
        if difference.field_name == "first_name"
    )
    assert first_name.cl2_value == "Peyton q"
    assert first_name.roster_value == "Peyton"

    output = format_identity_audit(report)
    assert "Peyton Rafter" in output
    assert "First Name differs" in output
    assert "CL2: Peyton q" in output
    assert "TU : Peyton" in output


def test_identity_audit_phan_le_middle_initial_differs(
    full_meet_cl2_path: Path,
    roster_path: Path,
) -> None:
    report = build_identity_audit_report_from_files(full_meet_cl2_path, roster_path)

    phan = next(entry for entry in report.entries if entry.swimmer.last_name == "Le")

    assert phan.display_name == "Phan Le"
    middle_initial = next(
        difference
        for difference in phan.differences
        if difference.field_name == "middle_initial"
    )
    assert middle_initial.cl2_value == ""
    assert middle_initial.roster_value == "D"

    output = format_identity_audit(report)
    assert "Phan Le" in output
    assert "Middle Initial differs" in output
    assert "CL2:" in output
    assert "TU : D" in output


def test_write_identity_audit_csv_exports_only_differences(
    full_meet_cl2_path: Path,
    roster_path: Path,
    tmp_path: Path,
) -> None:
    report = build_identity_audit_report_from_files(full_meet_cl2_path, roster_path)
    csv_path = tmp_path / "audit.csv"

    write_identity_audit_csv(report, csv_path)

    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle))

    assert rows[0] == [
        "last_name",
        "first_name",
        "field",
        "cl2_value",
        "roster_value",
    ]
    assert [
        "Rafter",
        "Peyton",
        "first_name",
        "Peyton q",
        "Peyton",
    ] in rows
    assert ["Le", "Phan", "middle_initial", "", "D"] in rows
    assert len(rows) > 1
