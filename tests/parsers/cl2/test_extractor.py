"""Unit tests for CL2 swimmer extraction."""

from datetime import date
from pathlib import Path

import pytest

from hytek_tools.models.enums import Gender
from hytek_tools.parsers.cl2 import (
    CL2DuplicateIdentity,
    CL2RecordLocation,
    CL2Swimmer,
    CL2SwimmerExtractor,
    CL2SwimmerIdentity,
    CL2SwimmerSummary,
    extract_swimmers,
    format_swimmer_summary,
    group_swimmers_by_identity,
    summarize_swimmers,
)


@pytest.fixture
def sample_cl2_path() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "sample"
        / "Meet Results-TOW vs SOUD 062326-23Jun2026-001.cl2"
    )


def _swimmer(
    *,
    first_name: str,
    last_name: str,
    line_number: int,
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


def test_extract_swimmers_returns_every_d01_record(sample_cl2_path: Path) -> None:
    swimmers = extract_swimmers(sample_cl2_path)

    assert len(swimmers) == 640


def test_extract_swimmers_decodes_identity_fields(sample_cl2_path: Path) -> None:
    swimmers = extract_swimmers(sample_cl2_path)
    danila = next(
        swimmer
        for swimmer in swimmers
        if swimmer.last_name == "Andryushin" and swimmer.first_name == "Danila"
    )

    assert danila.first_name == "Danila"
    assert danila.last_name == "Andryushin"
    assert danila.middle_initial is None
    assert danila.birthday == date(2013, 3, 1)
    assert danila.gender is Gender.MALE
    assert danila.teamunify_id is None
    assert danila.location.line_number == 4
    assert danila.location.byte_offset > 0


def test_extract_swimmers_includes_teamunify_id_when_present(
    sample_cl2_path: Path,
) -> None:
    swimmers = extract_swimmers(sample_cl2_path)
    charlotte = next(swimmer for swimmer in swimmers if swimmer.last_name == "Dalton")

    assert charlotte.teamunify_id == "050415CHARDAA"
    assert charlotte.middle_initial == "R"
    assert charlotte.location.line_number == 678


def test_group_swimmers_by_identity_uses_gender() -> None:
    swimmers = [
        _swimmer(
            first_name="Alex",
            last_name="Smith",
            birthday=date(2010, 1, 1),
            gender=Gender.MALE,
            line_number=1,
        ),
        _swimmer(
            first_name="Alex",
            last_name="Smith",
            birthday=date(2010, 1, 1),
            gender=Gender.FEMALE,
            line_number=2,
        ),
    ]

    grouped = group_swimmers_by_identity(swimmers)

    assert len(grouped) == 2


def test_summarize_sample_cl2_file(sample_cl2_path: Path) -> None:
    summary = summarize_swimmers(extract_swimmers(sample_cl2_path))

    assert summary == CL2SwimmerSummary(
        total_d01_records=640,
        unique_swimmers=258,
        additional_event_entries=382,
        swimmers_missing_teamunify_ids=110,
        duplicate_identities=(),
    )


def test_summarize_detects_conflicting_teamunify_ids() -> None:
    swimmers = [
        _swimmer(
            first_name="Gavin",
            last_name="Kleppinger",
            birthday=date(2012, 8, 1),
            gender=Gender.MALE,
            teamunify_id="080112GAVBKLEP",
            line_number=10,
        ),
        _swimmer(
            first_name="Gavin",
            last_name="Kleppinger",
            birthday=date(2012, 8, 1),
            gender=Gender.MALE,
            teamunify_id="080112GAVBKLEP2",
            line_number=20,
        ),
    ]

    summary = summarize_swimmers(swimmers)

    assert summary.unique_swimmers == 1
    assert summary.additional_event_entries == 1
    assert len(summary.duplicate_identities) == 1
    assert summary.duplicate_identities[0] == CL2DuplicateIdentity(
        identity=CL2SwimmerIdentity(
            birthday=date(2012, 8, 1),
            first_name="Gavin",
            last_name="Kleppinger",
            gender=Gender.MALE,
        ),
        swimmers=tuple(swimmers),
    )


def test_summarize_treats_matching_records_as_one_identity() -> None:
    swimmers = [
        _swimmer(
            first_name="Gavin",
            last_name="Kleppinger",
            birthday=date(2012, 8, 1),
            gender=Gender.MALE,
            teamunify_id="080112GAVBKLEP",
            middle_initial="B",
            line_number=10,
        ),
        _swimmer(
            first_name="gavin",
            last_name="kleppinger",
            birthday=date(2012, 8, 1),
            gender=Gender.MALE,
            teamunify_id="080112GAVBKLEP",
            middle_initial="B",
            line_number=20,
        ),
    ]

    summary = summarize_swimmers(swimmers)

    assert summary.unique_swimmers == 1
    assert summary.additional_event_entries == 1
    assert summary.duplicate_identities == ()


def test_cl2_swimmer_extractor_matches_helpers(sample_cl2_path: Path) -> None:
    extractor = CL2SwimmerExtractor(sample_cl2_path)

    assert extractor.summarize() == summarize_swimmers(
        extract_swimmers(sample_cl2_path)
    )


def test_format_swimmer_summary(sample_cl2_path: Path) -> None:
    summary = CL2SwimmerExtractor(sample_cl2_path).summarize()
    output = format_swimmer_summary(summary)

    assert output == (
        "Swimmer Summary\n"
        "\n"
        "Total D01 records: 640\n"
        "Unique swimmers: 258\n"
        "Additional event entries: 382\n"
        "Swimmers missing TeamUnify IDs: 110\n"
        "\n"
        "Duplicate identities (0)\n"
        "  (none)\n"
    )
