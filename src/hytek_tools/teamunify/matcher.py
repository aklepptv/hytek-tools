"""Match HY-TEK swimmers to TeamUnify roster members."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from hytek_tools.models.swimmer import Swimmer
from hytek_tools.teamunify.models import RosterMember


@dataclass(frozen=True, slots=True)
class MatchResult:
    """Outcome of matching a swimmer against a TeamUnify roster."""

    id_card: str | None
    confidence: str
    reason: str


class RosterMatcher:
    """Match swimmers to TeamUnify roster members by identity fields."""

    def __init__(self, roster: Sequence[RosterMember]) -> None:
        self._roster = tuple(roster)

    def match(self, swimmer: Swimmer) -> MatchResult:
        """Match a swimmer to a roster member and return an ID card when found."""
        if swimmer.birth_date is None:
            return MatchResult(
                id_card=None,
                confidence="none",
                reason="swimmer birth date is required for matching",
            )

        swimmer_last = _normalize_name(swimmer.last_name)
        swimmer_first = _normalize_name(swimmer.first_name)
        candidates = [
            member
            for member in self._roster
            if member.birthday == swimmer.birth_date
            and _normalize_name(member.last_name) == swimmer_last
            and _normalize_name(member.first_name) == swimmer_first
        ]

        if not candidates:
            return MatchResult(
                id_card=None,
                confidence="none",
                reason="no roster member matches birthday, first name, and last name",
            )

        if len(candidates) == 1:
            member = candidates[0]
            return _result_for_member(
                member,
                confidence="high",
                reason="matched birthday, first name, and last name",
            )

        swimmer_middle = _normalize_middle_initial(swimmer.middle_initial)
        if swimmer_middle is not None:
            narrowed = [
                member
                for member in candidates
                if _normalize_middle_initial(member.middle_initial) == swimmer_middle
            ]
            if len(narrowed) == 1:
                return _result_for_member(
                    narrowed[0],
                    confidence="high",
                    reason=(
                        "matched birthday, first name, last name, and middle initial"
                    ),
                )
            if len(narrowed) > 1:
                return MatchResult(
                    id_card=None,
                    confidence="none",
                    reason=(
                        "multiple roster members match birthday, name, "
                        "and middle initial"
                    ),
                )

        return MatchResult(
            id_card=None,
            confidence="none",
            reason=(
                "multiple roster members match birthday and name; "
                "middle initial required to disambiguate"
            ),
        )


def _result_for_member(
    member: RosterMember,
    *,
    confidence: str,
    reason: str,
) -> MatchResult:
    if member.id_card is None:
        return MatchResult(
            id_card=None,
            confidence="low",
            reason=f"{reason}, but roster member has no ID card",
        )
    return MatchResult(id_card=member.id_card, confidence=confidence, reason=reason)


def _normalize_name(value: str) -> str:
    return value.strip().casefold()


def _normalize_middle_initial(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped[0].casefold()
