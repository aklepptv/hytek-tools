"""Unit tests for CL2 swimmer trace."""

from pathlib import Path

import pytest

from hytek_tools.inspect.cl2_trace import (
    format_cl2_trace,
    parse_swimmer_name_query,
    trace_cl2_swimmer,
)

NATHAN_D01 = (
    "D01MA      Kleppinger, Nathan                      A   1014200718MM  "
    "503 22 15OV06232026                              31.57Y     1 6     4"
    "       4  03      NN19"
)
NATHAN_F01 = (
    "F01MA          MASOUDAKleppinger, Nathan                         "
    "1014200718M  3                                                              "
    "N07"
)
NATHAN_G01 = (
    "G01MA          Kleppinger, Nathan                      1 4   0C"
    "                                                                                "
    "F             N84"
)
PHAN_D01 = (
    "D01        Phan, Nathan                C1F230F7EF4CA   1118201411MM  "
    "504  8 111206232026                              34.96Y     1 7     2"
    "  3.   2  0400    NN08"
)


@pytest.fixture
def sample_cl2_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )


def test_parse_swimmer_name_query() -> None:
    assert parse_swimmer_name_query("Nathan Kleppinger") == ("Nathan", "Kleppinger")


def test_parse_swimmer_name_query_requires_two_parts() -> None:
    with pytest.raises(ValueError, match="first and last name"):
        parse_swimmer_name_query("Nathan")


def test_trace_cl2_swimmer_finds_nathan_records_on_sample(
    sample_cl2_path: Path,
) -> None:
    report = trace_cl2_swimmer(sample_cl2_path, "Nathan Kleppinger")

    assert len(report.records) == 5
    assert {entry.record_type for entry in report.records} == {"D01", "F0", "G0"}
    assert report.first_name == "Nathan"
    assert report.last_name == "Kleppinger"
    assert all(
        entry.parsed_fields[1][1] == "Kleppinger"
        for entry in report.records
        if entry.record_type == "D01"
    )
    assert report.records[3].parsed_fields[0][1] == "Kleppinger"


def test_trace_cl2_swimmer_highlights_birth_date_difference(
    sample_cl2_path: Path,
) -> None:
    report = trace_cl2_swimmer(sample_cl2_path, "Nathan Kleppinger")

    birth_difference = next(
        difference
        for difference in report.differences
        if difference.field_name == "birth_date"
    )
    assert birth_difference.values_by_record == (
        (1, "2007-10-14"),
        (2, "2007-10-14"),
        (3, "2007-10-14"),
        (4, "2007-10-14"),
        (5, None),
    )


def test_trace_cl2_swimmer_reports_identity_occurrences(tmp_path: Path) -> None:
    cl2_path = tmp_path / "meet.cl2"
    cl2_path.write_text(
        "\n".join([NATHAN_D01, NATHAN_F01, NATHAN_G01]) + "\n",
        encoding="latin-1",
    )

    output = format_cl2_trace(trace_cl2_swimmer(cl2_path, "Nathan Kleppinger"))

    assert "CL2 Identity Trace" in output
    assert "Records found: 3" in output
    assert "Record type: D01" in output
    assert "Record type: F0" in output
    assert "Record type: G0" in output
    assert "Byte offset:" in output
    assert "Raw record:" in output
    assert "Parsed fields:" in output
    assert "Identity Field Occurrences" in output
    assert "first_name:" in output
    assert "middle_initial:" in output
    assert "last_name:" in output
    assert "birth_date:" in output
    assert "registration_id:" in output
    assert "Differences" in output
    assert "birth_date:" in output.split("Differences", maxsplit=1)[1]


def test_trace_cl2_swimmer_parses_registration_id(tmp_path: Path) -> None:
    cl2_path = tmp_path / "meet.cl2"
    cl2_path.write_text(PHAN_D01 + "\n", encoding="latin-1")

    report = trace_cl2_swimmer(cl2_path, "Nathan Phan")

    assert len(report.records) == 1
    registration = next(
        field
        for field in report.records[0].identity_fields
        if field.field_name == "registration_id"
    )
    assert registration.value == "C1F230F7EF4CA"
    assert registration.byte_offset == 39


def test_trace_cl2_swimmer_returns_no_records_when_not_found(
    sample_cl2_path: Path,
) -> None:
    report = trace_cl2_swimmer(sample_cl2_path, "Nobody Missing")

    assert report.records == ()
    assert "No matching records found." in format_cl2_trace(report)
