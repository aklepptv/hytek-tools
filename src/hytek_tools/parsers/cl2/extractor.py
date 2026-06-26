"""Extract swimmers from CL2 meet files."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from pathlib import Path

from hytek_tools.models.enums import Gender
from hytek_tools.parsers.cl2.d01 import D01SwimmerRecord, decode_d01
from hytek_tools.parsers.cl2.models import (
    CL2DuplicateIdentity,
    CL2RecordLocation,
    CL2Swimmer,
    CL2SwimmerIdentity,
    CL2SwimmerSummary,
)
from hytek_tools.parsers.cl2.reader import CL2Reader


class CL2SwimmerExtractor:
    """Extract every swimmer record from a CL2 file."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def extract(self) -> tuple[CL2Swimmer, ...]:
        """Return one :class:`CL2Swimmer` for every D01 record in the file."""
        return tuple(extract_swimmers(self._path))

    def summarize(self) -> CL2SwimmerSummary:
        """Summarize extracted swimmers."""
        return summarize_swimmers(self.extract())


def extract_swimmers(path: Path | str) -> list[CL2Swimmer]:
    """Extract every swimmer record from D01 lines in a CL2 file."""
    cl2_path = Path(path)
    offsets = _line_byte_offsets(cl2_path)
    swimmers: list[CL2Swimmer] = []

    for index, record in enumerate(CL2Reader(cl2_path).read()):
        if record.record_type != "D01":
            continue
        decoded = decode_d01(record)
        swimmers.append(_to_cl2_swimmer(decoded, offsets[index]))

    return swimmers


def summarize_swimmers(swimmers: Sequence[CL2Swimmer]) -> CL2SwimmerSummary:
    """Summarize D01 records grouped by swimmer identity."""
    grouped = group_swimmers_by_identity(swimmers)
    duplicate_identities = tuple(
        CL2DuplicateIdentity(identity=identity, swimmers=tuple(group))
        for identity, group in sorted(
            grouped.items(),
            key=lambda item: (
                item[0].birthday or date.min,
                item[0].last_name.casefold(),
                item[0].first_name.casefold(),
                item[0].gender.value if item[0].gender is not None else "",
            ),
        )
        if _has_conflicting_data(group)
    )
    missing_teamunify_ids = sum(
        1
        for group in grouped.values()
        if all(member.teamunify_id is None for member in group)
    )
    unique_swimmers = len(grouped)

    return CL2SwimmerSummary(
        total_d01_records=len(swimmers),
        unique_swimmers=unique_swimmers,
        additional_event_entries=len(swimmers) - unique_swimmers,
        swimmers_missing_teamunify_ids=missing_teamunify_ids,
        duplicate_identities=duplicate_identities,
    )


def unique_swimmers(swimmers: Sequence[CL2Swimmer]) -> tuple[CL2Swimmer, ...]:
    """Return one representative swimmer per identity."""
    grouped = group_swimmers_by_identity(swimmers)
    return tuple(_representative_swimmer(group) for group in grouped.values())


def group_swimmers_by_identity(
    swimmers: Sequence[CL2Swimmer],
) -> dict[CL2SwimmerIdentity, list[CL2Swimmer]]:
    """Group swimmers by birthday, first name, last name, and gender."""
    grouped: dict[tuple[date | None, str, str, Gender | None], list[CL2Swimmer]] = (
        defaultdict(list)
    )
    for swimmer in swimmers:
        grouped[_identity_key(swimmer)].append(swimmer)

    return {_identity_from_group(group): group for group in grouped.values()}


def swimmer_identity_key(
    swimmer: CL2Swimmer,
) -> tuple[date | None, str, str, Gender | None]:
    """Return the normalized identity key used to group swimmers."""
    return _identity_key(swimmer)


def _identity_key(swimmer: CL2Swimmer) -> tuple[date | None, str, str, Gender | None]:
    return (
        swimmer.birthday,
        swimmer.first_name.casefold(),
        swimmer.last_name.casefold(),
        swimmer.gender,
    )


def _identity_from_group(group: Sequence[CL2Swimmer]) -> CL2SwimmerIdentity:
    swimmer = group[0]
    return CL2SwimmerIdentity(
        birthday=swimmer.birthday,
        first_name=swimmer.first_name,
        last_name=swimmer.last_name,
        gender=swimmer.gender,
    )


def _representative_swimmer(group: Sequence[CL2Swimmer]) -> CL2Swimmer:
    for swimmer in group:
        if swimmer.teamunify_id is not None:
            return swimmer
    return group[0]


def format_swimmer_summary(summary: CL2SwimmerSummary) -> str:
    """Format swimmer extraction summary for CLI output."""
    lines = [
        "Swimmer Summary",
        "",
        f"Total D01 records: {summary.total_d01_records}",
        f"Unique swimmers: {summary.unique_swimmers}",
        f"Additional event entries: {summary.additional_event_entries}",
        f"Swimmers missing TeamUnify IDs: {summary.swimmers_missing_teamunify_ids}",
        "",
        _format_duplicate_identities_section(summary.duplicate_identities),
    ]
    return "\n".join(lines) + "\n"


def _has_conflicting_data(group: Sequence[CL2Swimmer]) -> bool:
    if len(group) <= 1:
        return False

    middle_initials = {swimmer.middle_initial for swimmer in group}
    teamunify_ids = {swimmer.teamunify_id for swimmer in group}
    return len(middle_initials) > 1 or len(teamunify_ids) > 1


def _format_duplicate_identities_section(
    duplicates: tuple[CL2DuplicateIdentity, ...],
) -> str:
    lines = [f"Duplicate identities ({len(duplicates)})"]
    if not duplicates:
        lines.append("  (none)")
        return "\n".join(lines)

    for duplicate in duplicates:
        lines.append(f"  {_format_identity(duplicate.identity)}")
        for swimmer in duplicate.swimmers:
            lines.append(
                "    "
                f"line {swimmer.location.line_number}: "
                f"middle_initial={swimmer.middle_initial!r} "
                f"teamunify_id={swimmer.teamunify_id!r}"
            )
    return "\n".join(lines)


def _format_identity(identity: CL2SwimmerIdentity) -> str:
    if identity.birthday is None:
        birthday = "????-??-??"
    else:
        birthday = identity.birthday.isoformat()
    gender = identity.gender.value if identity.gender is not None else "?"
    return (
        f"{birthday} {identity.last_name}, {identity.first_name}  " f"gender={gender}"
    )


def _to_cl2_swimmer(record: D01SwimmerRecord, byte_offset: int) -> CL2Swimmer:
    if record.line_number is None:
        msg = "D01 swimmer record is missing a line number"
        raise ValueError(msg)

    return CL2Swimmer(
        first_name=record.first_name,
        last_name=record.last_name,
        middle_initial=record.middle_initial,
        birthday=record.birth_date,
        gender=record.gender,
        teamunify_id=record.teamunify_id,
        location=CL2RecordLocation(
            line_number=record.line_number,
            byte_offset=byte_offset,
        ),
    )


def _line_byte_offsets(path: Path) -> list[int]:
    """Return the byte offset of each line, matching :class:`CL2Reader` line splits."""
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
