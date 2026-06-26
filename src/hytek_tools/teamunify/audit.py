"""Audit CL2 swimmer identity fields against a TeamUnify roster."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from hytek_tools.models.enums import Gender
from hytek_tools.parsers.cl2.models import CL2Swimmer
from hytek_tools.teamunify.compare import (
    CompareEntry,
    CompareReport,
    build_compare_report,
    load_unique_swimmers,
)
from hytek_tools.teamunify.models import RosterMember
from hytek_tools.teamunify.roster import read_roster

_IDENTITY_FIELDS = (
    "first_name",
    "middle_initial",
    "last_name",
    "birthday",
    "gender",
)
_FIELD_LABELS = {
    "first_name": "First Name",
    "middle_initial": "Middle Initial",
    "last_name": "Last Name",
    "birthday": "Birthday",
    "gender": "Gender",
}


@dataclass(frozen=True, slots=True)
class IdentityFieldDifference:
    """One identity field that differs between CL2 and TeamUnify."""

    field_name: str
    cl2_value: str
    roster_value: str


@dataclass(frozen=True, slots=True)
class IdentityAuditEntry:
    """Identity audit outcome for one matched swimmer."""

    swimmer: CL2Swimmer
    roster_member: RosterMember
    differences: tuple[IdentityFieldDifference, ...]

    @property
    def display_name(self) -> str:
        return f"{self.swimmer.first_name} {self.swimmer.last_name}"

    @property
    def identity_matches(self) -> bool:
        return not self.differences


@dataclass(frozen=True, slots=True)
class IdentityAuditReport:
    """Identity audit results for all matched swimmers in a CL2 file."""

    entries: tuple[IdentityAuditEntry, ...]

    @property
    def matched_swimmers(self) -> int:
        return len(self.entries)

    @property
    def identity_matches(self) -> int:
        return sum(1 for entry in self.entries if entry.identity_matches)

    @property
    def identity_differences(self) -> int:
        return self.matched_swimmers - self.identity_matches

    @property
    def difference_rows(self) -> tuple[IdentityFieldDifference, ...]:
        rows: list[IdentityFieldDifference] = []
        for entry in self.entries:
            rows.extend(entry.differences)
        return tuple(rows)


def build_identity_audit_report(
    swimmers: tuple[CL2Swimmer, ...] | list[CL2Swimmer],
    roster: list[RosterMember] | tuple[RosterMember, ...],
) -> IdentityAuditReport:
    """Audit identity fields for swimmers matched to a TeamUnify roster."""
    compare_report = build_compare_report(swimmers, roster)
    entries = [
        _audit_entry(entry)
        for entry in _matched_compare_entries(compare_report)
        if entry.roster_member is not None
    ]
    return IdentityAuditReport(entries=tuple(entries))


def build_identity_audit_report_from_files(
    cl2_path: Path | str,
    roster_path: Path | str,
) -> IdentityAuditReport:
    """Read inputs and build an identity audit report."""
    swimmers = load_unique_swimmers(cl2_path)
    roster = read_roster(roster_path)
    return build_identity_audit_report(swimmers, roster)


def format_identity_audit(report: IdentityAuditReport) -> str:
    """Format an identity audit report for CLI output."""
    lines = [
        "Identity Audit",
        "",
        f"Matched swimmers: {report.matched_swimmers}",
        f"Identity matches: {report.identity_matches}",
        f"Identity differences: {report.identity_differences}",
        "",
    ]
    if not report.entries:
        lines.append("No matched swimmers found.")
        return "\n".join(lines) + "\n"

    for entry in report.entries:
        lines.append(entry.display_name)
        if entry.identity_matches:
            lines.append("✓ Identity matches")
            lines.append("")
            continue

        for difference in entry.differences:
            lines.append(f"{_FIELD_LABELS[difference.field_name]} differs")
            lines.append(f"CL2: {difference.cl2_value}")
            lines.append(f"TU : {difference.roster_value}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def write_identity_audit_csv(
    report: IdentityAuditReport,
    csv_path: Path | str,
) -> Path:
    """Write every identity field difference to a CSV file."""
    destination = Path(csv_path)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "last_name",
                "first_name",
                "field",
                "cl2_value",
                "roster_value",
            ]
        )
        for entry in report.entries:
            for difference in entry.differences:
                writer.writerow(
                    [
                        entry.swimmer.last_name,
                        entry.swimmer.first_name,
                        difference.field_name,
                        difference.cl2_value,
                        difference.roster_value,
                    ]
                )
    return destination


def _matched_compare_entries(
    compare_report: CompareReport,
) -> tuple[CompareEntry, ...]:
    buckets = (
        compare_report.exact_matches,
        compare_report.teamunify_id_missing_in_cl2,
        compare_report.missing_id_in_teamunify_roster,
        compare_report.name_mismatches,
        compare_report.birthday_mismatches,
    )
    entries = [entry for bucket in buckets for entry in bucket]
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                entry.swimmer.last_name.casefold(),
                entry.swimmer.first_name.casefold(),
                entry.swimmer.birthday or date.min,
            ),
        )
    )


def _audit_entry(entry: CompareEntry) -> IdentityAuditEntry:
    assert entry.roster_member is not None
    differences = _identity_differences(entry.swimmer, entry.roster_member)
    return IdentityAuditEntry(
        swimmer=entry.swimmer,
        roster_member=entry.roster_member,
        differences=differences,
    )


def _identity_differences(
    swimmer: CL2Swimmer,
    roster_member: RosterMember,
) -> tuple[IdentityFieldDifference, ...]:
    cl2_values = _cl2_identity_values(swimmer, roster_member)
    roster_values = _roster_identity_values(roster_member)
    differences: list[IdentityFieldDifference] = []

    for field_name in _IDENTITY_FIELDS:
        cl2_value = cl2_values[field_name]
        roster_value = roster_values[field_name]
        if cl2_value == roster_value:
            continue
        differences.append(
            IdentityFieldDifference(
                field_name=field_name,
                cl2_value=cl2_value,
                roster_value=roster_value,
            )
        )

    return tuple(differences)


def _cl2_identity_values(
    swimmer: CL2Swimmer,
    roster_member: RosterMember,
) -> dict[str, str]:
    return {
        "first_name": _cl2_first_name_value(swimmer, roster_member),
        "middle_initial": _format_middle_initial(swimmer.middle_initial),
        "last_name": swimmer.last_name,
        "birthday": _format_date(swimmer.birthday),
        "gender": _format_gender(swimmer.gender),
    }


def _roster_identity_values(member: RosterMember) -> dict[str, str]:
    return {
        "first_name": member.first_name,
        "middle_initial": _format_middle_initial(_roster_middle_initial(member)),
        "last_name": member.last_name,
        "birthday": _format_date(member.birthday),
        "gender": _format_gender(member.gender),
    }


def _cl2_first_name_value(
    swimmer: CL2Swimmer,
    roster_member: RosterMember,
) -> str:
    roster_middle = _roster_middle_initial(roster_member)
    if (
        swimmer.middle_initial is not None
        and len(swimmer.middle_initial) == 1
        and (
            roster_middle is None
            or swimmer.middle_initial.casefold() != roster_middle.casefold()
        )
    ):
        return f"{swimmer.first_name} {swimmer.middle_initial}"
    return swimmer.first_name


def _roster_middle_initial(member: RosterMember) -> str | None:
    if member.middle_initial is None:
        return None
    stripped = member.middle_initial.strip()
    if not stripped:
        return None
    return stripped[0]


def _format_middle_initial(value: str | None) -> str:
    if value is None:
        return ""
    return value


def _format_date(value: date | None) -> str:
    if value is None:
        return ""
    return value.isoformat()


def _format_gender(value: Gender | None) -> str:
    if value is None:
        return ""
    return value.value
