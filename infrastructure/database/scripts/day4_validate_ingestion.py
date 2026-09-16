import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from sqlalchemy import inspect, text

from backend.app.db.session import engine


REQUIRED_TABLES = {"ingestion_runs", "staged_source_records", "data_quality_issues", "source_mappings"}
REQUIRED_SOURCES = {"QMS", "PLM", "ERP_MES", "EVIDENCE"}


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    with engine.connect() as conn:
        tables = set(inspect(conn).get_table_names())
        check(REQUIRED_TABLES <= tables, f"Missing ingestion tables: {REQUIRED_TABLES - tables}")

        completed_files = conn.execute(
            text("SELECT count(distinct source_file) FROM ingestion_runs WHERE status in ('COMPLETED','COMPLETED_WITH_WARNINGS')")
        ).scalar_one()
        staged_records = conn.execute(text("SELECT count(*) FROM staged_source_records")).scalar_one()
        issues = conn.execute(text("SELECT count(*) FROM data_quality_issues")).scalar_one()
        mappings = conn.execute(text("SELECT count(*) FROM source_mappings")).scalar_one()
        sources = set(conn.execute(text("SELECT distinct source_system FROM staged_source_records")).scalars())
        checksum_missing = conn.execute(text("SELECT count(*) FROM ingestion_runs WHERE source_checksum IS NULL OR length(source_checksum) <> 64")).scalar_one()
        raw_missing = conn.execute(text("SELECT count(*) FROM staged_source_records WHERE raw_payload IS NULL OR parsed_payload IS NULL OR candidate_canonical_payload IS NULL")).scalar_one()
        gt_leaks = conn.execute(text("SELECT count(*) FROM staged_source_records WHERE source_file LIKE '%evaluation/ground_truth%'")).scalar_one()
        duplicate_staged = conn.execute(
            text(
                "SELECT count(*) FROM ("
                "SELECT tenant_id, source_system, source_file, source_record_id, source_checksum, count(*) c "
                "FROM staged_source_records GROUP BY tenant_id, source_system, source_file, source_record_id, source_checksum HAVING count(*) > 1"
                ") q"
            )
        ).scalar_one()
        already = conn.execute(text("SELECT count(*) FROM ingestion_runs WHERE status='ALREADY_INGESTED'")).scalar_one()

        check(completed_files >= 52, "Expected full Golden source ingestion")
        check(staged_records >= 337, "Expected staged Golden source records")
        check(issues > 0, "Expected controlled data quality issues")
        check(mappings >= 10, "Expected source mappings")
        check(REQUIRED_SOURCES <= sources, f"Missing source systems: {REQUIRED_SOURCES - sources}")
        check(checksum_missing == 0, "Missing source checksums")
        check(raw_missing == 0, "Missing raw/parsed/candidate payloads")
        check(gt_leaks == 0, "Ground Truth leaked into ingestion")
        check(duplicate_staged == 0, "Duplicate staged source records detected")

        print("DAY 4 INGESTION VALIDATION = PASS")
        print(f"files_ingested={completed_files}")
        print(f"staged_records={staged_records}")
        print(f"quality_issues={issues}")
        print(f"idempotent_runs={already}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"DAY 4 INGESTION VALIDATION = FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
