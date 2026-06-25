"""Unit tests for HY3Reader."""

from pathlib import Path

import pytest

from hytek_tools.parsers.hy3 import HY3Reader, Record

SAMPLE_HY3 = """\
A01V3     Meet Entries              Hy-Tek, Ltd         8.0CHy-Tek, Ltd         252-633-517702262016 TM41 N21
B11 YMCA 2001 District Champs      Kobler, NY          USA     Y0204200102112001 Y N79
C11Smith                    John                    M 01012010  0FAST
"""


@pytest.fixture
def sample_path(tmp_path: Path) -> Path:
    path = tmp_path / "sample.hy3"
    path.write_text(SAMPLE_HY3, encoding="latin-1")
    return path


def test_read_returns_one_record_per_line(sample_path: Path) -> None:
    records = HY3Reader(sample_path).read()

    assert len(records) == 3
    assert all(isinstance(record, Record) for record in records)


def test_read_preserves_raw_text(sample_path: Path) -> None:
    expected_lines = SAMPLE_HY3.splitlines()
    records = HY3Reader(sample_path).read()

    assert [record.raw_text for record in records] == expected_lines


def test_read_assigns_sequential_line_numbers(sample_path: Path) -> None:
    records = HY3Reader(sample_path).read()

    assert [record.line_number for record in records] == [1, 2, 3]


def test_read_extracts_record_type_from_first_two_characters(
    sample_path: Path,
) -> None:
    records = HY3Reader(sample_path).read()

    assert records[0].record_type == "A0"
    assert records[1].record_type == "B1"
    assert records[2].record_type == "C1"


def test_read_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.hy3"
    path.write_text("", encoding="latin-1")

    assert HY3Reader(path).read() == []


def test_read_preserves_blank_line(tmp_path: Path) -> None:
    path = tmp_path / "blank.hy3"
    path.write_text("A0header\n\nB1footer\n", encoding="latin-1")

    records = HY3Reader(path).read()

    assert len(records) == 3
    assert records[1].raw_text == ""
    assert records[1].record_type == ""
    assert records[1].line_number == 2


def test_read_preserves_trailing_whitespace(tmp_path: Path) -> None:
    line = "A0" + " " * 126 + "  "
    path = tmp_path / "padded.hy3"
    path.write_text(line + "\n", encoding="latin-1")

    records = HY3Reader(path).read()

    assert len(records) == 1
    assert records[0].raw_text == line
    assert len(records[0].raw_text) == 130


def test_read_short_line_record_type(tmp_path: Path) -> None:
    path = tmp_path / "short.hy3"
    path.write_text("A\n", encoding="latin-1")

    record = HY3Reader(path).read()[0]

    assert record.raw_text == "A"
    assert record.record_type == "A"


def test_read_accepts_str_path(sample_path: Path) -> None:
    records = HY3Reader(str(sample_path)).read()

    assert len(records) == 3
