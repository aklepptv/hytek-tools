"""Event model."""

from __future__ import annotations

from dataclasses import dataclass

from hytek_tools.models.enums import Gender, Stroke


@dataclass(frozen=True, slots=True)
class Event:
    """A scheduled competition event."""

    number: int
    distance: int
    stroke: Stroke
    gender: Gender
    age_min: int | None = None
    age_max: int | None = None
    name: str | None = None

    def __repr__(self) -> str:
        label = self.name or f"{self.distance} {self.stroke.value}"
        return (
            f"Event(#{self.number}, {label!r}, "
            f"{self.gender.value}, ages={self.age_min}-{self.age_max})"
        )
