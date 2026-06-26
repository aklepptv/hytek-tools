"""HY3 record catalog service."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from hytek_tools.parsers.hy3.reader import HY3Reader


@dataclass(frozen=True, slots=True)
class HY3CatalogStats:
    """Statistics from scanning an HY3 file without field decoding."""

    path: Path
    total_lines: int
    record_counts: dict[str, int]

    @property
    def unique_record_types(self) -> int:
        """Number of distinct two-character record-type prefixes."""
        return len(self.record_counts)


class HY3RecordCatalog:
    """Scan an HY3 file and catalog record types without parsing fields."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def catalog(self) -> HY3CatalogStats:
        """Read the file and return per-record-type statistics."""
        records = HY3Reader(self._path).read()
        counts: Counter[str] = Counter(record.record_type for record in records)
        return HY3CatalogStats(
            path=self._path,
            total_lines=len(records),
            record_counts=dict(counts),
        )
