import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

from backend.app.db.session import engine
from ingestion.adapters.csv_adapter import CSVSourceAdapter
from ingestion.adapters.evidence_file_adapter import EvidenceFileAdapter
from ingestion.adapters.json_adapter import JSONSourceAdapter
from ingestion.models.source import SourceFile, SourceRecord

ROOT = Path(__file__).resolve().parents[2]
MAPPINGS = ROOT / "ingestion" / "mappings"
GOLDEN_SOURCE = ROOT / "data" / "golden" / "source"
MANIFEST = ROOT / "data" / "golden" / "GOLDEN_DATASET_MANIFEST.json"
GROUND_TRUTH = ROOT / "evaluation" / "ground_truth"


SOURCE_REGISTRY = {
    "plm/products.csv": ("PLM", "plm", "product", "plm_product_v1.json"),
    "plm/product_versions.csv": ("PLM", "plm", "product_version", "plm_product_version_v1.json"),
    "plm/components.csv": ("PLM", "plm", "component", "plm_component_v1.json"),
    "plm/requirements.csv": ("PLM", "plm", "requirement", "plm_requirement_v1.json"),
    "plm/changes.csv": ("PLM", "plm", "change", "plm_change_v1.json"),
    "qms/complaints.csv": ("QMS", "qms", "complaint", "qms_complaint_v1.json"),
    "qms/investigations.csv": ("QMS", "qms", "investigation", "qms_investigation_v1.json"),
    "qms/risks.csv": ("QMS", "qms", "risk", "generic_source_v1.json"),
    "qms/failure_modes.csv": ("QMS", "qms", "failure_mode", "generic_source_v1.json"),
    "qms/controls.csv": ("QMS", "qms", "control", "generic_source_v1.json"),
    "erp_mes/suppliers.csv": ("ERP_MES", "erp_mes", "supplier", "erp_supplier_v1.json"),
    "erp_mes/manufacturing_sites.csv": ("ERP_MES", "erp_mes", "manufacturing_site", "erp_site_v1.json"),
    "erp_mes/lots.csv": ("ERP_MES", "erp_mes", "lot", "erp_lot_v1.json"),
    "documents/evidence_metadata.json": ("EVIDENCE", "evidence", "evidence_metadata", "generic_source_v1.json"),
}


@dataclass
class RecordOutcome:
    status: str
    issues: list[dict[str, Any]]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_sha256(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_mapping(name: str) -> dict[str, Any]:
    return load_json(MAPPINGS / name)


def parse_source_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text_value = str(value)
    try:
        if len(text_value) == 10:
            return datetime.fromisoformat(text_value).replace(tzinfo=timezone.utc)
        parsed = datetime.fromisoformat(text_value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def adapter_for(path: Path):
    if path.suffix.lower() == ".csv":
        return CSVSourceAdapter()
    if path.suffix.lower() == ".json":
        return JSONSourceAdapter()
    if path.suffix.lower() in {".md", ".txt"}:
        return EvidenceFileAdapter()
    raise ValueError(f"Unsupported source format: {path}")


def discover_sources(source_root: Path = GOLDEN_SOURCE) -> list[SourceFile]:
    sources: list[SourceFile] = []
    for relative, (source_system, source_type, record_type, mapping_name) in SOURCE_REGISTRY.items():
        path = source_root / relative
        if path.exists():
            sources.append(SourceFile(path, source_system, source_type, record_type, mapping_name))
    evidence_dir = source_root / "evidence"
    if evidence_dir.exists():
        for path in sorted(evidence_dir.glob("*.md")):
            sources.append(SourceFile(path, "EVIDENCE", "evidence", "evidence_file", "evidence_file_v1.json"))
    return sources


class IngestionService:
    def __init__(self, source_root: Path = GOLDEN_SOURCE):
        self.source_root = source_root

    def ingest_all(self, initiated_by: str = "day4-cli") -> dict[str, Any]:
        tenant_id = self.ensure_tenant()
        sources = discover_sources(self.source_root)
        results = [self.ingest_source(tenant_id, source, initiated_by) for source in sources]
        return {
            "files_discovered": len(sources),
            "files_ingested": sum(1 for result in results if result["status"] != "ALREADY_INGESTED"),
            "records_seen": sum(result["total_records"] for result in results),
            "records_accepted": sum(result["accepted_records"] for result in results),
            "records_with_warnings": sum(result["warning_records"] for result in results),
            "records_rejected": sum(result["rejected_records"] for result in results),
            "duplicate_source_records": sum(result["duplicate_source_records"] for result in results),
            "quality_issues": sum(result["quality_issues"] for result in results),
            "runs": results,
        }

    def ensure_tenant(self) -> str:
        manifest = load_json(MANIFEST)
        tenant_key = "ACME_CARE_SYNTHETIC"
        now = utcnow()
        with engine.begin() as conn:
            tenant_id = conn.execute(text("SELECT id FROM tenants WHERE tenant_key=:tenant_key"), {"tenant_key": tenant_key}).scalar_one_or_none()
            if tenant_id:
                return str(tenant_id)
            return str(conn.execute(
                text("INSERT INTO tenants (tenant_key, name, status, created_at, updated_at) VALUES (:tenant_key, :name, 'active', :now, :now) RETURNING id"),
                {"tenant_key": tenant_key, "name": manifest["fictional_company"], "now": now},
            ).scalar_one())

    def ingest_source(self, tenant_id: str, source: SourceFile, initiated_by: str) -> dict[str, Any]:
        if GROUND_TRUTH in source.path.resolve().parents:
            raise ValueError("Ground Truth path must not be ingested")
        mapping = load_mapping(source.mapping_name)
        checksum = file_sha256(source.path)
        source_file = source.path.relative_to(ROOT).as_posix() if source.path.is_relative_to(ROOT) else source.path.as_posix()
        now = utcnow()
        self.upsert_mapping(mapping, now)

        with engine.begin() as conn:
            existing = conn.execute(
                text(
                    "SELECT id FROM ingestion_runs WHERE tenant_id=:tenant_id AND source_system=:source_system "
                    "AND source_file=:source_file AND source_checksum=:checksum AND status in ('COMPLETED','COMPLETED_WITH_WARNINGS')"
                ),
                {"tenant_id": tenant_id, "source_system": source.source_system, "source_file": source_file, "checksum": checksum},
            ).scalar_one_or_none()
            if existing:
                run_id = conn.execute(
                    text(
                        "INSERT INTO ingestion_runs (tenant_id, source_system, source_type, source_file, source_checksum, ingestion_started_at, ingestion_completed_at, status, mapping_version, initiated_by, provenance, duplicate_source_records) "
                        "VALUES (:tenant_id, :source_system, :source_type, :source_file, :checksum, :now, :now, 'ALREADY_INGESTED', :mapping_version, :initiated_by, :provenance, 1) RETURNING id"
                    ),
                    {
                        "tenant_id": tenant_id,
                        "source_system": source.source_system,
                        "source_type": source.source_type,
                        "source_file": source_file,
                        "checksum": checksum,
                        "now": now,
                        "mapping_version": mapping["mapping_version"],
                        "initiated_by": initiated_by,
                        "provenance": json.dumps({"previous_run_id": str(existing), "idempotency": "checksum_match"}),
                    },
                ).scalar_one()
                return self.run_summary(conn, str(run_id))

            run_id = conn.execute(
                text(
                    "INSERT INTO ingestion_runs (tenant_id, source_system, source_type, source_file, source_checksum, ingestion_started_at, status, mapping_version, initiated_by, provenance) "
                    "VALUES (:tenant_id, :source_system, :source_type, :source_file, :checksum, :now, 'RUNNING', :mapping_version, :initiated_by, :provenance) RETURNING id"
                ),
                {
                    "tenant_id": tenant_id,
                    "source_system": source.source_system,
                    "source_type": source.source_type,
                    "source_file": source_file,
                    "checksum": checksum,
                    "now": now,
                    "mapping_version": mapping["mapping_version"],
                    "initiated_by": initiated_by,
                    "provenance": json.dumps({"schema_version": mapping["schema_version"], "adapter": source.path.suffix.lower()}),
                },
            ).scalar_one()

            try:
                records = adapter_for(source.path).read_records(source.path)
                self.validate_headers(source, records, mapping)
                accepted = warnings = rejected = issues = 0
                for record in records:
                    outcome = self.stage_record(conn, tenant_id, str(run_id), source, source_file, checksum, mapping, record)
                    if outcome.status == "ACCEPTED":
                        accepted += 1
                    elif outcome.status == "ACCEPTED_WITH_WARNINGS":
                        warnings += 1
                    else:
                        rejected += 1
                    issues += len(outcome.issues)
                status = "COMPLETED_WITH_WARNINGS" if warnings or rejected else "COMPLETED"
                conn.execute(
                    text(
                        "UPDATE ingestion_runs SET ingestion_completed_at=:now, status=:status, total_records=:total, accepted_records=:accepted, warning_records=:warnings, rejected_records=:rejected "
                        "WHERE id=:run_id"
                    ),
                    {"now": utcnow(), "status": status, "total": len(records), "accepted": accepted, "warnings": warnings, "rejected": rejected, "run_id": run_id},
                )
            except Exception as exc:
                conn.execute(
                    text("UPDATE ingestion_runs SET ingestion_completed_at=:now, status='FAILED', error_summary=:error WHERE id=:run_id"),
                    {"now": utcnow(), "error": safe_error(exc), "run_id": run_id},
                )
                return self.run_summary(conn, str(run_id))
            return self.run_summary(conn, str(run_id))

    def upsert_mapping(self, mapping: dict[str, Any], now: datetime) -> None:
        with engine.begin() as conn:
            exists = conn.execute(
                text("SELECT id FROM source_mappings WHERE source_system=:s AND record_type=:r AND mapping_version=:m"),
                {"s": mapping["source_system"], "r": mapping["record_type"], "m": mapping["mapping_version"]},
            ).scalar_one_or_none()
            if exists:
                return
            conn.execute(
                text(
                    "INSERT INTO source_mappings (source_system, record_type, mapping_version, schema_version, field_mappings, required_source_fields, timestamp_semantics, created_at) "
                    "VALUES (:s, :r, :m, :schema, :fields, :required, :timestamps, :now)"
                ),
                {
                    "s": mapping["source_system"],
                    "r": mapping["record_type"],
                    "m": mapping["mapping_version"],
                    "schema": mapping["schema_version"],
                    "fields": json.dumps(mapping["field_mappings"]),
                    "required": json.dumps(mapping["required_source_fields"]),
                    "timestamps": json.dumps(mapping.get("timestamp_semantics", {})),
                    "now": now,
                },
            )

    def validate_headers(self, source: SourceFile, records: list[SourceRecord], mapping: dict[str, Any]) -> None:
        if not records:
            raise ValueError(f"No records found in {source.path}")
        if source.path.suffix.lower() == ".csv":
            observed = set(records[0].raw_payload)
            required = set(mapping["required_source_fields"])
            missing = required - observed
            if missing:
                raise ValueError(f"Schema drift: missing required fields {sorted(missing)} in {source.path}")

    def stage_record(self, conn, tenant_id: str, run_id: str, source: SourceFile, source_file: str, file_checksum: str, mapping: dict[str, Any], record: SourceRecord) -> RecordOutcome:
        raw = record.raw_payload
        record_id = self.source_record_id(source, raw, record.row_index)
        parsed = dict(raw)
        candidate = {target: raw.get(source_field) for source_field, target in mapping["field_mappings"].items()}
        issues = self.record_issues(mapping, raw)
        quality = "ACCEPTED_WITH_WARNINGS" if issues else "ACCEPTED"
        checksum = record_sha256(raw)
        timestamps = self.extract_timestamps(raw)
        staged_id = conn.execute(
            text(
                "INSERT INTO staged_source_records (tenant_id, ingestion_run_id, source_system, source_type, record_type, source_file, source_row_index, source_record_id, source_checksum, raw_payload, parsed_payload, candidate_canonical_payload, source_timestamp, effective_timestamp, recorded_timestamp, ingestion_timestamp, data_quality_status, mapping_version, created_at) "
                "VALUES (:tenant_id, :run_id, :source_system, :source_type, :record_type, :source_file, :row_index, :record_id, :checksum, :raw, :parsed, :candidate, :source_ts, :effective_ts, :recorded_ts, :ingestion_ts, :quality, :mapping_version, :now) RETURNING id"
            ),
            {
                "tenant_id": tenant_id,
                "run_id": run_id,
                "source_system": source.source_system,
                "source_type": source.source_type,
                "record_type": source.record_type,
                "source_file": source_file,
                "row_index": record.row_index,
                "record_id": record_id,
                "checksum": checksum,
                "raw": json.dumps(raw),
                "parsed": json.dumps(parsed),
                "candidate": json.dumps(candidate),
                "source_ts": timestamps.get("source_timestamp"),
                "effective_ts": timestamps.get("effective_timestamp"),
                "recorded_ts": timestamps.get("recorded_timestamp"),
                "ingestion_ts": utcnow(),
                "quality": quality,
                "mapping_version": mapping["mapping_version"],
                "now": utcnow(),
            },
        ).scalar_one()
        for issue in issues:
            conn.execute(
                text(
                    "INSERT INTO data_quality_issues (tenant_id, ingestion_run_id, staged_source_record_id, issue_code, severity, field, observed_value, description, created_at) "
                    "VALUES (:tenant_id, :run_id, :record_id, :issue_code, :severity, :field, :observed_value, :description, :now)"
                ),
                {"tenant_id": tenant_id, "run_id": run_id, "record_id": staged_id, "now": utcnow(), **issue},
            )
        return RecordOutcome(quality, issues)

    def source_record_id(self, source: SourceFile, raw: dict[str, Any], row_index: int | None) -> str:
        for key in ["complaint_id", "product_id", "product_version_id", "component_id", "requirement_id", "change_id", "supplier_id", "site_id", "lot_id", "investigation_id", "risk_id", "failure_mode_id", "control_id", "evidence_id", "filename"]:
            if raw.get(key):
                return str(raw[key])
        return f"{source.record_type}:{row_index}"

    def extract_timestamps(self, raw: dict[str, Any]) -> dict[str, datetime | None]:
        return {
            "source_timestamp": parse_source_datetime(raw.get("source_timestamp") or raw.get("event_timestamp") or raw.get("manufactured_timestamp")),
            "effective_timestamp": parse_source_datetime(raw.get("effective_timestamp") or raw.get("manufactured_timestamp")),
            "recorded_timestamp": parse_source_datetime(raw.get("recorded_timestamp")),
        }

    def record_issues(self, mapping: dict[str, Any], raw: dict[str, Any]) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for field in mapping["required_source_fields"]:
            if raw.get(field) in (None, ""):
                issues.append(issue("MISSING_REQUIRED_FIELD", "ERROR", field, raw.get(field), f"Required source field {field} is missing"))
        if raw.get("lot_id") in (None, "") and ("lot_id" in raw):
            issues.append(issue("MISSING_LOT_REFERENCE", "WARNING", "lot_id", raw.get("lot_id"), "Source complaint has no lot reference"))
        if raw.get("traceability_status") == "incomplete":
            issues.append(issue("INCOMPLETE_TRACEABILITY", "WARNING", "traceability_status", raw.get("traceability_status"), "Source lot/component traceability is incomplete"))
        if str(raw.get("duplicate_candidate", "")).lower() == "true":
            issues.append(issue("DUPLICATE_CANDIDATE", "WARNING", "duplicate_candidate", raw.get("duplicate_candidate"), "Source marks this as a duplicate candidate"))
        for key in ["event_timestamp", "effective_timestamp", "recorded_timestamp", "ingestion_timestamp", "manufactured_timestamp"]:
            if raw.get(key) and len(str(raw.get(key))) == 10:
                issues.append(issue("DATE_WITHOUT_TIMEZONE", "INFO", key, raw.get(key), "Source provided date without timezone; raw value preserved"))
        return issues

    def run_summary(self, conn, run_id: str) -> dict[str, Any]:
        row = conn.execute(
            text(
                "SELECT id, source_system, source_type, source_file, status, total_records, accepted_records, warning_records, rejected_records, duplicate_source_records "
                "FROM ingestion_runs WHERE id=:run_id"
            ),
            {"run_id": run_id},
        ).mappings().one()
        quality_count = conn.execute(text("SELECT count(*) FROM data_quality_issues WHERE ingestion_run_id=:run_id"), {"run_id": run_id}).scalar_one()
        result = dict(row)
        result["id"] = str(result["id"])
        result["quality_issues"] = quality_count
        return result


def issue(code: str, severity: str, field: str | None, observed: Any, description: str) -> dict[str, Any]:
    return {
        "issue_code": code,
        "severity": severity,
        "field": field,
        "observed_value": None if observed is None else str(observed),
        "description": description,
    }


def safe_error(exc: Exception) -> str:
    text_value = str(exc)
    for marker in ["POSTGRES_PASSWORD", "://"]:
        text_value = text_value.replace(marker, "[redacted]")
    return text_value[:1000]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", default=str(GOLDEN_SOURCE))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = IngestionService(Path(args.source_root)).ingest_all()
    if args.json:
        print(json.dumps(result, indent=2, default=str, sort_keys=True))
    else:
        print("DAY 4 INGESTION = PASS")
        print(json.dumps({k: v for k, v in result.items() if k != "runs"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
