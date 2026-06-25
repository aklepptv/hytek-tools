"""Team model."""

from __future__ import annotations

from dataclasses import dataclass

from hytek_tools.models.swimmer import Swimmer


@dataclass(frozen=True, slots=True)
class Team:
    """A team participating in a meet."""

    code: str
    name: str
    nickname: str | None = None
    swimmers: tuple[Swimmer, ...] = ()

    def __repr__(self) -> str:
        swimmer_count = len(self.swimmers)
        return f"Team({self.code!r}, {self.name!r}, swimmers={swimmer_count})"
