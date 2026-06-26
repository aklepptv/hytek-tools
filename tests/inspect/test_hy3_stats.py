"""Unit tests for HY3 record-type statistics."""

from pathlib import Path

from hytek_tools.inspect.hy3_stats import count_record_types, format_record_counts

SAMPLE_HY3 = """\
D0header
D1swimmer1
D1swimmer2
D3event1
E0result1
E0result2
E0result3
"""


def test_count_record_types(tmp_path: Path) -> None:
    path = tmp_path / "meet.hy3"
    path.write_text(SAMPLE_HY3, encoding="latin-1")

    assert count_record_types(path) == {
        "D0": 1,
        "D1": 2,
        "D3": 1,
        "E0": 3,
    }


def test_count_record_types_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.hy3"
    path.write_text("", encoding="latin-1")

    assert count_record_types(path) == {}


def test_count_record_types_blank_line(tmp_path: Path) -> None:
    path = tmp_path / "blank.hy3"
    path.write_text("D0header\n\nE0result\n", encoding="latin-1")

    assert count_record_types(path) == {"D0": 1, "": 1, "E0": 1}


def test_format_record_counts() -> None:
    output = format_record_counts({"D0": 1, "D1": 68, "D3": 42, "E0": 84})

    assert output == ("Record counts\n" "\n" "D0 1\n" "D1 68\n" "D3 42\n" "E0 84\n")


def test_format_record_counts_empty() -> None:
    assert format_record_counts({}) == "Record counts\n\n"
