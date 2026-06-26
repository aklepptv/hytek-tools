"""Byte-for-byte CL2 file comparison."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CL2RecordDiff:
    """One CL2 record that differs between two files."""

    record_number: int
    record_type: str
    byte_offset: int
    original_bytes: bytes | None
    new_bytes: bytes | None


@dataclass(frozen=True, slots=True)
class CL2DiffReport:
    """Outcome of comparing two CL2 files byte-for-byte."""

    changed_records: tuple[CL2RecordDiff, ...]
    unchanged_records: int


@dataclass(frozen=True, slots=True)
class _FileLine:
    byte_offset: int
    body: bytes
    ending: bytes

    @property
    def raw(self) -> bytes:
        return self.body + self.ending


def compare_cl2_files(
    original_path: Path | str,
    new_path: Path | str,
) -> CL2DiffReport:
    """Compare two CL2 files byte-for-byte at the record level."""
    original_lines = _read_file_lines(Path(original_path))
    new_lines = _read_file_lines(Path(new_path))
    return _build_diff_report(original_lines, new_lines)


def format_cl2_diff(report: CL2DiffReport) -> str:
    """Format a CL2 binary diff report for CLI output."""
    lines = [
        "CL2 Binary Diff",
        "",
        f"Changed records: {len(report.changed_records)}",
        f"Unchanged records: {report.unchanged_records}",
    ]
    if not report.changed_records:
        return "\n".join(lines) + "\n"

    lines.append("")
    for entry in report.changed_records:
        lines.extend(_format_changed_record(entry))
    return "\n".join(lines).rstrip() + "\n"


def _format_changed_record(entry: CL2RecordDiff) -> list[str]:
    lines = [
        f"Changed record {entry.record_number}",
        f"  Record type: {entry.record_type}",
        f"  Byte offset: {entry.byte_offset}",
        f"  Original bytes: {_format_bytes(entry.original_bytes)}",
        f"  New bytes: {_format_bytes(entry.new_bytes)}",
        f"  ASCII original: {_format_ascii(entry.original_bytes)}",
        f"  ASCII new: {_format_ascii(entry.new_bytes)}",
        "",
    ]
    return lines


def _build_diff_report(
    original_lines: list[_FileLine],
    new_lines: list[_FileLine],
) -> CL2DiffReport:
    changed_records: list[CL2RecordDiff] = []
    unchanged_records = 0
    record_count = max(len(original_lines), len(new_lines))

    for index in range(record_count):
        original = original_lines[index] if index < len(original_lines) else None
        new = new_lines[index] if index < len(new_lines) else None

        if original is not None and new is not None and original.raw == new.raw:
            unchanged_records += 1
            continue

        record_number = index + 1
        if original is None:
            assert new is not None
            changed_records.append(
                CL2RecordDiff(
                    record_number=record_number,
                    record_type=_record_type(new.body),
                    byte_offset=new.byte_offset,
                    original_bytes=None,
                    new_bytes=new.raw,
                )
            )
            continue

        if new is None:
            changed_records.append(
                CL2RecordDiff(
                    record_number=record_number,
                    record_type=_record_type(original.body),
                    byte_offset=original.byte_offset,
                    original_bytes=original.raw,
                    new_bytes=None,
                )
            )
            continue

        diff_offset, original_bytes, new_bytes = _diff_span(original.raw, new.raw)
        changed_records.append(
            CL2RecordDiff(
                record_number=record_number,
                record_type=_record_type(original.body),
                byte_offset=original.byte_offset + diff_offset,
                original_bytes=original_bytes,
                new_bytes=new_bytes,
            )
        )

    return CL2DiffReport(
        changed_records=tuple(changed_records),
        unchanged_records=unchanged_records,
    )


def _read_file_lines(path: Path) -> list[_FileLine]:
    data = path.read_bytes()
    if not data:
        return []

    lines: list[_FileLine] = []
    index = 0
    while index <= len(data):
        if index == len(data) and lines:
            break
        if index == len(data):
            break

        line_start = index
        while index < len(data) and data[index] not in (0x0A, 0x0D):
            index += 1
        body = data[line_start:index]

        ending = b""
        if index < len(data):
            if data[index] == 0x0D:
                ending = b"\r"
                index += 1
                if index < len(data) and data[index] == 0x0A:
                    ending += b"\n"
                    index += 1
            elif data[index] == 0x0A:
                ending = b"\n"
                index += 1

        lines.append(_FileLine(byte_offset=line_start, body=body, ending=ending))
        if index == len(data) and not ending and not body:
            break

    return lines


def _diff_span(original: bytes, new: bytes) -> tuple[int, bytes, bytes]:
    min_len = min(len(original), len(new))
    start = 0
    while start < min_len and original[start] == new[start]:
        start += 1

    end_original = len(original)
    end_new = len(new)
    while (
        end_original > start
        and end_new > start
        and original[end_original - 1] == new[end_new - 1]
    ):
        end_original -= 1
        end_new -= 1

    return start, original[start:end_original], new[start:end_new]


def _record_type(body: bytes) -> str:
    text = body.decode("latin-1", errors="replace")
    if text.startswith("D01"):
        return "D01"
    return text[:2] if len(text) >= 2 else text


def _format_bytes(data: bytes | None) -> str:
    if data is None:
        return "(none)"
    return " ".join(f"{byte:02X}" for byte in data)


def _format_ascii(data: bytes | None) -> str:
    if data is None:
        return "(none)"
    return "".join(chr(byte) if 32 <= byte < 127 else "." for byte in data)
