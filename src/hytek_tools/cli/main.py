"""HYTEK Tools CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from hytek_tools.inspect.hy3_dump import HY3RecordInspector, format_dump
from hytek_tools.inspect.hy3_stats import count_record_types, format_record_counts


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
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the HYTEK Tools CLI."""
    args = _build_parser().parse_args(argv)

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
