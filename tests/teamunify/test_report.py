"""Unit tests for TeamUnify match reporting."""

from datetime import date
from pathlib import Path

import pytest

from hytek_tools.models.enums import Gender
from hytek_tools.models.swimmer import Swimmer
from hytek_tools.teamunify.match_report import (
    MatchCategory,
    MatchReport,
    MatchReportEntry,
    build_match_report,
    build_match_report_from_files,
    format_match_report,
)
from hytek_tools.teamunify.matcher import MatchResult
from hytek_tools.teamunify.models import RosterMember


@pytest.fixture
def sample_cl2_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )


@pytest.fixture
def roster_path() -> Path:
    return Path(__file__).resolve().parents[2] / "sample" / "roster.csv"


def test_build_match_report_classifies_exact_match() -> None:
    roster = [
        RosterMember(
            birthday=date(2012, 8, 1),
            gender=Gender.MALE,
            first_name="Gavin",
            middle_initial="Brady",
            last_name="Kleppinger",
            id_card="080112GAVBKLEP",
        )
    ]
    swimmers = [
        Swimmer(
            first_name="Gavin",
            last_name="Kleppinger",
            birth_date=date(2012, 8, 1),
        )
    ]

    report = build_match_report(swimmers, roster)

    assert len(report.exact_matches) == 1
    assert report.exact_matches[0].result.id_card == "080112GAVBKLEP"
    assert report.missing_id_cards == ()
    assert report.ambiguous_matches == ()
    assert report.unmatched_swimmers == ()


def test_build_match_report_classifies_missing_id_card() -> None:
    roster = [
        RosterMember(
            birthday=date(2013, 10, 24),
            gender=Gender.MALE,
            first_name="IZAAC",
            middle_initial="Von",
            last_name="GROFF",
            id_card=None,
        )
    ]
    swimmers = [
        Swimmer(
            first_name="Izaac",
            last_name="Groff",
            birth_date=date(2013, 10, 24),
        )
    ]

    report = build_match_report(swimmers, roster)

    assert report.exact_matches == ()
    assert len(report.missing_id_cards) == 1
    assert report.missing_id_cards[0].category is MatchCategory.MISSING_ID_CARD


def test_build_match_report_classifies_ambiguous_match() -> None:
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
    swimmers = [
        Swimmer(
            first_name="Alex",
            last_name="Smith",
            birth_date=date(2010, 1, 1),
        )
    ]

    report = build_match_report(swimmers, roster)

    assert len(report.ambiguous_matches) == 1
    assert report.ambiguous_matches[0].category is MatchCategory.AMBIGUOUS


def test_build_match_report_classifies_unmatched_swimmer() -> None:
    report = build_match_report(
        [Swimmer(first_name="Nobody", last_name="Here", birth_date=date(2000, 1, 1))],
        [],
    )

    assert len(report.unmatched_swimmers) == 1
    assert report.unmatched_swimmers[0].category is MatchCategory.UNMATCHED


def test_build_match_report_from_sample_files(
    sample_cl2_path: Path,
    roster_path: Path,
) -> None:
    report = build_match_report_from_files(sample_cl2_path, roster_path)

    assert report.total_swimmers == 258
    assert len(report.exact_matches) == 99
    assert len(report.missing_id_cards) == 1
    assert report.ambiguous_matches == ()
    assert len(report.unmatched_swimmers) == 158
    assert report.missing_id_cards[0].swimmer.last_name == "Groff"


def test_format_match_report_includes_sections() -> None:
    report = MatchReport(
        exact_matches=(
            MatchReportEntry(
                swimmer=Swimmer(
                    first_name="Gavin",
                    last_name="Kleppinger",
                    birth_date=date(2012, 8, 1),
                ),
                result=MatchResult(
                    id_card="080112GAVBKLEP",
                    confidence="high",
                    reason="matched birthday, first name, and last name",
                ),
                category=MatchCategory.EXACT,
            ),
        ),
        missing_id_cards=(),
        ambiguous_matches=(),
        unmatched_swimmers=(),
    )

    output = format_match_report(report)

    assert "Match Report" in output
    assert "Exact matches (1)" in output
    assert "080112GAVBKLEP" in output
    assert "Missing ID Cards (0)" in output
    assert "Ambiguous matches (0)" in output
    assert "Unmatched swimmers (0)" in output
