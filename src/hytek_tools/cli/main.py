"""HYTEK Tools CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hytek_tools.inspect.hy3_dump import HY3RecordInspector, format_dump
from hytek_tools.inspect.hy3_stats import count_record_types, format_record_counts
from hytek_tools.teamunify.match_report import (
    build_match_report_from_files,
    format_match_report,
)
from hytek_tools.teamunify.validation import format_roster_validation, validate_roster


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
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the HYTEK Tools CLI."""
    args = _build_parser().parse_args(argv)

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
