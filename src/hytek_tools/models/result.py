"""Result model."""

from __future__ import annotations

from dataclasses import dataclass

from hytek_tools.models.relay import Relay
from hytek_tools.models.swimmer import Swimmer


@dataclass(frozen=True, slots=True)
class Result:
    """A competition result for an individual or relay entry."""

    event_number: int
    swimmer: Swimmer | None = None
    relay: Relay | None = None
    time: str | None = None
    seed_time: str | None = None
    place: int | None = None
    heat: int | None = None
    lane: int | None = None
    points: float | None = None
    is_dq: bool = False
    is_scratch: bool = False

    def __repr__(self) -> str:
        entry = self.relay if self.relay is not None else self.swimmer
        status = ""
        if self.is_dq:
            status = ", DQ"
        elif self.is_scratch:
            status = ", SCR"
        return (
            f"Result(event=#{self.event_number}, entry={entry!r}, "
            f"time={self.time!r}, place={self.place}{status})"
        )
