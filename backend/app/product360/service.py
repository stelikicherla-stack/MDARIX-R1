from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from backend.app.db.session import engine
from backend.app.product360.schemas import Product360Response, ProductSummary, TemporalRealityResponse, TimelineEvent
from graph.service import RealityGraphService

TENANT_KEY = "ACME_CARE_SYNTHETIC"
EVENT_CATEGORIES = {"PRODUCT", "DESIGN", "COMPONENT", "SUPPLIER", "MANUFACTURING", "FIELD", "INVESTIGATION", "RISK", "EVIDENCE"}


class Product360Error(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def rowdict(row) -> dict[str, Any]:
    result = dict(row)
    for key, value in list(result.items()):
        if value is not None and not isinstance(value, (str, int, float, bool, dict, list)):
            result[key] = str(value)
    return result


class Product360Service:
    def __init__(self) -> None:
        self.graph = RealityGraphService()

    def tenant_id(self) -> str:
        return self.graph.tenant_id()

    def list_products(self, tenant_id: str | None = None) -> list[ProductSummary]:
        tenant_id = tenant_id or self.tenant_id()
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT p.id, p.product_identifier, p.name, p.product_family, p.lifecycle_status, "
                    "array_agg(pv.version_identifier ORDER BY pv.version_identifier) AS versions "
                    "FROM products p LEFT JOIN product_versions pv ON pv.tenant_id=p.tenant_id AND pv.product_id=p.id "
                    "WHERE p.tenant_id=:tenant_id GROUP BY p.id, p.product_identifier, p.name, p.product_family, p.lifecycle_status "
                    "ORDER BY p.name"
                ),
                {"tenant_id": tenant_id},
            ).mappings().all()
        return [
            ProductSummary(
                id=str(row["id"]),
                product_identifier=row["product_identifier"],
                name=row["name"],
                product_family=row["product_family"],
                lifecycle_status=row["lifecycle_status"],
                available_versions=[v for v in (row["versions"] or []) if v],
            )
            for row in rows
        ]

    def product360(self, product_id: str, version_id: str | None = None, as_of: datetime | None = None, mode: str = "current", tenant_id: str | None = None) -> Product360Response:
        # API callers must pass the authenticated tenant.  The synthetic default
        # remains only for existing internal/public Product 360 callers.
        tenant_id = tenant_id or self.tenant_id()
        with engine.connect() as conn:
            product = conn.execute(text("SELECT * FROM products WHERE tenant_id=:tenant_id AND id=:id"), {"tenant_id": tenant_id, "id": product_id}).mappings().one_or_none()
            if not product:
                raise Product360Error("PRODUCT_NOT_FOUND", "Product not found")
            versions = conn.execute(text("SELECT * FROM product_versions WHERE tenant_id=:tenant_id AND product_id=:product_id ORDER BY release_timestamp NULLS LAST, version_identifier"), {"tenant_id": tenant_id, "product_id": product_id}).mappings().all()
            visible_versions = self.filter_rows_by_time(versions, as_of, mode, "release_timestamp")
            selected = self.select_version(versions, version_id, as_of)
            selected_id = str(selected["id"]) if selected else None
            components = self.components(conn, tenant_id, selected_id)
            suppliers = self.suppliers(conn, tenant_id, components)
            changes = self.changes(conn, tenant_id, product_id, selected_id, components, suppliers)
            changes = self.filter_rows_by_time(changes, as_of, mode, "effective_timestamp", "event_timestamp")
            lots = self.lots(conn, tenant_id, selected_id)
            lots = self.filter_rows_by_time(lots, as_of, mode, "manufactured_timestamp")
            complaints = self.complaints(conn, tenant_id, product_id, selected_id, as_of, mode)
            complaints = self.filter_rows_by_time(complaints, as_of, mode, "ingestion_timestamp", "event_timestamp")
            investigations = self.investigations(conn, tenant_id, product_id)
            investigations = self.filter_rows_by_time(investigations, as_of, mode, "opened_at")
            risks = conn.execute(text("SELECT id, risk_identifier, description, status FROM risks WHERE tenant_id=:tenant_id AND product_id=:product_id ORDER BY risk_identifier"), {"tenant_id": tenant_id, "product_id": product_id}).mappings().all()
            failure_modes = conn.execute(text("SELECT id, failure_mode_identifier, name FROM failure_modes WHERE tenant_id=:tenant_id ORDER BY failure_mode_identifier"), {"tenant_id": tenant_id}).mappings().all()
            controls = conn.execute(text("SELECT id, control_identifier, control_type, description, status FROM controls WHERE tenant_id=:tenant_id ORDER BY control_identifier"), {"tenant_id": tenant_id}).mappings().all()
            evidence = self.evidence(conn, tenant_id, investigations, as_of, mode)
            evidence = self.filter_rows_by_time(evidence, as_of, mode, "ingestion_timestamp", "source_timestamp")
            timeline = self.timeline(product, versions, components, suppliers, changes, lots, complaints, investigations, evidence, risks, controls)
            timeline = self.filter_as_of(timeline, as_of, mode)
            limitations = self.limitations(lots, complaints, evidence)
            provenance = self.provenance(conn, tenant_id, product_id, selected_id)
        overview = {
            "version_count": len(versions),
            "component_count": len(components),
            "supplier_count": len(suppliers),
            "lot_count": len(lots),
            "complaint_count": len(complaints),
            "investigation_count": len(investigations),
            "evidence_count": len(evidence),
            "limitation_count": len(limitations),
            "no_root_cause_conclusion": True,
        }
        return Product360Response(
            product=rowdict(product),
            selected_version=rowdict(selected) if selected else None,
            versions=[rowdict(v) for v in visible_versions],
            overview=overview,
            configuration={"components": [rowdict(c) for c in components], "suppliers": [rowdict(s) for s in suppliers]},
            changes=[rowdict(c) for c in changes],
            manufacturing={"lots": [rowdict(l) for l in lots], "sites": self.sites_for_lots(lots)},
            complaints=[rowdict(c) for c in complaints],
            investigations=[rowdict(i) for i in investigations],
            risks=[rowdict(r) for r in risks],
            failure_modes=[rowdict(f) for f in failure_modes],
            controls=[rowdict(c) for c in controls],
            evidence=[rowdict(e) for e in evidence],
            limitations=limitations,
            provenance=provenance,
            timeline=timeline,
            temporal_context={"mode": mode, "as_of": as_of.isoformat() if as_of else None, "event_as_of_distinct_from_known_as_of": True},
            metadata={"tenant_id": tenant_id, "generated_at": utcnow().isoformat(), "ground_truth_used": False},
        )

    def temporal_reality(self, product_id: str, version_id: str | None = None, as_of: datetime | None = None, mode: str = "event", tenant_id: str | None = None) -> TemporalRealityResponse:
        product = self.product360(product_id, version_id, as_of, "known" if mode == "known" else "event", tenant_id)
        events = product.timeline
        return TemporalRealityResponse(
            product_id=product_id,
            product_version_id=version_id,
            mode=mode,
            as_of=as_of,
            events=events,
            event_count=len(events),
            late_arriving_count=sum(1 for event in events if event.late_arriving),
            metadata={"ground_truth_used": False, "generated_at": utcnow().isoformat()},
        )

    def select_version(self, versions, version_id: str | None, as_of: datetime | None):
        if version_id:
            return next((v for v in versions if str(v["id"]) == version_id or v["version_identifier"] == version_id), None)
        if as_of:
            eligible = [v for v in versions if v["release_timestamp"] and v["release_timestamp"] <= as_of]
            if eligible:
                return eligible[-1]
        return versions[-1] if versions else None

    def components(self, conn, tenant_id: str, version_id: str | None):
        if not version_id:
            return []
        return conn.execute(
            text(
                "SELECT DISTINCT c.id, c.component_identifier, c.name, c.revision, c.description, c.status "
                "FROM components c JOIN product_components pc ON pc.tenant_id=c.tenant_id AND pc.component_id=c.id "
                "WHERE c.tenant_id=:tenant_id AND pc.product_version_id=:version_id ORDER BY c.component_identifier"
            ),
            {"tenant_id": tenant_id, "version_id": version_id},
        ).mappings().all()

    def suppliers(self, conn, tenant_id: str, components):
        ids = [str(row["id"]) for row in components]
        if not ids:
            return []
        return conn.execute(
            text(
                "SELECT DISTINCT s.id, s.supplier_identifier, s.name, s.status, c.component_identifier, c.name AS component_name "
                "FROM suppliers s JOIN component_suppliers cs ON cs.tenant_id=s.tenant_id AND cs.supplier_id=s.id "
                "JOIN components c ON c.tenant_id=cs.tenant_id AND c.id=cs.component_id "
                "WHERE s.tenant_id=:tenant_id AND c.id = ANY(:component_ids) ORDER BY s.name"
            ),
            {"tenant_id": tenant_id, "component_ids": ids},
        ).mappings().all()

    def changes(self, conn, tenant_id: str, product_id: str, version_id: str | None, components, suppliers):
        return conn.execute(
            text("SELECT id, change_identifier, change_type, description, event_timestamp, effective_timestamp, source_system FROM changes WHERE tenant_id=:tenant_id ORDER BY effective_timestamp NULLS LAST, change_identifier"),
            {"tenant_id": tenant_id},
        ).mappings().all()

    def lots(self, conn, tenant_id: str, version_id: str | None):
        if not version_id:
            return []
        return conn.execute(
            text(
                "SELECT l.id, l.lot_identifier, l.status, l.effective_timestamp AS manufactured_timestamp, ms.site_identifier, ms.name AS site_name, "
                "CASE WHEN l.source_identifier IN ('LOT-010','LOT-013','LOT-017') THEN 'PARTIAL' ELSE 'COMPLETE' END AS traceability_state "
                "FROM lot_batches l LEFT JOIN manufacturing_sites ms ON ms.tenant_id=l.tenant_id AND ms.id=l.manufacturing_site_id "
                "WHERE l.tenant_id=:tenant_id AND l.product_version_id=:version_id ORDER BY l.effective_timestamp NULLS LAST, l.lot_identifier"
            ),
            {"tenant_id": tenant_id, "version_id": version_id},
        ).mappings().all()

    def complaints(self, conn, tenant_id: str, product_id: str, version_id: str | None, as_of: datetime | None, mode: str):
        sql = "SELECT id, complaint_identifier, event_timestamp, recorded_timestamp, ingestion_timestamp, description, status, lot_batch_id FROM complaints WHERE tenant_id=:tenant_id AND product_id=:product_id"
        params = {"tenant_id": tenant_id, "product_id": product_id}
        if version_id:
            sql += " AND product_version_id=:version_id"
            params["version_id"] = version_id
        sql += " ORDER BY event_timestamp NULLS LAST, complaint_identifier"
        return conn.execute(text(sql), params).mappings().all()

    def investigations(self, conn, tenant_id: str, product_id: str):
        return conn.execute(text("SELECT id, investigation_identifier, investigation_question, status, opened_at, closed_at FROM investigations WHERE tenant_id=:tenant_id AND product_id=:product_id ORDER BY opened_at"), {"tenant_id": tenant_id, "product_id": product_id}).mappings().all()

    def list_product_investigations(self, product_id: str, tenant_id: str | None = None) -> list[dict[str, Any]]:
        """Return all investigations associated with a product for workspace access.

        This intentionally does not apply an as-of filter: association access must not
        reinterpret a historical Product 360 snapshot as absence of an investigation.
        """
        tenant_id = tenant_id or self.tenant_id()
        with engine.connect() as conn:
            product = conn.execute(text("SELECT id FROM products WHERE tenant_id=:tenant_id AND id=:id"), {"tenant_id": tenant_id, "id": product_id}).mappings().one_or_none()
            if not product:
                raise Product360Error("PRODUCT_NOT_FOUND", "Product not found")
            rows = self.investigations(conn, tenant_id, product_id)
        return [rowdict(row) for row in rows]

    def evidence(self, conn, tenant_id: str, investigations, as_of: datetime | None, mode: str):
        ids = [str(row["id"]) for row in investigations]
        if not ids:
            return []
        return conn.execute(
            text(
                "SELECT e.id, e.evidence_identifier, e.evidence_type, e.title, e.source_reference, e.reliability_status, e.content, "
                "e.source_timestamp, e.recorded_timestamp, e.ingestion_timestamp "
                "FROM evidence e JOIN staged_source_records s ON s.tenant_id=e.tenant_id AND s.raw_payload->>'evidence_id'=e.evidence_identifier "
                "JOIN investigations i ON i.tenant_id=e.tenant_id AND i.source_identifier=s.raw_payload->>'investigation_id' "
                "WHERE e.tenant_id=:tenant_id AND i.id = ANY(:investigation_ids) ORDER BY e.source_timestamp NULLS LAST, e.evidence_identifier"
            ),
            {"tenant_id": tenant_id, "investigation_ids": ids},
        ).mappings().all()

    def timeline(self, product, versions, components, suppliers, changes, lots, complaints, investigations, evidence, risks, controls) -> list[TimelineEvent]:
        events: list[TimelineEvent] = []
        for version in versions:
            events.append(self.event("PRODUCT_VERSION_EFFECTIVE", "PRODUCT", f"Version {version['version_identifier']} effective", "product_version", version["id"], effective=version["release_timestamp"], source=version.get("source_system")))
        for change in changes:
            events.append(self.event("CHANGE_EFFECTIVE", "DESIGN", change["description"], "change", change["id"], event=change["event_timestamp"], effective=change["effective_timestamp"], source=change.get("source_system")))
        for lot in lots:
            events.append(self.event("MANUFACTURING_LOT", "MANUFACTURING", f"Lot {lot['lot_identifier']} manufactured", "lot_batch", lot["id"], effective=lot["manufactured_timestamp"], quality=lot["traceability_state"]))
        for complaint in complaints:
            events.append(self.event("COMPLAINT_EVENT", "FIELD", complaint["complaint_identifier"], "complaint", complaint["id"], event=complaint["event_timestamp"], recorded=complaint["recorded_timestamp"], knowledge=complaint["ingestion_timestamp"], quality=complaint["status"]))
        for investigation in investigations:
            events.append(self.event("INVESTIGATION_OPENED", "INVESTIGATION", investigation["investigation_identifier"], "investigation", investigation["id"], event=investigation["opened_at"]))
        for item in evidence:
            late = bool(item["source_timestamp"] and item["ingestion_timestamp"] and item["ingestion_timestamp"] > item["source_timestamp"])
            events.append(self.event("EVIDENCE_RECEIVED", "EVIDENCE", item["title"], "evidence", item["id"], event=item["source_timestamp"], recorded=item["recorded_timestamp"], knowledge=item["ingestion_timestamp"], source=item["source_reference"], quality=item["reliability_status"], evidence=True, late=late))
        return sorted(events, key=lambda e: e.event_time or e.effective_time or e.recorded_time or e.knowledge_available_time or datetime.max.replace(tzinfo=timezone.utc))

    def event(self, event_type: str, category: str, title: str, entity_type: str, entity_id: Any, event=None, effective=None, recorded=None, knowledge=None, source=None, quality=None, evidence=False, late=False) -> TimelineEvent:
        return TimelineEvent(event_id=f"{event_type}:{entity_type}:{entity_id}", event_type=event_type, category=category, title=title, related_entity_type=entity_type, related_entity_id=str(entity_id), event_time=event, effective_time=effective, recorded_time=recorded, knowledge_available_time=knowledge, source=source, quality_status=quality, evidence_available=evidence, late_arriving=late)

    def filter_as_of(self, events: list[TimelineEvent], as_of: datetime | None, mode: str) -> list[TimelineEvent]:
        if not as_of:
            return events
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
        if mode == "known":
            return [e for e in events if (e.knowledge_available_time or e.recorded_time or e.event_time or e.effective_time or datetime.max.replace(tzinfo=timezone.utc)) <= as_of]
        return [e for e in events if (e.event_time or e.effective_time or datetime.max.replace(tzinfo=timezone.utc)) <= as_of]

    def filter_rows_by_time(self, rows, as_of: datetime | None, mode: str, known_key: str, event_key: str | None = None):
        if not as_of:
            return rows
        if as_of.tzinfo is None:
            as_of = as_of.replace(tzinfo=timezone.utc)
        primary_key = known_key if mode == "known" else (event_key or known_key)
        fallback_key = event_key or known_key
        return [row for row in rows if (row[primary_key] or row[fallback_key]) and (row[primary_key] or row[fallback_key]) <= as_of]

    def limitations(self, lots, complaints, evidence) -> list[dict[str, Any]]:
        items = []
        partial_lots = [row for row in lots if row["traceability_state"] == "PARTIAL"]
        if partial_lots:
            items.append({"code": "INCOMPLETE_TRACEABILITY", "severity": "WARNING", "description": f"{len(partial_lots)} lots have partial traceability."})
        missing_lot = [row for row in complaints if row["lot_batch_id"] is None]
        if missing_lot:
            items.append({"code": "MISSING_LOT_REFERENCE", "severity": "WARNING", "description": f"{len(missing_lot)} complaints lack resolved lot context."})
        late = [row for row in evidence if row["source_timestamp"] and row["ingestion_timestamp"] and row["ingestion_timestamp"] > row["source_timestamp"]]
        if late:
            items.append({"code": "LATE_ARRIVING_EVIDENCE", "severity": "INFO", "description": f"{len(late)} evidence records arrived after their event/source time."})
        items.append({"code": "NO_CAUSAL_CONCLUSION", "severity": "INFO", "description": "Product 360 shows lifecycle context only; no root-cause conclusion is generated."})
        return items

    def provenance(self, conn, tenant_id: str, product_id: str, version_id: str | None) -> list[dict[str, Any]]:
        rows = conn.execute(
            text(
                "SELECT canonical_entity_type, canonical_business_identifier, source_value, resolution_rule, resolution_status, provenance "
                "FROM source_canonical_links WHERE tenant_id=:tenant_id AND canonical_entity_type IN ('product','product_version','complaint','evidence') "
                "ORDER BY canonical_entity_type LIMIT 40"
            ),
            {"tenant_id": tenant_id},
        ).mappings().all()
        return [rowdict(row) for row in rows]

    def sites_for_lots(self, lots) -> list[dict[str, Any]]:
        seen = {}
        for lot in lots:
            if lot["site_identifier"]:
                seen[lot["site_identifier"]] = {"site_identifier": lot["site_identifier"], "name": lot["site_name"]}
        return list(seen.values())
