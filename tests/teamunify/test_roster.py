"""Unit tests for TeamUnify roster CSV reading."""

from datetime import date
from pathlib import Path

import pytest

from hytek_tools.models.enums import Gender
from hytek_tools.teamunify.models import RosterMember
from hytek_tools.teamunify.roster import RosterLoader, read_roster


@pytest.fixture
def roster_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sample" / "roster.csv"


@pytest.fixture
def loader(roster_path: Path) -> RosterLoader:
    return RosterLoader(roster_path)


def test_roster_loader_loads_sample_file(loader: RosterLoader) -> None:
    assert len(loader.members()) == 127


def test_read_roster_loads_sample_file(roster_path: Path) -> None:
    roster = read_roster(roster_path)

    assert len(roster) == 127


def test_roster_loader_parses_member_fields(loader: RosterLoader) -> None:
    gavin = next(member for member in loader.members() if member.first_name == "Gavin")

    assert gavin == RosterMember(
        birthday=date(2012, 8, 1),
        gender=Gender.MALE,
        first_name="Gavin",
        middle_initial="Brady",
        last_name="Kleppinger",
        id_card="080112GAVBKLEP",
    )


def test_roster_loader_preserves_empty_middle_initial(loader: RosterLoader) -> None:
    mark = next(member for member in loader.members() if member.first_name == "Mark")

    assert mark.middle_initial is None
    assert mark.id_card == "062218MAR*ANDR"


def test_roster_loader_preserves_missing_id_card(loader: RosterLoader) -> None:
    izaac = next(member for member in loader.members() if member.first_name == "IZAAC")

    assert izaac.id_card is None
    assert izaac.last_name == "GROFF"


def test_roster_loader_by_birthdate_groups_members(loader: RosterLoader) -> None:
    by_birthdate = loader.by_birthdate()

    assert len(by_birthdate[date(2012, 4, 20)]) == 2
    assert {member.first_name for member in by_birthdate[date(2012, 4, 20)]} == {
        "Chase",
        "Aspen",
    }


def test_roster_loader_by_id_card_normalizes_case(loader: RosterLoader) -> None:
    by_id_card = loader.by_id_card()

    assert by_id_card["080112GAVBKLEP"].first_name == "Gavin"
    assert by_id_card["080112GAVBKLEP"].id_card == "080112GAVBKLEP"


def test_roster_loader_by_id_card_omits_missing_id_cards(loader: RosterLoader) -> None:
    by_id_card = loader.by_id_card()

    assert all(member.id_card is not None for member in by_id_card.values())
    assert len(by_id_card) == 126
