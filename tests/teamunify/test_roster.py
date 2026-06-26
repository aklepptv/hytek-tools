"""Unit tests for TeamUnify roster CSV reading."""

from datetime import date
from pathlib import Path

import pytest

from hytek_tools.models.enums import Gender
from hytek_tools.teamunify.roster import RosterMember, read_roster


@pytest.fixture
def roster_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sample" / "roster.csv"


def test_read_roster_loads_sample_file(roster_path: Path) -> None:
    roster = read_roster(roster_path)

    assert len(roster) == 127


def test_read_roster_parses_member_fields(roster_path: Path) -> None:
    roster = read_roster(roster_path)
    gavin = next(member for member in roster if member.first_name == "Gavin")

    assert gavin == RosterMember(
        birthday=date(2012, 8, 1),
        gender=Gender.MALE,
        first_name="Gavin",
        middle_initial="Brady",
        last_name="Kleppinger",
        id_card="080112GAVBKLEP",
    )


def test_read_roster_preserves_empty_middle_initial(roster_path: Path) -> None:
    roster = read_roster(roster_path)
    mark = next(member for member in roster if member.first_name == "Mark")

    assert mark.middle_initial is None
    assert mark.id_card == "062218MAR*ANDR"


def test_read_roster_preserves_missing_id_card(roster_path: Path) -> None:
    roster = read_roster(roster_path)
    izaac = next(member for member in roster if member.first_name == "IZAAC")

    assert izaac.id_card is None
    assert izaac.last_name == "GROFF"
