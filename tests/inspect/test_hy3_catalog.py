"""Unit tests for the HY3 record catalog service."""

from pathlib import Path

import pytest

from hytek_tools.inspect.hy3_catalog import HY3CatalogStats, HY3RecordCatalog

SAMPLE_HY3 = """\
D0header
D1M    1Smith               John                Johnny              J12345678901234   4207212012 13                             00
D1F    2Lee                 Amy                                                         01012010 15                             00
D3event1
E0result1
E0result2
E0result3
"""


@pytest.fixture
def sample_path(tmp_path: Path) -> Path:
    path = tmp_path / "meet.hy3"
    path.write_text(SAMPLE_HY3, encoding="latin-1")
    return path


def test_catalog_counts_every_record_type(sample_path: Path) -> None:
    stats = HY3RecordCatalog(sample_path).catalog()

    assert stats.record_counts == {
        "D0": 1,
        "D1": 2,
        "D3": 1,
        "E0": 3,
    }


def test_catalog_returns_total_line_count(sample_path: Path) -> None:
    stats = HY3RecordCatalog(sample_path).catalog()

    assert stats.total_lines == 7


def test_catalog_reports_unique_record_types(sample_path: Path) -> None:
    stats = HY3RecordCatalog(sample_path).catalog()

    assert stats.unique_record_types == 4


def test_catalog_preserves_path(sample_path: Path) -> None:
    stats = HY3RecordCatalog(sample_path).catalog()

    assert stats.path == sample_path


def test_catalog_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "empty.hy3"
    path.write_text("", encoding="latin-1")

    stats = HY3RecordCatalog(path).catalog()

    assert stats.total_lines == 0
    assert stats.record_counts == {}
    assert stats.unique_record_types == 0


def test_catalog_blank_line(tmp_path: Path) -> None:
    path = tmp_path / "blank.hy3"
    path.write_text("D0header\n\nE0result\n", encoding="latin-1")

    stats = HY3RecordCatalog(path).catalog()

    assert stats.total_lines == 3
    assert stats.record_counts == {"D0": 1, "": 1, "E0": 1}


def test_catalog_accepts_str_path(sample_path: Path) -> None:
    stats = HY3RecordCatalog(str(sample_path)).catalog()

    assert stats.total_lines == 7


def test_catalog_does_not_decode_swimmer_fields(sample_path: Path) -> None:
    """Catalog only counts record types; D1 lines stay opaque."""
    stats = HY3RecordCatalog(sample_path).catalog()

    assert isinstance(stats, HY3CatalogStats)
    assert stats.record_counts["D1"] == 2
    assert not hasattr(stats, "swimmer")
    assert not hasattr(stats, "swimmers")
