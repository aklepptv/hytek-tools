"""Unit tests for HY3 D1 swimmer record decoding."""

from datetime import date
from pathlib import Path

import pytest

from hytek_tools.models.enums import Gender
from hytek_tools.parsers.hy3 import (
    D1SwimmerRecord,
    HY3Reader,
    Record,
    UnknownField,
    decode_d1,
    decode_d1_line,
)

SAMPLE_D1_MALE = (
    "D1M    1Smith               John                Johnny              "
    "J12345678901234   4207212012 13                             00"
)
SAMPLE_D1_FEMALE = (
    "D1F    2Lee                 Amy                                                         "
    "01012010 15                             00"
)

_DECODED_RANGES = (
    (2, 3),
    (3, 8),
    (8, 28),
    (28, 48),
    (48, 68),
    (88, 96),
    (97, 99),
)


@pytest.fixture
def sample_path() -> Path:
    return Path(__file__).resolve().parents[3] / "samples" / "meet.hy3"


def test_decode_d1_line_male_swimmer() -> None:
    swimmer = decode_d1_line(SAMPLE_D1_MALE, line_number=2)

    assert swimmer == D1SwimmerRecord(
        raw_text=SAMPLE_D1_MALE,
        line_number=2,
        gender=Gender.MALE,
        internal_id="1",
        last_name="Smith",
        first_name="John",
        nickname="Johnny",
        birth_date=date(2012, 7, 21),
        age=13,
        unknown_fields=swimmer.unknown_fields,
    )


def test_decode_d1_line_female_swimmer_without_nickname() -> None:
    swimmer = decode_d1_line(SAMPLE_D1_FEMALE)

    assert swimmer.gender is Gender.FEMALE
    assert swimmer.internal_id == "2"
    assert swimmer.last_name == "Lee"
    assert swimmer.first_name == "Amy"
    assert swimmer.nickname is None
    assert swimmer.birth_date == date(2010, 1, 1)
    assert swimmer.age == 15


def test_decode_d1_accepts_reader_record() -> None:
    record = Record(record_type="D1", line_number=4, raw_text=SAMPLE_D1_MALE)
    swimmer = decode_d1(record)

    assert swimmer.line_number == 4
    assert swimmer.first_name == "John"


def test_decode_d1_from_sample_file(sample_path: Path) -> None:
    d1_records = [
        record for record in HY3Reader(sample_path).read() if record.record_type == "D1"
    ]

    assert len(d1_records) == 2

    swimmers = [decode_d1(record) for record in d1_records]

    assert swimmers[0].last_name == "Smith"
    assert swimmers[0].gender is Gender.MALE
    assert swimmers[1].last_name == "Lee"
    assert swimmers[1].gender is Gender.FEMALE
    assert all(
        swimmer.raw_text == record.raw_text
        for swimmer, record in zip(swimmers, d1_records, strict=True)
    )


def test_decode_d1_preserves_unknown_field_bytes() -> None:
    swimmer = decode_d1_line(SAMPLE_D1_MALE)

    assert swimmer.unknown_fields[0] == UnknownField(0, 2, "D1")
    assert swimmer.unknown_fields[1] == UnknownField(
        68,
        88,
        "J12345678901234   42",
    )
    assert swimmer.unknown_fields[2] == UnknownField(96, 97, " ")
    assert swimmer.unknown_fields[3].raw_text.endswith("00")


def test_decode_d1_unknown_fields_cover_entire_line() -> None:
    for raw_text in (SAMPLE_D1_MALE, SAMPLE_D1_FEMALE):
        swimmer = decode_d1_line(raw_text)
        covered: set[int] = set()
        for field in swimmer.unknown_fields:
            covered.update(range(field.start, field.end))
        for start, end in _DECODED_RANGES:
            covered.update(range(start, min(end, len(raw_text))))
        assert covered == set(range(len(raw_text)))


def test_decode_d1_unknown_fields_reconstruct_raw_line() -> None:
    for raw_text in (SAMPLE_D1_MALE, SAMPLE_D1_FEMALE):
        swimmer = decode_d1_line(raw_text)
        pieces: dict[tuple[int, int], str] = {
            (field.start, field.end): field.raw_text for field in swimmer.unknown_fields
        }
        for start, end in _DECODED_RANGES:
            pieces[(start, end)] = raw_text[start:end]

        reconstructed = "".join(pieces[(start, end)] for start, end in sorted(pieces))
        assert reconstructed == raw_text


def test_decode_d1_rejects_non_d1_record() -> None:
    with pytest.raises(ValueError, match="expected D1 record"):
        decode_d1_line("E0not-a-swimmer-record")
