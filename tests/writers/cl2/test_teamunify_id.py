"""Unit tests for CL2 TeamUnify ID writer."""

from pathlib import Path

import pytest

from hytek_tools.parsers.cl2.d01 import parse_teamunify_id
from hytek_tools.parsers.cl2.reader import CL2Reader
from hytek_tools.teamunify.compare import build_compare_report_from_files
from hytek_tools.writers.cl2.teamunify_id import (
    fix_cl2_teamunify_ids,
    format_fix_cl2_summary,
    write_teamunify_id_field,
)

SAMPLE_D01 = (
    "D01MA      Kleppinger, Nathan                       A   1014200713MM  "
    "503 20 131406232026   36.93Y                     38.68Y     2 6     0  "
    "     0  03     XNN99"
)


@pytest.fixture
def sample_cl2_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )


@pytest.fixture
def roster_path() -> Path:
    return Path(__file__).resolve().parents[3] / "sample" / "roster.csv"


def test_write_teamunify_id_field_replaces_only_id_slice() -> None:
    updated = write_teamunify_id_field(SAMPLE_D01, "101407NATTKLEP")

    assert updated[:39] == SAMPLE_D01[:39]
    assert updated[39:53] == "101407NATTKLEP"
    assert updated[53:] == SAMPLE_D01[53:]
    assert len(updated) == len(SAMPLE_D01)


def test_fix_cl2_teamunify_ids_sample_summary(
    sample_cl2_path: Path,
    roster_path: Path,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "MeetResults-fixed.cl2"
    original_bytes = sample_cl2_path.read_bytes()

    result = fix_cl2_teamunify_ids(sample_cl2_path, roster_path, output_path)

    assert output_path.is_file()
    assert sample_cl2_path.read_bytes() == original_bytes
    assert result.ids_written == 270
    assert result.records_unchanged == 370
    assert result.ambiguous == 0
    assert result.skipped == 158
    assert format_fix_cl2_summary(result) == (
        "Fix CL2 Summary\n"
        "\n"
        "IDs written: 270\n"
        "Records unchanged: 370\n"
        "Ambiguous: 0\n"
        "Skipped: 158\n"
    )


def test_fix_cl2_writes_nathan_kleppinger_id(
    sample_cl2_path: Path,
    roster_path: Path,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "fixed.cl2"
    fix_cl2_teamunify_ids(sample_cl2_path, roster_path, output_path)

    nathan_records = [
        record
        for record in CL2Reader(output_path).read()
        if record.record_type == "D01" and "Kleppinger, Nathan" in record.raw_text
    ]

    assert nathan_records
    assert all(
        parse_teamunify_id(record.raw_text[39:53]) == "101407NATTKLEP"
        for record in nathan_records
    )


def test_fix_cl2_leaves_non_writable_d01_bytes_unchanged(
    sample_cl2_path: Path,
    roster_path: Path,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "fixed.cl2"
    fix_cl2_teamunify_ids(sample_cl2_path, roster_path, output_path)

    original_records = {
        record.line_number: record.raw_text
        for record in CL2Reader(sample_cl2_path).read()
        if record.record_type == "D01"
    }
    updated_records = {
        record.line_number: record.raw_text
        for record in CL2Reader(output_path).read()
        if record.record_type == "D01"
    }

    for line_number, original in original_records.items():
        updated = updated_records[line_number]
        if original[39:53].strip() and original[39:53].strip()[0].isdigit():
            assert updated == original
            continue

        assert updated[:39] == original[:39]
        assert updated[53:] == original[53:]


def test_fix_cl2_makes_matches_exact(
    sample_cl2_path: Path,
    roster_path: Path,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "fixed.cl2"
    fix_cl2_teamunify_ids(sample_cl2_path, roster_path, output_path)

    report = build_compare_report_from_files(output_path, roster_path)

    # Peyton Rafter keeps a trailing "q" in the D01 name field; once the ID is
    # written, compare resolves middle initial from the ID and leaves "q" in the
    # first name, so that swimmer becomes a name mismatch instead of exact.
    assert len(report.exact_matches) == 99
    assert len(report.teamunify_id_missing_in_cl2) == 0
    assert len(report.name_mismatches) == 1
    peyton = report.name_mismatches[0]
    assert peyton.swimmer.last_name == "Rafter"
    assert peyton.swimmer.first_name == "Peyton q"
    assert peyton.swimmer.teamunify_id == "091408PEYSRAFT"
    nathan = next(
        entry
        for entry in report.exact_matches
        if entry.swimmer.last_name == "Kleppinger"
        and entry.swimmer.first_name == "Nathan"
    )
    assert nathan.swimmer.teamunify_id == "101407NATTKLEP"
