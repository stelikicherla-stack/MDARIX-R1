from abc import ABC, abstractmethod
from pathlib import Path

from ingestion.models.source import SourceRecord


class BaseSourceAdapter(ABC):
    supported_suffixes: set[str] = set()

    def validate_file(self, path: Path) -> None:
        if not path.exists():
            raise FileNotFoundError(path)
        if path.suffix.lower() not in self.supported_suffixes:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        if path.stat().st_size == 0:
            raise ValueError(f"Source file is empty: {path}")

    @abstractmethod
    def read_records(self, path: Path) -> list[SourceRecord]:
        raise NotImplementedError
