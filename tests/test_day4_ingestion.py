from pathlib import Path

import pytest
from sqlalchemy import text

from backend.app.db.session import engine
from ingestion.models.source import SourceFile
from ingestion.services.ingestion_service import GOLDEN_SOURCE, GROUND_TRUTH, IngestionService


def scalar(sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar_one()


def test_full_ingestion_preserves_source_layers():
    result = IngestionService(GOLDEN_SOURCE).ingest_all()
    assert result["files_discovered"] >= 52
    assert scalar("SELECT count(*) FROM staged_source_records") >= 337
    assert scalar("SELECT count(distinct source_system) FROM staged_source_records") == 4


def test_repeat_ingestion_is_idempotent():
    before = scalar("SELECT count(*) FROM staged_source_records")
    result = IngestionService(GOLDEN_SOURCE).ingest_all()
    after = scalar("SELECT count(*) FROM staged_source_records")
    assert after == before
    assert result["duplicate_source_records"] >= 1
    assert scalar("SELECT count(*) FROM ingestion_runs WHERE status='ALREADY_INGESTED'") >= 1


def test_qms_source_fidelity_and_missing_lot_warning():
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT raw_payload, candidate_canonical_payload FROM staged_source_records "
                "WHERE source_system='QMS' AND record_type='complaint' AND source_record_id='CMP-0001' LIMIT 1"
            )
        ).mappings().one()
        assert row["raw_payload"]["source_product_version"] == "Product-100 / Revision C"
        assert row["candidate_canonical_payload"]["candidate_product_version"] == "Product-100 / Revision C"
        assert "actual_root_cause" not in row["raw_payload"]
        assert conn.execute(text("SELECT count(*) FROM data_quality_issues WHERE issue_code='MISSING_LOT_REFERENCE'")).scalar_one() > 0


def test_temporal_fidelity_late_arriving_complaint_data():
    with engine.connect() as conn:
        row = conn.execute(
            text(
                "SELECT raw_payload, source_timestamp, recorded_timestamp, ingestion_timestamp "
                "FROM staged_source_records WHERE source_system='QMS' AND record_type='complaint' "
                "AND raw_payload->>'event_timestamp' < raw_payload->>'ingestion_timestamp' LIMIT 1"
            )
        ).mappings().one()
        assert row["raw_payload"]["event_timestamp"] <= row["raw_payload"]["recorded_timestamp"]
        assert row["source_timestamp"] != row["ingestion_timestamp"]


def test_vs001_observable_data_is_staged_without_conclusion():
    with engine.connect() as conn:
        assert conn.execute(text("SELECT count(*) FROM staged_source_records WHERE raw_payload::text LIKE '%Rev D%'")).scalar_one() > 0
        assert conn.execute(text("SELECT count(*) FROM staged_source_records WHERE raw_payload::text LIKE '%Component Rev B%' OR raw_payload::text LIKE '%Rev B%'")).scalar_one() > 0
        assert conn.execute(text("SELECT count(*) FROM staged_source_records WHERE raw_payload::text LIKE '%shutdown%'")).scalar_one() > 0
        assert conn.execute(text("SELECT count(*) FROM staged_source_records WHERE raw_payload::text LIKE '%Comparative Rev A versus Rev B testing unavailable%'")).scalar_one() > 0
        assert conn.execute(text("SELECT count(*) FROM staged_source_records WHERE raw_payload::text LIKE '%Component/supplier change is the leading hypothesis%'")).scalar_one() == 0


def test_ground_truth_path_is_rejected():
    gt_file = GROUND_TRUTH / "VS001" / "ground_truth.json"
    source = SourceFile(gt_file, "EVAL", "ground_truth", "ground_truth", "generic_source_v1.json")
    with pytest.raises(ValueError):
        IngestionService().ingest_source(IngestionService().ensure_tenant(), source, "test")


def test_schema_drift_failure_is_explicit(tmp_path):
    bad = tmp_path / "bad_complaints.csv"
    bad.write_text("complaint_id,narrative\nCMP-BAD,missing required fields\n", encoding="utf-8")
    source = SourceFile(bad, "QMS", "qms", "complaint", "qms_complaint_v1.json")
    result = IngestionService(tmp_path).ingest_source(IngestionService().ensure_tenant(), source, "test")
    assert result["status"] == "FAILED"
    assert scalar("SELECT count(*) FROM ingestion_runs WHERE status='FAILED'") >= 1


def test_day4_validator_passes():
    import subprocess
    import sys

    result = subprocess.run([sys.executable, "infrastructure/database/scripts/day4_validate_ingestion.py"], cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
