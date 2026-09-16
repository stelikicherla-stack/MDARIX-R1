import ast
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

from backend.app.db.session import engine

ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "ingestion" / "normalization" / "rules" / "identity_rules.json"
GROUND_TRUTH = ROOT / "evaluation" / "ground_truth"
NORMALIZATION_VERSION = "day5.normalization.v1"
RULE_SET_VERSION = "day5.rules.v1"
TENANT_KEY = "ACME_CARE_SYNTHETIC"


@dataclass
class LinkResult:
    canonical_entity_type: str
    canonical_entity_id: str | None
    canonical_business_identifier: str | None
    source_value: str | None
    normalized_value: str | None
    resolution_method: str
    resolution_rule: str
    resolution_status: str
    confidence_category: str
    evidence_context: dict[str, Any]
    provenance: dict[str, Any]


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text_value = unicodedata.normalize("NFKC", str(value)).strip()
    text_value = re.sub(r"\s+", " ", text_value)
    return text_value.casefold()


def normalize_product_identifier(value: Any) -> str | None:
    text_value = normalize_text(value)
    if not text_value:
        return None
    match = re.search(r"(?:prd|product)[-\s]*(?:aster[-\s]*)?(\d+)", text_value)
    if match:
        return f"PRD-{int(match.group(1)):03d}"
    if text_value in {"af-100", "prd-aster-100"}:
        return "PRD-100"
    if text_value in {"nv-200", "prd-nimbus-200"}:
        return "PRD-200"
    return text_value.upper()


def normalize_revision(value: Any) -> str | None:
    text_value = normalize_text(value)
    if not text_value:
        return None
    match = re.search(r"(?:revision|rev)\s*([a-z0-9]+)\b", text_value)
    if match:
        return match.group(1).upper()
    if len(text_value) <= 3:
        return text_value.upper().replace("REV", "")
    return text_value.upper()


def normalize_product_version_identifier(value: Any) -> str | None:
    text_value = normalize_text(value)
    if not text_value:
        return None
    product = normalize_product_identifier(text_value)
    revision = normalize_revision(text_value)
    if product and revision and product.startswith("PRD-"):
        return f"{product}:REV-{revision}"
    return text_value.upper()


def normalize_identifier(value: Any) -> str | None:
    text_value = normalize_text(value)
    if not text_value:
        return None
    return re.sub(r"\s+", "-", text_value.upper())


def normalize_status(value: Any) -> str | None:
    text_value = normalize_text(value)
    if not text_value:
        return None
    mapping = {
        "open": "open",
        "closed": "closed",
        "active": "active",
        "reviewed": "reviewed",
        "missing_lot": "missing_lot",
        "duplicate_candidate": "duplicate_candidate",
        "incomplete": "incomplete",
    }
    return mapping.get(text_value, text_value)


def parse_source_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text_value = str(value)
    parsed = datetime.fromisoformat(text_value)
    return parsed.replace(tzinfo=timezone.utc) if parsed.tzinfo is None else parsed


def parse_aliases(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    try:
        parsed = ast.literal_eval(str(value))
    except (SyntaxError, ValueError):
        return [str(value)]
    if isinstance(parsed, list):
        return [str(item) for item in parsed]
    return [str(parsed)]


def json_param(value: Any) -> str:
    return json.dumps(value, sort_keys=True, default=str)


class NormalizationService:
    def normalize_all(self) -> dict[str, Any]:
        tenant_id = self.tenant_id()
        now = utcnow()
        with engine.begin() as conn:
            self.ensure_rules(conn, now)
            run_id = conn.execute(
                text(
                    "INSERT INTO normalization_runs (tenant_id, normalization_version, rule_set_version, started_at, status, provenance) "
                    "VALUES (:tenant_id, :version, :rules, :now, 'RUNNING', :provenance) RETURNING id"
                ),
                {
                    "tenant_id": tenant_id,
                    "version": NORMALIZATION_VERSION,
                    "rules": RULE_SET_VERSION,
                    "now": now,
                    "provenance": json_param({"ground_truth_used": False, "source": "staged_source_records"}),
                },
            ).scalar_one()

            records = conn.execute(
                text(
                    "SELECT id, source_system, record_type, source_file, source_record_id, raw_payload, parsed_payload, candidate_canonical_payload, "
                    "source_timestamp, effective_timestamp, recorded_timestamp, ingestion_timestamp, data_quality_status, mapping_version "
                    "FROM staged_source_records WHERE tenant_id=:tenant_id ORDER BY CASE record_type "
                    "WHEN 'product' THEN 1 WHEN 'product_version' THEN 2 WHEN 'supplier' THEN 3 WHEN 'manufacturing_site' THEN 4 "
                    "WHEN 'component' THEN 5 WHEN 'lot' THEN 6 WHEN 'requirement' THEN 7 WHEN 'change' THEN 8 "
                    "WHEN 'risk' THEN 9 WHEN 'failure_mode' THEN 10 WHEN 'control' THEN 11 WHEN 'investigation' THEN 12 "
                    "WHEN 'complaint' THEN 13 WHEN 'evidence_metadata' THEN 14 WHEN 'evidence_file' THEN 15 ELSE 99 END, "
                    "source_system, source_file, source_row_index NULLS LAST, source_record_id"
                ),
                {"tenant_id": tenant_id},
            ).mappings().all()

            relationships_before = conn.execute(text("SELECT count(*) FROM canonical_relationships WHERE tenant_id=:tenant_id"), {"tenant_id": tenant_id}).scalar_one()
            link_count = 0
            ambiguous = unresolved = conflicts = warnings = errors = matched = 0
            created_before = self.canonical_count(conn, tenant_id)
            lookup: dict[str, dict[str, str]] = {name: {} for name in ["product", "product_version", "component", "supplier", "manufacturing_site", "lot_batch", "requirement", "change", "complaint", "investigation", "evidence"]}

            for record in records:
                results = self.normalize_record(conn, tenant_id, str(run_id), record, lookup)
                for result in results:
                    if result.resolution_status in {"MATCHED", "NEW_CANONICAL_OBJECT"}:
                        matched += 1
                    elif result.resolution_status == "AMBIGUOUS":
                        ambiguous += 1
                    elif result.resolution_status == "CONFLICT":
                        conflicts += 1
                    else:
                        unresolved += 1
                    if result.resolution_status == "REQUIRES_HUMAN_REVIEW":
                        warnings += 1
                    self.link(conn, tenant_id, str(run_id), str(record["id"]), result)
                    link_count += 1
                if record["data_quality_status"] == "ACCEPTED_WITH_WARNINGS":
                    warnings += 1

            relationship_count = self.resolve_relationships(conn, tenant_id, str(run_id), lookup)
            created_after = self.canonical_count(conn, tenant_id)
            status = "COMPLETED_WITH_WARNINGS" if warnings or unresolved or ambiguous or conflicts else "COMPLETED"
            conn.execute(
                text(
                    "UPDATE normalization_runs SET completed_at=:now, status=:status, records_processed=:processed, canonical_objects_created=:created, "
                    "records_matched=:matched, links_created=:links, relationships_resolved=:relationships, ambiguous_records=:ambiguous, "
                    "unresolved_records=:unresolved, conflicts=:conflicts, warnings=:warnings, errors=:errors WHERE id=:run_id"
                ),
                {
                    "now": utcnow(),
                    "status": status,
                    "processed": len(records),
                    "created": max(created_after - created_before, 0),
                    "matched": matched,
                    "links": link_count,
                    "relationships": max(relationship_count - relationships_before, 0),
                    "ambiguous": ambiguous,
                    "unresolved": unresolved,
                    "conflicts": conflicts,
                    "warnings": warnings,
                    "errors": errors,
                    "run_id": run_id,
                },
            )
            return self.summary(conn, str(run_id))

    def tenant_id(self) -> str:
        with engine.connect() as conn:
            tenant_id = conn.execute(text("SELECT id FROM tenants WHERE tenant_key=:key"), {"key": TENANT_KEY}).scalar_one_or_none()
        if not tenant_id:
            from ingestion.services.ingestion_service import IngestionService

            return IngestionService().ensure_tenant()
        return str(tenant_id)

    def ensure_rules(self, conn, now: datetime) -> None:
        rules = json.loads(RULES_PATH.read_text(encoding="utf-8"))
        for rule in rules:
            conn.execute(
                text(
                    "INSERT INTO identity_rules (rule_id, entity_type, version, precedence, purpose, match_conditions, ambiguity_behavior, created_at) "
                    "VALUES (:rule_id, :entity_type, :version, :precedence, :purpose, :match_conditions, :ambiguity_behavior, :now) "
                    "ON CONFLICT (rule_id, version) DO UPDATE SET purpose=EXCLUDED.purpose, match_conditions=EXCLUDED.match_conditions, ambiguity_behavior=EXCLUDED.ambiguity_behavior, active=true"
                ),
                {**rule, "match_conditions": json_param(rule["match_conditions"]), "now": now},
            )

    def normalize_record(self, conn, tenant_id: str, run_id: str, record, lookup: dict[str, dict[str, str]]) -> list[LinkResult]:
        raw = dict(record["raw_payload"])
        record_type = record["record_type"]
        handlers = {
            "product": self.product,
            "product_version": self.product_version,
            "component": self.component,
            "supplier": self.supplier,
            "manufacturing_site": self.site,
            "lot": self.lot,
            "requirement": self.requirement,
            "change": self.change,
            "complaint": self.complaint,
            "investigation": self.investigation,
            "evidence_metadata": self.evidence_metadata,
            "evidence_file": self.evidence_file,
            "risk": self.risk,
            "failure_mode": self.failure_mode,
            "control": self.control,
        }
        handler = handlers.get(record_type)
        if not handler:
            return [self.issue_link(record, record_type, "UNRESOLVED", "No Day 5 canonical handler for staged record type")]
        return handler(conn, tenant_id, record, raw, lookup)

    def product(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        business_id = raw["product_id"]
        canonical_display = "PRD-100" if business_id == "PRD-ASTER-100" else "PRD-200"
        product_id = conn.execute(
            text(
                "INSERT INTO products (tenant_id, product_identifier, name, description, lifecycle_status, product_family, source_system, source_identifier, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :name, :description, 'active', :family, :source_system, :source_identifier, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, product_identifier) DO UPDATE SET name=EXCLUDED.name, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": business_id, "name": raw["name"], "description": None, "family": raw.get("family_id"), "source_system": record["source_system"], "source_identifier": raw["product_id"], "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        lookup["product"][raw["product_id"]] = str(product_id)
        lookup["product"][canonical_display] = str(product_id)
        return [self.matched("product", product_id, business_id, raw["product_identifier"], normalize_product_identifier(raw["product_identifier"]), "PRODUCT_EXACT_ID_V1", record)]

    def product_version(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        product_id = lookup["product"].get(raw["product_id"]) or self.find_product(conn, tenant_id, raw["product_id"])
        if not product_id:
            return [self.issue_link(record, "product_version", "REQUIRES_HUMAN_REVIEW", "Product context missing for product version")]
        version = normalize_revision(raw["version_identifier"])
        product_version_id = conn.execute(
            text(
                "INSERT INTO product_versions (tenant_id, product_id, version_identifier, description, lifecycle_status, release_timestamp, source_system, source_identifier, effective_timestamp, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :product_id, :version, :description, 'active', :release_ts, :source_system, :source_identifier, :effective_ts, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, product_id, version_identifier) DO UPDATE SET description=EXCLUDED.description, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "product_id": product_id, "version": version, "description": raw.get("source_alias"), "release_ts": parse_source_datetime(raw.get("effective_timestamp")), "source_system": record["source_system"], "source_identifier": raw["product_version_id"], "effective_ts": parse_source_datetime(raw.get("effective_timestamp")), "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        lookup["product_version"][raw["product_version_id"]] = str(product_version_id)
        for value in [raw["version_identifier"], raw.get("source_alias"), raw["product_version_id"]]:
            if value:
                lookup["product_version"][normalize_product_version_identifier(value) or str(value)] = str(product_version_id)
        source_value = raw.get("source_alias") or raw["version_identifier"]
        return [self.matched("product_version", product_version_id, raw["product_version_id"], source_value, normalize_product_version_identifier(source_value), "PRODUCT_VERSION_COMPOSITE_V1", record)]

    def supplier(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        supplier_id = conn.execute(
            text(
                "INSERT INTO suppliers (tenant_id, supplier_identifier, name, status, source_system, source_identifier, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :name, 'active', :source_system, :source_identifier, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, supplier_identifier) DO UPDATE SET name=EXCLUDED.name, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": raw["supplier_id"], "name": raw["name"], "source_system": record["source_system"], "source_identifier": raw["supplier_id"], "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        for value in [raw["supplier_id"], raw["supplier_identifier"], raw["name"], *parse_aliases(raw.get("aliases"))]:
            lookup["supplier"][normalize_identifier(value) or str(value)] = str(supplier_id)
        return [self.matched("supplier", supplier_id, raw["supplier_id"], raw["name"], normalize_identifier(raw["name"]), "SUPPLIER_ALIAS_V1", record)]

    def component(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        supplier_id = lookup["supplier"].get(normalize_identifier(raw.get("supplier_id")))
        component_id = conn.execute(
            text(
                "INSERT INTO components (tenant_id, component_identifier, name, revision, description, status, source_system, source_identifier, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :name, :revision, :description, 'active', :source_system, :source_identifier, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, component_identifier, revision) DO UPDATE SET name=EXCLUDED.name, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": raw["component_id"], "name": raw["name"], "revision": normalize_revision(raw.get("revision")), "description": raw.get("description"), "source_system": record["source_system"], "source_identifier": raw["component_id"], "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        lookup["component"][raw["component_id"]] = str(component_id)
        lookup["component"][normalize_identifier(raw["component_identifier"]) or raw["component_identifier"]] = str(component_id)
        if supplier_id:
            self.upsert_relationship_table(conn, "component_suppliers", tenant_id, component_id=str(component_id), supplier_id=supplier_id)
        return [self.matched("component", component_id, raw["component_id"], raw["component_identifier"], f"{normalize_identifier(raw['component_identifier'])}:REV-{normalize_revision(raw.get('revision'))}", "COMPONENT_IDENTIFIER_REVISION_V1", record)]

    def site(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        site_id = conn.execute(
            text(
                "INSERT INTO manufacturing_sites (tenant_id, site_identifier, name, location, status, source_system, source_identifier, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :name, :location, 'active', :source_system, :source_identifier, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, site_identifier) DO UPDATE SET name=EXCLUDED.name, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": raw["site_id"], "name": raw.get("name") or raw.get("site_identifier"), "location": raw.get("location"), "source_system": record["source_system"], "source_identifier": raw["site_id"], "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        lookup["manufacturing_site"][raw["site_id"]] = str(site_id)
        lookup["manufacturing_site"][normalize_identifier(raw.get("site_identifier")) or raw["site_id"]] = str(site_id)
        return [self.matched("manufacturing_site", site_id, raw["site_id"], raw.get("site_identifier"), normalize_identifier(raw.get("site_identifier")), "SITE_IDENTIFIER_V1", record)]

    def lot(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        pv_id = lookup["product_version"].get(raw.get("product_version_id")) or self.find_product_version_source(conn, tenant_id, raw.get("product_version_id"))
        site_id = lookup["manufacturing_site"].get(raw.get("manufacturing_site_id")) or self.find_site_source(conn, tenant_id, raw.get("manufacturing_site_id"))
        lot_id = conn.execute(
            text(
                "INSERT INTO lot_batches (tenant_id, lot_identifier, product_version_id, manufacturing_site_id, status, source_system, source_identifier, effective_timestamp, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :product_version_id, :site_id, 'active', :source_system, :source_identifier, :effective_ts, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, lot_identifier) DO UPDATE SET product_version_id=EXCLUDED.product_version_id, manufacturing_site_id=EXCLUDED.manufacturing_site_id, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": raw["lot_id"], "product_version_id": pv_id, "site_id": site_id, "source_system": record["source_system"], "source_identifier": raw["lot_id"], "effective_ts": parse_source_datetime(raw.get("manufactured_timestamp")), "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        lookup["lot_batch"][raw["lot_id"]] = str(lot_id)
        lookup["lot_batch"][normalize_identifier(raw["lot_identifier"]) or raw["lot_identifier"]] = str(lot_id)
        return [self.matched("lot_batch", lot_id, raw["lot_id"], raw["lot_identifier"], f"{normalize_identifier(raw['lot_identifier'])}:{raw.get('product_version_id')}:{raw.get('manufacturing_site_id')}", "LOT_COMPOSITE_V1", record)]

    def requirement(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        product_id = lookup["product"].get(raw.get("product_id")) or self.find_product(conn, tenant_id, raw.get("product_id"))
        req_id = conn.execute(
            text(
                "INSERT INTO requirements (tenant_id, product_id, requirement_identifier, requirement_type, text, status, source_system, source_identifier, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :product_id, :identifier, :type, :text_value, 'active', :source_system, :source_identifier, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, requirement_identifier) DO UPDATE SET text=EXCLUDED.text, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "product_id": product_id, "identifier": raw["requirement_id"], "type": raw.get("requirement_type"), "text_value": raw["text"], "source_system": record["source_system"], "source_identifier": raw["requirement_id"], "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        return [self.matched("requirement", req_id, raw["requirement_id"], raw["requirement_identifier"], normalize_identifier(raw["requirement_identifier"]), "REQUIREMENT_IDENTIFIER_V1", record)]

    def change(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        change_id = conn.execute(
            text(
                "INSERT INTO changes (tenant_id, change_identifier, change_type, description, event_timestamp, effective_timestamp, source_system, source_identifier, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :type, :description, :event_ts, :effective_ts, :source_system, :source_identifier, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, change_identifier) DO UPDATE SET description=EXCLUDED.description, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": raw["change_id"], "type": raw["change_type"], "description": raw["description"], "event_ts": parse_source_datetime(raw.get("event_timestamp")), "effective_ts": parse_source_datetime(raw.get("effective_timestamp")), "source_system": record["source_system"], "source_identifier": raw["change_id"], "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        lookup["change"][raw["change_id"]] = str(change_id)
        return [self.matched("change", change_id, raw["change_id"], raw["change_identifier"], normalize_identifier(raw["change_identifier"]), "CHANGE_IDENTIFIER_V1", record)]

    def complaint(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        pv_id = lookup["product_version"].get(raw.get("product_version_id")) or lookup["product_version"].get(normalize_product_version_identifier(raw.get("source_product_version")))
        product_id = self.product_for_version(conn, tenant_id, pv_id)
        lot_id = lookup["lot_batch"].get(raw.get("lot_id")) if raw.get("lot_id") else None
        complaint_id = conn.execute(
            text(
                "INSERT INTO complaints (tenant_id, complaint_identifier, product_id, product_version_id, lot_batch_id, event_timestamp, complaint_timestamp, description, status, source_system, source_identifier, source_timestamp, recorded_timestamp, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :product_id, :pv_id, :lot_id, :event_ts, :complaint_ts, :description, :status, :source_system, :source_identifier, :source_ts, :recorded_ts, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, complaint_identifier) DO UPDATE SET product_version_id=EXCLUDED.product_version_id, lot_batch_id=EXCLUDED.lot_batch_id, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": raw["complaint_id"], "product_id": product_id, "pv_id": pv_id, "lot_id": lot_id, "event_ts": parse_source_datetime(raw.get("event_timestamp")), "complaint_ts": parse_source_datetime(raw.get("event_timestamp")), "description": raw["narrative"], "status": normalize_status(raw.get("data_quality_status")) or "open", "source_system": record["source_system"], "source_identifier": raw["complaint_id"], "source_ts": parse_source_datetime(raw.get("event_timestamp")), "recorded_ts": parse_source_datetime(raw.get("recorded_timestamp")), "ingestion_ts": parse_source_datetime(raw.get("ingestion_timestamp")), "now": utcnow()},
        ).scalar_one()
        status = "REQUIRES_HUMAN_REVIEW" if str(raw.get("duplicate_candidate", "")).lower() == "true" else "MATCHED"
        confidence = "AMBIGUOUS" if status == "REQUIRES_HUMAN_REVIEW" else "DETERMINISTIC"
        return [LinkResult("complaint", str(complaint_id), raw["complaint_id"], raw["complaint_identifier"], normalize_identifier(raw["complaint_identifier"]), "deterministic", "COMPLAINT_SOURCE_ID_V1", status, confidence, {"similar_narrative_not_merged": True}, self.provenance(record))]

    def investigation(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        product_id = lookup["product"].get(raw.get("product_id")) or self.find_product(conn, tenant_id, raw.get("product_id"))
        inv_id = conn.execute(
            text(
                "INSERT INTO investigations (tenant_id, investigation_identifier, product_id, investigation_question, status, opened_at, source_system, source_identifier, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :product_id, :question, :status, :opened_at, :source_system, :source_identifier, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, investigation_identifier) DO UPDATE SET investigation_question=EXCLUDED.investigation_question, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": raw["investigation_id"], "product_id": product_id, "question": raw["question"], "status": normalize_status(raw.get("status")) or "open", "opened_at": parse_source_datetime(raw.get("opened_at")), "source_system": record["source_system"], "source_identifier": raw["investigation_id"], "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        lookup["investigation"][raw["investigation_id"]] = str(inv_id)
        return [self.matched("investigation", inv_id, raw["investigation_id"], raw["investigation_identifier"], normalize_identifier(raw["investigation_identifier"]), "INVESTIGATION_SOURCE_ID_V1", record)]

    def risk(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        product_id = lookup["product"].get(raw.get("product_id")) or self.find_product(conn, tenant_id, raw.get("product_id"))
        risk_id = conn.execute(
            text(
                "INSERT INTO risks (tenant_id, product_id, risk_identifier, description, status, source_system, source_identifier, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :product_id, :identifier, :description, 'active', :source_system, :source_identifier, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, risk_identifier) DO UPDATE SET description=EXCLUDED.description, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "product_id": product_id, "identifier": raw["risk_id"], "description": raw["description"], "source_system": record["source_system"], "source_identifier": raw["risk_id"], "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        lookup.setdefault("risk", {})[raw["risk_id"]] = str(risk_id)
        return [self.matched("risk", risk_id, raw["risk_id"], raw["risk_identifier"], normalize_identifier(raw["risk_identifier"]), "RISK_IDENTIFIER_V1", record)]

    def failure_mode(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        failure_mode_id = conn.execute(
            text(
                "INSERT INTO failure_modes (tenant_id, failure_mode_identifier, name, description, source_system, source_identifier, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :name, :description, :source_system, :source_identifier, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, failure_mode_identifier) DO UPDATE SET name=EXCLUDED.name, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": raw["failure_mode_id"], "name": raw["name"], "description": None, "source_system": record["source_system"], "source_identifier": raw["failure_mode_id"], "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        lookup.setdefault("failure_mode", {})[raw["failure_mode_id"]] = str(failure_mode_id)
        return [self.matched("failure_mode", failure_mode_id, raw["failure_mode_id"], raw["failure_mode_identifier"], normalize_identifier(raw["failure_mode_identifier"]), "FAILURE_MODE_IDENTIFIER_V1", record)]

    def control(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        control_id = conn.execute(
            text(
                "INSERT INTO controls (tenant_id, control_identifier, control_type, description, status, source_system, source_identifier, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :control_type, :description, 'active', :source_system, :source_identifier, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, control_identifier) DO UPDATE SET description=EXCLUDED.description, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": raw["control_id"], "control_type": raw.get("control_type"), "description": raw["description"], "source_system": record["source_system"], "source_identifier": raw["control_id"], "ingestion_ts": record["ingestion_timestamp"], "now": utcnow()},
        ).scalar_one()
        lookup.setdefault("control", {})[raw["control_id"]] = str(control_id)
        return [self.matched("control", control_id, raw["control_id"], raw["control_identifier"], normalize_identifier(raw["control_identifier"]), "CONTROL_IDENTIFIER_V1", record)]

    def evidence_metadata(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        investigation_id = lookup["investigation"].get(raw.get("investigation_id")) or self.find_investigation(conn, tenant_id, raw.get("investigation_id"))
        evidence_id = conn.execute(
            text(
                "INSERT INTO evidence (tenant_id, evidence_identifier, investigation_id, evidence_type, title, source_reference, document_ref, reliability_status, fact_type, content, source_system, source_identifier, source_timestamp, recorded_timestamp, ingestion_timestamp, created_at, updated_at) "
                "VALUES (:tenant_id, :identifier, :investigation_id, :type, :title, :source_ref, :document_ref, :quality, 'source_fact', :content, :source_system, :source_identifier, :source_ts, :recorded_ts, :ingestion_ts, :now, :now) "
                "ON CONFLICT (tenant_id, evidence_identifier) DO UPDATE SET content=EXCLUDED.content, updated_at=EXCLUDED.updated_at RETURNING id"
            ),
            {"tenant_id": tenant_id, "identifier": raw["evidence_id"], "investigation_id": investigation_id, "type": raw["evidence_type"], "title": raw["title"], "source_ref": raw.get("source"), "document_ref": raw.get("document_path"), "quality": raw.get("quality") or "unreviewed", "content": raw.get("content"), "source_system": record["source_system"], "source_identifier": raw["evidence_id"], "source_ts": parse_source_datetime(raw.get("event_timestamp")), "recorded_ts": parse_source_datetime(raw.get("recorded_timestamp")), "ingestion_ts": parse_source_datetime(raw.get("ingestion_timestamp")), "now": utcnow()},
        ).scalar_one()
        lookup["evidence"][raw["evidence_id"]] = str(evidence_id)
        return [self.matched("evidence", evidence_id, raw["evidence_id"], raw["evidence_id"], normalize_identifier(raw["evidence_id"]), "EVIDENCE_IDENTIFIER_V1", record)]

    def evidence_file(self, conn, tenant_id: str, record, raw: dict[str, Any], lookup) -> list[LinkResult]:
        identifier = Path(raw.get("filename") or raw.get("relative_path")).stem
        evidence_id = lookup["evidence"].get(identifier) or self.find_evidence(conn, tenant_id, identifier)
        status = "MATCHED" if evidence_id else "UNRESOLVED"
        return [LinkResult("evidence", evidence_id, identifier, raw.get("filename"), normalize_identifier(identifier), "deterministic", "EVIDENCE_IDENTIFIER_V1", status, "DETERMINISTIC" if evidence_id else "UNRESOLVED", {"file_checksum_preserved": True}, self.provenance(record))]

    def matched(self, entity_type: str, entity_id: Any, business_id: str, source_value: Any, normalized: Any, rule: str, record) -> LinkResult:
        return LinkResult(entity_type, str(entity_id), business_id, None if source_value is None else str(source_value), None if normalized is None else str(normalized), "deterministic", rule, "MATCHED", "DETERMINISTIC", {"rule_precedence": rule}, self.provenance(record))

    def issue_link(self, record, entity_type: str, status: str, description: str) -> LinkResult:
        return LinkResult(entity_type, None, None, record["source_record_id"], normalize_identifier(record["source_record_id"]), "deterministic", "UNRESOLVED_IDENTITY_V1", status, "UNRESOLVED", {"description": description}, self.provenance(record))

    def link(self, conn, tenant_id: str, run_id: str, staged_id: str, result: LinkResult) -> None:
        conn.execute(
            text(
                "INSERT INTO source_canonical_links (tenant_id, normalization_run_id, staged_source_record_id, canonical_entity_type, canonical_entity_id, canonical_business_identifier, source_value, normalized_value, resolution_method, resolution_rule, resolution_status, confidence_category, human_review_status, evidence_context, provenance, resolved_at, updated_at) "
                "VALUES (:tenant_id, :run_id, :staged_id, :entity_type, :entity_id, :business_id, :source_value, :normalized_value, :method, :rule, :status, :confidence, :review, :context, :provenance, :now, :now) "
                "ON CONFLICT (tenant_id, staged_source_record_id, canonical_entity_type, resolution_rule) DO UPDATE SET "
                "normalization_run_id=EXCLUDED.normalization_run_id, canonical_entity_id=EXCLUDED.canonical_entity_id, "
                "canonical_business_identifier=EXCLUDED.canonical_business_identifier, source_value=EXCLUDED.source_value, "
                "normalized_value=EXCLUDED.normalized_value, resolution_status=EXCLUDED.resolution_status, "
                "confidence_category=EXCLUDED.confidence_category, human_review_status=EXCLUDED.human_review_status, "
                "evidence_context=EXCLUDED.evidence_context, provenance=EXCLUDED.provenance, updated_at=EXCLUDED.updated_at"
            ),
            {
                "tenant_id": tenant_id,
                "run_id": run_id,
                "staged_id": staged_id,
                "entity_type": result.canonical_entity_type,
                "entity_id": result.canonical_entity_id,
                "business_id": result.canonical_business_identifier,
                "source_value": result.source_value,
                "normalized_value": result.normalized_value,
                "method": result.resolution_method,
                "rule": result.resolution_rule,
                "status": result.resolution_status,
                "confidence": result.confidence_category,
                "review": "required" if result.resolution_status == "REQUIRES_HUMAN_REVIEW" else "not_required",
                "context": json_param(result.evidence_context),
                "provenance": json_param(result.provenance),
                "now": utcnow(),
            },
        )

    def resolve_relationships(self, conn, tenant_id: str, run_id: str, lookup: dict[str, dict[str, str]]) -> int:
        for lot_source, lot_id in lookup["lot_batch"].items():
            if not lot_source.startswith("LOT-"):
                continue
            row = conn.execute(text("SELECT product_version_id FROM lot_batches WHERE id=:id"), {"id": lot_id}).mappings().one_or_none()
            if row and row["product_version_id"]:
                self.canonical_relationship(conn, tenant_id, run_id, "lot_batch", lot_id, "product_version", str(row["product_version_id"]), "LOT_BUILT_AS_PRODUCT_VERSION", "LOT_COMPOSITE_V1")
        for component_id in lookup["component"].values():
            for supplier_id in set(lookup["supplier"].values()):
                exists = conn.execute(text("SELECT count(*) FROM component_suppliers WHERE tenant_id=:tenant_id AND component_id=:c AND supplier_id=:s"), {"tenant_id": tenant_id, "c": component_id, "s": supplier_id}).scalar_one()
                if exists:
                    self.canonical_relationship(conn, tenant_id, run_id, "component", component_id, "supplier", supplier_id, "COMPONENT_SUPPLIED_BY", "COMPONENT_IDENTIFIER_REVISION_V1")
        return conn.execute(text("SELECT count(*) FROM canonical_relationships WHERE tenant_id=:tenant_id"), {"tenant_id": tenant_id}).scalar_one()

    def canonical_relationship(self, conn, tenant_id: str, run_id: str, source_type: str, source_id: str, target_type: str, target_id: str, rel_type: str, rule: str) -> None:
        conn.execute(
            text(
                "INSERT INTO canonical_relationships (tenant_id, normalization_run_id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type, resolution_rule, assertion_status, provenance, created_at) "
                "VALUES (:tenant_id, :run_id, :source_type, :source_id, :target_type, :target_id, :rel_type, :rule, 'supported', :provenance, :now) "
                "ON CONFLICT (tenant_id, source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type) DO NOTHING"
            ),
            {"tenant_id": tenant_id, "run_id": run_id, "source_type": source_type, "source_id": source_id, "target_type": target_type, "target_id": target_id, "rel_type": rel_type, "rule": rule, "provenance": json_param({"causal_claim": False}), "now": utcnow()},
        )

    def upsert_relationship_table(self, conn, table: str, tenant_id: str, **ids: str) -> None:
        if table == "component_suppliers":
            conn.execute(
                text(
                    "INSERT INTO component_suppliers (tenant_id, component_id, supplier_id, created_at) VALUES (:tenant_id, :component_id, :supplier_id, :now) "
                    "ON CONFLICT (tenant_id, component_id, supplier_id) DO NOTHING"
                ),
                {"tenant_id": tenant_id, "now": utcnow(), **ids},
            )

    def provenance(self, record) -> dict[str, Any]:
        return {
            "staged_source_record_id": str(record["id"]),
            "source_system": record["source_system"],
            "record_type": record["record_type"],
            "source_file": record["source_file"],
            "mapping_version": record["mapping_version"],
            "source_preserved": True,
            "ground_truth_used": False,
        }

    def canonical_count(self, conn, tenant_id: str) -> int:
        total = 0
        for table in ["products", "product_versions", "components", "suppliers", "manufacturing_sites", "lot_batches", "requirements", "changes", "risks", "failure_modes", "controls", "complaints", "investigations", "evidence"]:
            total += conn.execute(text(f"SELECT count(*) FROM {table} WHERE tenant_id=:tenant_id"), {"tenant_id": tenant_id}).scalar_one()
        return total

    def find_product(self, conn, tenant_id: str, source_id: str | None) -> str | None:
        if not source_id:
            return None
        return conn.execute(text("SELECT id FROM products WHERE tenant_id=:tenant_id AND product_identifier=:id"), {"tenant_id": tenant_id, "id": source_id}).scalar_one_or_none()

    def find_product_version_source(self, conn, tenant_id: str, source_id: str | None) -> str | None:
        if not source_id:
            return None
        return conn.execute(text("SELECT id FROM product_versions WHERE tenant_id=:tenant_id AND source_identifier=:id"), {"tenant_id": tenant_id, "id": source_id}).scalar_one_or_none()

    def find_site_source(self, conn, tenant_id: str, source_id: str | None) -> str | None:
        if not source_id:
            return None
        return conn.execute(text("SELECT id FROM manufacturing_sites WHERE tenant_id=:tenant_id AND source_identifier=:id"), {"tenant_id": tenant_id, "id": source_id}).scalar_one_or_none()

    def product_for_version(self, conn, tenant_id: str, product_version_id: str | None) -> str | None:
        if not product_version_id:
            return None
        return conn.execute(text("SELECT product_id FROM product_versions WHERE tenant_id=:tenant_id AND id=:id"), {"tenant_id": tenant_id, "id": product_version_id}).scalar_one_or_none()

    def find_investigation(self, conn, tenant_id: str, source_id: str | None) -> str | None:
        return conn.execute(text("SELECT id FROM investigations WHERE tenant_id=:tenant_id AND investigation_identifier=:id"), {"tenant_id": tenant_id, "id": source_id}).scalar_one_or_none() if source_id else None

    def find_evidence(self, conn, tenant_id: str, source_id: str | None) -> str | None:
        return conn.execute(text("SELECT id FROM evidence WHERE tenant_id=:tenant_id AND evidence_identifier=:id"), {"tenant_id": tenant_id, "id": source_id}).scalar_one_or_none() if source_id else None

    def summary(self, conn, run_id: str) -> dict[str, Any]:
        row = conn.execute(text("SELECT * FROM normalization_runs WHERE id=:run_id"), {"run_id": run_id}).mappings().one()
        result = dict(row)
        result["id"] = str(result["id"])
        result["tenant_id"] = str(result["tenant_id"])
        return result
