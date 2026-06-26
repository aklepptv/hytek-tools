"""Unit tests for CL2 middle initial writer."""

from datetime import date
from pathlib import Path

import pytest

from hytek_tools.parsers.cl2.d01 import decode_d01_line, parse_teamunify_id
from hytek_tools.parsers.cl2.reader import CL2Reader
from hytek_tools.writers.cl2.middle_initial import (
    fix_cl2_middle_initials,
    format_fix_cl2_middle_initial_summary,
    write_middle_initial_name_field,
)

NATHAN_D01 = (
    "D01MA      Kleppinger, Nathan                      A   1014200718MM  "
    "503 22 15OV06232026                              31.57Y     1 6     4"
    "       4  03      NN19"
)
GAVIN_D01 = (
    "D01MA      Kleppinger, Gavin                       A   0801201213MM  "
    "503 22 15OV06232026                              31.57Y     1 6     4"
    "       4  03      NN19"
)
CHARLOTTE_D01 = (
    "D01        Dalton, Charlotte           050415CHARDAA   0504201511FF  "
    "504  7 111206232026                              45.07Y     2 5     0"
    "       0  04     XNN99"
)
WRONG_MI_D01 = (
    "D01MA      Rafter, Peyton q                        A   0914200817MM  "
    "504 12 15OV06232026   26.28Y                     27.05Y     1 4     5"
    "       5  04      NN09"
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


def test_write_middle_initial_name_field_replaces_only_name_slice() -> None:
    updated = write_middle_initial_name_field(NATHAN_D01, "T")

    assert updated[:11] == NATHAN_D01[:11]
    assert updated[11:39] == "Kleppinger, Nathan T        "
    assert updated[39:] == NATHAN_D01[39:]
    assert len(updated) == len(NATHAN_D01)


def test_write_middle_initial_name_field_rejects_embedded_teamunify_id() -> None:
    with pytest.raises(ValueError, match="embedded"):
        write_middle_initial_name_field(CHARLOTTE_D01, "R")


def test_fix_cl2_middle_initials_writes_nathan_kleppinger(
    roster_path: Path,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.cl2"
    output = tmp_path / "fixed.cl2"
    source.write_bytes(NATHAN_D01.encode("latin-1") + b"\n")

    result = fix_cl2_middle_initials(source, roster_path, output)

    assert result.middle_initials_added == 1
    assert result.middle_initials_changed == 0
    assert result.records_unchanged == 0
    swimmer = decode_d01_line(output.read_text(encoding="latin-1").strip())
    assert swimmer.first_name == "Nathan"
    assert swimmer.last_name == "Kleppinger"
    assert swimmer.middle_initial == "T"
    assert swimmer.birth_date == date(2007, 10, 14)


def test_fix_cl2_middle_initials_writes_gavin_kleppinger(
    roster_path: Path,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.cl2"
    output = tmp_path / "fixed.cl2"
    source.write_bytes(GAVIN_D01.encode("latin-1") + b"\n")

    fix_cl2_middle_initials(source, roster_path, output)

    swimmer = decode_d01_line(output.read_text(encoding="latin-1").strip())
    assert swimmer.first_name == "Gavin"
    assert swimmer.last_name == "Kleppinger"
    assert swimmer.middle_initial == "B"


def test_fix_cl2_middle_initials_leaves_embedded_id_records_unchanged(
    roster_path: Path,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.cl2"
    output = tmp_path / "fixed.cl2"
    source.write_bytes(CHARLOTTE_D01.encode("latin-1") + b"\n")

    result = fix_cl2_middle_initials(source, roster_path, output)

    assert result.middle_initials_added == 0
    assert result.middle_initials_changed == 0
    assert result.records_unchanged == 1
    assert output.read_bytes() == source.read_bytes()


def test_fix_cl2_middle_initials_changes_wrong_name_field_initial(
    roster_path: Path,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.cl2"
    output = tmp_path / "fixed.cl2"
    source.write_bytes(WRONG_MI_D01.encode("latin-1") + b"\n")

    result = fix_cl2_middle_initials(source, roster_path, output)

    assert result.middle_initials_changed == 1
    swimmer = decode_d01_line(output.read_text(encoding="latin-1").strip())
    assert swimmer.first_name == "Peyton"
    assert swimmer.middle_initial == "S"


def test_fix_cl2_middle_initials_preserves_bytes_outside_name_field(
    roster_path: Path,
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.cl2"
    output = tmp_path / "fixed.cl2"
    source.write_bytes(NATHAN_D01.encode("latin-1") + b"\n")

    fix_cl2_middle_initials(source, roster_path, output)

    original = source.read_text(encoding="latin-1")
    updated = output.read_text(encoding="latin-1")
    assert updated[:11] == original[:11]
    assert updated[39:] == original[39:]
    assert parse_teamunify_id(updated[39:53]) is None


def test_fix_cl2_middle_initials_sample_summary(
    sample_cl2_path: Path,
    roster_path: Path,
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "MeetResults-mi-fixed.cl2"
    original_bytes = sample_cl2_path.read_bytes()

    result = fix_cl2_middle_initials(sample_cl2_path, roster_path, output_path)

    assert output_path.is_file()
    assert sample_cl2_path.read_bytes() == original_bytes
    assert result.middle_initials_added == 261
    assert result.middle_initials_changed == 3
    assert result.records_unchanged == 376
    assert format_fix_cl2_middle_initial_summary(result) == (
        "Fix CL2 Summary\n"
        "\n"
        "Middle initials added: 261\n"
        "Middle initials changed: 3\n"
        "Records unchanged: 376\n"
    )

    nathan_records = [
        record
        for record in CL2Reader(output_path).read()
        if record.record_type == "D01" and "Kleppinger, Nathan" in record.raw_text
    ]
    assert nathan_records
    assert all(
        decode_d01_line(record.raw_text).middle_initial == "T"
        for record in nathan_records
    )
