"""Trace CL2 records associated with one swimmer identity."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from hytek_tools.parsers.cl2.d01 import (
    NAME_FIELD,
    TEAMUNIFY_ID_FIELD,
    decode_d01_line,
    parse_teamunify_id,
)
from hytek_tools.parsers.cl2.reader import CL2Reader

_BIRTH_DATE_FIELD = slice(55, 63)
_IDENTITY_FIELDS = (
    "first_name",
    "middle_initial",
    "last_name",
    "birth_date",
    "registration_id",
)


@dataclass(frozen=True, slots=True)
class IdentityFieldValue:
    """One parsed identity field from a traced record."""

    field_name: str
    value: str | None
    byte_offset: int | None


@dataclass(frozen=True, slots=True)
class CL2TracedRecord:
    """One CL2 record associated with a traced swimmer."""

    record_number: int
    line_number: int
    byte_offset: int
    record_type: str
    raw_text: str
    parsed_fields: tuple[tuple[str, str], ...]
    identity_fields: tuple[IdentityFieldValue, ...]


@dataclass(frozen=True, slots=True)
class IdentityDifference:
    """One identity field that varies across traced records."""

    field_name: str
    values_by_record: tuple[tuple[int, str | None], ...]


@dataclass(frozen=True, slots=True)
class CL2TraceReport:
    """All records and identity comparisons for one swimmer query."""

    query_name: str
    first_name: str
    last_name: str
    records: tuple[CL2TracedRecord, ...]
    differences: tuple[IdentityDifference, ...]


def trace_cl2_swimmer(
    cl2_path: Path | str,
    name: str,
) -> CL2TraceReport:
    """Locate every CL2 record related to a swimmer name query."""
    first_name, last_name = parse_swimmer_name_query(name)
    source_path = Path(cl2_path)
    offsets = _line_byte_offsets(source_path)
    traced_records: list[CL2TracedRecord] = []

    for index, record in enumerate(CL2Reader(source_path).read()):
        if not _record_matches_swimmer(record.raw_text, first_name, last_name):
            continue
        parsed_fields, identity_fields = _parse_record_identity(record.raw_text)
        traced_records.append(
            CL2TracedRecord(
                record_number=len(traced_records) + 1,
                line_number=record.line_number,
                byte_offset=offsets[index],
                record_type=record.record_type,
                raw_text=record.raw_text,
                parsed_fields=parsed_fields,
                identity_fields=identity_fields,
            )
        )

    return CL2TraceReport(
        query_name=name,
        first_name=first_name,
        last_name=last_name,
        records=tuple(traced_records),
        differences=_find_identity_differences(traced_records),
    )


def format_cl2_trace(report: CL2TraceReport) -> str:
    """Format a swimmer trace report for CLI output."""
    lines = [
        "CL2 Identity Trace",
        "",
        f'Query: {report.query_name}',
        f"Records found: {len(report.records)}",
        "",
    ]

    if not report.records:
        lines.append("No matching records found.")
        return "\n".join(lines) + "\n"

    for entry in report.records:
        lines.extend(_format_traced_record(entry))

    lines.extend(_format_identity_occurrences(report.records))
    lines.extend(_format_differences(report.differences))
    return "\n".join(lines).rstrip() + "\n"


def parse_swimmer_name_query(name: str) -> tuple[str, str]:
    """Parse a swimmer query like ``Nathan Kleppinger`` into first and last name."""
    parts = name.strip().split()
    if len(parts) < 2:
        msg = f'name query must include first and last name: {name!r}'
        raise ValueError(msg)
    return " ".join(parts[:-1]), parts[-1]


def _format_traced_record(entry: CL2TracedRecord) -> list[str]:
    lines = [
        f"Record {entry.record_number}",
        f"  Record type: {entry.record_type}",
        f"  Byte offset: {entry.byte_offset}",
        f"  Line number: {entry.line_number}",
        f"  Raw record: {entry.raw_text}",
    ]
    if entry.parsed_fields:
        lines.append("  Parsed fields:")
        for field_name, value in entry.parsed_fields:
            lines.append(f"    {field_name}: {value}")
    else:
        lines.append("  Parsed fields: (none)")
    lines.append("")
    return lines


def _format_identity_occurrences(
    records: tuple[CL2TracedRecord, ...],
) -> list[str]:
    lines = ["Identity Field Occurrences", ""]
    for field_name in _IDENTITY_FIELDS:
        lines.append(f"  {field_name}:")
        occurrences = _occurrences_for_field(records, field_name)
        if not occurrences:
            lines.append("    (none)")
            continue
        for record_label, value, byte_offset in occurrences:
            offset_label = "?" if byte_offset is None else str(byte_offset)
            value_label = "(none)" if value is None else value
            lines.append(
                f"    {record_label} @{offset_label}: {value_label}"
            )
        lines.append("")
    return lines


def _format_differences(differences: tuple[IdentityDifference, ...]) -> list[str]:
    lines = ["Differences", ""]
    if not differences:
        lines.append("  (none)")
        lines.append("")
        return lines

    for difference in differences:
        lines.append(f"  {difference.field_name}:")
        for record_number, value in difference.values_by_record:
            value_label = "(none)" if value is None else value
            lines.append(f"    Record {record_number}: {value_label}")
        lines.append("")
    return lines


def _occurrences_for_field(
    records: tuple[CL2TracedRecord, ...],
    field_name: str,
) -> list[tuple[str, str | None, int | None]]:
    occurrences: list[tuple[str, str | None, int | None]] = []
    for entry in records:
        for identity_field in entry.identity_fields:
            if identity_field.field_name != field_name:
                continue
            record_label = f"{entry.record_type}:{entry.line_number}"
            occurrences.append(
                (
                    record_label,
                    identity_field.value,
                    identity_field.byte_offset,
                )
            )
    return occurrences


def _find_identity_differences(
    records: list[CL2TracedRecord],
) -> tuple[IdentityDifference, ...]:
    differences: list[IdentityDifference] = []
    for field_name in _IDENTITY_FIELDS:
        values_by_record: list[tuple[int, str | None]] = []
        unique_values: set[str | None] = set()
        for entry in records:
            value = _identity_value(entry, field_name)
            values_by_record.append((entry.record_number, value))
            unique_values.add(value)
        if len(unique_values) > 1:
            differences.append(
                IdentityDifference(
                    field_name=field_name,
                    values_by_record=tuple(values_by_record),
                )
            )
    return tuple(differences)


def _identity_value(entry: CL2TracedRecord, field_name: str) -> str | None:
    for identity_field in entry.identity_fields:
        if identity_field.field_name == field_name:
            return identity_field.value
    return None


def _record_matches_swimmer(
    raw_text: str,
    first_name: str,
    last_name: str,
) -> bool:
    needle = f"{last_name}, {first_name}"
    return needle.casefold() in raw_text.casefold()


def _parse_record_identity(
    raw_text: str,
) -> tuple[tuple[tuple[str, str], ...], tuple[IdentityFieldValue, ...]]:
    if raw_text.startswith("D01"):
        return _parse_d01_identity(raw_text)
    if raw_text.startswith("F01"):
        return _parse_f01_identity(raw_text)
    if raw_text.startswith("G01"):
        return _parse_g01_identity(raw_text)
    return (), ()


def _parse_d01_identity(
    raw_text: str,
) -> tuple[tuple[tuple[str, str], ...], tuple[IdentityFieldValue, ...]]:
    decoded = decode_d01_line(raw_text)
    registration_id, registration_offset = _registration_id_from_field(raw_text)

    parsed_fields = (
        ("team_code", decoded.team_code),
        ("last_name", decoded.last_name),
        ("first_name", decoded.first_name),
        ("middle_initial", _format_optional(decoded.middle_initial)),
        ("birth_date", _format_date(decoded.birth_date)),
        ("age", _format_optional(decoded.age)),
        ("gender", _format_optional(decoded.gender.value if decoded.gender else None)),
        ("registration_id", _format_optional(registration_id)),
    )
    identity_fields = (
        IdentityFieldValue(
            "first_name",
            decoded.first_name,
            _field_offset(raw_text, decoded.first_name, NAME_FIELD.start),
        ),
        IdentityFieldValue(
            "middle_initial",
            decoded.middle_initial,
            _middle_initial_offset(raw_text, decoded.middle_initial),
        ),
        IdentityFieldValue(
            "last_name",
            decoded.last_name,
            _field_offset(raw_text, decoded.last_name, NAME_FIELD.start),
        ),
        IdentityFieldValue(
            "birth_date",
            _format_date(decoded.birth_date),
            _BIRTH_DATE_FIELD.start if decoded.birth_date else None,
        ),
        IdentityFieldValue(
            "registration_id",
            registration_id,
            registration_offset,
        ),
    )
    return parsed_fields, identity_fields


def _registration_id_from_field(raw_text: str) -> tuple[str | None, int | None]:
    field_value = raw_text[TEAMUNIFY_ID_FIELD]
    teamunify_id = parse_teamunify_id(field_value)
    if teamunify_id is not None:
        return teamunify_id, TEAMUNIFY_ID_FIELD.start
    stripped = field_value.strip()
    if not stripped:
        return None, None
    if stripped == "A":
        return None, None
    return stripped, TEAMUNIFY_ID_FIELD.start


def _parse_f01_identity(
    raw_text: str,
) -> tuple[tuple[tuple[str, str], ...], tuple[IdentityFieldValue, ...]]:
    last_name, first_name, middle_initial, name_offset = _parse_f01_name(raw_text)
    birth_date, birth_offset = _find_birth_date(raw_text)
    registration_id, registration_offset = _find_registration_id(raw_text)

    parsed_fields = (
        ("last_name", last_name),
        ("first_name", first_name),
        ("middle_initial", _format_optional(middle_initial)),
        ("birth_date", _format_date(birth_date)),
        ("registration_id", _format_optional(registration_id)),
    )
    identity_fields = (
        IdentityFieldValue(
            "first_name",
            first_name,
            _field_offset(raw_text, first_name, name_offset),
        ),
        IdentityFieldValue(
            "middle_initial",
            middle_initial,
            _middle_initial_offset(raw_text, middle_initial),
        ),
        IdentityFieldValue(
            "last_name",
            last_name,
            _field_offset(raw_text, last_name, name_offset),
        ),
        IdentityFieldValue(
            "birth_date",
            _format_date(birth_date),
            birth_offset,
        ),
        IdentityFieldValue(
            "registration_id",
            registration_id,
            registration_offset,
        ),
    )
    return parsed_fields, identity_fields


def _parse_g01_identity(
    raw_text: str,
) -> tuple[tuple[tuple[str, str], ...], tuple[IdentityFieldValue, ...]]:
    name_value = raw_text[NAME_FIELD]
    last_name, first_name, middle_initial = _parse_name_value(name_value)
    registration_id, registration_offset = _registration_id_from_field(raw_text)
    if registration_id is None:
        registration_id, registration_offset = _find_registration_id(raw_text)

    parsed_fields = (
        ("last_name", last_name),
        ("first_name", first_name),
        ("middle_initial", _format_optional(middle_initial)),
        ("registration_id", _format_optional(registration_id)),
    )
    identity_fields = (
        IdentityFieldValue(
            "first_name",
            first_name,
            _field_offset(raw_text, first_name, NAME_FIELD.start),
        ),
        IdentityFieldValue(
            "middle_initial",
            middle_initial,
            _middle_initial_offset(raw_text, middle_initial),
        ),
        IdentityFieldValue(
            "last_name",
            last_name,
            _field_offset(raw_text, last_name, NAME_FIELD.start),
        ),
        IdentityFieldValue("birth_date", None, None),
        IdentityFieldValue(
            "registration_id",
            registration_id,
            registration_offset,
        ),
    )
    return parsed_fields, identity_fields


def _parse_f01_name(raw_text: str) -> tuple[str, str, str | None, int]:
    match = re.search(r"([A-Za-z'\-]+),\s*([A-Za-z'\-]+(?:\s+[A-Za-z])?)", raw_text)
    if match is None:
        msg = f"could not parse swimmer name from record: {raw_text[:40]!r}"
        raise ValueError(msg)
    last_name = _clean_f01_last_name(match.group(1))
    first_name, middle_initial = _split_first_name_and_middle(match.group(2).strip())
    last_name_offset = raw_text.find(last_name, match.start(1))
    if last_name_offset < 0:
        last_name_offset = match.start(1)
    return last_name, first_name, middle_initial, last_name_offset


def _clean_f01_last_name(value: str) -> str:
    parts = re.findall(r"[A-Z][a-z]+(?:'[A-Za-z]+)?", value)
    if parts:
        return parts[-1]
    return value


def _parse_name_value(name_value: str) -> tuple[str, str, str | None]:
    cleaned = name_value.strip()
    if "," not in cleaned:
        return cleaned, "", None
    last_name, first_name = cleaned.split(",", 1)
    first_name, middle_initial = _split_first_name_and_middle(first_name.strip())
    return last_name.strip(), first_name, middle_initial


def _split_first_name_and_middle(first_name: str) -> tuple[str, str | None]:
    parts = first_name.split()
    if len(parts) >= 2 and len(parts[-1]) == 1:
        return " ".join(parts[:-1]), parts[-1]
    return first_name, None


def _find_birth_date(raw_text: str) -> tuple[date | None, int | None]:
    for match in re.finditer(r"(\d{8})", raw_text):
        digits = match.group(1)
        birth_date = _parse_birth_date_digits(digits)
        if birth_date is not None:
            return birth_date, match.start(1)
    return None, None


def _find_registration_id(raw_text: str) -> tuple[str | None, int | None]:
    embedded = parse_teamunify_id(raw_text[TEAMUNIFY_ID_FIELD])
    if embedded is not None:
        return embedded, TEAMUNIFY_ID_FIELD.start

    for match in re.finditer(r"\b([A-Z0-9]{8,14})\b", raw_text):
        candidate = match.group(1)
        if candidate.isdigit():
            continue
        if _parse_birth_date_digits(candidate[:8]) is not None:
            continue
        return candidate, match.start(1)
    return None, None


def _parse_birth_date_digits(digits: str) -> date | None:
    if len(digits) != 8 or not digits.isdigit():
        return None
    month = int(digits[0:2])
    day = int(digits[2:4])
    year = int(digits[4:8])
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _field_offset(raw_text: str, value: str, search_start: int) -> int | None:
    if not value:
        return None
    index = raw_text.find(value, search_start)
    if index < 0:
        return None
    return index


def _middle_initial_offset(
    raw_text: str,
    middle_initial: str | None,
) -> int | None:
    if middle_initial is None:
        return None
    index = raw_text.find(f" {middle_initial}", NAME_FIELD.start)
    if index < 0:
        return None
    return index + 1


def _format_optional(value: object | None) -> str:
    if value is None:
        return "(none)"
    return str(value)


def _format_date(value: date | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


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
