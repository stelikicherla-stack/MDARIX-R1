from pathlib import Path

from ingestion.adapters.base import BaseSourceAdapter
from ingestion.models.source import SourceRecord


class EvidenceFileAdapter(BaseSourceAdapter):
    supported_suffixes = {".md", ".txt"}

    def read_records(self, path: Path) -> list[SourceRecord]:
        self.validate_file(path)
        return [
            SourceRecord(
                source_file=path,
                row_index=1,
                raw_payload={
                    "filename": path.name,
                    "relative_path": path.as_posix(),
                    "content": path.read_text(encoding="utf-8"),
                },
            )
        ]
