"""Swimmer model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from hytek_tools.models.enums import Gender


@dataclass(frozen=True, slots=True)
class Swimmer:
    """A swimmer registered for competition."""

    first_name: str
    last_name: str
    middle_initial: str | None = None
    nickname: str | None = None
    birth_date: date | None = None
    gender: Gender | None = None
    team_code: str | None = None

    def __repr__(self) -> str:
        name = f"{self.last_name}, {self.first_name}"
        if self.team_code is not None:
            return f"Swimmer({name!r}, team={self.team_code!r})"
        return f"Swimmer({name!r})"
