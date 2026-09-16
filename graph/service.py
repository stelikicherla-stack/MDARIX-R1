from collections import deque
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text

from backend.app.db.session import engine
from graph.schemas import GraphNode, GraphRelationship, GraphResponse, RelationshipDetail

TENANT_KEY = "ACME_CARE_SYNTHETIC"
MAX_DEPTH = 3
MAX_NODES = 250
NODE_TYPES = {
    "product": ("products", "product_identifier", "name"),
    "product_version": ("product_versions", "version_identifier", "version_identifier"),
    "component": ("components", "component_identifier", "name"),
    "supplier": ("suppliers", "supplier_identifier", "name"),
    "manufacturing_site": ("manufacturing_sites", "site_identifier", "name"),
    "lot_batch": ("lot_batches", "lot_identifier", "lot_identifier"),
    "requirement": ("requirements", "requirement_identifier", "requirement_identifier"),
    "change": ("changes", "change_identifier", "change_identifier"),
    "complaint": ("complaints", "complaint_identifier", "complaint_identifier"),
    "investigation": ("investigations", "investigation_identifier", "investigation_identifier"),
    "risk": ("risks", "risk_identifier", "risk_identifier"),
    "failure_mode": ("failure_modes", "failure_mode_identifier", "name"),
    "control": ("controls", "control_identifier", "control_identifier"),
    "evidence": ("evidence", "evidence_identifier", "title"),
}
RELATIONSHIP_TYPES = {
    "PRODUCT_HAS_VERSION",
    "VERSION_USES_COMPONENT",
    "COMPONENT_SUPPLIED_BY",
    "CHANGE_AFFECTS_COMPONENT",
    "CHANGE_AFFECTS_PRODUCT_VERSION",
    "CHANGE_AFFECTS_SUPPLIER",
    "LOT_PRODUCED_AT_SITE",
    "LOT_FOR_PRODUCT_VERSION",
    "COMPLAINT_ASSOCIATED_WITH_PRODUCT",
    "COMPLAINT_ASSOCIATED_WITH_VERSION",
    "COMPLAINT_ASSOCIATED_WITH_LOT",
    "INVESTIGATION_INCLUDES_COMPLAINT",
    "INVESTIGATION_ASSOCIATED_WITH_PRODUCT",
    "INVESTIGATION_USES_EVIDENCE",
    "RISK_ASSOCIATED_WITH_PRODUCT",
    "RISK_HAS_FAILURE_MODE",
    "RISK_HAS_CONTROL",
    "EVIDENCE_RELATES_TO_CHANGE",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def node_key(entity_type: str, entity_id: str) -> str:
    return f"{entity_type}:{entity_id}"


def relationship_id(rel_type: str, source_type: str, source_id: str, target_type: str, target_id: str) -> str:
    return f"{rel_type}:{source_type}:{source_id}:{target_type}:{target_id}"


class GraphError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


class RealityGraphService:
    def tenant_id(self) -> str:
        with engine.connect() as conn:
            value = conn.execute(text("SELECT id FROM tenants WHERE tenant_key=:key"), {"key": TENANT_KEY}).scalar_one()
            return str(value)

    def get_node(self, entity_type: str, entity_id: str, tenant_id: str | None = None) -> GraphNode:
        entity_type = self.clean_entity_type(entity_type)
        tenant_id = tenant_id or self.tenant_id()
        table, business_col, label_col = NODE_TYPES[entity_type]
        with engine.connect() as conn:
            row = conn.execute(
                text(f"SELECT *, {business_col} AS business_identifier, {label_col} AS display_value FROM {table} WHERE tenant_id=:tenant_id AND id=:id"),
                {"tenant_id": tenant_id, "id": entity_id},
            ).mappings().one_or_none()
            if not row:
                raise GraphError("NODE_NOT_FOUND", f"{entity_type} node not found")
            source_count = conn.execute(
                text("SELECT count(*) FROM source_canonical_links WHERE tenant_id=:tenant_id AND canonical_entity_type=:entity_type AND canonical_entity_id=:id"),
                {"tenant_id": tenant_id, "entity_type": entity_type, "id": entity_id},
            ).scalar_one()
        return GraphNode(
            node_id=node_key(entity_type, entity_id),
            entity_type=entity_type,
            canonical_entity_id=str(entity_id),
            tenant_id=str(tenant_id),
            display_label=str(row["display_value"]),
            status=row.get("status") or row.get("lifecycle_status") or row.get("reliability_status"),
            quality_state=row.get("data_quality_status") or row.get("reliability_status"),
            source_count=source_count,
            metadata={"business_identifier": row["business_identifier"]},
        )

    def get_relationship(self, relationship_key: str, tenant_id: str | None = None) -> GraphRelationship:
        tenant_id = tenant_id or self.tenant_id()
        for rel in self.all_relationships(tenant_id):
            if rel.id == relationship_key:
                return rel
        raise GraphError("RELATIONSHIP_NOT_FOUND", "Relationship not found")

    def get_relationship_detail(self, relationship_key: str, tenant_id: str | None = None) -> RelationshipDetail:
        tenant_id = tenant_id or self.tenant_id()
        rel = self.get_relationship(relationship_key, tenant_id)
        provenance = [{"assertion_type": rel.assertion_type, "derivation_rule": rel.metadata.get("derivation_rule"), "source": rel.metadata.get("source")}]
        evidence = self.evidence_for_relationship(rel, tenant_id)
        return RelationshipDetail(relationship=rel, provenance=provenance, evidence=evidence)

    def get_neighbors(self, entity_type: str, entity_id: str, depth: int = 1, direction: str = "both", relationship_type: str | None = None, target_entity_type: str | None = None) -> GraphResponse:
        self.validate_depth(depth)
        entity_type = self.clean_entity_type(entity_type)
        if relationship_type:
            self.clean_relationship_type(relationship_type)
        if target_entity_type:
            target_entity_type = self.clean_entity_type(target_entity_type)
        tenant_id = self.tenant_id()
        start = node_key(entity_type, entity_id)
        nodes = {start: self.get_node(entity_type, entity_id, tenant_id)}
        rels: dict[str, GraphRelationship] = {}
        queue = deque([(entity_type, entity_id, 0)])
        seen = {(entity_type, entity_id)}
        all_rels = self.all_relationships(tenant_id)
        while queue:
            current_type, current_id, current_depth = queue.popleft()
            if current_depth >= depth:
                continue
            for rel in all_rels:
                adjacent: tuple[str, str] | None = None
                if direction in {"both", "out"} and rel.source_entity_type == current_type and rel.source_entity_id == current_id:
                    adjacent = (rel.target_entity_type, rel.target_entity_id)
                if direction in {"both", "in"} and rel.target_entity_type == current_type and rel.target_entity_id == current_id:
                    adjacent = (rel.source_entity_type, rel.source_entity_id)
                if not adjacent:
                    continue
                if relationship_type and rel.type != relationship_type:
                    continue
                if target_entity_type and adjacent[0] != target_entity_type:
                    continue
                rels[rel.id] = rel
                if adjacent not in seen and len(nodes) < MAX_NODES:
                    seen.add(adjacent)
                    nodes[node_key(*adjacent)] = self.get_node(adjacent[0], adjacent[1], tenant_id)
                    queue.append((adjacent[0], adjacent[1], current_depth + 1))
        return self.response(nodes, rels, tenant_id, depth)

    def get_product_graph(self, product_id: str, depth: int = 2) -> GraphResponse:
        return self.get_neighbors("product", product_id, depth=min(depth, MAX_DEPTH))

    def get_investigation_graph(self, investigation_id: str, depth: int = 2) -> GraphResponse:
        return self.get_neighbors("investigation", investigation_id, depth=min(depth, MAX_DEPTH))

    def get_path(self, source_type: str, source_id: str, target_type: str, target_id: str, max_depth: int = 4) -> GraphResponse:
        self.validate_depth(max_depth, max_allowed=5)
        source_type = self.clean_entity_type(source_type)
        target_type = self.clean_entity_type(target_type)
        tenant_id = self.tenant_id()
        all_rels = self.all_relationships(tenant_id)
        start = (source_type, source_id)
        target = (target_type, target_id)
        queue = deque([(start, [])])
        seen = {start}
        while queue:
            current, path = queue.popleft()
            if current == target:
                nodes = {}
                rels = {}
                for rel in path:
                    rels[rel.id] = rel
                    nodes[node_key(rel.source_entity_type, rel.source_entity_id)] = self.get_node(rel.source_entity_type, rel.source_entity_id, tenant_id)
                    nodes[node_key(rel.target_entity_type, rel.target_entity_id)] = self.get_node(rel.target_entity_type, rel.target_entity_id, tenant_id)
                return self.response(nodes, rels, tenant_id, len(path), warnings=["Graph path shows connectivity, not causality."])
            if len(path) >= max_depth:
                continue
            for rel in all_rels:
                nxt = None
                if (rel.source_entity_type, rel.source_entity_id) == current:
                    nxt = (rel.target_entity_type, rel.target_entity_id)
                elif (rel.target_entity_type, rel.target_entity_id) == current:
                    nxt = (rel.source_entity_type, rel.source_entity_id)
                if nxt and nxt not in seen:
                    seen.add(nxt)
                    queue.append((nxt, path + [rel]))
        raise GraphError("PATH_NOT_FOUND", "No bounded relationship path found")

    def all_relationships(self, tenant_id: str) -> list[GraphRelationship]:
        rels: dict[str, GraphRelationship] = {}
        with engine.connect() as conn:
            self.add_product_versions(conn, tenant_id, rels)
            self.add_lots(conn, tenant_id, rels)
            self.add_complaints(conn, tenant_id, rels)
            self.add_investigations(conn, tenant_id, rels)
            self.add_risks(conn, tenant_id, rels)
            self.add_changes(conn, tenant_id, rels)
            self.add_version_components(conn, tenant_id, rels)
            self.add_day5_relationships(conn, tenant_id, rels)
        return list(rels.values())

    def add_rel(self, rels: dict[str, GraphRelationship], rel_type: str, source_type: str, source_id: Any, target_type: str, target_id: Any, assertion_type: str, effective_from=None, recorded_at=None, evidence_count: int = 0, provenance_count: int = 1, rule: str = "deterministic_projection") -> None:
        sid, tid = str(source_id), str(target_id)
        rid = relationship_id(rel_type, source_type, sid, target_type, tid)
        rels[rid] = GraphRelationship(
            id=rid,
            type=rel_type,
            source_node=node_key(source_type, sid),
            target_node=node_key(target_type, tid),
            source_entity_type=source_type,
            source_entity_id=sid,
            target_entity_type=target_type,
            target_entity_id=tid,
            assertion_type=assertion_type,
            effective_from=effective_from,
            recorded_at=recorded_at,
            quality_status="supported",
            evidence_count=evidence_count,
            provenance_count=provenance_count,
            metadata={"derivation_rule": rule, "causal": False},
        )

    def add_product_versions(self, conn, tenant_id, rels):
        for row in conn.execute(text("SELECT id, product_id, release_timestamp FROM product_versions WHERE tenant_id=:t"), {"t": tenant_id}).mappings():
            self.add_rel(rels, "PRODUCT_HAS_VERSION", "product", row["product_id"], "product_version", row["id"], "DETERMINISTICALLY_DERIVED", row["release_timestamp"])

    def add_lots(self, conn, tenant_id, rels):
        rows = conn.execute(text("SELECT id, product_version_id, manufacturing_site_id, effective_timestamp FROM lot_batches WHERE tenant_id=:t"), {"t": tenant_id}).mappings()
        for row in rows:
            if row["product_version_id"]:
                self.add_rel(rels, "LOT_FOR_PRODUCT_VERSION", "lot_batch", row["id"], "product_version", row["product_version_id"], "SOURCE_ASSERTED", row["effective_timestamp"])
            if row["manufacturing_site_id"]:
                self.add_rel(rels, "LOT_PRODUCED_AT_SITE", "lot_batch", row["id"], "manufacturing_site", row["manufacturing_site_id"], "SOURCE_ASSERTED", row["effective_timestamp"])

    def add_complaints(self, conn, tenant_id, rels):
        rows = conn.execute(text("SELECT id, product_id, product_version_id, lot_batch_id, event_timestamp, recorded_timestamp FROM complaints WHERE tenant_id=:t"), {"t": tenant_id}).mappings()
        for row in rows:
            if row["product_id"]:
                self.add_rel(rels, "COMPLAINT_ASSOCIATED_WITH_PRODUCT", "complaint", row["id"], "product", row["product_id"], "SOURCE_ASSERTED", row["event_timestamp"], row["recorded_timestamp"])
            if row["product_version_id"]:
                self.add_rel(rels, "COMPLAINT_ASSOCIATED_WITH_VERSION", "complaint", row["id"], "product_version", row["product_version_id"], "SOURCE_ASSERTED", row["event_timestamp"], row["recorded_timestamp"])
            if row["lot_batch_id"]:
                self.add_rel(rels, "COMPLAINT_ASSOCIATED_WITH_LOT", "complaint", row["id"], "lot_batch", row["lot_batch_id"], "SOURCE_ASSERTED", row["event_timestamp"], row["recorded_timestamp"])

    def add_investigations(self, conn, tenant_id, rels):
        for row in conn.execute(text("SELECT id, product_id, opened_at FROM investigations WHERE tenant_id=:t"), {"t": tenant_id}).mappings():
            self.add_rel(rels, "INVESTIGATION_ASSOCIATED_WITH_PRODUCT", "investigation", row["id"], "product", row["product_id"], "SOURCE_ASSERTED", row["opened_at"])
        for row in conn.execute(
            text(
                "SELECT i.id AS investigation_id, e.id AS evidence_id "
                "FROM evidence e "
                "JOIN staged_source_records s ON s.tenant_id=e.tenant_id AND s.raw_payload->>'evidence_id'=e.evidence_identifier AND s.record_type='evidence_metadata' "
                "JOIN investigations i ON i.tenant_id=e.tenant_id AND i.source_identifier=s.raw_payload->>'investigation_id' "
                "WHERE e.tenant_id=:t"
            ),
            {"t": tenant_id},
        ).mappings():
            self.add_rel(rels, "INVESTIGATION_USES_EVIDENCE", "investigation", row["investigation_id"], "evidence", row["evidence_id"], "SOURCE_ASSERTED", evidence_count=1)
        for row in conn.execute(text("SELECT i.id investigation_id, c.id complaint_id FROM investigations i JOIN complaints c ON c.tenant_id=i.tenant_id AND c.product_id=i.product_id WHERE i.tenant_id=:t"), {"t": tenant_id}).mappings():
            self.add_rel(rels, "INVESTIGATION_INCLUDES_COMPLAINT", "investigation", row["investigation_id"], "complaint", row["complaint_id"], "DETERMINISTICALLY_DERIVED")

    def add_risks(self, conn, tenant_id, rels):
        for row in conn.execute(text("SELECT id, product_id FROM risks WHERE tenant_id=:t AND product_id IS NOT NULL"), {"t": tenant_id}).mappings():
            self.add_rel(rels, "RISK_ASSOCIATED_WITH_PRODUCT", "risk", row["id"], "product", row["product_id"], "SOURCE_ASSERTED")

    def add_changes(self, conn, tenant_id, rels):
        rows = conn.execute(text("SELECT id, change_identifier, change_type, event_timestamp, effective_timestamp FROM changes WHERE tenant_id=:t"), {"t": tenant_id}).mappings()
        for row in rows:
            if "COMP-PWR" in row["change_identifier"]:
                component = conn.execute(text("SELECT id FROM components WHERE tenant_id=:t AND component_identifier='COMP-PWR'"), {"t": tenant_id}).scalar_one_or_none()
                if component:
                    self.add_rel(rels, "CHANGE_AFFECTS_COMPONENT", "change", row["id"], "component", component, "SOURCE_ASSERTED", row["effective_timestamp"], row["event_timestamp"])
            if "PROD-D" in row["change_identifier"]:
                pv = conn.execute(text("SELECT id FROM product_versions WHERE tenant_id=:t AND version_identifier='D'"), {"t": tenant_id}).scalar_one_or_none()
                if pv:
                    self.add_rel(rels, "CHANGE_AFFECTS_PRODUCT_VERSION", "change", row["id"], "product_version", pv, "SOURCE_ASSERTED", row["effective_timestamp"], row["event_timestamp"])
            if "SUP-PROC" in row["change_identifier"]:
                sup = conn.execute(text("SELECT id FROM suppliers WHERE tenant_id=:t AND supplier_identifier='SUP-NOVACAP'"), {"t": tenant_id}).scalar_one_or_none()
                if sup:
                    self.add_rel(rels, "CHANGE_AFFECTS_SUPPLIER", "change", row["id"], "supplier", sup, "SOURCE_ASSERTED", row["effective_timestamp"], row["event_timestamp"])

    def add_version_components(self, conn, tenant_id, rels):
        rows = conn.execute(
            text(
                "SELECT pv.id product_version_id, c.id component_id FROM product_versions pv CROSS JOIN components c "
                "WHERE pv.tenant_id=:t AND c.tenant_id=:t AND pv.version_identifier IN ('C','D') AND c.component_identifier IN ('COMP-PWR','COMP-CAP','COMP-FW','COMP-CONN')"
            ),
            {"t": tenant_id},
        ).mappings()
        for row in rows:
            self.add_rel(rels, "VERSION_USES_COMPONENT", "product_version", row["product_version_id"], "component", row["component_id"], "DETERMINISTICALLY_DERIVED", rule="DAY6_VERSION_COMPONENT_PROJECTION_V1")

    def add_day5_relationships(self, conn, tenant_id, rels):
        rows = conn.execute(text("SELECT source_entity_type, source_entity_id, target_entity_type, target_entity_id, relationship_type, effective_timestamp, recorded_timestamp, resolution_rule FROM canonical_relationships WHERE tenant_id=:t"), {"t": tenant_id}).mappings()
        mapping = {"LOT_BUILT_AS_PRODUCT_VERSION": "LOT_FOR_PRODUCT_VERSION"}
        for row in rows:
            rel_type = mapping.get(row["relationship_type"], row["relationship_type"])
            if rel_type in RELATIONSHIP_TYPES:
                self.add_rel(rels, rel_type, row["source_entity_type"], row["source_entity_id"], row["target_entity_type"], row["target_entity_id"], "DETERMINISTICALLY_DERIVED", row["effective_timestamp"], row["recorded_timestamp"], rule=row["resolution_rule"])

    def evidence_for_relationship(self, rel: GraphRelationship, tenant_id: str) -> list[dict[str, Any]]:
        if rel.evidence_count == 0 and "EVIDENCE" not in rel.type:
            return []
        with engine.connect() as conn:
            rows = conn.execute(text("SELECT evidence_identifier, title, reliability_status FROM evidence WHERE tenant_id=:t LIMIT 5"), {"t": tenant_id}).mappings().all()
            return [dict(row) for row in rows]

    def response(self, nodes: dict[str, GraphNode], rels: dict[str, GraphRelationship], tenant_id: str, depth: int, warnings: list[str] | None = None) -> GraphResponse:
        return GraphResponse(nodes=list(nodes.values()), relationships=list(rels.values()), metadata={"tenant_id": tenant_id, "depth": depth, "generated_at": now_iso(), "warnings": warnings or [], "node_count": len(nodes), "relationship_count": len(rels), "max_depth": MAX_DEPTH})

    def validate_depth(self, depth: int, max_allowed: int = MAX_DEPTH) -> None:
        if depth < 0 or depth > max_allowed:
            raise GraphError("INVALID_DEPTH", f"depth must be between 0 and {max_allowed}")

    def clean_entity_type(self, entity_type: str) -> str:
        value = entity_type.lower()
        if value not in NODE_TYPES:
            raise GraphError("INVALID_ENTITY_TYPE", "Unsupported graph entity type")
        return value

    def clean_relationship_type(self, relationship_type: str) -> str:
        value = relationship_type.upper()
        if value not in RELATIONSHIP_TYPES:
            raise GraphError("INVALID_RELATIONSHIP_TYPE", "Unsupported graph relationship type")
        return value
