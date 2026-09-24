"""Controlled metadata contracts for the Mapping Studio.

The catalog is deliberately server-owned: the frontend consumes these
responses and does not carry a second hard-coded field model.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from backend.app.db.models.foundation import AuthUser, MappingImpactHistory
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/v1/admin/mapping", tags=["Mapping Studio Catalog"])

class DriftRequest(BaseModel):
    source_object_id: str = Field(min_length=3)
    source_fields: list[str] = []

class DryRunRequest(BaseModel):
    source_object_id: str = Field(min_length=3)
    rules: list[dict] = []
    records: list[dict] = []

class ValidationRequest(BaseModel):
    entity_id: str = Field(min_length=1)
    rules: list[dict] = []

class DiscoveryRequest(BaseModel):
    source_object_id: str = Field(min_length=3)
    fields: list[dict] = []
    baseline_fields: list[dict] = []

class CompareRequest(BaseModel):
    master_mapping_id: uuid.UUID
    from_version: str = Field(min_length=1)
    to_version: str = Field(min_length=1)
    from_rules: list[dict] = []
    to_rules: list[dict] = []

class SuggestionRequest(BaseModel):
    source_fields: list[dict] = []
    canonical_fields: list[dict] = []

class SuggestionDecision(BaseModel):
    suggestion_id: str = Field(min_length=1)
    decision: str = Field(pattern="^(ACCEPT|MODIFY|REJECT)$")
    reason: str | None = None

APPLICATIONS = [
    ("TRACKWISE", "TrackWise Digital", "QMS", "REST"), ("VEEVA_QMS", "Veeva Vault QMS", "QMS", "REST"),
    ("SALESFORCE_SERVICE", "Salesforce Service", "CRM", "REST"), ("TEAMCENTER", "Teamcenter PLM", "PLM", "REST"),
    ("WINDCHILL", "Windchill PLM", "PLM", "REST"), ("SAP_ERP", "SAP ERP", "ERP", "REST"),
    ("ORACLE_ERP", "Oracle ERP", "ERP", "REST"), ("RISK", "Risk Management System", "RISK", "REST"),
    ("RIM", "RIM / Vigilance System", "REGULATORY", "REST"), ("SAFETY", "Safety / Field Action System", "SAFETY", "REST"),
    ("LIMS", "LIMS", "LABORATORY", "REST"), ("MES", "MES", "MANUFACTURING", "REST"),
]
OBJECTS = {
    "TRACKWISE": ["Complaint", "Investigation", "CAPA", "Evidence", "Quality Event"],
    "VEEVA_QMS": ["Quality Event", "Investigation", "Evidence", "Document"],
    "TEAMCENTER": ["Product", "Product Version", "Component", "BOM", "Change"],
    "WINDCHILL": ["Product", "Product Version", "Component", "BOM", "Change"],
    "SAP_ERP": ["Supplier", "Manufacturing Site", "Lot", "Batch", "Material"],
    "SALESFORCE_SERVICE": ["Case", "Service Event", "Complaint Intake"],
    "ORACLE_ERP": ["Supplier", "Manufacturing Site", "Lot", "Batch", "Material"],
    "RISK": ["Risk", "Failure Mode", "Control", "Hazard"], "RIM": ["Vigilance", "Regulatory Assessment"],
    "SAFETY": ["Field Action", "Recall"], "LIMS": ["Result", "Sample"], "MES": ["Production Record", "Genealogy", "Process Event"],
}
TRACKWISE_FIELDS = [
    "complaint_id", "complaint_number", "product_code", "product_revision", "event_date", "received_date", "awareness_date", "country", "reporter_type", "complaint_type", "problem_code", "problem_description", "severity", "lot_number", "serial_number", "udi", "device_returned", "patient_involved", "serious_injury", "death", "malfunction", "status", "investigation_number", "created_at", "updated_at",
]
FIELD_GROUPS = {
    "complaint_id": "IDENTIFIERS", "complaint_number": "IDENTIFIERS", "product_code": "PRODUCT",
    "product_revision": "PRODUCT", "event_date": "DATES", "received_date": "DATES",
    "awareness_date": "DATES", "country": "REPORTER", "reporter_type": "REPORTER",
    "complaint_type": "CLASSIFICATION", "problem_code": "CLASSIFICATION",
    "problem_description": "CLASSIFICATION", "severity": "CLASSIFICATION", "lot_number": "PRODUCT",
    "serial_number": "PRODUCT", "udi": "PRODUCT", "device_returned": "CLINICAL",
    "patient_involved": "CLINICAL", "serious_injury": "CLINICAL", "death": "CLINICAL",
    "malfunction": "CLINICAL", "status": "LIFECYCLE", "investigation_number": "RELATIONSHIPS",
    "created_at": "AUDIT", "updated_at": "AUDIT",
}
CONNECTOR_VERSIONS = [
    {"application_id": "TRACKWISE", "connector_type": "REST", "version": "v1", "status": "ACTIVE", "supports_schema_discovery": True},
    {"application_id": "TEAMCENTER", "connector_type": "REST", "version": "v1", "status": "ACTIVE", "supports_schema_discovery": True},
    {"application_id": "SAP_ERP", "connector_type": "REST", "version": "v1", "status": "ACTIVE", "supports_schema_discovery": True},
    {"application_id": "SALESFORCE_SERVICE", "connector_type": "REST", "version": "v1", "status": "ACTIVE", "supports_schema_discovery": True},
]
CANONICAL = {
    "Complaint": ["external_id", "complaint_number", "product_id", "product_version_id", "event_at", "received_at", "awareness_at", "country", "reporter_type", "complaint_type", "problem_code", "problem_description", "severity", "lot_id", "serial_number", "udi", "device_returned", "patient_involved", "serious_injury", "death", "malfunction", "status", "source_created_at", "source_updated_at"],
    "Product": ["external_id", "product_identifier", "name", "status"], "ProductVersion": ["external_id", "product_id", "version_code", "version_name", "effective_at", "released_at", "status", "software_version", "configuration_reference", "change_reference", "source_recorded_at", "source_known_at"],
    "Investigation": ["external_id", "investigation_number", "status"], "Evidence": ["external_id", "identifier", "title", "status"], "Supplier": ["external_id", "supplier_identifier", "name", "status"], "Site": ["external_id", "site_identifier", "name", "status"], "Lot": ["external_id", "lot_identifier", "status"], "Risk": ["external_id", "risk_identifier", "description", "status"], "FailureMode": ["external_id", "failure_mode_identifier", "name", "status"], "Control": ["external_id", "control_identifier", "control_type", "status"], "CAPA": ["external_id", "capa_identifier", "status"], "VigilanceAssessment": ["external_id", "assessment_identifier", "status"], "FieldAction": ["external_id", "action_identifier", "status"],
}
PROTECTED = {"tenant_id", "id", "created_by", "audit_id", "provenance_id", "mapping_version_id", "authorization_metadata", "source_identity"}
FAMILIES = ["TRACKWISE_COMPLAINT", "TRACKWISE_INVESTIGATION", "TRACKWISE_CAPA", "TRACKWISE_EVIDENCE", "VEEVA_QUALITY_EVENT", "VEEVA_INVESTIGATION", "VEEVA_EVIDENCE", "VEEVA_DOCUMENT", "PLM_PRODUCT", "PLM_PRODUCT_VERSION", "PLM_COMPONENT", "PLM_BOM", "PLM_PRODUCT_CHANGE", "SAP_SUPPLIER", "SAP_SITE", "SAP_LOT", "SAP_BATCH", "SAP_MATERIAL", "SALESFORCE_CASE", "SALESFORCE_SERVICE_EVENT", "RISK_RISK", "RISK_FAILURE_MODE", "RISK_CONTROL", "RIM_VIGILANCE", "RIM_REGULATORY_ASSESSMENT", "SAFETY_FIELD_ACTION", "SAFETY_RECALL", "LIMS_RESULT", "LIMS_SAMPLE", "MES_PRODUCTION_RECORD", "MES_GENEALOGY", "MES_PROCESS_EVENT"]
INITIAL_MAPPINGS = [
    {"mapping_id": "TRACKWISE_COMPLAINT_V1", "family": "TRACKWISE_COMPLAINT", "source_object_id": "TRACKWISE:COMPLAINT", "canonical_entity": "Complaint", "version": "v1", "status": "ACTIVE", "rules": [{"source": s, "target": t, "transform": x} for s, t, x in [
        ("complaint_id", "external_id", "DIRECT"), ("complaint_number", "complaint_number", "DIRECT"), ("product_code", "product_id", "REFERENCE_LOOKUP"), ("product_revision", "product_version_id", "REFERENCE_LOOKUP"), ("event_date", "event_at", "DATE_ISO8601"), ("received_date", "received_at", "DATE_ISO8601"), ("awareness_date", "awareness_at", "DATE_ISO8601"), ("country", "country", "DIRECT"), ("reporter_type", "reporter_type", "DIRECT"), ("complaint_type", "complaint_type", "DIRECT"), ("problem_code", "problem_code", "DIRECT"), ("problem_description", "problem_description", "DIRECT"), ("severity", "severity", "DIRECT"), ("lot_number", "lot_id", "REFERENCE_LOOKUP"), ("serial_number", "serial_number", "DIRECT"), ("udi", "udi", "DIRECT"), ("device_returned", "device_returned", "DIRECT"), ("patient_involved", "patient_involved", "DIRECT"), ("serious_injury", "serious_injury", "DIRECT"), ("death", "death", "DIRECT"), ("malfunction", "malfunction", "DIRECT"), ("status", "status", "DIRECT"), ("created_at", "source_created_at", "DIRECT"), ("updated_at", "source_updated_at", "DIRECT")]]},
    {"mapping_id": "PLM_PRODUCT_VERSION_V1", "family": "PLM_PRODUCT_VERSION", "source_object_id": "TEAMCENTER:PRODUCT_VERSION", "canonical_entity": "ProductVersion", "version": "v1", "status": "ACTIVE", "rules": [{"source": s, "target": t, "transform": x} for s, t, x in [
        ("version_id", "external_id", "DIRECT"), ("product_id", "product_id", "REFERENCE_LOOKUP"), ("revision", "version_code", "DIRECT"), ("version_name", "version_name", "DIRECT"), ("effective_date", "effective_at", "DATE_ISO8601"), ("release_date", "released_at", "DATE_ISO8601"), ("status", "status", "DIRECT"), ("software_version", "software_version", "DIRECT"), ("configuration_id", "configuration_reference", "DIRECT"), ("change_order_id", "change_reference", "DIRECT"), ("recorded_at", "source_recorded_at", "DIRECT"), ("known_at", "source_known_at", "DIRECT")]]},
]

def _platform_admin(db: Session, ctx: AuthenticatedRequestContext):
    user = db.query(AuthUser).filter(AuthUser.id == ctx.user_id, AuthUser.tenant_id == ctx.tenant_id, AuthUser.status == "ACTIVE").first()
    if user is None or user.role not in {"Administrator", "Platform Admin", "PLATFORM_ADMIN"}:
        raise HTTPException(403, detail={"code": "PLATFORM_ADMIN_REQUIRED", "message": "Platform administrator access is required"})

def _app(code, name, category, connector):
    return {"application_id": code, "application_code": code, "display_name": name, "category": category, "status": "ACTIVE", "description": f"Controlled {name} metadata catalog", "default_connector_type": connector, "supports_schema_discovery": True, "supports_sample_payload": True, "created_at": None, "updated_at": None}

def _guard(db, ctx): _platform_admin(db, ctx)

@router.get("/applications")
def applications(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); return [_app(*item) for item in APPLICATIONS]

@router.get("/applications/{application_id}/objects")
def application_objects(application_id: str, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); objects = OBJECTS.get(application_id.upper())
    if objects is None: raise HTTPException(404, detail={"code": "APPLICATION_NOT_FOUND", "message": "External application is not available"})
    return [{"source_object_id": f"{application_id.upper()}:{item.upper().replace(' ', '_')}", "application_id": application_id.upper(), "object_name": item, "status": "ACTIVE"} for item in objects]

@router.get("/objects/{source_object_id}/fields")
def source_fields(source_object_id: str, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); app, _, obj = source_object_id.partition(":")
    if app not in OBJECTS or obj.replace("_", " ").title() not in OBJECTS[app]: raise HTTPException(404, detail={"code": "SOURCE_OBJECT_NOT_FOUND", "message": "Source object is not available for this application"})
    names = TRACKWISE_FIELDS if app == "TRACKWISE" and obj == "COMPLAINT" else ["id", "name", "status", "created_at", "updated_at"]
    return [{"source_field_id": f"{source_object_id}:{name}", "application_id": app, "source_object_id": source_object_id, "field_name": name, "field_label": name.replace("_", " ").title(), "field_group": FIELD_GROUPS.get(name, "GENERAL"), "data_type": "string", "required": name in {"complaint_id", "complaint_number"}, "nullable": name not in {"complaint_id", "complaint_number"}, "sample_value": None, "enum_values": [], "schema_version": "v1", "status": "ACTIVE", "is_standard_field": True, "is_customer_field": False, "sensitivity_classification": "CONTROLLED"} for name in names]

@router.get("/canonical/entities")
def canonical_entities(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); return [{"entity_id": key, "entity_name": key, "status": "ACTIVE"} for key in CANONICAL]

@router.get("/canonical/entities/{entity_id}/fields")
def canonical_fields(entity_id: str, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); fields = CANONICAL.get(entity_id)
    if fields is None: raise HTTPException(404, detail={"code": "CANONICAL_ENTITY_NOT_FOUND", "message": "Canonical entity is not available"})
    return [{"canonical_field_id": f"{entity_id}:{field}", "entity_id": entity_id, "field_name": field, "field_label": field.replace("_", " ").title(), "data_type": "string", "required": field in {"external_id", "complaint_number", "product_identifier"}, "nullable": field not in {"external_id", "complaint_number", "product_identifier"}, "system_managed": field in PROTECTED, "mapping_allowed": field not in PROTECTED, "override_policy": "PLATFORM_ONLY" if field in PROTECTED else "TENANT_ALLOWED", "validation_rule": None, "reference_entity": "Product" if field == "product_id" else "ProductVersion" if field == "product_version_id" else "Lot" if field == "lot_id" else None, "status": "ACTIVE"} for field in fields]

@router.get("/transforms")
def transforms(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); return [{"code": code, "label": label} for code, label in [("DIRECT", "Direct copy"), ("TRIM", "Trim whitespace"), ("UPPER", "Uppercase"), ("LOWER", "Lowercase"), ("DATE_ISO8601", "Normalize ISO date"), ("ENUM_MAP", "Controlled enum mapping"), ("REFERENCE_LOOKUP", "Reference lookup")]]

@router.get("/validation-rules")
def validation_rules(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); return [{"code": code, "label": label} for code, label in [("REQUIRED", "Required"), ("MAX_LENGTH", "Maximum length"), ("ENUM", "Controlled enum"), ("REFERENCE_EXISTS", "Reference must resolve"), ("DATE_VALID", "Valid date")]]

@router.get("/override-policies")
def override_policies(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); return [{"code": "PLATFORM_ONLY", "label": "Platform only"}, {"code": "TENANT_ALLOWED", "label": "Tenant override allowed"}, {"code": "APPROVAL_REQUIRED", "label": "Tenant override requires approval"}]

@router.get("/source-priorities")
def source_priorities(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); return [{"code": code, "label": label} for code, label in [("PRIMARY", "Primary source"), ("SECONDARY", "Secondary source"), ("FALLBACK", "Fallback source")]]

@router.get("/families")
def mapping_families(db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); return [{"code": code, "status": "ACTIVE"} for code in FAMILIES]

@router.get("/connector-versions")
def connector_versions(application_id: str | None = None, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx)
    return [item for item in CONNECTOR_VERSIONS if application_id is None or item["application_id"] == application_id.upper()]

@router.get("/initial-mappings")
def initial_mappings(family: str | None = None, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx)
    return [item for item in INITIAL_MAPPINGS if family is None or item["family"] == family.upper()]

@router.post("/schema-drift")
def schema_drift(payload: DriftRequest, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx)
    app, _, obj = payload.source_object_id.partition(":")
    expected = TRACKWISE_FIELDS if app == "TRACKWISE" and obj == "COMPLAINT" else ["id", "name", "status", "created_at", "updated_at"]
    unknown = sorted(set(payload.source_fields) - set(expected))
    return {"source_object_id": payload.source_object_id, "status": "DRIFT_DETECTED" if unknown else "NO_DRIFT", "expected_fields": expected, "unknown_fields": unknown}

@router.post("/dry-run")
def dry_run(payload: DryRunRequest, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx)
    output = []
    for record in payload.records:
        target = {}
        warnings = []
        blocked = []
        for rule in payload.rules:
            source, dest = str(rule.get("source", "")), str(rule.get("target", ""))
            if not source or not dest:
                continue
            if dest in PROTECTED:
                blocked.append({"target": dest, "code": "PROTECTED_FIELD"})
                continue
            value = record.get(source)
            transform = str(rule.get("transform", "DIRECT"))
            if value is not None and transform == "TRIM": value = str(value).strip()
            elif value is not None and transform == "UPPER": value = str(value).upper()
            elif value is not None and transform == "LOWER": value = str(value).lower()
            elif value is not None and transform == "DATE_ISO8601":
                try: value = datetime.fromisoformat(str(value).replace("Z", "+00:00")).date().isoformat()
                except ValueError: blocked.append({"target": dest, "code": "INVALID_DATE"}); continue
            if value is None and rule.get("required"): warnings.append({"target": dest, "code": "REQUIRED_VALUE_MISSING"})
            target[dest] = value
        outcome = "BLOCKED" if blocked else "PASS WITH LIMITATIONS" if warnings else "PASS"
        output.append({"source": record, "target": target, "warnings": warnings, "blocked": blocked, "outcome": outcome})
    blocked_count = sum(1 for row in output if row["outcome"] == "BLOCKED")
    warning_count = sum(1 for row in output if row["outcome"] == "PASS WITH LIMITATIONS")
    return {"status": "READY", "outcome": "BLOCKED" if blocked_count else "PASS WITH LIMITATIONS" if warning_count else "PASS", "source_object_id": payload.source_object_id, "record_count": len(output), "passed": len(output) - blocked_count - warning_count, "warnings": warning_count, "blocked": blocked_count, "records": output, "persisted": False}

@router.post("/validate")
def validate_mapping(payload: ValidationRequest, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx)
    allowed_transforms = {"DIRECT", "TRIM", "UPPER", "LOWER", "DATE_ISO8601", "ENUM_MAP", "REFERENCE_LOOKUP"}
    fields = {name: {"required": name in {"external_id", "complaint_number", "product_identifier"}} for name in CANONICAL.get(payload.entity_id, [])}
    targets = [str(rule.get("target", "")) for rule in payload.rules]
    errors = []
    for target in sorted({t for t in targets if targets.count(t) > 1}): errors.append({"code": "DUPLICATE_TARGET", "target": target})
    seen_refs: dict[str, str] = {}
    for rule in payload.rules:
        target = str(rule.get("target", "")); transform = str(rule.get("transform", "DIRECT"))
        if target in PROTECTED: errors.append({"code": "PROTECTED_FIELD", "target": target})
        if target not in fields: errors.append({"code": "UNKNOWN_TARGET", "target": target})
        if transform not in allowed_transforms: errors.append({"code": "INVALID_TRANSFORM", "transform": transform})
        if transform == "REFERENCE_LOOKUP" and target not in {"product_id", "product_version_id", "lot_id"}: errors.append({"code": "INVALID_REFERENCE", "target": target})
        reference = rule.get("reference_entity")
        if reference and reference == payload.entity_id: errors.append({"code": "CIRCULAR_REFERENCE", "target": target})
        if reference:
            seen_refs[target] = str(reference)
        if rule.get("enum_values") is not None and not isinstance(rule.get("enum_values"), list): errors.append({"code": "INVALID_ENUM_CONFIG", "target": target})
        if rule.get("source_type") and rule.get("target_type") and rule["source_type"] != rule["target_type"] and transform == "DIRECT": errors.append({"code": "TYPE_INCOMPATIBLE", "target": target})
        if rule.get("override_policy") not in {None, "TENANT_ALLOWED", "PLATFORM_ONLY", "APPROVAL_REQUIRED"}: errors.append({"code": "INVALID_OVERRIDE_POLICY", "target": target})
    missing = [name for name, meta in fields.items() if meta.get("required") and name not in targets]
    return {"status": "PASS" if not errors and not missing else "BLOCKED", "errors": errors, "missing_required": missing, "checked_rules": len(payload.rules), "schema_compatible": not any(e["code"] in {"TYPE_INCOMPATIBLE", "UNKNOWN_TARGET"} for e in errors), "release_blocked": bool(errors or missing)}

@router.post("/schema-discovery")
def schema_discovery(payload: DiscoveryRequest, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx)
    before = {str(x.get("name")): x for x in payload.baseline_fields}; after = {str(x.get("name")): x for x in payload.fields}
    changes = [{"type": "NEW_FIELD", "field": name, "risk": "LOW"} for name in sorted(set(after) - set(before))] + [{"type": "REMOVED_FIELD", "field": name, "risk": "HIGH"} for name in sorted(set(before) - set(after))]
    for name in sorted(set(before) & set(after)):
        if before[name].get("data_type") != after[name].get("data_type"): changes.append({"type": "TYPE_CHANGED", "field": name, "from": before[name].get("data_type"), "to": after[name].get("data_type"), "risk": "CRITICAL"})
        if before[name].get("required") != after[name].get("required") or before[name].get("nullable") != after[name].get("nullable"): changes.append({"type": "REQUIRED_NULLABLE_CHANGED", "field": name, "risk": "HIGH"})
        if before[name].get("enum_values") != after[name].get("enum_values"): changes.append({"type": "ENUM_CHANGED", "field": name, "risk": "MEDIUM"})
    return {"source_object_id": payload.source_object_id, "schema_status": "DRIFT_DETECTED" if changes else "UNCHANGED", "changes": changes, "auto_applied": False}

@router.post("/compare")
def compare_versions(payload: CompareRequest, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx)
    before = {f"{r.get('source')}->{r.get('target')}": r for r in payload.from_rules}; after = {f"{r.get('source')}->{r.get('target')}": r for r in payload.to_rules}
    changes = []
    for key in sorted(set(after) - set(before)): changes.append({"change_type": "ADDED", "mapping": after[key], "risk": "LOW"})
    for key in sorted(set(before) - set(after)): changes.append({"change_type": "REMOVED", "mapping": before[key], "risk": "HIGH"})
    for key in sorted(set(before) & set(after)):
        if before[key] != after[key]: changes.append({"change_type": "MODIFIED", "mapping": after[key], "old_mapping": before[key], "risk": "MEDIUM"})
    impact = {"changes": changes, "affected_rules": len(changes), "tenant_overrides_preserved": True}
    row = MappingImpactHistory(id=uuid.uuid4(), tenant_id=ctx.tenant_id, master_mapping_id=payload.master_mapping_id, from_version=payload.from_version, to_version=payload.to_version, impact=impact, created_at=datetime.now(timezone.utc))
    db.add(row); db.commit()
    return {"id": str(row.id), "from_version": payload.from_version, "to_version": payload.to_version, "impact": impact, "persisted": True}

@router.get("/impact-history")
def impact_history(master_mapping_id: uuid.UUID | None = None, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); query = db.query(MappingImpactHistory).filter(MappingImpactHistory.tenant_id == ctx.tenant_id)
    if master_mapping_id: query = query.filter(MappingImpactHistory.master_mapping_id == master_mapping_id)
    return [{"id": str(row.id), "master_mapping_id": str(row.master_mapping_id), "from_version": row.from_version, "to_version": row.to_version, "impact": row.impact, "created_at": row.created_at} for row in query.order_by(MappingImpactHistory.created_at.desc()).all()]

@router.post("/suggestions")
def suggestions(payload: SuggestionRequest, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); canonical = {str(f.get("field_name")): f for f in payload.canonical_fields}; result = []
    for field in payload.source_fields:
        source = str(field.get("field_name", "")); candidates = [name for name in canonical if name.lower() == source.lower() or name.lower().replace("_", "") == source.lower().replace("_", "")]
        if candidates: result.append({"suggestion_id": str(uuid.uuid4()), "source_field": source, "suggested_target": candidates[0], "transformation": "DIRECT", "reason": "Name similarity", "confidence": "MEDIUM", "status": "AI_SUGGESTION_NOT_ACTIVE"})
    return {"suggestions": result, "activation": "HUMAN_ACCEPTANCE_REQUIRED"}

@router.post("/suggestions/decision")
def suggestion_decision(payload: SuggestionDecision, db: Session = Depends(get_db), ctx: AuthenticatedRequestContext = Depends(get_request_context)):
    _guard(db, ctx); return {"suggestion_id": payload.suggestion_id, "decision": payload.decision, "reason": payload.reason, "status": "RECORDED", "active": False, "human_acceptance_required": True}
