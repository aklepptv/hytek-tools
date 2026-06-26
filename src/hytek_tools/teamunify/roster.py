"""TeamUnify roster CSV reader."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

from hytek_tools.models.enums import Gender

_BIRTHDAY_FORMAT = "%m/%d/%Y"
_GENDER_MAP = {"M": Gender.MALE, "F": Gender.FEMALE}


@dataclass(frozen=True, slots=True)
class RosterMember:
    """One swimmer from a TeamUnify roster export."""

    birthday: date
    gender: Gender
    first_name: str
    middle_initial: str | None
    last_name: str
    id_card: str | None


def read_roster(path: Path | str) -> list[RosterMember]:
    """Read a TeamUnify roster CSV export."""
    roster_path = Path(path)
    members: list[RosterMember] = []

    with roster_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            members.append(_parse_row(row))

    return members


def _parse_row(row: dict[str, str | None]) -> RosterMember:
    birthday_raw = _required_field(row, "Birthday")
    gender_raw = _required_field(row, "Gender")
    first_name = _required_field(row, "Memb. First Name")
    last_name = _required_field(row, "Memb. Last Name")
    middle_initial = _optional_field(row, "Memb. Middle Initial")
    id_card = _optional_field(row, "ID Card #")

    gender = _GENDER_MAP.get(gender_raw.upper())
    if gender is None:
        msg = f"unsupported roster gender: {gender_raw!r}"
        raise ValueError(msg)

    return RosterMember(
        birthday=datetime.strptime(birthday_raw, _BIRTHDAY_FORMAT).date(),
        gender=gender,
        first_name=first_name,
        middle_initial=middle_initial,
        last_name=last_name,
        id_card=id_card,
    )


def _required_field(row: dict[str, str | None], key: str) -> str:
    value = row.get(key)
    if value is None or not value.strip():
        msg = f"missing required roster field {key!r}"
        raise ValueError(msg)
    return value.strip()


def _optional_field(row: dict[str, str | None], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
