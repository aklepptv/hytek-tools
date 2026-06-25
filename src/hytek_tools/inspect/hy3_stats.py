"""HY3 record-type statistics without field parsing."""

from __future__ import annotations

from collections import Counter
from pathlib import Path


def count_record_types(path: Path | str) -> dict[str, int]:
    """Count HY3 lines by their two-character record-type prefix."""
    counts: Counter[str] = Counter()
    with Path(path).open(encoding="latin-1") as handle:
        for line in handle:
            counts[line.rstrip("\r\n")[:2]] += 1
    return dict(counts)


def format_record_counts(counts: dict[str, int]) -> str:
    """Format record-type counts for CLI output."""
    lines = ["Record counts", ""]
    for record_type in sorted(counts):
        lines.append(f"{record_type} {counts[record_type]}")
    return "\n".join(lines) + "\n"
