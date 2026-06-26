"""Unit tests for TeamUnify roster validation."""

from datetime import date
from pathlib import Path

import pytest

from hytek_tools.models.enums import Gender
from hytek_tools.teamunify.models import RosterMember
from hytek_tools.teamunify.roster import RosterLoader
from hytek_tools.teamunify.validation import (
    InvalidBirthdayEntry,
    format_roster_validation,
    validate_roster,
)

_ROSTER_HEADER = (
    "Birthday,Gender,ID Card #,Memb. First Name,Memb. Last Name,"
    "Memb. Middle Initial\n"
)


@pytest.fixture
def roster_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sample" / "roster.csv"


def test_validate_sample_roster(roster_path: Path) -> None:
    report = validate_roster(roster_path)

    assert report.total_swimmers == 127
    assert len(report.missing_id_cards) == 1
    assert report.missing_id_cards[0].first_name == "IZAAC"
    assert len(report.duplicate_id_cards) == 0
    assert len(report.duplicate_identities) == 0
    assert len(report.invalid_birthdays) == 0


def test_roster_loader_validate_matches_validate_roster(roster_path: Path) -> None:
    loader = RosterLoader(roster_path)

    assert loader.validate() == validate_roster(roster_path)


def test_validate_roster_detects_missing_id_cards(tmp_path: Path) -> None:
    path = tmp_path / "roster.csv"
    path.write_text(
        _ROSTER_HEADER
        + "06/22/2018,M,062218MAR*ANDR,Mark,Andryushin,\n"
        + "10/24/2013,M,,IZAAC,GROFF,Von\n",
        encoding="utf-8",
    )

    report = validate_roster(path)

    assert report.total_swimmers == 2
    assert len(report.missing_id_cards) == 1
    assert report.missing_id_cards[0] == RosterMember(
        birthday=date(2013, 10, 24),
        gender=Gender.MALE,
        first_name="IZAAC",
        middle_initial="Von",
        last_name="GROFF",
        id_card=None,
    )


def test_validate_roster_detects_duplicate_id_cards(tmp_path: Path) -> None:
    path = tmp_path / "roster.csv"
    path.write_text(
        _ROSTER_HEADER
        + "08/01/2012,M,080112GAVBKLEP,Gavin,Kleppinger,Brady\n"
        + "08/01/2012,M,080112gavbklep,Gavin,Clone,Brady\n",
        encoding="utf-8",
    )

    report = validate_roster(path)

    assert len(report.duplicate_id_cards) == 1
    id_card, members = report.duplicate_id_cards[0]
    assert id_card == "080112GAVBKLEP"
    assert len(members) == 2


def test_validate_roster_detects_duplicate_identities_case_insensitively(
    tmp_path: Path,
) -> None:
    path = tmp_path / "roster.csv"
    path.write_text(
        _ROSTER_HEADER
        + "08/01/2012,M,080112GAVBKLEP,Gavin,Kleppinger,Brady\n"
        + "08/01/2012,M,080112GAVBKLEP2,gAvIn,kleppinger,Brady\n",
        encoding="utf-8",
    )

    report = validate_roster(path)

    assert len(report.duplicate_identities) == 1
    identity, members = report.duplicate_identities[0]
    assert identity == (date(2012, 8, 1), "gavin", "kleppinger")
    assert len(members) == 2


def test_validate_roster_detects_invalid_birthdays(tmp_path: Path) -> None:
    path = tmp_path / "roster.csv"
    path.write_text(
        _ROSTER_HEADER
        + "13/40/2012,M,080112GAVBKLEP,Gavin,Kleppinger,Brady\n"
        + "08/01/2012,M,080112GAVBKLEP,Gavin,Kleppinger,Brady\n",
        encoding="utf-8",
    )

    report = validate_roster(path)

    assert report.total_swimmers == 2
    assert len(report.invalid_birthdays) == 1
    assert report.invalid_birthdays[0] == InvalidBirthdayEntry(
        line_number=2,
        first_name="Gavin",
        last_name="Kleppinger",
        birthday_raw="13/40/2012",
    )


def test_format_roster_validation_sample_roster(roster_path: Path) -> None:
    output = format_roster_validation(validate_roster(roster_path))

    assert "Roster Validation" in output
    assert "Total swimmers: 127" in output
    assert "Missing ID Cards (1)" in output
    assert "GROFF, IZAAC  2013-10-24" in output
    assert "Duplicate ID Cards (0)" in output
    assert "Duplicate DOB + First + Last (0)" in output
    assert "Invalid birthdays (0)" in output
