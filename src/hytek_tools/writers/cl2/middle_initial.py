"""Write middle initials into CL2 D01 name fields."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from hytek_tools.parsers.cl2.d01 import (
    NAME_FIELD,
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
from hytek_tools.writers.cl2.teamunify_id import _split_line_ending

_NAME_FIELD_WIDTH = NAME_FIELD.stop - NAME_FIELD.start


@dataclass(frozen=True, slots=True)
class FixCl2MiddleInitialResult:
    """Outcome of writing middle initials into a CL2 file."""

    middle_initials_added: int
    middle_initials_changed: int
    records_unchanged: int
    output_path: Path


def fix_cl2_middle_initials(
    cl2_path: Path | str,
    roster_path: Path | str,
    output_path: Path | str,
) -> FixCl2MiddleInitialResult:
    """Write roster middle initials into writable CL2 D01 name fields."""
    source_path = Path(cl2_path)
    destination_path = Path(output_path)
    compare_report = build_compare_report_from_files(source_path, roster_path)
    middle_initial_by_identity = _writable_middle_initial_map(compare_report)

    middle_initials_added = 0
    middle_initials_changed = 0
    records_unchanged = 0
    output_lines: list[str] = []

    with source_path.open(encoding="latin-1", newline="") as handle:
        content = handle.read()

    for line in content.splitlines(keepends=True):
        body, ending = _split_line_ending(line)
        if not body.startswith("D01"):
            output_lines.append(line)
            continue

        updated_body, change_kind = _maybe_write_middle_initial(
            body,
            middle_initial_by_identity=middle_initial_by_identity,
        )
        if change_kind == "added":
            middle_initials_added += 1
            output_lines.append(updated_body + ending)
        elif change_kind == "changed":
            middle_initials_changed += 1
            output_lines.append(updated_body + ending)
        else:
            records_unchanged += 1
            output_lines.append(line)

    destination_path.write_text("".join(output_lines), encoding="latin-1", newline="")

    return FixCl2MiddleInitialResult(
        middle_initials_added=middle_initials_added,
        middle_initials_changed=middle_initials_changed,
        records_unchanged=records_unchanged,
        output_path=destination_path,
    )


def format_fix_cl2_middle_initial_summary(result: FixCl2MiddleInitialResult) -> str:
    """Format fix-cl2 middle-initial summary output for the CLI."""
    return (
        "Fix CL2 Summary\n"
        "\n"
        f"Middle initials added: {result.middle_initials_added}\n"
        f"Middle initials changed: {result.middle_initials_changed}\n"
        f"Records unchanged: {result.records_unchanged}\n"
    )


def write_middle_initial_name_field(line: str, middle_initial: str) -> str:
    """Replace only the middle-initial portion of a D01 name field."""
    if not line.startswith("D01"):
        msg = f"expected D01 record, got {line[:3]!r}"
        raise ValueError(msg)
    if len(line) < NAME_FIELD.stop:
        msg = f"D01 record is too short to update middle initial: {len(line)}"
        raise ValueError(msg)
    if parse_teamunify_id(line[TEAMUNIFY_ID_FIELD]) is not None:
        msg = "cannot update middle initial in name when TeamUnify ID is embedded"
        raise ValueError(msg)

    mi_char = _normalize_middle_initial(middle_initial)
    if mi_char is None:
        msg = f"middle initial is empty: {middle_initial!r}"
        raise ValueError(msg)

    decoded = decode_d01_line(line)
    name_field = _format_name_field(
        decoded.last_name,
        decoded.first_name,
        mi_char,
    )
    return line[: NAME_FIELD.start] + name_field + line[NAME_FIELD.stop :]


def _writable_middle_initial_map(
    compare_report: CompareReport,
) -> dict[tuple[object, ...], str]:
    middle_initial_by_identity: dict[tuple[object, ...], str] = {}
    for entry in _writable_compare_entries(compare_report):
        roster_member = entry.roster_member
        if roster_member is None:
            continue
        middle_initial = _normalize_middle_initial(roster_member.middle_initial)
        if middle_initial is None:
            continue
        middle_initial_by_identity[swimmer_identity_key(entry.swimmer)] = middle_initial
    return middle_initial_by_identity


def _writable_compare_entries(
    compare_report: CompareReport,
) -> tuple[CompareEntry, ...]:
    return (
        compare_report.exact_matches
        + compare_report.teamunify_id_missing_in_cl2
        + compare_report.missing_id_in_teamunify_roster
    )


def _maybe_write_middle_initial(
    line: str,
    *,
    middle_initial_by_identity: dict[tuple[object, ...], str],
) -> tuple[str, str | None]:
    if parse_teamunify_id(line[TEAMUNIFY_ID_FIELD]) is not None:
        return line, None

    swimmer = _swimmer_from_line(line)
    target_middle_initial = middle_initial_by_identity.get(
        swimmer_identity_key(swimmer),
    )
    if target_middle_initial is None:
        return line, None

    current_middle_initial = _name_field_middle_initial(line)
    if current_middle_initial == target_middle_initial:
        return line, None

    updated = write_middle_initial_name_field(line, target_middle_initial)
    if current_middle_initial is None:
        return updated, "added"
    return updated, "changed"


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


def _name_field_middle_initial(line: str) -> str | None:
    name_value = line[NAME_FIELD]
    if "," not in name_value:
        return None
    _last_name, first_name = name_value.split(",", 1)
    parts = first_name.strip().split()
    if len(parts) >= 2 and len(parts[-1]) == 1:
        return parts[-1]
    return None


def _format_name_field(last_name: str, first_name: str, middle_initial: str) -> str:
    base = f"{last_name}, {first_name} {middle_initial}"
    if len(base) > _NAME_FIELD_WIDTH:
        msg = f"name field is too long after adding middle initial: {base!r}"
        raise ValueError(msg)
    return base.ljust(_NAME_FIELD_WIDTH)


def _normalize_middle_initial(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return stripped[0]
