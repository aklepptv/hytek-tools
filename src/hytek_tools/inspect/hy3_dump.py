"""HY3 record inspector without field decoding."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hytek_tools.parsers.hy3.reader import HY3Reader


@dataclass(frozen=True, slots=True)
class HY3DumpRecord:
    """Metadata for one HY3 line returned by :class:`HY3RecordInspector`."""

    record_number: int
    byte_offset: int
    line_number: int
    record_type: str
    record_length: int
    raw_text: str


class HY3RecordInspector:
    """Dump every HY3 record line without parsing field contents."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def dump(self) -> list[HY3DumpRecord]:
        """Read the file and return inspection metadata for every record."""
        records = HY3Reader(self._path).read()
        offsets = _line_byte_offsets(self._path)
        return [
            HY3DumpRecord(
                record_number=index + 1,
                byte_offset=offsets[index],
                line_number=record.line_number,
                record_type=record.record_type,
                record_length=len(record.raw_text),
                raw_text=record.raw_text,
            )
            for index, record in enumerate(records)
        ]


def format_dump_record(entry: HY3DumpRecord) -> str:
    """Format one inspection record for CLI output."""
    return (
        f"Record {entry.record_number}\n"
        f"  Byte offset: {entry.byte_offset}\n"
        f"  Line number: {entry.line_number}\n"
        f"  Record type: {entry.record_type}\n"
        f"  Record length: {entry.record_length}\n"
        f"  Raw text: {entry.raw_text}\n"
    )


def format_dump(entries: list[HY3DumpRecord]) -> str:
    """Format all inspection records for CLI output."""
    if not entries:
        return ""
    return "\n".join(format_dump_record(entry).rstrip("\n") for entry in entries) + "\n"


def _line_byte_offsets(path: Path) -> list[int]:
    """Return the byte offset of each line, matching :class:`HY3Reader` line splits."""
    data = path.read_bytes()
    if not data:
        return []

    offsets: list[int] = []
    index = 0
    while True:
        offsets.append(index)
        while index < len(data) and data[index] not in (0x0A, 0x0D):
            index += 1
        if index >= len(data):
            break
        if data[index] == 0x0D:
            index += 1
            if index < len(data) and data[index] == 0x0A:
                index += 1
        elif data[index] == 0x0A:
            index += 1
    return offsets
