from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceRecord:
    source_file: Path
    row_index: int | None
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class SourceFile:
    path: Path
    source_system: str
    source_type: str
    record_type: str
    mapping_name: str
