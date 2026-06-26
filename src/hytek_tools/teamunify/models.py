"""TeamUnify roster models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from hytek_tools.models.enums import Gender


@dataclass(frozen=True, slots=True)
class RosterMember:
    """One swimmer from a TeamUnify roster export."""

    birthday: date
    gender: Gender
    first_name: str
    middle_initial: str | None
    last_name: str
    id_card: str | None
