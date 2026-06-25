"""HYTEK Tools CLI entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the HYTEK Tools CLI."""
    args = _build_parser().parse_args(argv)

    if args.command == "inspect":
        path: Path = args.file
        if not path.is_file():
            print(f"error: file not found: {path}", file=sys.stderr)
            return 1
        counts = count_record_types(path)
        sys.stdout.write(format_record_counts(counts))
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
