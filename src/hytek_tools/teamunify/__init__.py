"""TeamUnify roster import and identity matching."""

from hytek_tools.teamunify.match_report import (
    MatchCategory,
    MatchReport,
    MatchReportEntry,
    build_match_report,
    build_match_report_from_files,
    format_match_report,
)
from hytek_tools.teamunify.matcher import MatchResult, RosterMatcher
from hytek_tools.teamunify.models import RosterMember
from hytek_tools.teamunify.roster import RosterLoader, read_roster
from hytek_tools.teamunify.validation import (
    InvalidBirthdayEntry,
    RosterValidation,
    format_roster_validation,
    validate_roster,
)

__all__ = [
    "MatchCategory",
    "MatchReport",
    "MatchReportEntry",
    "InvalidBirthdayEntry",
    "MatchResult",
    "RosterLoader",
    "RosterValidation",
    "RosterMatcher",
    "RosterMember",
    "build_match_report",
    "build_match_report_from_files",
    "format_match_report",
    "format_roster_validation",
    "read_roster",
    "validate_roster",
]
