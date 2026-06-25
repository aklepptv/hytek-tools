"""Meet model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from hytek_tools.models.event import Event
from hytek_tools.models.record import Record
from hytek_tools.models.result import Result
from hytek_tools.models.team import Team


@dataclass(frozen=True, slots=True)
class Meet:
    """A swimming meet."""

    name: str
    start_date: date | None = None
    end_date: date | None = None
    location: str | None = None
    venue: str | None = None
    teams: tuple[Team, ...] = ()
    events: tuple[Event, ...] = ()
    results: tuple[Result, ...] = ()
    records: tuple[Record, ...] = ()

    def __repr__(self) -> str:
        return (
            f"Meet({self.name!r}, teams={len(self.teams)}, "
            f"events={len(self.events)}, results={len(self.results)})"
        )
