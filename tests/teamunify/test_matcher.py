"""Unit tests for TeamUnify roster matching."""

from datetime import date
from pathlib import Path

import pytest

from hytek_tools.models.enums import Gender
from hytek_tools.models.swimmer import Swimmer
from hytek_tools.teamunify import MatchResult, RosterMatcher, read_roster
from hytek_tools.teamunify.models import RosterMember


@pytest.fixture
def roster_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sample" / "roster.csv"


@pytest.fixture
def matcher(roster_path: Path) -> RosterMatcher:
    return RosterMatcher(read_roster(roster_path))


def test_match_unique_swimmer(matcher: RosterMatcher) -> None:
    swimmer = Swimmer(
        first_name="Gavin",
        last_name="Kleppinger",
        middle_initial="B",
        birth_date=date(2012, 8, 1),
        gender=Gender.MALE,
    )

    result = matcher.match(swimmer)

    assert result == MatchResult(
        id_card="080112GAVBKLEP",
        confidence="high",
        reason="matched birthday, first name, and last name",
    )


def test_match_is_case_insensitive(matcher: RosterMatcher) -> None:
    swimmer = Swimmer(
        first_name="gAvIn",
        last_name="kleppinger",
        birth_date=date(2012, 8, 1),
    )

    result = matcher.match(swimmer)

    assert result.id_card == "080112GAVBKLEP"
    assert result.confidence == "high"


def test_match_swimmer_without_middle_initial(matcher: RosterMatcher) -> None:
    swimmer = Swimmer(
        first_name="Mark",
        last_name="Andryushin",
        birth_date=date(2018, 6, 22),
        gender=Gender.MALE,
    )

    result = matcher.match(swimmer)

    assert result.id_card == "062218MAR*ANDR"
    assert result.confidence == "high"


def test_match_uses_middle_initial_to_disambiguate() -> None:
    roster = [
        RosterMember(
            birthday=date(2010, 1, 1),
            gender=Gender.MALE,
            first_name="Alex",
            middle_initial="James",
            last_name="Smith",
            id_card="010110ALEJSMIT",
        ),
        RosterMember(
            birthday=date(2010, 1, 1),
            gender=Gender.MALE,
            first_name="Alex",
            middle_initial="Robert",
            last_name="Smith",
            id_card="010110ALERSMIT",
        ),
    ]
    matcher = RosterMatcher(roster)

    result = matcher.match(
        Swimmer(
            first_name="Alex",
            last_name="Smith",
            middle_initial="R",
            birth_date=date(2010, 1, 1),
        )
    )

    assert result == MatchResult(
        id_card="010110ALERSMIT",
        confidence="high",
        reason="matched birthday, first name, last name, and middle initial",
    )


def test_match_reports_missing_id_card(matcher: RosterMatcher) -> None:
    swimmer = Swimmer(
        first_name="IZAAC",
        last_name="GROFF",
        middle_initial="V",
        birth_date=date(2013, 10, 24),
        gender=Gender.MALE,
    )

    result = matcher.match(swimmer)

    assert result.id_card is None
    assert result.confidence == "low"
    assert "no ID card" in result.reason


def test_match_requires_birth_date(matcher: RosterMatcher) -> None:
    swimmer = Swimmer(first_name="Gavin", last_name="Kleppinger")

    result = matcher.match(swimmer)

    assert result == MatchResult(
        id_card=None,
        confidence="none",
        reason="swimmer birth date is required for matching",
    )


def test_match_returns_none_when_not_found(matcher: RosterMatcher) -> None:
    swimmer = Swimmer(
        first_name="Nobody",
        last_name="Here",
        birth_date=date(2000, 1, 1),
    )

    result = matcher.match(swimmer)

    assert result.id_card is None
    assert result.confidence == "none"
    assert "no roster member matches" in result.reason


def test_match_requires_middle_initial_when_multiple_candidates() -> None:
    roster = [
        RosterMember(
            birthday=date(2010, 1, 1),
            gender=Gender.MALE,
            first_name="Alex",
            middle_initial="James",
            last_name="Smith",
            id_card="010110ALEJSMIT",
        ),
        RosterMember(
            birthday=date(2010, 1, 1),
            gender=Gender.MALE,
            first_name="Alex",
            middle_initial="Robert",
            last_name="Smith",
            id_card="010110ALERSMIT",
        ),
    ]
    matcher = RosterMatcher(roster)

    result = matcher.match(
        Swimmer(
            first_name="Alex",
            last_name="Smith",
            birth_date=date(2010, 1, 1),
        )
    )

    assert result.id_card is None
    assert result.confidence == "none"
    assert "middle initial required to disambiguate" in result.reason
