import json
from pathlib import Path

from ingestion.adapters.base import BaseSourceAdapter
from ingestion.models.source import SourceRecord


class JSONSourceAdapter(BaseSourceAdapter):
    supported_suffixes = {".json"}

    def read_records(self, path: Path) -> list[SourceRecord]:
        self.validate_file(path)
        payload = json.loads(path.read_text(encoding="utf-8"))
        records = payload if isinstance(payload, list) else payload.get("records", payload.get("evidence", payload if isinstance(payload, list) else []))
        if isinstance(records, dict):
            records = [records]
        if not isinstance(records, list):
            raise ValueError(f"JSON source must contain an object/list record structure: {path}")
        return [
            SourceRecord(source_file=path, row_index=index, raw_payload=dict(record))
            for index, record in enumerate(records, start=1)
        ]
