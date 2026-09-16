import csv
from pathlib import Path

from ingestion.adapters.base import BaseSourceAdapter
from ingestion.models.source import SourceRecord


class CSVSourceAdapter(BaseSourceAdapter):
    supported_suffixes = {".csv"}

    def read_records(self, path: Path) -> list[SourceRecord]:
        self.validate_file(path)
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError(f"CSV headers missing: {path}")
            return [
                SourceRecord(source_file=path, row_index=index, raw_payload=dict(row))
                for index, row in enumerate(reader, start=2)
            ]
