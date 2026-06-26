"""Unit tests for swimmer D01 diff."""

from pathlib import Path

import pytest

from hytek_tools.inspect.cl2_swimmer_diff import (
    compare_swimmer_d01_records,
    format_cl2_swimmer_diff,
)
from hytek_tools.writers.cl2 import fix_cl2_middle_initials, fix_cl2_teamunify_ids

NATHAN_D01 = (
    "D01MA      Kleppinger, Nathan                      A   1014200718MM  "
    "503 22 15OV06232026                              31.57Y     1 6     4"
    "       4  03      NN19"
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


def test_compare_identical_files_reports_no_changes(
    sample_cl2_path: Path,
) -> None:
    report = compare_swimmer_d01_records(
        sample_cl2_path,
        sample_cl2_path,
        "Nathan Kleppinger",
    )

    assert report.before_record_count == 3
    assert report.after_record_count == 3
    assert len(report.records) == 3
    assert report.unchanged_records == 3
    assert report.modified_records == 0
    assert report.modified_records_identical is None
    assert all(not entry.byte_changes for entry in report.records)
    assert all(not entry.parsed_field_diffs for entry in report.records)

    output = format_cl2_swimmer_diff(report)
    assert "All modified records identical: (none)" in output
    assert "Changed bytes: (none)" in output


def test_compare_nathan_middle_initial_fix(
    sample_cl2_path: Path,
    roster_path: Path,
    tmp_path: Path,
) -> None:
    after_path = tmp_path / "mi-fixed.cl2"
    fix_cl2_middle_initials(sample_cl2_path, roster_path, after_path)

    report = compare_swimmer_d01_records(
        sample_cl2_path,
        after_path,
        "Nathan Kleppinger",
    )

    assert report.before_record_count == 3
    assert report.after_record_count == 3
    assert len(report.records) == 3
    assert report.unchanged_records == 0
    assert report.modified_records == 3
    assert report.modified_records_identical is True
    assert report.unpaired_before_line_numbers == ()
    assert report.unpaired_after_line_numbers == ()

    for entry in report.records:
        assert len(entry.byte_changes) == 1
        change = entry.byte_changes[0]
        assert change.record_offset == 30
        assert change.before_byte == ord(" ")
        assert change.after_byte == ord("T")
        assert len(entry.parsed_field_diffs) == 1
        assert entry.parsed_field_diffs[0].field_name == "middle_initial"
        assert entry.parsed_field_diffs[0].before_value == "(none)"
        assert entry.parsed_field_diffs[0].after_value == "T"

    output = format_cl2_swimmer_diff(report)
    assert "All modified records identical: yes" in output
    assert "middle_initial: (none) -> T" in output
    assert "record@30" in output
    assert "20 -> 54" in output
    assert "Identical modification pattern" in output


def test_compare_nathan_teamunify_id_fix(
    sample_cl2_path: Path,
    roster_path: Path,
    tmp_path: Path,
) -> None:
    after_path = tmp_path / "id-fixed.cl2"
    fix_cl2_teamunify_ids(sample_cl2_path, roster_path, after_path)

    report = compare_swimmer_d01_records(
        sample_cl2_path,
        after_path,
        "Nathan Kleppinger",
    )

    assert report.modified_records == 3
    assert report.modified_records_identical is True

    for entry in report.records:
        diff_fields = {diff.field_name for diff in entry.parsed_field_diffs}
        assert diff_fields == {"middle_initial", "teamunify_id"}
        teamunify_diff = next(
            diff
            for diff in entry.parsed_field_diffs
            if diff.field_name == "teamunify_id"
        )
        assert teamunify_diff.after_value == "101407NATTKLEP"
        assert entry.byte_changes
        assert all(
            change.record_offset >= 39 and change.record_offset < 53
            for change in entry.byte_changes
        )


def test_compare_single_record_fixture(tmp_path: Path) -> None:
    before_path = tmp_path / "before.cl2"
    after_path = tmp_path / "after.cl2"
    before_path.write_bytes(NATHAN_D01.encode("latin-1") + b"\n")
    after_path.write_bytes(
        NATHAN_D01[:30].encode("latin-1")
        + b"T"
        + NATHAN_D01[31:].encode("latin-1")
        + b"\n"
    )

    report = compare_swimmer_d01_records(before_path, after_path, "Nathan Kleppinger")

    assert len(report.records) == 1
    entry = report.records[0]
    assert entry.file_offset_before == 0
    assert entry.file_offset_after == 0
    assert entry.byte_changes[0].file_offset_before == 30
    assert entry.byte_changes[0].file_offset_after == 30


def test_compare_reports_unpaired_line_numbers(tmp_path: Path) -> None:
    before_path = tmp_path / "before.cl2"
    after_path = tmp_path / "after.cl2"
    before_path.write_bytes(
        NATHAN_D01.encode("latin-1") + b"\n" + NATHAN_D01.encode("latin-1") + b"\n"
    )
    after_path.write_bytes(NATHAN_D01.encode("latin-1") + b"\n")

    report = compare_swimmer_d01_records(before_path, after_path, "Nathan Kleppinger")

    assert len(report.records) == 1
    assert report.unpaired_before_line_numbers == (2,)
    assert report.unpaired_after_line_numbers == ()


def test_compare_invalid_name_query(sample_cl2_path: Path) -> None:
    with pytest.raises(ValueError, match="first and last name"):
        compare_swimmer_d01_records(
            sample_cl2_path,
            sample_cl2_path,
            "Nathan",
        )
