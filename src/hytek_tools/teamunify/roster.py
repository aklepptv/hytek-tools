"""TeamUnify roster CSV reader."""

from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from hytek_tools.models.enums import Gender
from hytek_tools.teamunify.models import RosterMember

_BIRTHDAY_FORMAT = "%m/%d/%Y"
_GENDER_MAP = {"M": Gender.MALE, "F": Gender.FEMALE}


class RosterLoader:
    """Read and index a TeamUnify roster CSV export."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)
        members = self._load_members()
        self._members = tuple(members)
        self._by_birthdate_index = _index_by_birthdate(members)
        self._by_id_card_index = _index_by_id_card(members)

    def members(self) -> tuple[RosterMember, ...]:
        """Return every roster member in file order."""
        return self._members

    def by_birthdate(self) -> dict[date, tuple[RosterMember, ...]]:
        """Return members grouped by birthday."""
        return dict(self._by_birthdate_index)

    def by_id_card(self) -> dict[str, RosterMember]:
        """Return members keyed by normalized ID card."""
        return dict(self._by_id_card_index)

    def _load_members(self) -> list[RosterMember]:
        members: list[RosterMember] = []

        with self._path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                members.append(_parse_row(row))

        return members


def read_roster(path: Path | str) -> list[RosterMember]:
    """Read a TeamUnify roster CSV export."""
    return list(RosterLoader(path).members())


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


def _index_by_birthdate(
    members: list[RosterMember],
) -> dict[date, tuple[RosterMember, ...]]:
    grouped: dict[date, list[RosterMember]] = defaultdict(list)
    for member in members:
        grouped[member.birthday].append(member)
    return {birthday: tuple(group) for birthday, group in grouped.items()}


def _index_by_id_card(members: list[RosterMember]) -> dict[str, RosterMember]:
    indexed: dict[str, RosterMember] = {}
    for member in members:
        if member.id_card is None:
            continue
        indexed[member.id_card.upper()] = member
    return indexed


def _required_field(row: dict[str, str | None], key: str) -> str:
    value = row.get(key)
    if value is None or not value.strip():
        msg = f"missing required roster field {key!r}"
        raise ValueError(msg)
    return _normalize_whitespace(value)


def _optional_field(row: dict[str, str | None], key: str) -> str | None:
    value = row.get(key)
    if value is None:
        return None
    stripped = _normalize_whitespace(value)
    return stripped or None


def _normalize_whitespace(value: str) -> str:
    return value.strip()
