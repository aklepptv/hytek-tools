"""HY3 D1 swimmer record decoder."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from hytek_tools.models.enums import Gender
from hytek_tools.parsers.hy3.record import Record

# Fixed-width field offsets (0-indexed, end exclusive) for HY3 D1 records.
# Layout follows wp-swimteam HY3_D1_RECORD / HY3D1Record.ParseRecord.
_GENDER = slice(2, 3)
_INTERNAL_ID = slice(3, 8)
_LAST_NAME = slice(8, 28)
_FIRST_NAME = slice(28, 48)
_NICKNAME = slice(48, 68)
_BIRTH_DATE = slice(88, 96)
_AGE = slice(97, 99)

_DECODED_RANGES: tuple[tuple[int, int], ...] = (
    (2, 3),
    (3, 8),
    (8, 28),
    (28, 48),
    (48, 68),
    (88, 96),
    (97, 99),
)


@dataclass(frozen=True, slots=True)
class UnknownField:
    """A preserved slice of a D1 line that is not decoded into typed fields."""

    start: int
    end: int
    raw_text: str


@dataclass(frozen=True, slots=True)
class D1SwimmerRecord:
    """Decoded HY3 D1 swimmer administrative record."""

    raw_text: str
    gender: Gender | None
    internal_id: str | None
    last_name: str
    first_name: str
    nickname: str | None
    birth_date: date | None
    age: int | None
    unknown_fields: tuple[UnknownField, ...]
    line_number: int | None = None


def decode_d1(record: Record) -> D1SwimmerRecord:
    """Decode a raw HY3 :class:`Record` when it is a D1 swimmer line."""
    return decode_d1_line(record.raw_text, line_number=record.line_number)


def decode_d1_line(raw_text: str, *, line_number: int | None = None) -> D1SwimmerRecord:
    """Decode a single HY3 D1 swimmer line."""
    if raw_text[:2] != "D1":
        msg = f"expected D1 record, got {raw_text[:2]!r}"
        raise ValueError(msg)

    return D1SwimmerRecord(
        raw_text=raw_text,
        line_number=line_number,
        gender=_parse_gender(_slice(raw_text, _GENDER)),
        internal_id=_parse_optional_text(_slice(raw_text, _INTERNAL_ID)),
        last_name=_parse_name(_slice(raw_text, _LAST_NAME)),
        first_name=_parse_name(_slice(raw_text, _FIRST_NAME)),
        nickname=_parse_optional_name(_slice(raw_text, _NICKNAME)),
        birth_date=_parse_birth_date(_slice(raw_text, _BIRTH_DATE)),
        age=_parse_age(_slice(raw_text, _AGE)),
        unknown_fields=_collect_unknown_fields(raw_text),
    )


def _slice(raw_text: str, field_slice: slice) -> str:
    return raw_text[field_slice]


def _parse_name(value: str) -> str:
    return value.rstrip()


def _parse_optional_name(value: str) -> str | None:
    stripped = value.rstrip()
    return stripped or None


def _parse_optional_text(value: str) -> str | None:
    stripped = value.strip()
    return stripped or None


def _parse_gender(value: str) -> Gender | None:
    code = value.strip().upper()
    if code == "M":
        return Gender.MALE
    if code == "F":
        return Gender.FEMALE
    return None


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


def _collect_unknown_fields(raw_text: str) -> tuple[UnknownField, ...]:
    """Return every byte range not covered by decoded D1 fields."""
    decoded = set()
    for start, end in _DECODED_RANGES:
        decoded.update(range(start, min(end, len(raw_text))))

    unknown: list[UnknownField] = []
    index = 0
    while index < len(raw_text):
        if index in decoded:
            index += 1
            continue
        start = index
        while index < len(raw_text) and index not in decoded:
            index += 1
        unknown.append(
            UnknownField(
                start=start,
                end=index,
                raw_text=raw_text[start:index],
            )
        )
    return tuple(unknown)
