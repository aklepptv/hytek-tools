"""Unit tests for CL2 binary diff."""

from pathlib import Path

import pytest

from hytek_tools.inspect.cl2_diff import compare_cl2_files, format_cl2_diff
from hytek_tools.writers.cl2 import fix_cl2_teamunify_ids

SAMPLE_D01 = (
    "D01MA      Kleppinger, Nathan                       A   1014200713MM  "
    "503 20 131406232026   36.93Y                     38.68Y     2 6     0  "
    "     0  03     XNN99"
)


@pytest.fixture
def sample_cl2_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )


@pytest.fixture
def roster_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sample" / "roster.csv"


def test_compare_identical_files_reports_no_changes(tmp_path: Path) -> None:
    original = tmp_path / "original.cl2"
    original.write_bytes(b"A01Meet\nB01Team\n")

    report = compare_cl2_files(original, original)

    assert report.changed_records == ()
    assert report.unchanged_records == 2
    assert format_cl2_diff(report) == (
        "CL2 Binary Diff\n" "\n" "Changed records: 0\n" "Unchanged records: 2\n"
    )


def test_compare_reports_changed_byte_span(tmp_path: Path) -> None:
    original = tmp_path / "original.cl2"
    modified = tmp_path / "modified.cl2"
    original.write_bytes(SAMPLE_D01.encode("latin-1") + b"\n")
    modified.write_bytes(
        SAMPLE_D01[:39].encode("latin-1")
        + b"101407NATTKLEP"
        + SAMPLE_D01[53:].encode("latin-1")
        + b"\n"
    )

    report = compare_cl2_files(original, modified)

    assert len(report.changed_records) == 1
    entry = report.changed_records[0]
    assert entry.record_number == 1
    assert entry.record_type == "D01"
    assert entry.byte_offset == 39
    assert entry.original_bytes == b"             A"
    assert entry.new_bytes == b"101407NATTKLEP"
    assert report.unchanged_records == 0

    output = format_cl2_diff(report)
    assert "Changed record 1" in output
    assert "Record type: D01" in output
    assert "Byte offset: 39" in output
    assert "ASCII original:              A" in output
    assert "ASCII new: 101407NATTKLEP" in output


def test_compare_reports_added_and_removed_records(tmp_path: Path) -> None:
    original = tmp_path / "original.cl2"
    modified = tmp_path / "modified.cl2"
    original.write_bytes(b"A01Meet\nB01Team\n")
    modified.write_bytes(b"A01Meet\nC01Changed\nD01Added\n")

    report = compare_cl2_files(original, modified)

    assert report.unchanged_records == 1
    assert len(report.changed_records) == 2

    removed = report.changed_records[0]
    assert removed.record_number == 2
    assert removed.record_type == "B0"
    assert removed.byte_offset == 8
    assert removed.original_bytes == b"B01Team"
    assert removed.new_bytes == b"C01Changed"

    added = report.changed_records[1]
    assert added.record_number == 3
    assert added.record_type == "D01"
    assert added.byte_offset == 19
    assert added.original_bytes is None
    assert added.new_bytes == b"D01Added\n"


def test_compare_sample_fix_cl2_output(
    sample_cl2_path: Path,
    roster_path: Path,
    tmp_path: Path,
) -> None:
    fixed = tmp_path / "fixed.cl2"
    fix_cl2_teamunify_ids(sample_cl2_path, roster_path, fixed)

    report = compare_cl2_files(sample_cl2_path, fixed)

    assert report.unchanged_records == 1101
    assert len(report.changed_records) == 270
    assert sample_cl2_path.read_bytes() != fixed.read_bytes()

    nathan = next(
        entry
        for entry in report.changed_records
        if entry.new_bytes == b"101407NATTKLEP"
    )
    assert nathan.record_type == "D01"
