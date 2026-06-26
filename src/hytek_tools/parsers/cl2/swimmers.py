"""Extract unique swimmers from CL2 meet files."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from hytek_tools.models.swimmer import Swimmer
from hytek_tools.parsers.cl2.d01 import decode_d01_swimmer
from hytek_tools.parsers.cl2.reader import CL2Reader


def read_swimmers(path: Path | str) -> list[Swimmer]:
    """Read unique swimmers from D01 records in a CL2 file."""
    unique: dict[tuple[str, str, object], Swimmer] = {}
    for record in CL2Reader(path).read():
        if record.record_type != "D01":
            continue
        swimmer = decode_d01_swimmer(record)
        key = (
            swimmer.last_name.casefold(),
            swimmer.first_name.casefold(),
            swimmer.birth_date,
        )
        unique.setdefault(key, swimmer)
    return sorted(
        unique.values(),
        key=lambda swimmer: (
            swimmer.last_name.casefold(),
            swimmer.first_name.casefold(),
            swimmer.birth_date or date.min,
        ),
    )
