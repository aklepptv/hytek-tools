"""CL2 D01 individual event swimmer decoder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from hytek_tools.models.enums import Gender
from hytek_tools.models.swimmer import Swimmer
from hytek_tools.parsers.cl2.record import Record

# Fixed-width field offsets (0-indexed, end exclusive) for CL2 D01 records.
# Layout follows SDIF v3 D0; CL2 uses a three-character "D01" prefix.
_NAME = slice(11, 39)
_TEAMUNIFY_ID = slice(39, 53)
_BIRTH_DATE = slice(55, 63)
_AGE = slice(63, 65)
_GENDER = slice(65, 66)


@dataclass(frozen=True, slots=True)
class D01SwimmerRecord:
    """Decoded CL2 D01 swimmer identity fields."""

    raw_text: str
    team_code: str
    last_name: str
    first_name: str
    birth_date: date | None
    age: int | None
    gender: Gender | None
    teamunify_id: str | None = None
    middle_initial: str | None = None
    line_number: int | None = None


def decode_d01(record: Record) -> D01SwimmerRecord:
    """Decode a raw CL2 :class:`Record` when it is a D01 swimmer line."""
    return decode_d01_line(record.raw_text, line_number=record.line_number)


def decode_d01_line(
    raw_text: str,
    *,
    line_number: int | None = None,
) -> D01SwimmerRecord:
    """Decode a single CL2 D01 individual event line."""
    if not raw_text.startswith("D01"):
        msg = f"expected D01 record, got {raw_text[:3]!r}"
        raise ValueError(msg)

    last_name, first_name = _parse_name(_slice(raw_text, _NAME))
    teamunify_id = parse_teamunify_id(_slice(raw_text, _TEAMUNIFY_ID))
    middle_initial = _middle_initial_from_teamunify_id(teamunify_id)
    if middle_initial is None:
        middle_initial = _middle_initial_from_name(first_name)
        first_name = _first_name_without_middle_initial(first_name)

    return D01SwimmerRecord(
        raw_text=raw_text,
        line_number=line_number,
        team_code=raw_text[3:5],
        last_name=last_name,
        first_name=first_name,
        birth_date=_parse_birth_date(_slice(raw_text, _BIRTH_DATE)),
        age=_parse_age(_slice(raw_text, _AGE)),
        gender=_parse_gender(_slice(raw_text, _GENDER)),
        teamunify_id=teamunify_id,
        middle_initial=middle_initial,
    )


def decode_d01_swimmer(record: Record) -> Swimmer:
    """Decode a D01 record into the shared :class:`Swimmer` model."""
    return d01_swimmer_record_to_model(decode_d01(record))


def d01_swimmer_record_to_model(record: D01SwimmerRecord) -> Swimmer:
    """Convert a decoded D01 record into the shared :class:`Swimmer` model."""
    return Swimmer(
        first_name=record.first_name,
        last_name=record.last_name,
        middle_initial=record.middle_initial,
        birth_date=record.birth_date,
        gender=record.gender,
        team_code=record.team_code,
    )


def _slice(raw_text: str, field_slice: slice) -> str:
    return raw_text[field_slice]


def _parse_name(value: str) -> tuple[str, str]:
    cleaned = value.strip()
    if not cleaned:
        return "", ""
    if "," in cleaned:
        last_name, first_name = cleaned.split(",", 1)
        return last_name.strip(), first_name.strip()
    parts = cleaned.split()
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], " ".join(parts[1:])


def _parse_birth_date(value: str) -> date | None:
    digits = value.strip()
    if len(digits) != 8 or not digits.isdigit():
        return None
    month = int(digits[0:2])
    day = int(digits[2:4])
    year = int(digits[4:8])
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _parse_age(value: str) -> int | None:
    stripped = value.strip()
    if not stripped.isdigit():
        return None
    return int(stripped)


def _parse_gender(value: str) -> Gender | None:
    code = value.strip().upper()
    if code == "M":
        return Gender.MALE
    if code == "F":
        return Gender.FEMALE
    return None


def parse_teamunify_id(value: str) -> str | None:
    """Parse a TeamUnify ID from a D01 fixed-width field."""
    stripped = value.strip()
    if not stripped or not stripped[0].isdigit():
        return None
    return stripped


TEAMUNIFY_ID_FIELD = _TEAMUNIFY_ID


def _middle_initial_from_teamunify_id(teamunify_id: str | None) -> str | None:
    if teamunify_id is None or len(teamunify_id) < 10:
        return None
    middle = teamunify_id[9]
    if middle == "*":
        return None
    return middle


def _middle_initial_from_name(first_name: str) -> str | None:
    parts = first_name.split()
    if len(parts) >= 2 and len(parts[-1]) == 1:
        return parts[-1]
    return None


def _first_name_without_middle_initial(first_name: str) -> str:
    parts = first_name.split()
    if len(parts) >= 2 and len(parts[-1]) == 1:
        return " ".join(parts[:-1])
    return first_name
