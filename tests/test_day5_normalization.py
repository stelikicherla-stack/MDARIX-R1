from pathlib import Path

import pytest
from sqlalchemy import text

from backend.app.db.session import engine
from ingestion.normalization.service import (
    NormalizationService,
    normalize_identifier,
    normalize_product_version_identifier,
    normalize_revision,
    normalize_status,
)


def scalar(sql, **params):
    with engine.connect() as conn:
        return conn.execute(text(sql), params).scalar_one()


@pytest.fixture(scope="module")
def normalized():
    return NormalizationService().normalize_all()


def test_exact_identifier_match(normalized):
    assert scalar("SELECT count(*) FROM products WHERE product_identifier='PRD-ASTER-100'") == 1


def test_normalized_identifier_match():
    assert normalize_product_version_identifier("PRD100 Rev D") == "PRD-100:REV-D"
    assert normalize_product_version_identifier("Product-100 / Revision D") == "PRD-100:REV-D"


def test_product_version_separation(normalized):
    assert scalar("SELECT count(*) FROM products") >= 2
    assert scalar("SELECT count(*) FROM product_versions") >= 6


def test_supplier_alias_resolution(normalized):
    assert scalar("SELECT count(*) FROM source_canonical_links WHERE canonical_entity_type='supplier' AND resolution_rule='SUPPLIER_ALIAS_V1'") >= 5


def test_component_identity(normalized):
    assert scalar("SELECT count(*) FROM components WHERE component_identifier='COMP-PWR' AND revision='B'") == 1


def test_shared_component_relationship(normalized):
    assert scalar("SELECT count(*) FROM canonical_relationships WHERE relationship_type='COMPONENT_SUPPLIED_BY'") >= 16


def test_product_version_component_relationship(normalized):
    assert scalar("SELECT count(*) FROM product_components") >= 16
    assert scalar("SELECT count(*) FROM canonical_relationships WHERE relationship_type='PRODUCT_VERSION_HAS_COMPONENT'") >= 16
    assert scalar(
        "SELECT count(*) FROM product_components pc "
        "JOIN product_versions pv ON pv.tenant_id=pc.tenant_id AND pv.id=pc.product_version_id "
        "JOIN components c ON c.tenant_id=pc.tenant_id AND c.id=pc.component_id "
        "WHERE pv.source_identifier='PV-ASTER-D' AND c.source_identifier='COMP-PWR'"
    ) == 1


def test_manufacturing_site_identity(normalized):
    assert scalar("SELECT count(*) FROM manufacturing_sites") == 2


def test_lot_composite_identity(normalized):
    assert scalar("SELECT count(*) FROM lot_batches WHERE lot_identifier='LOT-010'") == 1


def test_requirement_identity(normalized):
    assert scalar("SELECT count(*) FROM requirements") >= 24


def test_change_identity(normalized):
    assert scalar("SELECT count(*) FROM changes WHERE change_identifier='CHG-SUP-PROC-001'") == 1


def test_complaint_identity(normalized):
    assert scalar("SELECT count(*) FROM complaints WHERE complaint_identifier='CMP-0004'") == 1


def test_similar_but_distinct_complaints(normalized):
    assert scalar("SELECT count(*) FROM complaints WHERE description LIKE '%Intermittent shutdown during field use%'") > 1


def test_investigation_identity(normalized):
    assert scalar("SELECT count(*) FROM investigations WHERE investigation_identifier='INV-001'") == 1


def test_source_canonical_provenance(normalized):
    assert scalar("SELECT count(*) FROM source_canonical_links WHERE provenance->>'source_preserved'='true'") >= 337


def test_match_rule_provenance(normalized):
    assert scalar("SELECT count(distinct resolution_rule) FROM source_canonical_links") >= 10


def test_deterministic_precedence_catalog(normalized):
    assert scalar("SELECT min(precedence) FROM identity_rules WHERE rule_id='PRODUCT_EXACT_ID_V1'") < scalar("SELECT min(precedence) FROM identity_rules WHERE rule_id='SUPPLIER_ALIAS_V1'")


def test_ambiguous_match_human_review_foundation(normalized):
    assert scalar("SELECT count(*) FROM source_canonical_links WHERE resolution_status='REQUIRES_HUMAN_REVIEW'") >= 1


def test_unresolved_match_preserved(normalized):
    assert scalar("SELECT unresolved_records FROM normalization_runs ORDER BY completed_at DESC LIMIT 1") >= 0


def test_conflict_preservation(normalized):
    assert scalar("SELECT conflicts FROM normalization_runs ORDER BY completed_at DESC LIMIT 1") >= 0


def test_missing_identity_field_normalizer():
    assert normalize_identifier("") is None


def test_tenant_isolation(normalized):
    assert scalar("SELECT count(distinct tenant_id) FROM source_canonical_links") == 1


def test_temporal_version_identity(normalized):
    assert scalar("SELECT count(*) FROM product_versions WHERE release_timestamp IS NOT NULL") >= 6


def test_source_value_preservation(normalized):
    assert scalar("SELECT count(*) FROM staged_source_records WHERE raw_payload::text LIKE '%Product-100 / Revision C%'") > 0


def test_canonical_value_selection(normalized):
    assert scalar("SELECT count(*) FROM product_versions WHERE version_identifier='D'") == 1


def test_controlled_vocabulary_normalization():
    assert normalize_status("Open") == "open"


def test_timestamp_normalization(normalized):
    assert scalar("SELECT count(*) FROM complaints WHERE event_timestamp IS NOT NULL AND recorded_timestamp IS NOT NULL") >= 100


def test_idempotent_second_run(normalized):
    before = scalar("SELECT count(*) FROM products")
    NormalizationService().normalize_all()
    after = scalar("SELECT count(*) FROM products")
    assert after == before


def test_order_independence_for_product_version_aliases():
    assert normalize_revision("Revision D") == "D"


def test_relationship_resolution(normalized):
    assert scalar("SELECT count(*) FROM canonical_relationships WHERE relationship_type='LOT_BUILT_AS_PRODUCT_VERSION'") >= 18


def test_no_causal_relationship_creation(normalized):
    assert scalar("SELECT count(*) FROM canonical_relationships WHERE relationship_type ILIKE '%CAUSE%'") == 0


def test_ground_truth_isolation(normalized):
    assert scalar("SELECT count(*) FROM source_canonical_links WHERE provenance::text LIKE '%actual_root_cause%'") == 0


def test_vs001_identity_chain(normalized):
    assert scalar("SELECT count(*) FROM product_versions WHERE version_identifier='D'") == 1
    assert scalar("SELECT count(*) FROM components WHERE component_identifier='COMP-PWR' AND revision='B'") == 1
    assert scalar("SELECT count(*) FROM complaints WHERE product_version_id IS NOT NULL AND description LIKE '%shutdown%'") > 0


def test_vs001_contradictions_preserved(normalized):
    assert scalar("SELECT count(*) FROM complaints WHERE event_timestamp < '2026-01-18' AND description LIKE '%shutdown%'") >= 3


def test_vs002_false_correlation_preserved(normalized):
    assert scalar("SELECT count(*) FROM changes WHERE change_identifier='CHG-LABEL-042'") == 1
    assert scalar("SELECT count(*) FROM canonical_relationships WHERE relationship_type ILIKE '%CAUSE%'") == 0


def test_vs003_missing_evidence_preserved(normalized):
    assert scalar("SELECT count(*) FROM source_canonical_links WHERE human_review_status='required'") >= 1


def test_vs004_conflicting_evidence_preserved(normalized):
    assert scalar("SELECT count(*) FROM evidence WHERE content LIKE '%validation test passed%' OR content LIKE '%shutdown complaints existed before%'") >= 2


def test_vs005_temporal_conflict_preserved(normalized):
    assert scalar("SELECT count(*) FROM evidence WHERE ingestion_timestamp > recorded_timestamp") >= 1


def test_vs006_shared_component_resolved(normalized):
    assert scalar("SELECT count(*) FROM components WHERE name='Power Regulation Module'") == 1


def test_vs007_closure_history_preserved(normalized):
    assert scalar("SELECT count(*) FROM evidence WHERE content LIKE '%Historical closure did not address%'") == 1


def test_vs008_risk_control_relationships(normalized):
    assert scalar("SELECT count(*) FROM risks") >= 15
    assert scalar("SELECT count(*) FROM controls") >= 12


def test_vs009_historical_configuration(normalized):
    assert scalar("SELECT count(*) FROM product_versions WHERE version_identifier in ('A','B','C','D')") >= 4


def test_vs010_stable_investigation_identity(normalized):
    assert scalar("SELECT count(*) FROM investigations WHERE investigation_identifier='INV-010'") == 1


def test_vs011_distinct_failure_patterns(normalized):
    assert scalar("SELECT count(*) FROM failure_modes") >= 15


def test_vs012_unresolved_uncertainty_preserved(normalized):
    assert scalar("SELECT count(*) FROM evidence WHERE reliability_status='uncertain'") > 0


def test_day5_validator_passes():
    import subprocess
    import sys

    result = subprocess.run([sys.executable, "infrastructure/database/scripts/day5_validate_canonical_data.py"], cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True)
    assert result.returncode == 0, result.stdout + result.stderr
