"""Compare D01 records for one swimmer between two CL2 files."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

from hytek_tools.inspect.cl2_trace import parse_swimmer_name_query
from hytek_tools.parsers.cl2.d01 import D01SwimmerRecord, decode_d01_line
from hytek_tools.parsers.cl2.reader import CL2Reader

_D01_PARSED_FIELDS = (
    "team_code",
    "last_name",
    "first_name",
    "middle_initial",
    "birth_date",
    "age",
    "gender",
    "teamunify_id",
)


@dataclass(frozen=True, slots=True)
class ParsedFieldDiff:
    """One parsed D01 field that differs between before and after."""

    field_name: str
    before_value: str
    after_value: str


@dataclass(frozen=True, slots=True)
class ByteChange:
    """One byte that differs within a paired D01 record."""

    record_offset: int
    file_offset_before: int
    file_offset_after: int
    before_byte: int
    after_byte: int


@dataclass(frozen=True, slots=True)
class SwimmerD01RecordDiff:
    """Comparison of one swimmer D01 record between two CL2 files."""

    record_number: int
    line_number: int
    file_offset_before: int
    file_offset_after: int
    parsed_field_diffs: tuple[ParsedFieldDiff, ...]
    byte_changes: tuple[ByteChange, ...]


@dataclass(frozen=True, slots=True)
class CL2SwimmerDiffReport:
    """Outcome of comparing swimmer D01 records in two CL2 files."""

    query_name: str
    first_name: str
    last_name: str
    before_record_count: int
    after_record_count: int
    records: tuple[SwimmerD01RecordDiff, ...]
    unpaired_before_line_numbers: tuple[int, ...]
    unpaired_after_line_numbers: tuple[int, ...]
    unchanged_records: int
    modified_records: int
    modified_records_identical: bool | None


@dataclass(frozen=True, slots=True)
class _SwimmerD01Record:
    line_number: int
    file_offset: int
    raw_text: str


def compare_swimmer_d01_records(
    before_path: Path | str,
    after_path: Path | str,
    name: str,
) -> CL2SwimmerDiffReport:
    """Compare every D01 record for one swimmer between two CL2 files."""
    first_name, last_name = parse_swimmer_name_query(name)
    before_file = Path(before_path)
    after_file = Path(after_path)

    before_records = _collect_swimmer_d01_records(before_file, first_name, last_name)
    after_records = _collect_swimmer_d01_records(after_file, first_name, last_name)
    after_by_line = {record.line_number: record for record in after_records}

    paired_diffs: list[SwimmerD01RecordDiff] = []
    unpaired_before: list[int] = []
    unpaired_after = set(after_by_line)

    for index, before_record in enumerate(before_records, start=1):
        after_record = after_by_line.pop(before_record.line_number, None)
        if after_record is None:
            unpaired_before.append(before_record.line_number)
            continue
        unpaired_after.discard(after_record.line_number)
        paired_diffs.append(_compare_paired_records(index, before_record, after_record))

    unchanged_records = sum(1 for entry in paired_diffs if not entry.byte_changes)
    modified_records = len(paired_diffs) - unchanged_records
    modified_byte_changes = tuple(
        entry.byte_changes for entry in paired_diffs if entry.byte_changes
    )
    modified_records_identical = _modified_records_identical(modified_byte_changes)

    return CL2SwimmerDiffReport(
        query_name=name,
        first_name=first_name,
        last_name=last_name,
        before_record_count=len(before_records),
        after_record_count=len(after_records),
        records=tuple(paired_diffs),
        unpaired_before_line_numbers=tuple(unpaired_before),
        unpaired_after_line_numbers=tuple(sorted(unpaired_after)),
        unchanged_records=unchanged_records,
        modified_records=modified_records,
        modified_records_identical=modified_records_identical,
    )


def format_cl2_swimmer_diff(report: CL2SwimmerDiffReport) -> str:
    """Format a swimmer D01 diff report for CLI output."""
    lines = [
        "CL2 Swimmer D01 Diff",
        "",
        f"Query: {report.query_name}",
        f"D01 records before: {report.before_record_count}",
        f"D01 records after: {report.after_record_count}",
        f"Paired D01 records: {len(report.records)}",
        f"Unchanged records: {report.unchanged_records}",
        f"Modified records: {report.modified_records}",
    ]

    if report.modified_records == 0 or report.modified_records_identical is None:
        lines.append("All modified records identical: (none)")
    else:
        identical_label = "yes" if report.modified_records_identical else "no"
        lines.append(f"All modified records identical: {identical_label}")

    if report.unpaired_before_line_numbers or report.unpaired_after_line_numbers:
        lines.append("")
        lines.append("Unpaired records:")
        if report.unpaired_before_line_numbers:
            before_lines = ", ".join(
                str(line_number) for line_number in report.unpaired_before_line_numbers
            )
            lines.append(f"  Before only (line numbers): {before_lines}")
        if report.unpaired_after_line_numbers:
            after_lines = ", ".join(
                str(line_number) for line_number in report.unpaired_after_line_numbers
            )
            lines.append(f"  After only (line numbers): {after_lines}")

    if not report.records:
        lines.append("")
        lines.append("No paired D01 records found.")
        return "\n".join(lines) + "\n"

    lines.append("")
    for entry in report.records:
        lines.extend(_format_record_diff(entry))

    if report.modified_records_identical and report.modified_records > 0:
        lines.extend(_format_identical_change_summary(report.records))

    return "\n".join(lines).rstrip() + "\n"


def _collect_swimmer_d01_records(
    path: Path,
    first_name: str,
    last_name: str,
) -> list[_SwimmerD01Record]:
    offsets = _line_byte_offsets(path)
    records: list[_SwimmerD01Record] = []
    for index, record in enumerate(CL2Reader(path).read()):
        if record.record_type != "D01":
            continue
        if not _record_matches_swimmer(record.raw_text, first_name, last_name):
            continue
        records.append(
            _SwimmerD01Record(
                line_number=record.line_number,
                file_offset=offsets[index],
                raw_text=record.raw_text,
            )
        )
    return records


def _compare_paired_records(
    record_number: int,
    before_record: _SwimmerD01Record,
    after_record: _SwimmerD01Record,
) -> SwimmerD01RecordDiff:
    before_decoded = decode_d01_line(
        before_record.raw_text,
        line_number=before_record.line_number,
    )
    after_decoded = decode_d01_line(
        after_record.raw_text,
        line_number=after_record.line_number,
    )
    return SwimmerD01RecordDiff(
        record_number=record_number,
        line_number=before_record.line_number,
        file_offset_before=before_record.file_offset,
        file_offset_after=after_record.file_offset,
        parsed_field_diffs=_parsed_field_diffs(before_decoded, after_decoded),
        byte_changes=_byte_changes(
            before_record,
            after_record,
        ),
    )


def _parsed_field_diffs(
    before: D01SwimmerRecord,
    after: D01SwimmerRecord,
) -> tuple[ParsedFieldDiff, ...]:
    differences: list[ParsedFieldDiff] = []
    for field_name in _D01_PARSED_FIELDS:
        before_value = _format_parsed_value(getattr(before, field_name))
        after_value = _format_parsed_value(getattr(after, field_name))
        if before_value != after_value:
            differences.append(
                ParsedFieldDiff(
                    field_name=field_name,
                    before_value=before_value,
                    after_value=after_value,
                )
            )
    return tuple(differences)


def _byte_changes(
    before_record: _SwimmerD01Record,
    after_record: _SwimmerD01Record,
) -> tuple[ByteChange, ...]:
    before_bytes = before_record.raw_text.encode("latin-1")
    after_bytes = after_record.raw_text.encode("latin-1")
    max_len = max(len(before_bytes), len(after_bytes))
    changes: list[ByteChange] = []

    for offset in range(max_len):
        before_byte = before_bytes[offset] if offset < len(before_bytes) else None
        after_byte = after_bytes[offset] if offset < len(after_bytes) else None
        if before_byte == after_byte:
            continue
        changes.append(
            ByteChange(
                record_offset=offset,
                file_offset_before=before_record.file_offset + offset,
                file_offset_after=after_record.file_offset + offset,
                before_byte=-1 if before_byte is None else before_byte,
                after_byte=-1 if after_byte is None else after_byte,
            )
        )
    return tuple(changes)


def _modified_records_identical(
    modified_byte_changes: tuple[tuple[ByteChange, ...], ...],
) -> bool | None:
    if not modified_byte_changes:
        return None
    first = modified_byte_changes[0]
    return all(
        _normalized_byte_changes(entry) == _normalized_byte_changes(first)
        for entry in modified_byte_changes[1:]
    )


def _normalized_byte_changes(
    changes: tuple[ByteChange, ...],
) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        (change.record_offset, change.before_byte, change.after_byte)
        for change in changes
    )


def _format_record_diff(entry: SwimmerD01RecordDiff) -> list[str]:
    status = "unchanged" if not entry.byte_changes else "modified"
    lines = [
        f"D01 record {entry.record_number} ({status})",
        f"  Line number: {entry.line_number}",
        f"  File offset before: {entry.file_offset_before}",
        f"  File offset after: {entry.file_offset_after}",
    ]

    if entry.parsed_field_diffs:
        lines.append("  Parsed field differences:")
        for diff in entry.parsed_field_diffs:
            lines.append(
                f"    {diff.field_name}: {diff.before_value} -> {diff.after_value}"
            )
    else:
        lines.append("  Parsed field differences: (none)")

    if entry.byte_changes:
        lines.append("  Changed bytes:")
        for change in entry.byte_changes:
            before_label = _format_byte(change.before_byte)
            after_label = _format_byte(change.after_byte)
            before_ascii = _format_ascii_byte(change.before_byte)
            after_ascii = _format_ascii_byte(change.after_byte)
            lines.append(
                "    "
                f"record@{change.record_offset} "
                f"before@{change.file_offset_before} "
                f"after@{change.file_offset_after}: "
                f"{before_label} -> {after_label} "
                f"({before_ascii} -> {after_ascii})"
            )
    else:
        lines.append("  Changed bytes: (none)")

    lines.append("")
    return lines


def _format_identical_change_summary(
    records: tuple[SwimmerD01RecordDiff, ...],
) -> list[str]:
    template = next(entry for entry in records if entry.byte_changes)
    lines = [
        "Identical modification pattern",
        "",
        "  Changed bytes:",
    ]
    for change in template.byte_changes:
        lines.append(
            "    "
            f"record@{change.record_offset}: "
            f"{_format_byte(change.before_byte)} -> {_format_byte(change.after_byte)} "
            f"({_format_ascii_byte(change.before_byte)} -> "
            f"{_format_ascii_byte(change.after_byte)})"
        )
    lines.append("")
    return lines


def _format_parsed_value(value: object | None) -> str:
    if value is None:
        return "(none)"
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _format_byte(value: int) -> str:
    if value < 0:
        return "(missing)"
    return f"{value:02X}"


def _format_ascii_byte(value: int) -> str:
    if value < 0:
        return "."
    if 32 <= value < 127:
        return chr(value)
    return "."


def _record_matches_swimmer(
    raw_text: str,
    first_name: str,
    last_name: str,
) -> bool:
    needle = f"{last_name}, {first_name}"
    return needle.casefold() in raw_text.casefold()


def _line_byte_offsets(path: Path) -> list[int]:
    data = path.read_bytes()
    if not data:
        return []

    offsets: list[int] = []
    index = 0
    while index < len(data):
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
