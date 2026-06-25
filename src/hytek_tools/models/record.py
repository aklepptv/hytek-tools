"""Record model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from hytek_tools.models.enums import Gender, Stroke
from hytek_tools.models.swimmer import Swimmer


@dataclass(frozen=True, slots=True)
class Record:
    """A swimming record (meet, pool, state, etc.)."""

    record_type: str
    time: str
    event_number: int | None = None
    distance: int | None = None
    stroke: Stroke | None = None
    gender: Gender | None = None
    swimmer: Swimmer | None = None
    holder_name: str | None = None
    date_set: date | None = None
    meet_name: str | None = None

    def __repr__(self) -> str:
        holder = self.swimmer or self.holder_name or "unknown"
        return (
            f"Record({self.record_type!r}, time={self.time!r}, "
            f"holder={holder!r})"
        )
