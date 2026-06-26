"""CL2 file reader."""

from __future__ import annotations

from pathlib import Path

from hytek_tools.parsers.cl2.record import Record


def _record_type(raw_text: str) -> str:
    if raw_text.startswith("D01"):
        return "D01"
    return raw_text[:2]


class CL2Reader:
    """Read a CL2 file into one :class:`Record` per line."""

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
                        record_type=_record_type(raw_text),
                        line_number=line_number,
                        raw_text=raw_text,
                    )
                )
        return records
