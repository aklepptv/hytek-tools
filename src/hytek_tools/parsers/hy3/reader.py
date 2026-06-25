"""HY3 file reader."""

from __future__ import annotations

from pathlib import Path

from hytek_tools.parsers.hy3.record import Record


class HY3Reader:
    """Read an HY3 file into one :class:`Record` per line."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def read(self) -> list[Record]:
        """Read the file line by line and return a record for every line."""
        records: list[Record] = []
        with self._path.open(encoding="latin-1") as handle:
            for line_number, line in enumerate(handle, start=1):
                raw_text = line.rstrip("\r\n")
                records.append(
                    Record(
                        record_type=raw_text[:2],
                        line_number=line_number,
                        raw_text=raw_text,
                    )
                )
        return records
