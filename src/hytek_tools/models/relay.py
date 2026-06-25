"""Relay models."""

from __future__ import annotations

from dataclasses import dataclass

from hytek_tools.models.swimmer import Swimmer


@dataclass(frozen=True, slots=True)
class RelayLeg:
    """One swimmer's leg within a relay."""

    swimmer: Swimmer
    leg: int
    split_time: str | None = None

    def __repr__(self) -> str:
        return f"RelayLeg(leg={self.leg}, swimmer={self.swimmer!r})"


@dataclass(frozen=True, slots=True)
class Relay:
    """A relay team entry."""

    name: str
    team_code: str
    event_number: int
    legs: tuple[RelayLeg, ...] = ()

    def __repr__(self) -> str:
        return (
            f"Relay({self.name!r}, team={self.team_code!r}, "
            f"event=#{self.event_number}, legs={len(self.legs)})"
        )
