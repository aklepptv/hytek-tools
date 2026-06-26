"""Unit tests for CL2-to-TeamUnify comparison reporting."""

from datetime import date
from pathlib import Path

import pytest

from hytek_tools.models.enums import Gender
from hytek_tools.parsers.cl2.extractor import extract_swimmers, unique_swimmers
from hytek_tools.parsers.cl2.models import CL2RecordLocation, CL2Swimmer
from hytek_tools.teamunify.compare import (
    CompareEntry,
    CompareStatus,
    build_compare_entries,
    build_compare_report,
    build_compare_report_from_files,
    format_compare_debug_from_files,
    format_compare_report,
    load_unique_swimmers,
)
from hytek_tools.teamunify.models import RosterMember
from hytek_tools.teamunify.roster import read_roster


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


def _cl2_swimmer(
    *,
    first_name: str,
    last_name: str,
    line_number: int = 1,
    middle_initial: str | None = None,
    birthday: date | None = None,
    gender: Gender | None = None,
    teamunify_id: str | None = None,
) -> CL2Swimmer:
    return CL2Swimmer(
        first_name=first_name,
        last_name=last_name,
        middle_initial=middle_initial,
        birthday=birthday,
        gender=gender,
        teamunify_id=teamunify_id,
        location=CL2RecordLocation(line_number=line_number, byte_offset=line_number),
    )


def test_build_compare_report_classifies_exact_match() -> None:
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
        _cl2_swimmer(
            first_name="Gavin",
            last_name="Kleppinger",
            birthday=date(2012, 8, 1),
            gender=Gender.MALE,
            teamunify_id="080112GAVBKLEP",
        )
    ]

    report = build_compare_report(swimmers, roster)

    assert report.exact_matches == (
        CompareEntry(
            swimmer=swimmers[0],
            roster_member=roster[0],
            status=CompareStatus.EXACT_MATCH,
            reason="matched TeamUnify ID, birthday, and name",
        ),
    )
    assert report.total_swimmers == 1


def test_build_compare_report_classifies_missing_cl2_id() -> None:
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
        _cl2_swimmer(
            first_name="Gavin",
            last_name="Kleppinger",
            birthday=date(2012, 8, 1),
            gender=Gender.MALE,
        )
    ]

    report = build_compare_report(swimmers, roster)

    assert len(report.teamunify_id_missing_in_cl2) == 1
    assert report.teamunify_id_missing_in_cl2[0].status is (
        CompareStatus.TEAMUNIFY_ID_MISSING_IN_CL2
    )


def test_build_compare_report_classifies_missing_roster_id() -> None:
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
        _cl2_swimmer(
            first_name="IZAAC",
            last_name="GROFF",
            birthday=date(2013, 10, 24),
            gender=Gender.MALE,
        )
    ]

    report = build_compare_report(swimmers, roster)

    assert len(report.missing_id_in_teamunify_roster) == 1


def test_build_compare_report_classifies_name_mismatch() -> None:
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
        _cl2_swimmer(
            first_name="Kevin",
            last_name="Kleppinger",
            birthday=date(2012, 8, 1),
            gender=Gender.MALE,
            teamunify_id="080112GAVBKLEP",
        )
    ]

    report = build_compare_report(swimmers, roster)

    assert len(report.name_mismatches) == 1
    assert report.name_mismatches[0].status is CompareStatus.NAME_MISMATCH


def test_build_compare_report_classifies_birthday_mismatch() -> None:
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
        _cl2_swimmer(
            first_name="Gavin",
            last_name="Kleppinger",
            birthday=date(2013, 8, 1),
            gender=Gender.MALE,
            teamunify_id="080112GAVBKLEP",
        )
    ]

    report = build_compare_report(swimmers, roster)

    assert len(report.birthday_mismatches) == 1
    assert report.birthday_mismatches[0].status is CompareStatus.BIRTHDAY_MISMATCH


def test_build_compare_report_classifies_ambiguous_match() -> None:
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
        _cl2_swimmer(
            first_name="Alex",
            last_name="Smith",
            birthday=date(2010, 1, 1),
            gender=Gender.MALE,
        )
    ]

    report = build_compare_report(swimmers, roster)

    assert len(report.ambiguous_matches) == 1


def test_build_compare_report_classifies_no_match() -> None:
    swimmers = [
        _cl2_swimmer(
            first_name="Nobody",
            last_name="Here",
            birthday=date(2000, 1, 1),
            gender=Gender.MALE,
        )
    ]

    report = build_compare_report(swimmers, [])

    assert len(report.no_matches) == 1


def test_build_compare_report_from_files_uses_unique_swimmers(
    sample_cl2_path: Path,
    roster_path: Path,
) -> None:
    all_records = extract_swimmers(sample_cl2_path)
    unique = unique_swimmers(all_records)
    roster = read_roster(roster_path)

    report = build_compare_report_from_files(sample_cl2_path, roster_path)
    report_from_all_records = build_compare_report(all_records, roster)

    assert len(all_records) == 640
    assert len(unique) == 258
    assert len(load_unique_swimmers(sample_cl2_path)) == 258
    assert report.total_swimmers == 258
    assert report_from_all_records.total_swimmers == 640


def test_nathan_kleppinger_classified_from_sample_files(
    sample_cl2_path: Path,
    roster_path: Path,
) -> None:
    swimmers = load_unique_swimmers(sample_cl2_path)
    roster = read_roster(roster_path)
    nathan = next(
        swimmer
        for swimmer in swimmers
        if swimmer.last_name == "Kleppinger" and swimmer.first_name == "Nathan"
    )

    entry = build_compare_entries((nathan,), roster)[0]

    assert nathan.teamunify_id is None
    assert nathan.birthday == date(2007, 10, 14)
    assert entry.status is CompareStatus.TEAMUNIFY_ID_MISSING_IN_CL2
    assert entry.roster_member is not None
    assert entry.roster_member.id_card == "101407NATTKLEP"
    assert "CL2 has no TeamUnify ID" in entry.reason


def test_format_compare_debug_shows_first_twenty_swimmers(
    sample_cl2_path: Path,
    roster_path: Path,
) -> None:
    output = format_compare_debug_from_files(sample_cl2_path, roster_path)

    assert "Compare Debug" in output
    assert "Unique swimmers compared: 258" in output
    assert "Showing first 20 swimmers" in output
    assert "Swimmer 1" in output
    assert "Swimmer 20" in output
    assert "Swimmer 21" not in output
    assert "CL2 birthday:" in output
    assert "CL2 first name:" in output
    assert "CL2 last name:" in output
    assert "CL2 TeamUnify ID:" in output
    assert "Matched roster record:" in output
    assert "Match reason:" in output
    assert "Final classification:" in output


def test_build_compare_report_from_sample_files(
    sample_cl2_path: Path,
    roster_path: Path,
) -> None:
    report = build_compare_report_from_files(sample_cl2_path, roster_path)

    assert report.total_swimmers == 258
    assert len(report.exact_matches) == 0
    assert len(report.teamunify_id_missing_in_cl2) == 100
    assert len(report.missing_id_in_teamunify_roster) == 1
    assert len(report.name_mismatches) == 0
    assert len(report.birthday_mismatches) == 0
    assert len(report.ambiguous_matches) == 0
    assert len(report.no_matches) == 157


def test_format_compare_report(sample_cl2_path: Path, roster_path: Path) -> None:
    report = build_compare_report_from_files(sample_cl2_path, roster_path)
    output = format_compare_report(report)

    assert "Comparison Report" in output
    assert "Swimmers: 258" in output
    assert "Exact Match (0)" in output
    assert "TeamUnify ID Missing in CL2 (100)" in output
    assert "Missing ID in TeamUnify Roster (1)" in output
    assert "No Match (157)" in output
    assert "Groff, Izaac" in output
