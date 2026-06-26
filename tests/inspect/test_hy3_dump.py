"""Unit tests for the HY3 record inspector."""

from pathlib import Path

import pytest

from hytek_tools.inspect.hy3_dump import HY3RecordInspector, format_dump
from hytek_tools.parsers.hy3 import HY3Reader

SAMPLE_HY3 = """\
D0header
D1swimmer1
D3event1
"""


@pytest.fixture
def sample_path(tmp_path: Path) -> Path:
    path = tmp_path / "meet.hy3"
    path.write_text(SAMPLE_HY3, encoding="latin-1")
    return path


def test_dump_returns_one_entry_per_line(sample_path: Path) -> None:
    entries = HY3RecordInspector(sample_path).dump()

    assert len(entries) == 3


def test_dump_matches_reader_record_count(sample_path: Path) -> None:
    records = HY3Reader(sample_path).read()
    entries = HY3RecordInspector(sample_path).dump()

    assert len(entries) == len(records)


def test_dump_assigns_sequential_record_numbers(sample_path: Path) -> None:
    entries = HY3RecordInspector(sample_path).dump()

    assert [entry.record_number for entry in entries] == [1, 2, 3]


def test_dump_includes_line_numbers(sample_path: Path) -> None:
    entries = HY3RecordInspector(sample_path).dump()

    assert [entry.line_number for entry in entries] == [1, 2, 3]


def test_dump_includes_record_types(sample_path: Path) -> None:
    entries = HY3RecordInspector(sample_path).dump()

    assert [entry.record_type for entry in entries] == ["D0", "D1", "D3"]


def test_dump_includes_record_lengths(sample_path: Path) -> None:
    entries = HY3RecordInspector(sample_path).dump()

    assert [entry.record_length for entry in entries] == [8, 10, 8]


def test_dump_preserves_raw_text(sample_path: Path) -> None:
    expected_lines = SAMPLE_HY3.splitlines()
    entries = HY3RecordInspector(sample_path).dump()

    assert [entry.raw_text for entry in entries] == expected_lines


def test_dump_includes_byte_offsets(sample_path: Path) -> None:
    entries = HY3RecordInspector(sample_path).dump()

    assert [entry.byte_offset for entry in entries] == [0, 9, 20]


def test_dump_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.hy3"
    path.write_text("", encoding="latin-1")

    assert HY3RecordInspector(path).dump() == []


def test_dump_blank_line(tmp_path: Path) -> None:
    path = tmp_path / "blank.hy3"
    path.write_text("D0header\n\nE0result\n", encoding="latin-1")

    entries = HY3RecordInspector(path).dump()

    assert len(entries) == 3
    assert entries[1].raw_text == ""
    assert entries[1].record_type == ""
    assert entries[1].byte_offset == 9


def test_dump_crlf_byte_offsets(tmp_path: Path) -> None:
    path = tmp_path / "crlf.hy3"
    path.write_bytes(b"D0header\r\nD1swimmer\r\n")

    entries = HY3RecordInspector(path).dump()

    assert [entry.byte_offset for entry in entries] == [0, 10]
    assert [entry.raw_text for entry in entries] == ["D0header", "D1swimmer"]


def test_dump_does_not_decode_swimmer_fields(sample_path: Path) -> None:
    path = sample_path
    path.write_text(
        "D1M    1Smith               John\n",
        encoding="latin-1",
    )

    entry = HY3RecordInspector(path).dump()[0]

    assert entry.record_type == "D1"
    assert "Smith" in entry.raw_text
    assert not hasattr(entry, "swimmer")


def test_format_dump(sample_path: Path) -> None:
    output = format_dump(HY3RecordInspector(sample_path).dump())

    assert output.startswith(
        "Record 1\n"
        "  Byte offset: 0\n"
        "  Line number: 1\n"
        "  Record type: D0\n"
        "  Record length: 8\n"
        "  Raw text: D0header\n"
    )
    assert "Record 3\n" in output
    assert output.endswith("  Raw text: D3event1\n")


def test_format_dump_empty() -> None:
    assert format_dump([]) == ""
