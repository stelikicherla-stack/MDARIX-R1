"""Controlled metadata contracts for the Mapping Studio.

The catalog is deliberately server-owned: the frontend consumes these
responses and does not carry a second hard-coded field model.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.request_context import AuthenticatedRequestContext, get_request_context
from backend.app.db.models.foundation import AuthUser

router = APIRouter(prefix="/api/v1/admin/mapping", tags=["Mapping Studio Catalog"])

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
