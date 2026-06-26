"""Raw CL2 line record."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Record:
    """A single line from a CL2 file before field decoding."""

    record_type: str
    line_number: int
    raw_text: str
