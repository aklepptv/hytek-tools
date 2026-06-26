"""TeamUnify roster-to-CL2 match reporting."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path

from hytek_tools.models.swimmer import Swimmer
from hytek_tools.parsers.cl2.swimmers import read_swimmers
from hytek_tools.teamunify.matcher import MatchResult, RosterMatcher
from hytek_tools.teamunify.roster import RosterMember, read_roster


class MatchCategory(Enum):
    """Classification for a swimmer-to-roster match outcome."""

    EXACT = "exact"
    MISSING_ID_CARD = "missing_id_card"
    AMBIGUOUS = "ambiguous"
    UNMATCHED = "unmatched"


@dataclass(frozen=True, slots=True)
class MatchReportEntry:
    """One swimmer and its roster match outcome."""

    swimmer: Swimmer
    result: MatchResult
    category: MatchCategory


@dataclass(frozen=True, slots=True)
class MatchReport:
    """Grouped outcomes from matching CL2 swimmers to a TeamUnify roster."""

    exact_matches: tuple[MatchReportEntry, ...]
    missing_id_cards: tuple[MatchReportEntry, ...]
    ambiguous_matches: tuple[MatchReportEntry, ...]
    unmatched_swimmers: tuple[MatchReportEntry, ...]

    @property
    def total_swimmers(self) -> int:
        return (
            len(self.exact_matches)
            + len(self.missing_id_cards)
            + len(self.ambiguous_matches)
            + len(self.unmatched_swimmers)
        )


def build_match_report(
    swimmers: Sequence[Swimmer],
    roster: Sequence[RosterMember],
) -> MatchReport:
    """Match swimmers against a roster and group the outcomes."""
    matcher = RosterMatcher(roster)
    exact: list[MatchReportEntry] = []
    missing_id_cards: list[MatchReportEntry] = []
    ambiguous: list[MatchReportEntry] = []
    unmatched: list[MatchReportEntry] = []

    for swimmer in swimmers:
        result = matcher.match(swimmer)
        entry = MatchReportEntry(
            swimmer=swimmer,
            result=result,
            category=_classify_match(result),
        )
        if entry.category is MatchCategory.EXACT:
            exact.append(entry)
        elif entry.category is MatchCategory.MISSING_ID_CARD:
            missing_id_cards.append(entry)
        elif entry.category is MatchCategory.AMBIGUOUS:
            ambiguous.append(entry)
        else:
            unmatched.append(entry)

    return MatchReport(
        exact_matches=tuple(exact),
        missing_id_cards=tuple(missing_id_cards),
        ambiguous_matches=tuple(ambiguous),
        unmatched_swimmers=tuple(unmatched),
    )


def build_match_report_from_files(
    cl2_path: Path | str,
    roster_path: Path | str,
) -> MatchReport:
    """Read a CL2 file and roster CSV, then build a match report."""
    swimmers = read_swimmers(cl2_path)
    roster = read_roster(roster_path)
    return build_match_report(swimmers, roster)


def format_match_report(report: MatchReport) -> str:
    """Format a match report for CLI output."""
    lines = [
        "Match Report",
        "",
        f"Swimmers: {report.total_swimmers}",
        "",
        _format_section(
            "Exact matches",
            report.exact_matches,
            _format_exact_entry,
        ),
        _format_section(
            "Missing ID Cards",
            report.missing_id_cards,
            _format_reason_entry,
        ),
        _format_section(
            "Ambiguous matches",
            report.ambiguous_matches,
            _format_reason_entry,
        ),
        _format_section(
            "Unmatched swimmers",
            report.unmatched_swimmers,
            _format_reason_entry,
        ),
    ]
    return "\n".join(lines)


def _classify_match(result: MatchResult) -> MatchCategory:
    if result.confidence == "high" and result.id_card is not None:
        return MatchCategory.EXACT
    if result.confidence == "low":
        return MatchCategory.MISSING_ID_CARD
    if result.confidence == "none" and (
        "multiple roster members" in result.reason
        or "middle initial required" in result.reason
    ):
        return MatchCategory.AMBIGUOUS
    return MatchCategory.UNMATCHED


def _format_section(
    title: str,
    entries: Sequence[MatchReportEntry],
    formatter: Callable[[MatchReportEntry], str],
) -> str:
    lines = [f"{title} ({len(entries)})"]
    if not entries:
        lines.append("  (none)")
        return "\n".join(lines)

    for entry in entries:
        lines.append(f"  {formatter(entry)}")
    return "\n".join(lines)


def _format_swimmer_name(swimmer: Swimmer) -> str:
    return f"{swimmer.last_name}, {swimmer.first_name}"


def _format_birth_date(birth_date: date | None) -> str:
    if birth_date is None:
        return "????-??-??"
    return birth_date.isoformat()


def _format_exact_entry(entry: MatchReportEntry) -> str:
    swimmer = entry.swimmer
    return (
        f"{_format_swimmer_name(swimmer)}  "
        f"{_format_birth_date(swimmer.birth_date)}  ->  {entry.result.id_card}"
    )


def _format_reason_entry(entry: MatchReportEntry) -> str:
    swimmer = entry.swimmer
    return (
        f"{_format_swimmer_name(swimmer)}  "
        f"{_format_birth_date(swimmer.birth_date)}  ({entry.result.reason})"
    )
