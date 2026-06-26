"""CL2-specific models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from hytek_tools.models.enums import Gender


@dataclass(frozen=True, slots=True)
class CL2RecordLocation:
    """Location of a swimmer record inside a CL2 file."""

    line_number: int
    byte_offset: int


@dataclass(frozen=True, slots=True)
class CL2Swimmer:
    """One swimmer identity extracted from a CL2 D01 record."""

    first_name: str
    last_name: str
    middle_initial: str | None
    birthday: date | None
    gender: Gender | None
    teamunify_id: str | None
    location: CL2RecordLocation


@dataclass(frozen=True, slots=True)
class CL2SwimmerIdentity:
    """Normalized swimmer identity used to group D01 records."""

    birthday: date | None
    first_name: str
    last_name: str
    gender: Gender | None


@dataclass(frozen=True, slots=True)
class CL2DuplicateIdentity:
    """One identity with conflicting data across multiple D01 records."""

    identity: CL2SwimmerIdentity
    swimmers: tuple[CL2Swimmer, ...]


@dataclass(frozen=True, slots=True)
class CL2SwimmerSummary:
    """Summary of swimmers extracted from a CL2 file."""

    total_d01_records: int
    unique_swimmers: int
    additional_event_entries: int
    swimmers_missing_teamunify_ids: int
    duplicate_identities: tuple[CL2DuplicateIdentity, ...]
