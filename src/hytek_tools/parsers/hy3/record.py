"""Raw HY3 line record."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Record:
    """A single line from an HY3 file before field decoding."""

    record_type: str
    line_number: int
    raw_text: str
