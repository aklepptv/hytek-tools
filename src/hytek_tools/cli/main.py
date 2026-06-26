"""HYTEK Tools CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hytek_tools.inspect.cl2_diff import compare_cl2_files, format_cl2_diff
from hytek_tools.inspect.cl2_trace import format_cl2_trace, trace_cl2_swimmer
from hytek_tools.inspect.hy3_dump import HY3RecordInspector, format_dump
from hytek_tools.inspect.hy3_stats import count_record_types, format_record_counts
from hytek_tools.parsers.cl2.extractor import (
    CL2SwimmerExtractor,
    format_swimmer_summary,
)
from hytek_tools.teamunify.audit import (
    build_identity_audit_report_from_files,
    format_identity_audit,
    write_identity_audit_csv,
)
from hytek_tools.teamunify.compare import (
    build_compare_report_from_files,
    format_compare_debug_from_files,
    format_compare_report,
)
from hytek_tools.teamunify.match_report import (
    build_match_report_from_files,
    format_match_report,
)
from hytek_tools.teamunify.validation import format_roster_validation, validate_roster
from hytek_tools.writers.cl2 import (
    fix_cl2_middle_initials,
    fix_cl2_teamunify_ids,
    format_fix_cl2_middle_initial_summary,
    format_fix_cl2_summary,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hytek")
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect",
        help="show record-type statistics for a meet file",
    )
    inspect_parser.add_argument(
        "file",
        type=Path,
        help="path to an HY3 meet file",
    )

    dump_parser = subparsers.add_parser(
        "dump",
        help="dump every HY3 record without decoding fields",
    )
    dump_parser.add_argument(
        "file",
        type=Path,
        help="path to an HY3 meet file",
    )

    match_report_parser = subparsers.add_parser(
        "match-report",
        help="match CL2 swimmers to a TeamUnify roster",
    )
    match_report_parser.add_argument(
        "--cl2",
        type=Path,
        required=True,
        help="path to a CL2 meet file",
    )
    match_report_parser.add_argument(
        "--roster",
        type=Path,
        required=True,
        help="path to a TeamUnify roster CSV export",
    )

    roster_parser = subparsers.add_parser(
        "roster",
        help="validate a TeamUnify roster CSV export",
    )
    roster_parser.add_argument(
        "file",
        type=Path,
        help="path to a TeamUnify roster CSV export",
    )

    swimmers_parser = subparsers.add_parser(
        "swimmers",
        help="summarize swimmers in a CL2 meet file",
    )
    swimmers_parser.add_argument(
        "file",
        type=Path,
        help="path to a CL2 meet file",
    )

    compare_parser = subparsers.add_parser(
        "compare",
        help="compare CL2 swimmers to a TeamUnify roster",
    )
    compare_parser.add_argument(
        "--cl2",
        type=Path,
        required=True,
        help="path to a CL2 meet file",
    )
    compare_parser.add_argument(
        "--roster",
        type=Path,
        required=True,
        help="path to a TeamUnify roster CSV export",
    )
    compare_parser.add_argument(
        "--debug",
        action="store_true",
        help="print detailed comparison output for the first 20 swimmers",
    )

    fix_cl2_parser = subparsers.add_parser(
        "fix-cl2",
        help="write TeamUnify IDs into CL2 D01 records",
    )
    fix_cl2_parser.add_argument(
        "--cl2",
        type=Path,
        required=True,
        help="path to a CL2 meet file",
    )
    fix_cl2_parser.add_argument(
        "--roster",
        type=Path,
        required=True,
        help="path to a TeamUnify roster CSV export",
    )
    fix_cl2_parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="path for the updated CL2 meet file",
    )
    fix_cl2_parser.add_argument(
        "--middle-initial",
        action="store_true",
        help="write roster middle initials into CL2 D01 name fields",
    )

    diff_cl2_parser = subparsers.add_parser(
        "diff-cl2",
        help="compare two CL2 files byte-for-byte",
    )
    diff_cl2_parser.add_argument(
        "--original",
        type=Path,
        required=True,
        help="path to the original CL2 meet file",
    )
    diff_cl2_parser.add_argument(
        "--new",
        type=Path,
        required=True,
        help="path to the updated CL2 meet file",
    )

    audit_parser = subparsers.add_parser(
        "audit",
        help="audit CL2 swimmer identity fields against a TeamUnify roster",
    )
    audit_parser.add_argument(
        "--cl2",
        type=Path,
        required=True,
        help="path to a CL2 meet file",
    )
    audit_parser.add_argument(
        "--roster",
        type=Path,
        required=True,
        help="path to a TeamUnify roster CSV export",
    )
    audit_parser.add_argument(
        "--csv",
        type=Path,
        help="optional path to export identity differences as CSV",
    )

    trace_parser = subparsers.add_parser(
        "trace",
        help="trace all CL2 records for one swimmer",
    )
    trace_parser.add_argument(
        "--cl2",
        type=Path,
        required=True,
        help="path to a CL2 meet file",
    )
    trace_parser.add_argument(
        "--name",
        required=True,
        help='swimmer name query, for example "Nathan Kleppinger"',
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the HYTEK Tools CLI."""
    args = _build_parser().parse_args(argv)

    if args.command == "audit":
        audit_cl2_path: Path = args.cl2
        audit_roster_path: Path = args.roster
        if not audit_cl2_path.is_file():
            print(f"error: file not found: {audit_cl2_path}", file=sys.stderr)
            return 1
        if not audit_roster_path.is_file():
            print(f"error: file not found: {audit_roster_path}", file=sys.stderr)
            return 1
        audit_report = build_identity_audit_report_from_files(
            audit_cl2_path,
            audit_roster_path,
        )
        sys.stdout.write(format_identity_audit(audit_report))
        if args.csv is not None:
            write_identity_audit_csv(audit_report, args.csv)
        return 0

    if args.command == "trace":
        trace_cl2_path: Path = args.cl2
        if not trace_cl2_path.is_file():
            print(f"error: file not found: {trace_cl2_path}", file=sys.stderr)
            return 1
        try:
            trace_report = trace_cl2_swimmer(trace_cl2_path, args.name)
        except ValueError as error:
            print(f"error: {error}", file=sys.stderr)
            return 1
        sys.stdout.write(format_cl2_trace(trace_report))
        return 0

    if args.command == "diff-cl2":
        diff_original_path: Path = args.original
        diff_new_path: Path = args.new
        if not diff_original_path.is_file():
            print(f"error: file not found: {diff_original_path}", file=sys.stderr)
            return 1
        if not diff_new_path.is_file():
            print(f"error: file not found: {diff_new_path}", file=sys.stderr)
            return 1
        diff_report = compare_cl2_files(diff_original_path, diff_new_path)
        sys.stdout.write(format_cl2_diff(diff_report))
        return 0

    if args.command == "fix-cl2":
        fix_cl2_path: Path = args.cl2
        fix_roster_path: Path = args.roster
        fix_output_path: Path = args.output
        if not fix_cl2_path.is_file():
            print(f"error: file not found: {fix_cl2_path}", file=sys.stderr)
            return 1
        if not fix_roster_path.is_file():
            print(f"error: file not found: {fix_roster_path}", file=sys.stderr)
            return 1
        if args.middle_initial:
            middle_initial_result = fix_cl2_middle_initials(
                fix_cl2_path,
                fix_roster_path,
                fix_output_path,
            )
            sys.stdout.write(
                format_fix_cl2_middle_initial_summary(middle_initial_result)
            )
            return 0
        teamunify_id_result = fix_cl2_teamunify_ids(
            fix_cl2_path,
            fix_roster_path,
            fix_output_path,
        )
        sys.stdout.write(format_fix_cl2_summary(teamunify_id_result))
        return 0

    if args.command == "compare":
        compare_cl2_path: Path = args.cl2
        compare_roster_path: Path = args.roster
        if not compare_cl2_path.is_file():
            print(f"error: file not found: {compare_cl2_path}", file=sys.stderr)
            return 1
        if not compare_roster_path.is_file():
            print(f"error: file not found: {compare_roster_path}", file=sys.stderr)
            return 1
        comparison = build_compare_report_from_files(
            compare_cl2_path,
            compare_roster_path,
        )
        if args.debug:
            sys.stdout.write(
                format_compare_debug_from_files(
                    compare_cl2_path,
                    compare_roster_path,
                )
            )
        sys.stdout.write(format_compare_report(comparison))
        return 0

    if args.command == "swimmers":
        cl2_file: Path = args.file
        if not cl2_file.is_file():
            print(f"error: file not found: {cl2_file}", file=sys.stderr)
            return 1
        summary = CL2SwimmerExtractor(cl2_file).summarize()
        sys.stdout.write(format_swimmer_summary(summary))
        return 0

    if args.command == "roster":
        roster_file: Path = args.file
        if not roster_file.is_file():
            print(f"error: file not found: {roster_file}", file=sys.stderr)
            return 1
        validation = validate_roster(roster_file)
        sys.stdout.write(format_roster_validation(validation))
        return 0

    if args.command == "match-report":
        cl2_path: Path = args.cl2
        roster_path: Path = args.roster
        if not cl2_path.is_file():
            print(f"error: file not found: {cl2_path}", file=sys.stderr)
            return 1
        if not roster_path.is_file():
            print(f"error: file not found: {roster_path}", file=sys.stderr)
            return 1
        match_report = build_match_report_from_files(cl2_path, roster_path)
        sys.stdout.write(format_match_report(match_report))
        return 0

    path: Path = args.file
    if not path.is_file():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 1

    if args.command == "inspect":
        counts = count_record_types(path)
        sys.stdout.write(format_record_counts(counts))
        return 0

    if args.command == "dump":
        entries = HY3RecordInspector(path).dump()
        sys.stdout.write(format_dump(entries))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
