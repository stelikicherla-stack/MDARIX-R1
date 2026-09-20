import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from access_control.policy import PermissionSet, Role, User, effective_permissions
from auth.service import auth_service
from auth.service import _hash
from backend.app.db.session import get_db
from backend.app.db.models.foundation import (
    AuthUser, PersonaAssignment, RoleAssignment, RoleDefinition,
    RolePermissionSet, PermissionSetDefinition, TenantMembership,
    FeatureEntitlement, PlanDefinition, TenantPlanAssignment, Product, ProductVersion,
    ApprovalAuthority, SegregationOfDutiesPolicy, ConnectorConfiguration, MappingConfiguration, AuditEvent,
    MasterMapping, TenantMappingVersion, TenantMappingOverride,
)
from access_control.personas import R1_PERSONAS as PERSONAS, get_persona
from access_control.configuration_safety import safe_configuration
from integration.gateway import ConnectionConfig, Connector, MappingDefinition, preview
from sqlalchemy.orm import Session

router=APIRouter(prefix="/api/v1",tags=["Access Control"])
class RoleSwitch(BaseModel): role: str
class MembershipRequest(BaseModel): user_id: uuid.UUID; is_default: bool = False
class PersonaRequest(BaseModel): user_id: uuid.UUID; persona_code: str
class PermissionSetRequest(BaseModel): code: str = Field(min_length=1, max_length=100); object_permissions: dict = {}; field_permissions: dict = {}; action_permissions: dict = {}; version: str = "v1"
class RoleRequest(BaseModel): code: str = Field(min_length=1, max_length=100); name: str = Field(min_length=1, max_length=120); version: str = "v1"
class RoleAssignmentRequest(BaseModel): user_id: uuid.UUID; role_id: uuid.UUID
class RolePermissionRequest(BaseModel): role_id: uuid.UUID; permission_set_id: uuid.UUID
class TenantSwitchRequest(BaseModel): tenant_id: uuid.UUID
class UserStatusRequest(BaseModel): status: str = Field(pattern="^(ACTIVE|SUSPENDED|OFFBOARDED)$")
class AuthorityRequest(BaseModel): role_name: str; object_type: str; decision_type: str; authority: str = "AUTHORIZED"; version: str = "v1"
class SodRequest(BaseModel): name: str; object_type: str; decision_type: str; creator_cannot_approve: bool = True; last_material_editor_cannot_approve: bool = True; version: str = "v1"
class ConnectorRequest(BaseModel): code: str; connector_type: str; configuration: dict = {}; version: str = "v1"
class MappingRequest(BaseModel): code: str; source_system: str; target_entity: str; mapping_rules: dict = {}; version: str = "v1"
class UserCreateRequest(BaseModel): email: str = Field(min_length=3, max_length=254); display_name: str = Field(min_length=1, max_length=120); company: str = Field(min_length=1, max_length=160); password: str = Field(min_length=12, max_length=128); role: str = "Viewer"
class AdminUpdateRequest(BaseModel): values: dict
class ProductRequest(BaseModel): product_identifier: str; name: str; description: str | None = None; product_family: str | None = None; manufacturer_context: str | None = None
class ProductVersionRequest(BaseModel): product_id: uuid.UUID; version_identifier: str; description: str | None = None; release_timestamp: str | None = None
class MasterMappingRequest(BaseModel): code: str; source_system: str; target_entity: str; definition: dict = {}
class MappingVersionRequest(BaseModel): master_mapping_id: uuid.UUID; version: str; rules: dict = {}; effective_from: str | None = None
class MappingOverrideRequest(BaseModel): mapping_version_id: uuid.UUID; field_name: str; override_rule: dict = {}
class LifecycleRequest(BaseModel): lifecycle_status: str = Field(pattern="^(active|retired|archived)$")
class ConnectorRunRequest(BaseModel): records: list[dict] = []; source_system: str = "SIMULATED"; required_fields: list[str] = []
class MappingPreviewRequest(BaseModel): records: list[dict]; rules: dict; source_object: str; target_entity: str; mapping_version: str
class StatusRequest(BaseModel): status: str = Field(pattern="^(DRAFT|ACTIVE|RETIRED)$")


def _require_administrator(request: Request, db: Session) -> AuthUser:
    user = _authenticated_user(request, db)
    if (user.role or "").upper() not in {"ADMINISTRATOR", "ADMIN", "MDARIX ADMINISTRATOR"}:
        raise HTTPException(403, detail={"code": "ADMINISTRATOR_REQUIRED", "message": "Administrator role required"})
    return user

def _authenticated_user(request: Request, db: Session) -> AuthUser:
    token = request.cookies.get("mdarix_session", "")
    try:
        context = auth_service.context(token)
    except ValueError as exc:
        raise HTTPException(401, detail={"code": "UNAUTHENTICATED", "message": "Authentication required"}) from exc
    user = db.query(AuthUser).filter(AuthUser.id == context["user_id"]).first()
    if user is None or user.status != "ACTIVE" or str(user.tenant_id) != str(context["tenant_id"]):
        raise HTTPException(401, detail={"code": "UNAUTHENTICATED", "message": "Authentication required"})
    return user

@router.get("/me/context")
def context(request: Request, db: Session = Depends(get_db)):
    user = _authenticated_user(request, db)
    # Legacy AuthUser.role remains the compatibility default until every
    # existing tenant has durable role assignments. New assignments always
    # take precedence and are constrained to the authenticated tenant.
    role_name = user.role or "Viewer"
    role_version = "legacy"
    permission_sets = [PermissionSet("persisted", {})]
    try:
        membership = db.query(TenantMembership).filter(
            TenantMembership.tenant_id == user.tenant_id,
            TenantMembership.user_id == user.id,
            TenantMembership.status == "ACTIVE",
        ).first()
        if membership is not None:
            assignments = db.query(RoleAssignment).filter(
                RoleAssignment.tenant_id == user.tenant_id,
                RoleAssignment.user_id == user.id,
                RoleAssignment.status == "ACTIVE",
            ).all()
            for assignment in assignments:
                role_row = db.query(RoleDefinition).filter(
                    RoleDefinition.tenant_id == user.tenant_id,
                    RoleDefinition.id == assignment.role_id,
                    RoleDefinition.status == "ACTIVE",
                ).first()
                if role_row is None:
                    continue
                role_name = role_row.name
                role_version = role_row.version
                links = db.query(RolePermissionSet).filter(
                    RolePermissionSet.tenant_id == user.tenant_id,
                    RolePermissionSet.role_id == role_row.id,
                ).all()
                permission_sets = []
                for link in links:
                    definition = db.query(PermissionSetDefinition).filter(
                        PermissionSetDefinition.tenant_id == user.tenant_id,
                        PermissionSetDefinition.id == link.permission_set_id,
                        PermissionSetDefinition.status == "ACTIVE",
                    ).first()
                    if definition is not None:
                        permission_sets.append(PermissionSet(definition.code, {
                            **(definition.object_permissions or {}),
                            **(definition.action_permissions or {}),
                        }))
                break
    except Exception:
        # Keep the endpoint usable against pre-migration test doubles and
        # legacy databases; durable records are used whenever available.
        pass
    role = Role(str(user.tenant_id), role_name, permission_sets, role_version, "ACTIVE")
    persisted = User(str(user.tenant_id), str(user.id), user.display_name, [role], role.name)
    permissions = effective_permissions(persisted)
    personas = []
    try:
        assignments = db.query(PersonaAssignment).filter(
            PersonaAssignment.tenant_id == user.tenant_id,
            PersonaAssignment.user_id == user.id,
            PersonaAssignment.status == "ACTIVE",
        ).all()
        personas = [{"code": row.persona_code, "label": get_persona(row.persona_code).label} for row in assignments]
    except Exception:
        personas = []
    return {"user_id": str(user.id), "display_name": user.display_name, "email": user.username, "tenant_id": str(user.tenant_id), "active_role": role.name, "role_version": role.version, "personas": personas, "permissions": permissions}

@router.post("/me/active-role")
def active_role(request: RoleSwitch, http_request: Request, db: Session = Depends(get_db)):
    user = _authenticated_user(http_request, db)
    if request.role != user.role:
        raise HTTPException(403, detail={"code":"ROLE_NOT_ASSIGNED","message":"Requested role is not assigned to the authenticated user"})
    return context(http_request, db)


@router.get("/admin/identity/personas")
def persona_catalog(request: Request, db: Session = Depends(get_db)):
    """Read-only administrator catalog used by the identity control plane."""
    _require_administrator(request, db)
    return [{"code": persona.code, "label": persona.label, "dashboard_emphasis": list(persona.dashboard_emphasis)} for persona in PERSONAS]


def _admin_tenant(request: Request, db: Session) -> AuthUser:
    return _require_administrator(request, db)


def _audit_configuration(db, admin, action, entity_type, entity_id, version):
    db.add(AuditEvent(id=uuid.uuid4(), tenant_id=admin.tenant_id, actor_ref=str(admin.id), action=action, entity_type=entity_type, entity_id=entity_id, details={"version": version, "source": "ADMIN_CONTROL_PLANE"}, created_at=datetime.now(timezone.utc)))


@router.get("/admin/identity/users/{user_id}")
def admin_user(user_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    user = db.query(AuthUser).filter(AuthUser.id == user_id, AuthUser.tenant_id == admin.tenant_id).first()
    if user is None:
        raise HTTPException(404, detail={"code": "USER_NOT_FOUND", "message": "User is not available for this tenant"})
    return context(request, db) if user.id == admin.id else {
        "user_id": str(user.id), "display_name": user.display_name, "email": user.username,
        "tenant_id": str(user.tenant_id), "role": user.role, "status": user.status,
    }


@router.post("/admin/identity/memberships")
def create_membership(payload: MembershipRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    user = db.query(AuthUser).filter(AuthUser.id == payload.user_id, AuthUser.tenant_id == admin.tenant_id).first()
    if user is None:
        raise HTTPException(404, detail={"code": "USER_NOT_FOUND", "message": "User is not available for this tenant"})
    existing = db.query(TenantMembership).filter_by(tenant_id=admin.tenant_id, user_id=user.id).first()
    if existing:
        existing.status = "ACTIVE"; existing.is_default = payload.is_default
        result = existing
    else:
        result = TenantMembership(id=uuid.uuid4(), tenant_id=admin.tenant_id, user_id=user.id, status="ACTIVE", is_default=payload.is_default, created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc))
        db.add(result)
    db.commit()
    return {"membership_id": str(result.id), "tenant_id": str(admin.tenant_id), "user_id": str(user.id), "status": result.status}


@router.post("/admin/identity/persona-assignments")
def assign_persona(payload: PersonaRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    try: persona = get_persona(payload.persona_code)
    except ValueError as exc: raise HTTPException(422, detail={"code": "UNKNOWN_PERSONA", "message": "Persona is not in the R1 catalog"}) from exc
    user = db.query(AuthUser).filter(AuthUser.id == payload.user_id, AuthUser.tenant_id == admin.tenant_id).first()
    if user is None: raise HTTPException(404, detail={"code": "USER_NOT_FOUND", "message": "User is not available for this tenant"})
    row = db.query(PersonaAssignment).filter_by(tenant_id=admin.tenant_id, user_id=user.id, persona_code=persona.code).first()
    if row is None:
        row = PersonaAssignment(id=uuid.uuid4(), tenant_id=admin.tenant_id, user_id=user.id, persona_code=persona.code, status="ACTIVE", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)); db.add(row)
    else: row.status = "ACTIVE"
    db.commit()
    return {"assignment_id": str(row.id), "user_id": str(user.id), "persona_code": persona.code, "status": row.status}


@router.post("/admin/identity/permission-sets")
def create_permission_set(payload: PermissionSetRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); now = datetime.now(timezone.utc)
    row = PermissionSetDefinition(id=uuid.uuid4(), tenant_id=admin.tenant_id, code=payload.code, object_permissions=payload.object_permissions, field_permissions=payload.field_permissions, action_permissions=payload.action_permissions, version=payload.version, status="DRAFT", created_at=now, updated_at=now)
    db.add(row); db.commit()
    return {"permission_set_id": str(row.id), "tenant_id": str(admin.tenant_id), "code": row.code, "version": row.version, "status": row.status}


@router.post("/admin/identity/roles")
def create_role(payload: RoleRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); now = datetime.now(timezone.utc)
    row = RoleDefinition(id=uuid.uuid4(), tenant_id=admin.tenant_id, code=payload.code, name=payload.name, version=payload.version, status="DRAFT", created_at=now, updated_at=now)
    db.add(row); db.commit()
    return {"role_id": str(row.id), "tenant_id": str(admin.tenant_id), "code": row.code, "name": row.name, "version": row.version, "status": row.status}


@router.post("/admin/identity/role-assignments")
def assign_role(payload: RoleAssignmentRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    user = db.query(AuthUser).filter(AuthUser.id == payload.user_id, AuthUser.tenant_id == admin.tenant_id).first()
    role = db.query(RoleDefinition).filter(RoleDefinition.id == payload.role_id, RoleDefinition.tenant_id == admin.tenant_id, RoleDefinition.status == "ACTIVE").first()
    if user is None or role is None:
        raise HTTPException(404, detail={"code": "ROLE_ASSIGNMENT_SCOPE_INVALID", "message": "User and role must belong to this tenant and be active"})
    row = db.query(RoleAssignment).filter_by(tenant_id=admin.tenant_id, user_id=user.id, role_id=role.id).first()
    if row is None:
        row = RoleAssignment(id=uuid.uuid4(), tenant_id=admin.tenant_id, user_id=user.id, role_id=role.id, status="ACTIVE", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)); db.add(row)
    else: row.status = "ACTIVE"
    db.commit(); return {"assignment_id": str(row.id), "user_id": str(user.id), "role_id": str(role.id), "status": row.status}


@router.post("/admin/identity/role-permission-sets")
def link_permission_set(payload: RolePermissionRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    role = db.query(RoleDefinition).filter(RoleDefinition.id == payload.role_id, RoleDefinition.tenant_id == admin.tenant_id).first()
    permission_set = db.query(PermissionSetDefinition).filter(PermissionSetDefinition.id == payload.permission_set_id, PermissionSetDefinition.tenant_id == admin.tenant_id).first()
    if role is None or permission_set is None:
        raise HTTPException(404, detail={"code": "PERMISSION_LINK_SCOPE_INVALID", "message": "Role and permission set must belong to this tenant"})
    row = db.query(RolePermissionSet).filter_by(tenant_id=admin.tenant_id, role_id=role.id, permission_set_id=permission_set.id).first()
    if row is None:
        row = RolePermissionSet(id=uuid.uuid4(), tenant_id=admin.tenant_id, role_id=role.id, permission_set_id=permission_set.id, created_at=datetime.now(timezone.utc)); db.add(row); db.commit()
    return {"link_id": str(row.id), "role_id": str(role.id), "permission_set_id": str(permission_set.id)}


@router.patch("/admin/identity/users/{user_id}/status")
def update_user_status(user_id: uuid.UUID, payload: UserStatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    user = db.query(AuthUser).filter(AuthUser.id == user_id, AuthUser.tenant_id == admin.tenant_id).first()
    if user is None: raise HTTPException(404, detail={"code": "USER_NOT_FOUND", "message": "User is not available for this tenant"})
    user.status = payload.status; user.updated_at = datetime.now(timezone.utc); db.commit()
    return {"user_id": str(user.id), "tenant_id": str(user.tenant_id), "status": user.status}


@router.post("/me/tenant-context")
def switch_tenant(payload: TenantSwitchRequest, request: Request, db: Session = Depends(get_db)):
    user = _authenticated_user(request, db)
    membership = db.query(TenantMembership).filter(TenantMembership.user_id == user.id, TenantMembership.tenant_id == payload.tenant_id, TenantMembership.status == "ACTIVE").first()
    if membership is None:
        raise HTTPException(403, detail={"code": "TENANT_MEMBERSHIP_REQUIRED", "message": "Active membership is required for this tenant"})
    token = request.cookies.get("mdarix_session", "")
    try: auth_service.switch_tenant(token, str(payload.tenant_id))
    except ValueError as exc: raise HTTPException(401, detail={"code": "UNAUTHENTICATED", "message": "Authentication required"}) from exc
    return {"status": "SWITCHED", "tenant_id": str(payload.tenant_id)}


@router.get("/me/entitlements/{feature_code}")
def entitlement(feature_code: str, request: Request, db: Session = Depends(get_db)):
    user = _authenticated_user(request, db); now = datetime.now(timezone.utc)
    row = db.query(TenantPlanAssignment).join(PlanDefinition, PlanDefinition.id == TenantPlanAssignment.plan_id).join(FeatureEntitlement, FeatureEntitlement.plan_id == PlanDefinition.id).filter(TenantPlanAssignment.tenant_id == user.tenant_id, TenantPlanAssignment.status == "ACTIVE", PlanDefinition.status == "ACTIVE", FeatureEntitlement.feature_code == feature_code, FeatureEntitlement.status == "ACTIVE", FeatureEntitlement.enabled == True, TenantPlanAssignment.effective_from <= now).first()
    return {"feature": feature_code, "entitled": row is not None, "limits": (row[0].limits if isinstance(row, tuple) else row.limits) if row else {}}


@router.post("/admin/governance/approval-authorities")
def create_authority(payload: AuthorityRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); now = datetime.now(timezone.utc)
    row = ApprovalAuthority(id=uuid.uuid4(), tenant_id=admin.tenant_id, role_name=payload.role_name, object_type=payload.object_type, decision_type=payload.decision_type, scope={}, authority=payload.authority, version=payload.version, status="DRAFT", effective_from=now, created_at=now, updated_at=now)
    db.add(row); _audit_configuration(db, admin, "APPROVAL_AUTHORITY_CREATED", "ApprovalAuthority", row.id, row.version); db.commit(); return {"authority_id": str(row.id), "tenant_id": str(admin.tenant_id), "status": row.status}


@router.post("/admin/governance/sod-policies")
def create_sod(payload: SodRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); now = datetime.now(timezone.utc)
    row = SegregationOfDutiesPolicy(id=uuid.uuid4(), tenant_id=admin.tenant_id, name=payload.name, object_type=payload.object_type, decision_type=payload.decision_type, creator_cannot_approve=payload.creator_cannot_approve, last_material_editor_cannot_approve=payload.last_material_editor_cannot_approve, version=payload.version, status="DRAFT", effective_from=now, created_at=now, updated_at=now)
    db.add(row); _audit_configuration(db, admin, "SOD_POLICY_CREATED", "SegregationOfDutiesPolicy", row.id, row.version); db.commit(); return {"policy_id": str(row.id), "tenant_id": str(admin.tenant_id), "status": row.status}


@router.post("/admin/configuration/connectors")
def create_connector(payload: ConnectorRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); now = datetime.now(timezone.utc)
    try: configuration = safe_configuration(payload.configuration)
    except ValueError as exc: raise HTTPException(422, detail={"code": "SENSITIVE_CONFIGURATION_REJECTED", "message": "Secrets must be stored in a managed secret provider, not configuration"}) from exc
    row = ConnectorConfiguration(id=uuid.uuid4(), tenant_id=admin.tenant_id, code=payload.code, connector_type=payload.connector_type, configuration=configuration, version=payload.version, status="DRAFT", created_at=now, updated_at=now)
    db.add(row); _audit_configuration(db, admin, "CONNECTOR_CONFIGURATION_CREATED", "ConnectorConfiguration", row.id, row.version); db.commit(); return {"connector_id": str(row.id), "tenant_id": str(admin.tenant_id), "code": row.code, "version": row.version, "status": row.status}


@router.post("/admin/configuration/mappings")
def create_mapping(payload: MappingRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); now = datetime.now(timezone.utc)
    row = MappingConfiguration(id=uuid.uuid4(), tenant_id=admin.tenant_id, code=payload.code, source_system=payload.source_system, target_entity=payload.target_entity, mapping_rules=payload.mapping_rules, version=payload.version, status="DRAFT", created_at=now, updated_at=now)
    db.add(row); _audit_configuration(db, admin, "MAPPING_CONFIGURATION_CREATED", "MappingConfiguration", row.id, row.version); db.commit(); return {"mapping_id": str(row.id), "tenant_id": str(admin.tenant_id), "code": row.code, "version": row.version, "status": row.status}


@router.get("/admin/configuration/connectors")
def list_connectors(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(ConnectorConfiguration).filter(ConnectorConfiguration.tenant_id == admin.tenant_id).order_by(ConnectorConfiguration.code, ConnectorConfiguration.version).all()
    return [{"id": str(row.id), "code": row.code, "connector_type": row.connector_type, "version": row.version, "status": row.status, "configuration": row.configuration} for row in rows]


@router.get("/admin/configuration/mappings")
def list_mappings(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(MappingConfiguration).filter(MappingConfiguration.tenant_id == admin.tenant_id).order_by(MappingConfiguration.code, MappingConfiguration.version).all()
    return [{"id": str(row.id), "code": row.code, "source_system": row.source_system, "target_entity": row.target_entity, "version": row.version, "status": row.status, "mapping_rules": row.mapping_rules} for row in rows]


@router.patch("/admin/configuration/connectors/{configuration_id}/status")
def activate_connector(configuration_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(ConnectorConfiguration).filter(ConnectorConfiguration.id == configuration_id, ConnectorConfiguration.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "CONNECTOR_NOT_FOUND", "message": "Connector configuration is not available for this tenant"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "CONNECTOR_CONFIGURATION_STATUS_CHANGED", "ConnectorConfiguration", row.id, row.version); db.commit()
    return {"id": str(row.id), "status": row.status, "version": row.version}


@router.get("/admin/governance/policies")
def governance_policies(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    authorities = db.query(ApprovalAuthority).filter(ApprovalAuthority.tenant_id == admin.tenant_id).all()
    sod = db.query(SegregationOfDutiesPolicy).filter(SegregationOfDutiesPolicy.tenant_id == admin.tenant_id).all()
    return {"approval_authorities": [{"id": str(row.id), "role_name": row.role_name, "object_type": row.object_type, "decision_type": row.decision_type, "authority": row.authority, "version": row.version, "status": row.status} for row in authorities], "sod_policies": [{"id": str(row.id), "name": row.name, "object_type": row.object_type, "decision_type": row.decision_type, "creator_cannot_approve": row.creator_cannot_approve, "last_material_editor_cannot_approve": row.last_material_editor_cannot_approve, "version": row.version, "status": row.status} for row in sod]}


@router.get("/admin/audit-history")
def audit_history(request: Request, action: str | None = None, entity_type: str | None = None, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    query = db.query(AuditEvent).filter(AuditEvent.tenant_id == admin.tenant_id)
    if action: query = query.filter(AuditEvent.action == action)
    if entity_type: query = query.filter(AuditEvent.entity_type == entity_type)
    rows = query.order_by(AuditEvent.created_at.desc()).limit(200).all()
    return [{"id": str(row.id), "tenant_id": str(row.tenant_id), "actor_ref": row.actor_ref, "action": row.action, "entity_type": row.entity_type, "entity_id": str(row.entity_id) if row.entity_id else None, "details": row.details, "created_at": row.created_at} for row in rows]


@router.get("/admin/identity/users")
def list_users(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(AuthUser).filter(AuthUser.tenant_id == admin.tenant_id).order_by(AuthUser.username).all()
    return [{"id": str(row.id), "email": row.username, "display_name": row.display_name, "role": row.role, "status": row.status, "tenant_id": str(row.tenant_id)} for row in rows]


@router.post("/admin/identity/users")
def create_user(payload: UserCreateRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    email = payload.email.strip().lower()
    if db.query(AuthUser).filter(AuthUser.tenant_id == admin.tenant_id, AuthUser.username == email).first():
        raise HTTPException(409, detail={"code": "ACCOUNT_EXISTS", "message": "A user with this email already exists in this tenant"})
    now = datetime.now(timezone.utc)
    row = AuthUser(id=uuid.uuid4(), tenant_id=admin.tenant_id, username=email, display_name=payload.display_name.strip(), company=payload.company.strip(), password_hash=_hash(payload.password), role=payload.role.strip(), status="ACTIVE", email_verified=True, created_at=now, updated_at=now)
    db.add(row); db.flush()
    db.add(TenantMembership(id=uuid.uuid4(), tenant_id=admin.tenant_id, user_id=row.id, status="ACTIVE", is_default=True, created_at=now, updated_at=now))
    _audit_configuration(db, admin, "USER_CREATED", "AuthUser", row.id, "v1"); db.commit()
    return {"id": str(row.id), "email": row.username, "display_name": row.display_name, "tenant_id": str(row.tenant_id), "role": row.role, "status": row.status}


@router.get("/admin/identity/persona-assignments")
def list_persona_assignments(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(PersonaAssignment).filter(PersonaAssignment.tenant_id == admin.tenant_id).order_by(PersonaAssignment.user_id, PersonaAssignment.persona_code).all()
    return [{"id": str(row.id), "user_id": str(row.user_id), "tenant_id": str(row.tenant_id), "persona_code": row.persona_code, "status": row.status} for row in rows]


@router.get("/admin/identity/role-assignments")
def list_role_assignments(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(RoleAssignment).filter(RoleAssignment.tenant_id == admin.tenant_id).order_by(RoleAssignment.user_id).all()
    return [{"id": str(row.id), "user_id": str(row.user_id), "role_id": str(row.role_id), "tenant_id": str(row.tenant_id), "status": row.status} for row in rows]


@router.get("/admin/identity/role-permission-sets")
def list_role_permission_sets(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(RolePermissionSet).filter(RolePermissionSet.tenant_id == admin.tenant_id).all()
    return [{"id": str(row.id), "role_id": str(row.role_id), "permission_set_id": str(row.permission_set_id), "tenant_id": str(row.tenant_id)} for row in rows]


@router.patch("/admin/identity/roles/{role_id}/status")
def update_role_status(role_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(RoleDefinition).filter(RoleDefinition.id == role_id, RoleDefinition.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "ROLE_NOT_FOUND", "message": "Role is not available for this tenant"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "ROLE_STATUS_CHANGED", "RoleDefinition", row.id, row.version); db.commit(); return {"id": str(row.id), "status": row.status, "version": row.version}


@router.patch("/admin/identity/permission-sets/{permission_set_id}/status")
def update_permission_status(permission_set_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(PermissionSetDefinition).filter(PermissionSetDefinition.id == permission_set_id, PermissionSetDefinition.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "PERMISSION_SET_NOT_FOUND", "message": "Permission set is not available for this tenant"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "PERMISSION_SET_STATUS_CHANGED", "PermissionSetDefinition", row.id, row.version); db.commit(); return {"id": str(row.id), "status": row.status, "version": row.version}


@router.patch("/admin/identity/memberships/{membership_id}/status")
def update_membership_status(membership_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(TenantMembership).filter(TenantMembership.id == membership_id, TenantMembership.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "MEMBERSHIP_NOT_FOUND", "message": "Membership is not available for this tenant"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "MEMBERSHIP_STATUS_CHANGED", "TenantMembership", row.id, "v1"); db.commit(); return {"id": str(row.id), "status": row.status}


@router.patch("/admin/identity/persona-assignments/{assignment_id}/status")
def update_persona_status(assignment_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(PersonaAssignment).filter(PersonaAssignment.id == assignment_id, PersonaAssignment.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "PERSONA_ASSIGNMENT_NOT_FOUND", "message": "Persona assignment is not available for this tenant"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "PERSONA_ASSIGNMENT_STATUS_CHANGED", "PersonaAssignment", row.id, "v1"); db.commit(); return {"id": str(row.id), "status": row.status, "persona_code": row.persona_code}


@router.patch("/admin/identity/role-assignments/{assignment_id}/status")
def update_role_assignment_status(assignment_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(RoleAssignment).filter(RoleAssignment.id == assignment_id, RoleAssignment.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "ROLE_ASSIGNMENT_NOT_FOUND", "message": "Role assignment is not available for this tenant"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "ROLE_ASSIGNMENT_STATUS_CHANGED", "RoleAssignment", row.id, "v1"); db.commit(); return {"id": str(row.id), "status": row.status}


@router.get("/admin/identity/users/{user_id}/effective-access")
def user_effective_access(user_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    user = db.query(AuthUser).filter(AuthUser.id == user_id, AuthUser.tenant_id == admin.tenant_id).first()
    if user is None: raise HTTPException(404, detail={"code": "USER_NOT_FOUND", "message": "User is not available for this tenant"})
    assignments = db.query(RoleAssignment).filter(RoleAssignment.user_id == user.id, RoleAssignment.tenant_id == admin.tenant_id, RoleAssignment.status == "ACTIVE").all()
    roles = []
    for assignment in assignments:
        role = db.query(RoleDefinition).filter(RoleDefinition.id == assignment.role_id, RoleDefinition.tenant_id == admin.tenant_id).first()
        if role: roles.append({"id": str(role.id), "code": role.code, "name": role.name, "version": role.version, "status": role.status})
    personas = db.query(PersonaAssignment).filter(PersonaAssignment.user_id == user.id, PersonaAssignment.tenant_id == admin.tenant_id, PersonaAssignment.status == "ACTIVE").all()
    return {"user_id": str(user.id), "tenant_id": str(admin.tenant_id), "status": user.status, "roles": roles, "personas": [{"code": row.persona_code, "status": row.status} for row in personas]}


@router.get("/admin/governance/entitlements")
def tenant_entitlements(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(FeatureEntitlement).join(PlanDefinition, PlanDefinition.id == FeatureEntitlement.plan_id).join(TenantPlanAssignment, TenantPlanAssignment.plan_id == PlanDefinition.id).filter(TenantPlanAssignment.tenant_id == admin.tenant_id).all()
    return [{"feature": row.feature_code, "enabled": row.enabled, "limits": row.limits or {}, "plan_id": str(row.plan_id), "status": row.status} for row in rows]


@router.get("/admin/identity/roles/{role_id}/permission-sets")
def role_permission_detail(role_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    role = db.query(RoleDefinition).filter(RoleDefinition.id == role_id, RoleDefinition.tenant_id == admin.tenant_id).first()
    if role is None: raise HTTPException(404, detail={"code": "ROLE_NOT_FOUND", "message": "Role is not available for this tenant"})
    links = db.query(RolePermissionSet).filter(RolePermissionSet.role_id == role.id, RolePermissionSet.tenant_id == admin.tenant_id).all()
    result = []
    for link in links:
        row = db.query(PermissionSetDefinition).filter(PermissionSetDefinition.id == link.permission_set_id, PermissionSetDefinition.tenant_id == admin.tenant_id).first()
        if row: result.append({"id": str(row.id), "code": row.code, "version": row.version, "status": row.status, "object_permissions": row.object_permissions, "field_permissions": row.field_permissions, "action_permissions": row.action_permissions})
    return {"role_id": str(role.id), "role_code": role.code, "permission_sets": result}


@router.get("/admin/configuration/connectors/{code}/versions")
def connector_versions(code: str, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(ConnectorConfiguration).filter(ConnectorConfiguration.tenant_id == admin.tenant_id, ConnectorConfiguration.code == code).order_by(ConnectorConfiguration.version).all()
    return [{"id": str(row.id), "code": row.code, "connector_type": row.connector_type, "version": row.version, "status": row.status} for row in rows]


@router.get("/admin/configuration/mappings/{code}/versions")
def mapping_versions(code: str, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(MappingConfiguration).filter(MappingConfiguration.tenant_id == admin.tenant_id, MappingConfiguration.code == code).order_by(MappingConfiguration.version).all()
    return [{"id": str(row.id), "code": row.code, "source_system": row.source_system, "target_entity": row.target_entity, "version": row.version, "status": row.status} for row in rows]


@router.patch("/admin/control-plane/{resource}/{resource_id}")
def update_control_plane_resource(resource: str, resource_id: uuid.UUID, payload: AdminUpdateRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    resources = {
        "users": (AuthUser, {"display_name", "company", "role", "status"}, "USER_UPDATED"),
        "roles": (RoleDefinition, {"code", "name", "version", "status"}, "ROLE_UPDATED"),
        "permission-sets": (PermissionSetDefinition, {"code", "version", "status", "object_permissions", "field_permissions", "action_permissions"}, "PERMISSION_SET_UPDATED"),
        "connectors": (ConnectorConfiguration, {"code", "connector_type", "version", "status", "configuration"}, "CONNECTOR_UPDATED"),
        "mappings": (MappingConfiguration, {"code", "source_system", "target_entity", "version", "status", "mapping_rules"}, "MAPPING_UPDATED"),
        "approval-authorities": (ApprovalAuthority, {"role_name", "object_type", "decision_type", "authority", "version", "status"}, "APPROVAL_AUTHORITY_UPDATED"),
        "sod-policies": (SegregationOfDutiesPolicy, {"name", "object_type", "decision_type", "version", "status", "creator_cannot_approve", "last_material_editor_cannot_approve"}, "SOD_POLICY_UPDATED"),
        "persona-assignments": (PersonaAssignment, {"persona_code", "status"}, "PERSONA_ASSIGNMENT_UPDATED"),
    }
    item = resources.get(resource)
    if item is None: raise HTTPException(404, detail={"code": "RESOURCE_NOT_SUPPORTED", "message": "Administrator resource is not supported"})
    model, allowed_fields, action = item
    unknown = set(payload.values) - allowed_fields
    if unknown: raise HTTPException(422, detail={"code": "FIELD_NOT_ALLOWED", "message": "One or more fields cannot be edited"})
    row = db.query(model).filter(model.id == resource_id, model.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "RESOURCE_NOT_FOUND", "message": "Resource is not available for this tenant"})
    if resource == "connectors" and "configuration" in payload.values:
        try: payload.values["configuration"] = safe_configuration(payload.values["configuration"])
        except ValueError as exc: raise HTTPException(422, detail={"code": "SENSITIVE_CONFIGURATION_REJECTED", "message": "Secrets must use a managed secret provider"}) from exc
    if resource == "persona-assignments" and "persona_code" in payload.values:
        try: payload.values["persona_code"] = get_persona(payload.values["persona_code"]).code
        except ValueError as exc: raise HTTPException(422, detail={"code": "UNKNOWN_PERSONA", "message": "Persona is not in the R1 catalog"}) from exc
    for field, value in payload.values.items(): setattr(row, field, value)
    if hasattr(row, "updated_at"): row.updated_at = datetime.now(timezone.utc)
    version = getattr(row, "version", "v1"); _audit_configuration(db, admin, action, model.__name__, row.id, version); db.commit()
    return {"id": str(row.id), "resource": resource, "status": getattr(row, "status", "ACTIVE"), "version": version}


@router.post("/admin/catalog/products")
def create_product(payload: ProductRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); now = datetime.now(timezone.utc)
    if db.query(Product).filter(Product.tenant_id == admin.tenant_id, Product.product_identifier == payload.product_identifier).first():
        raise HTTPException(409, detail={"code": "PRODUCT_EXISTS", "message": "Product identifier already exists for this tenant"})
    row = Product(id=uuid.uuid4(), tenant_id=admin.tenant_id, product_identifier=payload.product_identifier, name=payload.name, description=payload.description, product_family=payload.product_family, manufacturer_context=payload.manufacturer_context, lifecycle_status="active", created_at=now, updated_at=now)
    db.add(row); _audit_configuration(db, admin, "PRODUCT_CREATED", "Product", row.id, "v1"); db.commit(); return {"id": str(row.id), "product_identifier": row.product_identifier, "name": row.name, "tenant_id": str(row.tenant_id)}


@router.post("/admin/catalog/product-versions")
def create_product_version(payload: ProductVersionRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); now = datetime.now(timezone.utc)
    product = db.query(Product).filter(Product.id == payload.product_id, Product.tenant_id == admin.tenant_id).first()
    if product is None: raise HTTPException(404, detail={"code": "PRODUCT_NOT_FOUND", "message": "Product is not available for this tenant"})
    if db.query(ProductVersion).filter(ProductVersion.tenant_id == admin.tenant_id, ProductVersion.product_id == product.id, ProductVersion.version_identifier == payload.version_identifier).first():
        raise HTTPException(409, detail={"code": "PRODUCT_VERSION_EXISTS", "message": "ProductVersion already exists"})
    release_timestamp = datetime.fromisoformat(payload.release_timestamp.replace("Z", "+00:00")) if payload.release_timestamp else None
    row = ProductVersion(id=uuid.uuid4(), tenant_id=admin.tenant_id, product_id=product.id, version_identifier=payload.version_identifier, description=payload.description, lifecycle_status="active", release_timestamp=release_timestamp, created_at=now, updated_at=now)
    db.add(row); _audit_configuration(db, admin, "PRODUCT_VERSION_CREATED", "ProductVersion", row.id, "v1"); db.commit(); return {"id": str(row.id), "product_id": str(row.product_id), "version_identifier": row.version_identifier, "tenant_id": str(row.tenant_id)}


@router.patch("/admin/catalog/products/{product_id}")
def update_product(product_id: uuid.UUID, payload: AdminUpdateRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); allowed = {"product_identifier", "name", "description", "product_family", "manufacturer_context", "lifecycle_status"}
    if set(payload.values) - allowed: raise HTTPException(422, detail={"code": "FIELD_NOT_ALLOWED", "message": "Product field cannot be edited"})
    row = db.query(Product).filter(Product.id == product_id, Product.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "PRODUCT_NOT_FOUND", "message": "Product is not available for this tenant"})
    for field, value in payload.values.items(): setattr(row, field, value)
    row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "PRODUCT_UPDATED", "Product", row.id, "v1"); db.commit(); return {"id": str(row.id), "status": row.lifecycle_status}


@router.patch("/admin/catalog/product-versions/{version_id}")
def update_product_version(version_id: uuid.UUID, payload: AdminUpdateRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); allowed = {"version_identifier", "description", "lifecycle_status", "release_timestamp"}
    if set(payload.values) - allowed: raise HTTPException(422, detail={"code": "FIELD_NOT_ALLOWED", "message": "ProductVersion field cannot be edited"})
    row = db.query(ProductVersion).filter(ProductVersion.id == version_id, ProductVersion.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "PRODUCT_VERSION_NOT_FOUND", "message": "ProductVersion is not available for this tenant"})
    if "release_timestamp" in payload.values and payload.values["release_timestamp"]: payload.values["release_timestamp"] = datetime.fromisoformat(str(payload.values["release_timestamp"]).replace("Z", "+00:00"))
    for field, value in payload.values.items(): setattr(row, field, value)
    row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "PRODUCT_VERSION_UPDATED", "ProductVersion", row.id, "v1"); db.commit(); return {"id": str(row.id), "status": row.lifecycle_status}


@router.patch("/admin/catalog/products/{product_id}/lifecycle")
def update_product_lifecycle(product_id: uuid.UUID, payload: LifecycleRequest, request: Request, db: Session = Depends(get_db)):
    return update_product(product_id, AdminUpdateRequest(values={"lifecycle_status": payload.lifecycle_status}), request, db)


@router.patch("/admin/catalog/product-versions/{version_id}/lifecycle")
def update_product_version_lifecycle(version_id: uuid.UUID, payload: LifecycleRequest, request: Request, db: Session = Depends(get_db)):
    return update_product_version(version_id, AdminUpdateRequest(values={"lifecycle_status": payload.lifecycle_status}), request, db)


@router.post("/admin/configuration/connectors/{configuration_id}/test")
def test_connector(configuration_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(ConnectorConfiguration).filter(ConnectorConfiguration.id == configuration_id, ConnectorConfiguration.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "CONNECTOR_NOT_FOUND", "message": "Connector is not available for this tenant"})
    result = Connector(ConnectionConfig(str(admin.tenant_id), str(row.id), row.code, row.connector_type, "CONFIGURED")).test_connection(); _audit_configuration(db, admin, "CONNECTOR_TEST_EXECUTED", "ConnectorConfiguration", row.id, row.version); db.commit(); return result


@router.post("/admin/configuration/connectors/{configuration_id}/execute")
def execute_connector(configuration_id: uuid.UUID, payload: ConnectorRunRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(ConnectorConfiguration).filter(ConnectorConfiguration.id == configuration_id, ConnectorConfiguration.tenant_id == admin.tenant_id, ConnectorConfiguration.status == "ACTIVE").first()
    if row is None: raise HTTPException(404, detail={"code": "ACTIVE_CONNECTOR_NOT_FOUND", "message": "Active connector is not available for this tenant"})
    connector = Connector(ConnectionConfig(str(admin.tenant_id), str(row.id), row.code, row.connector_type, payload.source_system), payload.records); result = connector.read_records(); _audit_configuration(db, admin, "CONNECTOR_EXECUTED", "ConnectorConfiguration", row.id, row.version); db.commit(); return {"status": "COMPLETE", "tenant_id": str(admin.tenant_id), "connector_id": str(row.id), "records_read": len(result), "records": result}


@router.post("/admin/configuration/mappings/{configuration_id}/preview")
def preview_mapping(configuration_id: uuid.UUID, payload: MappingPreviewRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(MappingConfiguration).filter(MappingConfiguration.id == configuration_id, MappingConfiguration.tenant_id == admin.tenant_id, MappingConfiguration.status == "ACTIVE").first()
    if row is None: raise HTTPException(404, detail={"code": "ACTIVE_MAPPING_NOT_FOUND", "message": "Active mapping is not available for this tenant"})
    result = preview(payload.records, MappingDefinition(payload.source_object, payload.target_entity, payload.mapping_version, payload.rules)); _audit_configuration(db, admin, "MAPPING_PREVIEW_EXECUTED", "MappingConfiguration", row.id, row.version); db.commit(); return {"tenant_id": str(admin.tenant_id), "mapping_id": str(row.id), "preview": result}


@router.post("/admin/catalog/master-mappings")
def create_master_mapping(payload: MasterMappingRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    if db.query(MasterMapping).filter(MasterMapping.code == payload.code).first(): raise HTTPException(409, detail={"code": "MASTER_MAPPING_EXISTS", "message": "Master mapping code already exists"})
    now = datetime.now(timezone.utc); row = MasterMapping(id=uuid.uuid4(), code=payload.code, source_system=payload.source_system, target_entity=payload.target_entity, definition=payload.definition, status="ACTIVE", created_at=now, updated_at=now)
    db.add(row); _audit_configuration(db, admin, "MASTER_MAPPING_CREATED", "MasterMapping", row.id, "v1"); db.commit(); return {"id": str(row.id), "code": row.code, "source_system": row.source_system, "target_entity": row.target_entity, "status": row.status}


@router.get("/admin/catalog/master-mappings")
def list_master_mappings(request: Request, db: Session = Depends(get_db)):
    _admin_tenant(request, db); rows = db.query(MasterMapping).filter(MasterMapping.status == "ACTIVE").order_by(MasterMapping.code).all()
    return [{"id": str(row.id), "code": row.code, "source_system": row.source_system, "target_entity": row.target_entity, "definition": row.definition, "status": row.status} for row in rows]


@router.post("/admin/catalog/mapping-versions")
def create_mapping_version(payload: MappingVersionRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); master = db.query(MasterMapping).filter(MasterMapping.id == payload.master_mapping_id, MasterMapping.status == "ACTIVE").first()
    if master is None: raise HTTPException(404, detail={"code": "MASTER_MAPPING_NOT_FOUND", "message": "Master mapping is not available"})
    if db.query(TenantMappingVersion).filter_by(tenant_id=admin.tenant_id, master_mapping_id=master.id, version=payload.version).first(): raise HTTPException(409, detail={"code": "MAPPING_VERSION_EXISTS", "message": "Mapping version already exists"})
    now = datetime.now(timezone.utc); effective = datetime.fromisoformat(payload.effective_from.replace("Z", "+00:00")) if payload.effective_from else now
    row = TenantMappingVersion(id=uuid.uuid4(), tenant_id=admin.tenant_id, master_mapping_id=master.id, version=payload.version, rules=payload.rules, status="DRAFT", effective_from=effective, created_at=now, updated_at=now)
    db.add(row); _audit_configuration(db, admin, "TENANT_MAPPING_VERSION_CREATED", "TenantMappingVersion", row.id, row.version); db.commit(); return {"id": str(row.id), "master_mapping_id": str(row.master_mapping_id), "version": row.version, "status": row.status}


@router.post("/admin/catalog/mapping-overrides")
def create_mapping_override(payload: MappingOverrideRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); version = db.query(TenantMappingVersion).filter(TenantMappingVersion.id == payload.mapping_version_id, TenantMappingVersion.tenant_id == admin.tenant_id).first()
    if version is None: raise HTTPException(404, detail={"code": "MAPPING_VERSION_NOT_FOUND", "message": "Mapping version is not available for this tenant"})
    row = TenantMappingOverride(id=uuid.uuid4(), tenant_id=admin.tenant_id, mapping_version_id=version.id, field_name=payload.field_name, override_rule=payload.override_rule, status="ACTIVE", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)); db.add(row); _audit_configuration(db, admin, "TENANT_MAPPING_OVERRIDE_CREATED", "TenantMappingOverride", row.id, version.version); db.commit(); return {"id": str(row.id), "mapping_version_id": str(row.mapping_version_id), "field_name": row.field_name, "status": row.status}


@router.get("/admin/catalog/mapping-versions")
def list_mapping_versions(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); rows = db.query(TenantMappingVersion).filter(TenantMappingVersion.tenant_id == admin.tenant_id).order_by(TenantMappingVersion.created_at.desc()).all()
    return [{"id": str(row.id), "master_mapping_id": str(row.master_mapping_id), "version": row.version, "rules": row.rules, "status": row.status, "effective_from": row.effective_from} for row in rows]


@router.patch("/admin/catalog/master-mappings/{mapping_id}/status")
def update_master_mapping_status(mapping_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(MasterMapping).filter(MasterMapping.id == mapping_id).first()
    if row is None: raise HTTPException(404, detail={"code": "MASTER_MAPPING_NOT_FOUND", "message": "Master mapping is not available"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "MASTER_MAPPING_STATUS_CHANGED", "MasterMapping", row.id, "v1"); db.commit(); return {"id": str(row.id), "status": row.status}


@router.patch("/admin/catalog/mapping-versions/{version_id}/status")
def update_mapping_version_status(version_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(TenantMappingVersion).filter(TenantMappingVersion.id == version_id, TenantMappingVersion.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "MAPPING_VERSION_NOT_FOUND", "message": "Mapping version is not available for this tenant"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "TENANT_MAPPING_VERSION_STATUS_CHANGED", "TenantMappingVersion", row.id, row.version); db.commit(); return {"id": str(row.id), "version": row.version, "status": row.status}


@router.patch("/admin/catalog/mapping-overrides/{override_id}")
def update_mapping_override(override_id: uuid.UUID, payload: AdminUpdateRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); allowed = {"field_name", "override_rule", "status"}; unknown = set(payload.values) - allowed
    if unknown: raise HTTPException(422, detail={"code": "FIELD_NOT_ALLOWED", "message": "Only field_name, override_rule, and status can be edited"})
    row = db.query(TenantMappingOverride).filter(TenantMappingOverride.id == override_id, TenantMappingOverride.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "MAPPING_OVERRIDE_NOT_FOUND", "message": "Mapping override is not available for this tenant"})
    for field, value in payload.values.items(): setattr(row, field, value)
    row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "TENANT_MAPPING_OVERRIDE_UPDATED", "TenantMappingOverride", row.id, "v1"); db.commit(); return {"id": str(row.id), "field_name": row.field_name, "status": row.status}


@router.get("/admin/identity/roles")
def list_roles(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(RoleDefinition).filter(RoleDefinition.tenant_id == admin.tenant_id).order_by(RoleDefinition.code, RoleDefinition.version).all()
    return [{"id": str(row.id), "code": row.code, "name": row.name, "version": row.version, "status": row.status} for row in rows]


@router.get("/admin/identity/permission-sets")
def list_permission_sets(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(PermissionSetDefinition).filter(PermissionSetDefinition.tenant_id == admin.tenant_id).order_by(PermissionSetDefinition.code, PermissionSetDefinition.version).all()
    return [{"id": str(row.id), "code": row.code, "version": row.version, "status": row.status, "object_permissions": row.object_permissions, "field_permissions": row.field_permissions, "action_permissions": row.action_permissions} for row in rows]


@router.get("/admin/identity/memberships")
def list_memberships(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(TenantMembership).filter(TenantMembership.tenant_id == admin.tenant_id).all()
    return [{"id": str(row.id), "user_id": str(row.user_id), "tenant_id": str(row.tenant_id), "status": row.status, "is_default": row.is_default} for row in rows]


@router.patch("/admin/configuration/mappings/{configuration_id}/status")
def activate_mapping(configuration_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(MappingConfiguration).filter(MappingConfiguration.id == configuration_id, MappingConfiguration.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "MAPPING_NOT_FOUND", "message": "Mapping configuration is not available for this tenant"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "MAPPING_CONFIGURATION_STATUS_CHANGED", "MappingConfiguration", row.id, row.version); db.commit()
    return {"id": str(row.id), "status": row.status, "version": row.version}


@router.patch("/admin/governance/policies/{policy_type}/{policy_id}/status")
def activate_policy(policy_type: str, policy_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    model, entity = ({"authority": (ApprovalAuthority, "ApprovalAuthority"), "sod": (SegregationOfDutiesPolicy, "SegregationOfDutiesPolicy")}).get(policy_type, (None, None))
    if model is None: raise HTTPException(422, detail={"code": "POLICY_TYPE_INVALID", "message": "Policy type must be authority or sod"})
    row = db.query(model).filter(model.id == policy_id, model.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "POLICY_NOT_FOUND", "message": "Policy is not available for this tenant"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "GOVERNANCE_POLICY_STATUS_CHANGED", entity, row.id, row.version); db.commit()
    return {"id": str(row.id), "policy_type": policy_type, "status": row.status, "version": row.version}
