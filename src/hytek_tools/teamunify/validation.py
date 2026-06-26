"""TeamUnify roster validation."""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from hytek_tools.teamunify.models import RosterMember
from hytek_tools.teamunify.roster import _BIRTHDAY_FORMAT, _parse_row

_BIRTHDAY_FIELD = "Birthday"
_FIRST_NAME_FIELD = "Memb. First Name"
_LAST_NAME_FIELD = "Memb. Last Name"


@dataclass(frozen=True, slots=True)
class InvalidBirthdayEntry:
    """A roster row with a birthday that could not be parsed."""

    line_number: int
    first_name: str
    last_name: str
    birthday_raw: str


@dataclass(frozen=True, slots=True)
class RosterValidation:
    """Validation findings for a TeamUnify roster export."""

    total_swimmers: int
    missing_id_cards: tuple[RosterMember, ...]
    duplicate_id_cards: tuple[tuple[str, tuple[RosterMember, ...]], ...]
    duplicate_identities: tuple[
        tuple[tuple[date, str, str], tuple[RosterMember, ...]],
        ...,
    ]
    invalid_birthdays: tuple[InvalidBirthdayEntry, ...]


def validate_roster(path: Path | str) -> RosterValidation:
    """Validate a TeamUnify roster CSV export."""
    roster_path = Path(path)
    members: list[RosterMember] = []
    invalid_birthdays: list[InvalidBirthdayEntry] = []
    total_swimmers = 0

    with roster_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for line_number, row in enumerate(reader, start=2):
            total_swimmers += 1
            birthday_raw = (row.get(_BIRTHDAY_FIELD) or "").strip()
            first_name = (row.get(_FIRST_NAME_FIELD) or "").strip()
            last_name = (row.get(_LAST_NAME_FIELD) or "").strip()

            if not _is_valid_birthday(birthday_raw):
                invalid_birthdays.append(
                    InvalidBirthdayEntry(
                        line_number=line_number,
                        first_name=first_name,
                        last_name=last_name,
                        birthday_raw=birthday_raw,
                    )
                )
                continue

            members.append(_parse_row(row))

    return RosterValidation(
        total_swimmers=total_swimmers,
        missing_id_cards=tuple(member for member in members if member.id_card is None),
        duplicate_id_cards=_find_duplicate_id_cards(members),
        duplicate_identities=_find_duplicate_identities(members),
        invalid_birthdays=tuple(invalid_birthdays),
    )


def format_roster_validation(report: RosterValidation) -> str:
    """Format roster validation findings for CLI output."""
    lines = [
        "Roster Validation",
        "",
        f"Total swimmers: {report.total_swimmers}",
        "",
        _format_member_section("Missing ID Cards", report.missing_id_cards),
        _format_duplicate_id_card_section(report.duplicate_id_cards),
        _format_duplicate_identity_section(report.duplicate_identities),
        _format_invalid_birthday_section(report.invalid_birthdays),
    ]
    return "\n".join(lines)


def _is_valid_birthday(value: str) -> bool:
    if not value:
        return False
    try:
        datetime.strptime(value, _BIRTHDAY_FORMAT)
    except ValueError:
        return False
    return True


def _find_duplicate_id_cards(
    members: list[RosterMember],
) -> tuple[tuple[str, tuple[RosterMember, ...]], ...]:
    grouped: dict[str, list[RosterMember]] = defaultdict(list)
    for member in members:
        if member.id_card is None:
            continue
        grouped[member.id_card.upper()].append(member)

    duplicates = [
        (id_card, tuple(group))
        for id_card, group in sorted(grouped.items())
        if len(group) > 1
    ]
    return tuple(duplicates)


def _find_duplicate_identities(
    members: list[RosterMember],
) -> tuple[tuple[tuple[date, str, str], tuple[RosterMember, ...]], ...]:
    grouped: dict[tuple[date, str, str], list[RosterMember]] = defaultdict(list)
    for member in members:
        identity = (
            member.birthday,
            member.first_name.casefold(),
            member.last_name.casefold(),
        )
        grouped[identity].append(member)

    duplicates = [
        (identity, tuple(group))
        for identity, group in sorted(
            grouped.items(),
            key=lambda item: (item[0][0], item[0][2], item[0][1]),
        )
        if len(group) > 1
    ]
    return tuple(duplicates)


def _format_member_section(title: str, members: tuple[RosterMember, ...]) -> str:
    lines = [f"{title} ({len(members)})"]
    if not members:
        lines.append("  (none)")
        return "\n".join(lines)

    for member in members:
        lines.append(f"  {_format_member(member)}")
    return "\n".join(lines)


def _format_duplicate_id_card_section(
    duplicates: tuple[tuple[str, tuple[RosterMember, ...]], ...],
) -> str:
    lines = [f"Duplicate ID Cards ({len(duplicates)})"]
    if not duplicates:
        lines.append("  (none)")
        return "\n".join(lines)

    for id_card, members in duplicates:
        lines.append(f"  {id_card}")
        for member in members:
            lines.append(f"    {_format_member(member)}")
    return "\n".join(lines)


def _format_duplicate_identity_section(
    duplicates: tuple[tuple[tuple[date, str, str], tuple[RosterMember, ...]], ...],
) -> str:
    lines = [f"Duplicate DOB + First + Last ({len(duplicates)})"]
    if not duplicates:
        lines.append("  (none)")
        return "\n".join(lines)

    for identity, members in duplicates:
        birthday, first_name, last_name = identity
        lines.append(
            f"  {birthday.isoformat()} {last_name.title()}, {first_name.title()}"
        )
        for member in members:
            lines.append(f"    {_format_member(member)}")
    return "\n".join(lines)


def _format_invalid_birthday_section(
    entries: tuple[InvalidBirthdayEntry, ...],
) -> str:
    lines = [f"Invalid birthdays ({len(entries)})"]
    if not entries:
        lines.append("  (none)")
        return "\n".join(lines)

    for entry in entries:
        lines.append(
            "  "
            f"line {entry.line_number}: "
            f"{entry.last_name}, {entry.first_name}  "
            f"{entry.birthday_raw!r}"
        )
    return "\n".join(lines)


def _format_member(member: RosterMember) -> str:
    return f"{member.last_name}, {member.first_name}  {member.birthday.isoformat()}"
