"""Unit tests for CL2 D01 swimmer record decoding."""

from datetime import date
from pathlib import Path

import pytest

from hytek_tools.models.enums import Gender
from hytek_tools.parsers.cl2 import (
    CL2Reader,
    D01SwimmerRecord,
    Record,
    decode_d01,
    decode_d01_line,
    decode_d01_swimmer,
    read_swimmers,
)

SAMPLE_D01 = (
    "D01MA      Andryushin, Danila                      A   0301201313MM  "
    "503 20 131406232026   36.93Y                     38.68Y     2 6     0"
    "       0  03     XNN99"
)


@pytest.fixture
def sample_cl2_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )


def test_decode_d01_line_swimmer_fields() -> None:
    swimmer = decode_d01_line(SAMPLE_D01, line_number=4)

    assert swimmer == D01SwimmerRecord(
        raw_text=SAMPLE_D01,
        line_number=4,
        team_code="MA",
        last_name="Andryushin",
        first_name="Danila",
        birth_date=date(2013, 3, 1),
        age=13,
        gender=Gender.MALE,
    )


def test_decode_d01_parses_apostrophe_last_name() -> None:
    line = (
        "D01MA      D'Antonio, Ella                         A   11032017 8FF  "
        "253 13 UN0806232026   33.44Y                     33.87Y     1 6     2"
        "  3.   2  0300    NN48"
    )

    swimmer = decode_d01_line(line)

    assert swimmer.last_name == "D'Antonio"
    assert swimmer.first_name == "Ella"
    assert swimmer.birth_date == date(2017, 11, 3)


def test_decode_d01_accepts_reader_record() -> None:
    record = Record(record_type="D01", line_number=4, raw_text=SAMPLE_D01)

    swimmer = decode_d01(record)

    assert swimmer.first_name == "Danila"
    assert swimmer.line_number == 4


def test_decode_d01_swimmer_returns_shared_model() -> None:
    record = Record(record_type="D01", line_number=4, raw_text=SAMPLE_D01)

    swimmer = decode_d01_swimmer(record)

    assert swimmer.last_name == "Andryushin"
    assert swimmer.team_code == "MA"


def test_read_swimmers_returns_unique_swimmers(sample_cl2_path: Path) -> None:
    swimmers = read_swimmers(sample_cl2_path)

    assert len(swimmers) == 258
    names = {(swimmer.last_name, swimmer.first_name) for swimmer in swimmers}
    assert ("Andryushin", "Danila") in names
    assert ("Kleppinger", "Nathan") in names


def test_read_swimmers_from_sample_file(sample_cl2_path: Path) -> None:
    records = [
        record
        for record in CL2Reader(sample_cl2_path).read()
        if record.record_type == "D01"
    ]

    assert len(records) == 640
    assert decode_d01(records[0]).last_name == "Andryushin"
