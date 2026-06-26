"""Compare CL2 swimmers against a TeamUnify roster."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path

from hytek_tools.parsers.cl2.extractor import extract_swimmers, unique_swimmers
from hytek_tools.parsers.cl2.models import CL2Swimmer
from hytek_tools.teamunify.models import RosterMember
from hytek_tools.teamunify.roster import read_roster


class CompareStatus(Enum):
    """Classification for a CL2 swimmer compared to a TeamUnify roster."""

    EXACT_MATCH = "exact_match"
    TEAMUNIFY_ID_MISSING_IN_CL2 = "teamunify_id_missing_in_cl2"
    MISSING_ID_IN_TEAMUNIFY_ROSTER = "missing_id_in_teamunify_roster"
    NAME_MISMATCH = "name_mismatch"
    BIRTHDAY_MISMATCH = "birthday_mismatch"
    AMBIGUOUS_MATCH = "ambiguous_match"
    NO_MATCH = "no_match"


@dataclass(frozen=True, slots=True)
class CompareEntry:
    """One CL2 swimmer and its roster comparison outcome."""

    swimmer: CL2Swimmer
    roster_member: RosterMember | None
    status: CompareStatus
    reason: str


@dataclass(frozen=True, slots=True)
class CompareReport:
    """Grouped outcomes from comparing CL2 swimmers to a TeamUnify roster."""

    exact_matches: tuple[CompareEntry, ...]
    teamunify_id_missing_in_cl2: tuple[CompareEntry, ...]
    missing_id_in_teamunify_roster: tuple[CompareEntry, ...]
    name_mismatches: tuple[CompareEntry, ...]
    birthday_mismatches: tuple[CompareEntry, ...]
    ambiguous_matches: tuple[CompareEntry, ...]
    no_matches: tuple[CompareEntry, ...]

    @property
    def total_swimmers(self) -> int:
        return (
            len(self.exact_matches)
            + len(self.teamunify_id_missing_in_cl2)
            + len(self.missing_id_in_teamunify_roster)
            + len(self.name_mismatches)
            + len(self.birthday_mismatches)
            + len(self.ambiguous_matches)
            + len(self.no_matches)
        )


def build_compare_report(
    swimmers: Sequence[CL2Swimmer],
    roster: Sequence[RosterMember],
) -> CompareReport:
    """Compare unique CL2 swimmers against a TeamUnify roster."""
    roster_by_id = _index_roster_by_id(roster)
    grouped: dict[CompareStatus, list[CompareEntry]] = {
        status: [] for status in CompareStatus
    }

    for swimmer in swimmers:
        entry = _compare_swimmer(swimmer, roster, roster_by_id)
        grouped[entry.status].append(entry)

    return CompareReport(
        exact_matches=_sorted_entries(grouped[CompareStatus.EXACT_MATCH]),
        teamunify_id_missing_in_cl2=_sorted_entries(
            grouped[CompareStatus.TEAMUNIFY_ID_MISSING_IN_CL2]
        ),
        missing_id_in_teamunify_roster=_sorted_entries(
            grouped[CompareStatus.MISSING_ID_IN_TEAMUNIFY_ROSTER]
        ),
        name_mismatches=_sorted_entries(grouped[CompareStatus.NAME_MISMATCH]),
        birthday_mismatches=_sorted_entries(grouped[CompareStatus.BIRTHDAY_MISMATCH]),
        ambiguous_matches=_sorted_entries(grouped[CompareStatus.AMBIGUOUS_MATCH]),
        no_matches=_sorted_entries(grouped[CompareStatus.NO_MATCH]),
    )


def build_compare_report_from_files(
    cl2_path: Path | str,
    roster_path: Path | str,
) -> CompareReport:
    """Read a CL2 file and roster CSV, then build a comparison report."""
    swimmers = load_unique_swimmers(cl2_path)
    roster = read_roster(roster_path)
    return build_compare_report(swimmers, roster)


def load_unique_swimmers(cl2_path: Path | str) -> tuple[CL2Swimmer, ...]:
    """Load one representative CL2 swimmer per identity from a meet file."""
    return unique_swimmers(extract_swimmers(cl2_path))


def build_compare_entries(
    swimmers: Sequence[CL2Swimmer],
    roster: Sequence[RosterMember],
) -> tuple[CompareEntry, ...]:
    """Compare swimmers and return one entry per swimmer in input order."""
    roster_by_id = _index_roster_by_id(roster)
    return tuple(
        _compare_swimmer(swimmer, roster, roster_by_id) for swimmer in swimmers
    )


def format_compare_debug(
    swimmers: Sequence[CL2Swimmer],
    roster: Sequence[RosterMember],
    *,
    limit: int = 20,
) -> str:
    """Format detailed comparison output for the first swimmers."""
    entries = build_compare_entries(swimmers, roster)[:limit]
    lines = [
        "Compare Debug",
        "",
        f"Unique swimmers compared: {len(swimmers)}",
        f"Showing first {len(entries)} swimmers",
        "",
    ]

    for index, entry in enumerate(entries, start=1):
        swimmer = entry.swimmer
        lines.extend(
            [
                f"Swimmer {index}",
                f"  CL2 birthday: {_format_birth_date(swimmer.birthday)}",
                f"  CL2 first name: {swimmer.first_name}",
                f"  CL2 last name: {swimmer.last_name}",
                f"  CL2 TeamUnify ID: {_format_optional_id(swimmer.teamunify_id)}",
                (
                    "  Matched roster record: "
                    f"{_format_roster_member(entry.roster_member)}"
                ),
                f"  Match reason: {entry.reason}",
                f"  Final classification: {_format_status(entry.status)}",
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def format_compare_debug_from_files(
    cl2_path: Path | str,
    roster_path: Path | str,
    *,
    limit: int = 20,
) -> str:
    """Read inputs and format debug comparison output."""
    swimmers = load_unique_swimmers(cl2_path)
    roster = read_roster(roster_path)
    return format_compare_debug(swimmers, roster, limit=limit)


def format_compare_report(report: CompareReport) -> str:
    """Format a comparison report for CLI output."""
    lines = [
        "Comparison Report",
        "",
        f"Swimmers: {report.total_swimmers}",
        "",
        _format_section(
            "Exact Match",
            report.exact_matches,
            _format_exact_entry,
        ),
        _format_section(
            "TeamUnify ID Missing in CL2",
            report.teamunify_id_missing_in_cl2,
            _format_roster_id_entry,
        ),
        _format_section(
            "Missing ID in TeamUnify Roster",
            report.missing_id_in_teamunify_roster,
            _format_reason_entry,
        ),
        _format_section(
            "Name Mismatch",
            report.name_mismatches,
            _format_reason_entry,
        ),
        _format_section(
            "Birthday Mismatch",
            report.birthday_mismatches,
            _format_reason_entry,
        ),
        _format_section(
            "Ambiguous Match",
            report.ambiguous_matches,
            _format_reason_entry,
        ),
        _format_section(
            "No Match",
            report.no_matches,
            _format_reason_entry,
        ),
    ]
    return "\n".join(lines) + "\n"


def _compare_swimmer(
    swimmer: CL2Swimmer,
    roster: Sequence[RosterMember],
    roster_by_id: dict[str, RosterMember],
) -> CompareEntry:
    if swimmer.teamunify_id is not None:
        member = roster_by_id.get(swimmer.teamunify_id.upper())
        if member is not None:
            return _compare_by_teamunify_id(swimmer, member)

    candidates = _identity_candidates(swimmer, roster)
    if not candidates:
        return CompareEntry(
            swimmer=swimmer,
            roster_member=None,
            status=CompareStatus.NO_MATCH,
            reason="no roster member matches birthday, name, and gender",
        )

    if len(candidates) > 1:
        narrowed = _narrow_by_middle_initial(swimmer, candidates)
        if len(narrowed) == 1:
            return _compare_identity_match(swimmer, narrowed[0])
        return CompareEntry(
            swimmer=swimmer,
            roster_member=None,
            status=CompareStatus.AMBIGUOUS_MATCH,
            reason=_ambiguous_reason(len(narrowed) or len(candidates)),
        )

    return _compare_identity_match(swimmer, candidates[0])


def _compare_by_teamunify_id(
    swimmer: CL2Swimmer,
    member: RosterMember,
) -> CompareEntry:
    if swimmer.birthday is not None and swimmer.birthday != member.birthday:
        return CompareEntry(
            swimmer=swimmer,
            roster_member=member,
            status=CompareStatus.BIRTHDAY_MISMATCH,
            reason=(
                f"CL2 birthday {swimmer.birthday.isoformat()} does not match "
                f"roster birthday {member.birthday.isoformat()}"
            ),
        )

    if not _names_match(swimmer, member):
        return CompareEntry(
            swimmer=swimmer,
            roster_member=member,
            status=CompareStatus.NAME_MISMATCH,
            reason=(
                "CL2 name does not match roster name for TeamUnify ID "
                f"{member.id_card}"
            ),
        )

    return CompareEntry(
        swimmer=swimmer,
        roster_member=member,
        status=CompareStatus.EXACT_MATCH,
        reason="matched TeamUnify ID, birthday, and name",
    )


def _compare_identity_match(
    swimmer: CL2Swimmer,
    member: RosterMember,
) -> CompareEntry:
    if member.id_card is None:
        return CompareEntry(
            swimmer=swimmer,
            roster_member=member,
            status=CompareStatus.MISSING_ID_IN_TEAMUNIFY_ROSTER,
            reason="matched birthday, name, and gender, but roster has no ID card",
        )

    if swimmer.teamunify_id is None:
        return CompareEntry(
            swimmer=swimmer,
            roster_member=member,
            status=CompareStatus.TEAMUNIFY_ID_MISSING_IN_CL2,
            reason=(
                "matched birthday, name, and gender, but CL2 has no TeamUnify ID "
                f"(roster id {member.id_card})"
            ),
        )

    if swimmer.teamunify_id.upper() != member.id_card.upper():
        return CompareEntry(
            swimmer=swimmer,
            roster_member=member,
            status=CompareStatus.NAME_MISMATCH,
            reason=(
                "matched birthday, name, and gender, but CL2 TeamUnify ID "
                f"{swimmer.teamunify_id!r} does not match roster id {member.id_card!r}"
            ),
        )

    return CompareEntry(
        swimmer=swimmer,
        roster_member=member,
        status=CompareStatus.EXACT_MATCH,
        reason="matched birthday, name, gender, and TeamUnify ID",
    )


def _identity_candidates(
    swimmer: CL2Swimmer,
    roster: Sequence[RosterMember],
) -> list[RosterMember]:
    if swimmer.birthday is None:
        return []

    return [
        member
        for member in roster
        if member.birthday == swimmer.birthday
        and _names_match(swimmer, member)
        and _genders_match(swimmer, member)
    ]


def _narrow_by_middle_initial(
    swimmer: CL2Swimmer,
    candidates: Sequence[RosterMember],
) -> list[RosterMember]:
    swimmer_middle = _normalize_middle_initial(swimmer.middle_initial)
    if swimmer_middle is None:
        return []

    return [
        member
        for member in candidates
        if _normalize_middle_initial(member.middle_initial) == swimmer_middle
    ]


def _index_roster_by_id(
    roster: Sequence[RosterMember],
) -> dict[str, RosterMember]:
    indexed: dict[str, RosterMember] = {}
    for member in roster:
        if member.id_card is None:
            continue
        indexed[member.id_card.upper()] = member
    return indexed


def _names_match(swimmer: CL2Swimmer, member: RosterMember) -> bool:
    return (
        swimmer.first_name.casefold() == member.first_name.casefold()
        and swimmer.last_name.casefold() == member.last_name.casefold()
    )


def _genders_match(swimmer: CL2Swimmer, member: RosterMember) -> bool:
    if swimmer.gender is None or member.gender is None:
        return True
    return swimmer.gender == member.gender


def _normalize_middle_initial(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped[0].casefold()


def _ambiguous_reason(candidate_count: int) -> str:
    if candidate_count > 1:
        return (
            "multiple roster members match birthday, name, gender, and middle initial"
        )
    return "multiple roster members match birthday, name, and gender"


def _sorted_entries(entries: Sequence[CompareEntry]) -> tuple[CompareEntry, ...]:
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


def _format_section(
    title: str,
    entries: Sequence[CompareEntry],
    formatter: Callable[[CompareEntry], str],
) -> str:
    lines = [f"{title} ({len(entries)})"]
    if not entries:
        lines.append("  (none)")
        return "\n".join(lines)

    for entry in entries:
        lines.append(f"  {formatter(entry)}")
    return "\n".join(lines)


def _format_swimmer_name(swimmer: CL2Swimmer) -> str:
    return f"{swimmer.last_name}, {swimmer.first_name}"


def _format_birth_date(birth_date: date | None) -> str:
    if birth_date is None:
        return "????-??-??"
    return birth_date.isoformat()


def _format_exact_entry(entry: CompareEntry) -> str:
    swimmer = entry.swimmer
    roster_id = entry.roster_member.id_card if entry.roster_member is not None else None
    return (
        f"{_format_swimmer_name(swimmer)}  "
        f"{_format_birth_date(swimmer.birthday)}  ->  {roster_id}"
    )


def _format_roster_id_entry(entry: CompareEntry) -> str:
    swimmer = entry.swimmer
    roster_id = entry.roster_member.id_card if entry.roster_member is not None else None
    return (
        f"{_format_swimmer_name(swimmer)}  "
        f"{_format_birth_date(swimmer.birthday)}  ->  {roster_id}"
    )


def _format_reason_entry(entry: CompareEntry) -> str:
    swimmer = entry.swimmer
    return (
        f"{_format_swimmer_name(swimmer)}  "
        f"{_format_birth_date(swimmer.birthday)}  ({entry.reason})"
    )


def _format_optional_id(teamunify_id: str | None) -> str:
    if teamunify_id is None:
        return "(none)"
    return teamunify_id


def _format_roster_member(member: RosterMember | None) -> str:
    if member is None:
        return "(none)"
    return (
        f"{member.last_name}, {member.first_name}  "
        f"{_format_birth_date(member.birthday)}  "
        f"id={_format_optional_id(member.id_card)}"
    )


def _format_status(status: CompareStatus) -> str:
    labels = {
        CompareStatus.EXACT_MATCH: "Exact Match",
        CompareStatus.TEAMUNIFY_ID_MISSING_IN_CL2: "TeamUnify ID Missing in CL2",
        CompareStatus.MISSING_ID_IN_TEAMUNIFY_ROSTER: "Missing ID in TeamUnify Roster",
        CompareStatus.NAME_MISMATCH: "Name Mismatch",
        CompareStatus.BIRTHDAY_MISMATCH: "Birthday Mismatch",
        CompareStatus.AMBIGUOUS_MATCH: "Ambiguous Match",
        CompareStatus.NO_MATCH: "No Match",
    }
    return labels[status]
