"""Write TeamUnify IDs into CL2 D01 records."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hytek_tools.parsers.cl2.d01 import (
    TEAMUNIFY_ID_FIELD,
    decode_d01_line,
    parse_teamunify_id,
)
from hytek_tools.parsers.cl2.extractor import swimmer_identity_key
from hytek_tools.parsers.cl2.models import CL2RecordLocation, CL2Swimmer
from hytek_tools.teamunify.compare import (
    CompareEntry,
    CompareReport,
    build_compare_report_from_files,
)

_TEAMUNIFY_ID_WIDTH = TEAMUNIFY_ID_FIELD.stop - TEAMUNIFY_ID_FIELD.start


@dataclass(frozen=True, slots=True)
class FixCl2TeamUnifyIdResult:
    """Outcome of writing TeamUnify IDs into a CL2 file."""

    ids_written: int
    records_unchanged: int
    ambiguous: int
    skipped: int
    output_path: Path


def fix_cl2_teamunify_ids(
    cl2_path: Path | str,
    roster_path: Path | str,
    output_path: Path | str,
) -> FixCl2TeamUnifyIdResult:
    """Write roster TeamUnify IDs into writable CL2 D01 records."""
    source_path = Path(cl2_path)
    destination_path = Path(output_path)
    compare_report = build_compare_report_from_files(source_path, roster_path)
    id_by_identity = _writable_id_map(compare_report.teamunify_id_missing_in_cl2)

    ids_written = 0
    records_unchanged = 0
    output_lines: list[str] = []

    with source_path.open(encoding="latin-1", newline="") as handle:
        content = handle.read()

    for line in content.splitlines(keepends=True):
        body, ending = _split_line_ending(line)
        if not body.startswith("D01"):
            output_lines.append(line)
            continue

        updated_body = _maybe_write_teamunify_id(
            body,
            id_by_identity=id_by_identity,
        )
        if updated_body == body:
            records_unchanged += 1
            output_lines.append(line)
        else:
            ids_written += 1
            output_lines.append(updated_body + ending)

    destination_path.write_text("".join(output_lines), encoding="latin-1", newline="")

    return FixCl2TeamUnifyIdResult(
        ids_written=ids_written,
        records_unchanged=records_unchanged,
        ambiguous=len(compare_report.ambiguous_matches),
        skipped=_skipped_swimmer_count(compare_report),
        output_path=destination_path,
    )


def format_fix_cl2_summary(result: FixCl2TeamUnifyIdResult) -> str:
    """Format fix-cl2 summary output for the CLI."""
    return (
        "Fix CL2 Summary\n"
        "\n"
        f"IDs written: {result.ids_written}\n"
        f"Records unchanged: {result.records_unchanged}\n"
        f"Ambiguous: {result.ambiguous}\n"
        f"Skipped: {result.skipped}\n"
    )


def write_teamunify_id_field(line: str, teamunify_id: str) -> str:
    """Replace only the TeamUnify ID field in a D01 line."""
    if not line.startswith("D01"):
        msg = f"expected D01 record, got {line[:3]!r}"
        raise ValueError(msg)
    if len(line) < TEAMUNIFY_ID_FIELD.stop:
        msg = f"D01 record is too short to update TeamUnify ID: {len(line)}"
        raise ValueError(msg)
    if len(teamunify_id) > _TEAMUNIFY_ID_WIDTH:
        msg = f"TeamUnify ID is too long for D01 field: {teamunify_id!r}"
        raise ValueError(msg)

    field = teamunify_id.ljust(_TEAMUNIFY_ID_WIDTH)
    return line[: TEAMUNIFY_ID_FIELD.start] + field + line[TEAMUNIFY_ID_FIELD.stop :]


def _writable_id_map(
    entries: tuple[CompareEntry, ...],
) -> dict[tuple[object, ...], str]:
    id_by_identity: dict[tuple[object, ...], str] = {}
    for entry in entries:
        roster_member = entry.roster_member
        if roster_member is None or roster_member.id_card is None:
            continue
        id_by_identity[swimmer_identity_key(entry.swimmer)] = roster_member.id_card
    return id_by_identity


def _maybe_write_teamunify_id(
    line: str,
    *,
    id_by_identity: dict[tuple[object, ...], str],
) -> str:
    if parse_teamunify_id(line[TEAMUNIFY_ID_FIELD]) is not None:
        return line

    swimmer = _swimmer_from_line(line)
    teamunify_id = id_by_identity.get(swimmer_identity_key(swimmer))
    if teamunify_id is None:
        return line

    return write_teamunify_id_field(line, teamunify_id)


def _swimmer_from_line(line: str) -> CL2Swimmer:
    decoded = decode_d01_line(line)
    return CL2Swimmer(
        first_name=decoded.first_name,
        last_name=decoded.last_name,
        middle_initial=decoded.middle_initial,
        birthday=decoded.birth_date,
        gender=decoded.gender,
        teamunify_id=decoded.teamunify_id,
        location=CL2RecordLocation(line_number=0, byte_offset=0),
    )


def _skipped_swimmer_count(compare_report: CompareReport) -> int:
    return (
        len(compare_report.exact_matches)
        + len(compare_report.missing_id_in_teamunify_roster)
        + len(compare_report.name_mismatches)
        + len(compare_report.birthday_mismatches)
        + len(compare_report.no_matches)
    )


def _split_line_ending(line: str) -> tuple[str, str]:
    if line.endswith("\r\n"):
        return line[:-2], "\r\n"
    if line.endswith("\n"):
        return line[:-1], "\n"
    if line.endswith("\r"):
        return line[:-1], "\r"
    return line, ""
