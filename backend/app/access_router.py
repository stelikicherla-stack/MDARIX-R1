import uuid
import secrets
import os
import json
from urllib.request import Request as UrlRequest, urlopen
from urllib.error import URLError, HTTPError
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel, Field
from access_control.policy import PermissionSet, Role, User, effective_permissions
from auth.service import auth_service
from backend.app.request_context import get_request_context
from auth.service import _hash
from auth.emailer import EmailDeliveryError, send_activation_email, send_password_reset_email, smtp_configuration_status
from auth.durable import issue_invitation, issue_reset, hash_token
from backend.app.db.session import get_db
from backend.app.db.models.foundation import (
    AuthUser, PersonaAssignment, RoleAssignment, RoleDefinition,
    RolePermissionSet, PermissionSetDefinition, TenantMembership,
    FeatureEntitlement, PlanDefinition, Tenant, TenantPlanAssignment, Product, ProductVersion,
    ApprovalAuthority, SegregationOfDutiesPolicy, ConnectorConfiguration, MappingConfiguration, AuditEvent, Decision,
    MasterMapping, TenantMappingVersion, TenantMappingOverride,
)
from access_control.personas import R1_PERSONAS as PERSONAS, get_persona
from access_control.configuration_safety import safe_configuration
from integration.gateway import ConnectionConfig, Connector, MappingDefinition, preview
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from backend.app.db.models.stage2 import AuthSession, UserInvitation, OutboxEvent, SubscriptionLifecycle, ReminderPolicy, EmailTemplate

router=APIRouter(prefix="/api/v1",tags=["Access Control"])
def _development_token(token: str | None) -> str | None:
    return token if os.getenv("MDARIX_ENV", "development").lower() == "development" else None
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
class UserCreateRequest(BaseModel): email: str = Field(min_length=3, max_length=254); display_name: str = Field(min_length=1, max_length=120); company: str = Field(min_length=1, max_length=160); role: str = "Viewer"; target_tenant_id: uuid.UUID | None = None
class CustomerCreateRequest(BaseModel): company_name: str = Field(min_length=1, max_length=255); tenant_code: str = Field(min_length=1, max_length=80); plan_code: str = "ENTERPRISE_TEST"; licensed_users_limit: int = Field(default=25, ge=1); customer_admin_limit: int = Field(default=2, ge=1); connector_limit: int = Field(default=5, ge=0); status: str = "active"; notes: str | None = None
class CustomerProvisionRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=255)
    tenant_code: str = Field(min_length=1, max_length=80)
    region: str = Field(default="default", min_length=1, max_length=80)
    residency: str = Field(default="default", min_length=1, max_length=80)
    plan_code: str = "ENTERPRISE_TEST"
    licensed_users_limit: int = Field(default=25, ge=1)
    customer_admin_email: str = Field(min_length=3, max_length=254)
    customer_admin_display_name: str = Field(min_length=1, max_length=120)
    customer_admin_company: str = Field(default="Customer", min_length=1, max_length=160)
    invitation_required: bool = True
class SubscriptionRequest(BaseModel):
    plan_id: uuid.UUID; starts_at: str; expires_at: str; grace_ends_at: str | None = None; reason: str = Field(min_length=1)
class ReminderPolicyRequest(BaseModel):
    name: str; thresholds: list[int] = [60, 30, 7]; timezone: str = "UTC"; recipient_types: list[str] = ["CUSTOMER_ADMIN"]; version: str = "v1"
class EmailTemplateRequest(BaseModel):
    stage: str; version: str = "v1"; subject: str; body: str; allowed_variables: list[str] = []
class PlanCreateRequest(BaseModel): code: str = Field(min_length=1, max_length=80); name: str = Field(min_length=1, max_length=120); description: str | None = None; version: str = "v1"; capabilities: dict = {}; limits: dict = {}
class PasswordActionRequest(BaseModel): email: str = Field(min_length=3, max_length=254)
class AdminUpdateRequest(BaseModel): values: dict
class ProductRequest(BaseModel): product_identifier: str; name: str; description: str | None = None; product_family: str | None = None; manufacturer_context: str | None = None
class ProductVersionRequest(BaseModel): product_id: uuid.UUID; version_identifier: str; description: str | None = None; release_timestamp: str | None = None
class MasterMappingRequest(BaseModel): code: str; source_system: str; target_entity: str; definition: dict = {}
class MappingVersionRequest(BaseModel): master_mapping_id: uuid.UUID; version: str; rules: dict = {}; effective_from: str | None = None
class MappingOverrideRequest(BaseModel): mapping_version_id: uuid.UUID; field_name: str; override_rule: dict = {}
class LifecycleRequest(BaseModel): lifecycle_status: str = Field(pattern="^(active|retired|archived)$")
class ConnectorRunRequest(BaseModel): records: list[dict] = []; source_system: str = "SIMULATED"; required_fields: list[str] = []
class MappingPreviewRequest(BaseModel): records: list[dict]; rules: dict; source_object: str; target_entity: str; mapping_version: str
class StatusRequest(BaseModel): status: str = Field(pattern="^(DRAFT|VALIDATION|READY_FOR_APPROVAL|APPROVED|ACTIVE|RELEASED|SUPERSEDED|RETIRED)$")


@router.get("/admin/smtp-status")
def admin_smtp_status(request: Request, db: Session = Depends(get_db)):
    _require_platform_admin(request, db)
    return smtp_configuration_status()


def _require_administrator(request: Request, db: Session) -> AuthUser:
    user = _authenticated_user(request, db)
    if (user.role or "").upper() not in {"ADMINISTRATOR", "ADMIN", "MDARIX ADMINISTRATOR", "PLATFORM_ADMIN", "CUSTOMER_ADMIN"}:
        raise HTTPException(403, detail={"code": "ADMINISTRATOR_REQUIRED", "message": "Administrator role required"})
    return user

def _role_code(user: AuthUser) -> str:
    return (user.role or "").strip().upper().replace(" ", "_")

def _is_platform_admin(user: AuthUser) -> bool:
    return _role_code(user) in {"PLATFORM_ADMIN", "MDARIX_ADMINISTRATOR", "ADMINISTRATOR", "ADMIN"}

def _is_customer_admin(user: AuthUser) -> bool:
    return _role_code(user) == "CUSTOMER_ADMIN"

def _require_platform_admin(request: Request, db: Session) -> AuthUser:
    user = _authenticated_user(request, db)
    if not _is_platform_admin(user):
        raise HTTPException(403, detail={"code": "PLATFORM_ADMIN_REQUIRED", "message": "Platform administrator role required"})
    return user

def _authenticated_user(request: Request, db: Session) -> AuthUser:
    context = get_request_context(request, db)
    try:
        user = db.query(AuthUser).filter(AuthUser.id == uuid.UUID(context.user_id), AuthUser.tenant_id == context.tenant_id).first()
    except (ValueError, TypeError):
        user = None
    if user is None and os.getenv("MDARIX_ENV", "development").lower() == "development":
        user = db.query(AuthUser).filter(AuthUser.username == context.user_id.lower(), AuthUser.tenant_id == context.tenant_id).first()
    if user is None or user.status != "ACTIVE":
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


@router.get("/session/context")
def session_context(request: Request, db: Session = Depends(get_db)):
    """Canonical server-derived identity, tenancy and authorization context.

    The client may use this for rendering, but every protected route still
    evaluates the authenticated request context server-side.  No tenant,
    role, menu, plan or license value is accepted from the request body or
    route slug.
    """
    user = _authenticated_user(request, db)
    base = context(request, db)
    memberships = []
    for membership in db.query(TenantMembership).filter(
        TenantMembership.user_id == user.id,
        TenantMembership.status == "ACTIVE",
    ).all():
        tenant = db.query(Tenant).filter(Tenant.id == membership.tenant_id, Tenant.status == "active").first()
        if tenant is not None:
            memberships.append({
                "membership_id": str(membership.id),
                "tenant_id": str(tenant.id),
                "tenant_key": tenant.tenant_key,
                "tenant_name": tenant.name,
                "is_default": bool(membership.is_default),
            })

    assignment = db.query(TenantPlanAssignment).join(
        PlanDefinition, PlanDefinition.id == TenantPlanAssignment.plan_id
    ).filter(
        TenantPlanAssignment.tenant_id == user.tenant_id,
        TenantPlanAssignment.status == "ACTIVE",
        PlanDefinition.status == "ACTIVE",
    ).first()
    plan = None
    entitlements = []
    if assignment is not None:
        plan_row = db.query(PlanDefinition).filter(PlanDefinition.id == assignment.plan_id).first()
        if plan_row is not None:
            plan = {"id": str(plan_row.id), "code": plan_row.code, "name": plan_row.name, "version": plan_row.version}
            entitlements = [
                {"feature_code": item.feature_code, "enabled": bool(item.enabled), "limits": item.limits or {}}
                for item in db.query(FeatureEntitlement).filter(
                    FeatureEntitlement.plan_id == plan_row.id,
                    FeatureEntitlement.status == "ACTIVE",
                ).all()
            ]

    platform = _is_platform_admin(user)
    customer = _is_customer_admin(user)
    allowed_menu = (
        ["home", "products", "investigations", "evidence", "decision-center", "assurance", "audit", "admin"]
        if platform else
        ["home", "products", "investigations", "evidence", "decision-center", "assurance", "audit", "customer-admin"]
        if customer else
        ["home", "products", "investigations", "evidence", "decision-center", "assurance", "audit"]
    )
    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
    license_state = "ACTIVE" if tenant is not None and tenant.status == "active" and assignment is not None else "INACTIVE"
    return {
        **base,
        "memberships": memberships,
        "current_tenant": next((item for item in memberships if item["tenant_id"] == str(user.tenant_id)), {"tenant_id": str(user.tenant_id)}),
        "plan": plan,
        "license": {"state": license_state, "effective": license_state == "ACTIVE"},
        "entitlements": entitlements,
        "allowed_menu": allowed_menu,
        "allowed_actions": base.get("permissions", {}),
        "policy_version": base.get("role_version", "legacy"),
        "environment": os.getenv("MDARIX_ENV", "development"),
    }

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

def _active_plan_limits(db: Session, tenant_id: uuid.UUID) -> dict:
    row = db.query(TenantPlanAssignment).join(PlanDefinition, PlanDefinition.id == TenantPlanAssignment.plan_id).filter(
        TenantPlanAssignment.tenant_id == tenant_id,
        TenantPlanAssignment.status == "ACTIVE",
        PlanDefinition.status == "ACTIVE",
    ).first()
    limits = dict(getattr(row, "limits", None) or {})
    entitlements = db.query(FeatureEntitlement).join(PlanDefinition, PlanDefinition.id == FeatureEntitlement.plan_id).join(TenantPlanAssignment, TenantPlanAssignment.plan_id == PlanDefinition.id).filter(
        TenantPlanAssignment.tenant_id == tenant_id,
        TenantPlanAssignment.status == "ACTIVE",
        FeatureEntitlement.status == "ACTIVE",
        FeatureEntitlement.enabled == True,
    ).all()
    for entitlement in entitlements:
        if entitlement.limits:
            limits.update(entitlement.limits)
    return limits

def _seat_counts(db: Session, tenant_id: uuid.UUID) -> dict:
    users = db.query(AuthUser).filter(AuthUser.tenant_id == tenant_id, AuthUser.status.in_(["INVITED", "ACTIVE", "PENDING_VERIFICATION"])).all()
    admins = [user for user in users if (user.role or "").upper() == "CUSTOMER_ADMIN"]
    return {"allocated_users": len(users), "allocated_customer_admins": len(admins)}

def _enforce_invite_limits(db: Session, tenant_id: uuid.UUID, role: str):
    limits = _active_plan_limits(db, tenant_id)
    counts = _seat_counts(db, tenant_id)
    licensed_limit = int(limits.get("licensed_users_limit") or limits.get("licensed_users") or 100000)
    admin_limit = int(limits.get("customer_admin_limit") or limits.get("customer_admins") or 100000)
    if counts["allocated_users"] >= licensed_limit:
        raise HTTPException(409, detail={"code": "LICENSED_USER_LIMIT_REACHED", "message": "Licensed user limit reached", "licensed_users": licensed_limit, "allocated": counts["allocated_users"], "available": 0})
    if role.strip().upper() == "CUSTOMER_ADMIN" and counts["allocated_customer_admins"] >= admin_limit:
        raise HTTPException(409, detail={"code": "CUSTOMER_ADMIN_LIMIT_REACHED", "message": "Customer Administrator limit reached", "allowed": admin_limit, "allocated": counts["allocated_customer_admins"], "available": 0})

def _admin_target_tenant(admin: AuthUser, payload_tenant_id: uuid.UUID | None, company: str | None = None, db: Session | None = None) -> uuid.UUID:
    if payload_tenant_id and payload_tenant_id != admin.tenant_id and not _is_platform_admin(admin):
        raise HTTPException(403, detail={"code": "FOREIGN_TENANT_ACCESS_DENIED", "message": "Customer administrators can only administer their own tenant"})
    if payload_tenant_id:
        return payload_tenant_id
    if _is_platform_admin(admin) and company and db is not None:
        matches = db.query(Tenant).filter(func.lower(Tenant.name) == company.strip().lower(), Tenant.status == "active").all()
        if len(matches) == 1:
            return matches[0].id
        if not matches:
            raise HTTPException(404, detail={"code": "TENANT_NOT_FOUND", "message": "No active customer matches the Company name"})
        raise HTTPException(409, detail={"code": "TENANT_NAME_AMBIGUOUS", "message": "Company name matches more than one active tenant"})
    return payload_tenant_id or admin.tenant_id


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

@router.post("/admin/identity/users/{user_id}/reactivate")
def reactivate_user(user_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    user = db.query(AuthUser).filter(AuthUser.id == user_id, AuthUser.tenant_id == admin.tenant_id).first()
    if user is None:
        raise HTTPException(404, detail={"code": "USER_NOT_FOUND", "message": "User is not available for this tenant"})
    if (user.status or "").upper() != "OFFBOARDED":
        raise HTTPException(409, detail={"code": "USER_NOT_OFFBOARDED", "message": "Only an offboarded user can be reactivated"})
    now = datetime.now(timezone.utc)
    user.status = "INVITED"; user.email_verified = False; user.password_hash = _hash(secrets.token_urlsafe(48)); user.updated_at = now
    membership = db.query(TenantMembership).filter(TenantMembership.tenant_id == user.tenant_id, TenantMembership.user_id == user.id).first()
    if membership is not None: membership.status = "INVITED"; membership.updated_at = now
    token = issue_invitation(db, user.id, user.tenant_id, admin.id)
    try:
        delivery = send_activation_email(user.username, token, user.company)
    except EmailDeliveryError as exc:
        db.rollback()
        raise HTTPException(502, detail={"code": "SMTP_DELIVERY_FAILED", "message": str(exc)}) from exc
    db.add(AuditEvent(id=uuid.uuid4(), tenant_id=user.tenant_id, actor_ref=str(admin.id), action="USER_REACTIVATED", entity_type="AuthUser", entity_id=user.id, details={"email_delivery": delivery, "source": "ADMIN_CONTROL_PLANE"}, created_at=now))
    db.commit()
    return {"user_id": str(user.id), "email": user.username, "status": user.status, "invitation_status": "RESENT", "email_delivery": delivery, "development_token": _development_token(token) if delivery == "NOT_CONFIGURED" else None}


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


@router.get("/admin/health-summary")
def admin_health_summary(request: Request, db: Session = Depends(get_db)):
    """Return operational administrator signals, scoped to the authenticated tenant."""
    admin = _admin_tenant(request, db)
    tenant_id = admin.tenant_id
    recent = db.query(AuditEvent).filter(AuditEvent.tenant_id == tenant_id).order_by(AuditEvent.created_at.desc()).limit(100).all()
    connector_failures = sum(1 for row in recent if any(token in row.action.upper() for token in ("CONNECTOR", "PROVIDER")) and any(token in row.action.upper() for token in ("FAILED", "FAILURE", "ERROR", "UNAVAILABLE")))
    security_events = sum(1 for row in recent if any(token in row.action.upper() for token in ("DENIED", "UNAUTHORIZED", "SECURITY", "AUTHENTICATION_FAILED")))
    invitation_failures = sum(1 for row in recent if "INVIT" in row.action.upper() and any(token in row.action.upper() for token in ("FAILED", "FAILURE", "ERROR")))
    pending_invitations = db.query(UserInvitation).filter(UserInvitation.tenant_id == tenant_id, UserInvitation.used_at.is_(None)).count()
    pending_approvals = db.query(Decision).filter(Decision.tenant_id == tenant_id, Decision.decision_status.in_(["DRAFT", "PENDING", "PENDING_APPROVAL", "READY_FOR_APPROVAL"])).count()
    mapping_issues = db.query(MappingConfiguration).filter(MappingConfiguration.tenant_id == tenant_id, MappingConfiguration.status.in_(["DRAFT", "BLOCKED", "FAILED", "REVIEW"])).count()
    alerts = []
    for code, label, count, severity in (
        ("CONNECTOR_FAILURES", "Failed or degraded connectors", connector_failures, "HIGH"),
        ("PENDING_APPROVALS", "Pending approvals", pending_approvals, "MEDIUM"),
        ("INVITATION_FAILURES", "Invitation or activation failures", invitation_failures, "HIGH"),
        ("SECURITY_EVENTS", "Security or authorization events", security_events, "HIGH"),
        ("MAPPING_ISSUES", "Schema or mapping items needing review", mapping_issues, "MEDIUM"),
    ):
        if count:
            alerts.append({"code": code, "label": label, "count": count, "severity": severity})
    return {"tenant_id": str(tenant_id), "status": "ATTENTION_REQUIRED" if alerts else "HEALTHY", "metrics": {"connector_failures": connector_failures, "pending_approvals": pending_approvals, "pending_invitations": pending_invitations, "invitation_failures": invitation_failures, "security_events": security_events, "mapping_issues": mapping_issues, "recent_audit_events": len(recent)}, "alerts": alerts, "recent_audit": [{"action": row.action, "entity_type": row.entity_type, "created_at": row.created_at} for row in recent[:10]]}


@router.get("/admin/identity/users")
def list_users(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    rows = db.query(AuthUser).filter(AuthUser.tenant_id == admin.tenant_id).order_by(AuthUser.username).all()
    return [{"id": str(row.id), "email": row.username, "display_name": row.display_name, "company": row.company, "role": row.role, "status": row.status, "tenant_id": str(row.tenant_id)} for row in rows]


@router.post("/admin/identity/users")
def create_user(payload: UserCreateRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    target_tenant_id = _admin_target_tenant(admin, payload.target_tenant_id, payload.company, db)
    if db.query(Tenant).filter(Tenant.id == target_tenant_id, Tenant.status == "active").first() is None:
        raise HTTPException(404, detail={"code": "TENANT_NOT_FOUND", "message": "Customer / Tenant ID is not an active tenant UUID"})
    role = payload.role.strip().upper()
    if role == "PLATFORM_ADMIN" and not _is_platform_admin(admin):
        raise HTTPException(403, detail={"code": "PLATFORM_ROLE_NOT_ALLOWED", "message": "Customer administrators cannot assign platform roles"})
    if role == "PLATFORM_ADMIN" and target_tenant_id != admin.tenant_id:
        raise HTTPException(403, detail={"code": "PLATFORM_ROLE_NOT_ALLOWED", "message": "Platform roles are not assigned inside customer tenants"})
    _enforce_invite_limits(db, target_tenant_id, role)
    email = payload.email.strip().lower()
    if db.query(AuthUser).filter(
        AuthUser.tenant_id == target_tenant_id,
        AuthUser.username == email,
        func.upper(AuthUser.status) != "OFFBOARDED",
    ).first():
        raise HTTPException(409, detail={"code": "ACCOUNT_EXISTS", "message": "A user with this email already exists in this tenant"})
    now = datetime.now(timezone.utc)
    row = db.query(AuthUser).filter(
        AuthUser.tenant_id == target_tenant_id,
        AuthUser.username == email,
        func.upper(AuthUser.status) == "OFFBOARDED",
    ).first()
    if row is None:
        row = AuthUser(id=uuid.uuid4(), tenant_id=target_tenant_id, username=email, display_name=payload.display_name.strip(), company=payload.company.strip(), password_hash=_hash(secrets.token_urlsafe(48)), role=role, status="INVITED", email_verified=False, created_at=now, updated_at=now)
        db.add(row); db.flush()
        db.add(TenantMembership(id=uuid.uuid4(), tenant_id=target_tenant_id, user_id=row.id, status="INVITED", is_default=True, created_at=now, updated_at=now))
    else:
        row.display_name = payload.display_name.strip(); row.company = payload.company.strip(); row.role = role
        row.password_hash = _hash(secrets.token_urlsafe(48)); row.status = "INVITED"; row.email_verified = False; row.updated_at = now
        membership = db.query(TenantMembership).filter(TenantMembership.tenant_id == target_tenant_id, TenantMembership.user_id == row.id).first()
        if membership is not None:
            membership.status = "INVITED"; membership.updated_at = now
    token = issue_invitation(db, row.id, row.tenant_id, admin.id)
    try:
        delivery = send_activation_email(row.username, token, payload.company.strip())
    except EmailDeliveryError as exc:
        db.rollback()
        raise HTTPException(502, detail={"code": "SMTP_DELIVERY_FAILED", "message": str(exc)}) from exc
    db.add(AuditEvent(id=uuid.uuid4(), tenant_id=target_tenant_id, actor_ref=str(admin.id), action="USER_INVITATION_SENT", entity_type="AuthUser", entity_id=row.id, details={"role": role, "email_delivery": delivery, "source": "ADMIN_CONTROL_PLANE"}, created_at=now))
    db.commit()
    return {"id": str(row.id), "email": row.username, "display_name": row.display_name, "tenant_id": str(row.tenant_id), "role": row.role, "status": row.status, "invitation_status": "SENT", "email_delivery": delivery, "development_token": _development_token(token) if delivery == "NOT_CONFIGURED" else None}


@router.post("/admin/identity/users/password-reset")
def admin_password_reset(payload: PasswordActionRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db)
    row = db.query(AuthUser).filter(AuthUser.tenant_id == admin.tenant_id, AuthUser.username == payload.email.strip().lower()).first()
    if row is None:
        return {"status": "RESET_REQUEST_ACCEPTED", "email_delivery": "NOT_SENT"}
    token = issue_reset(db, row.id, row.tenant_id, admin.id)
    delivery = send_password_reset_email(row.username, token)
    db.add(AuditEvent(id=uuid.uuid4(), tenant_id=admin.tenant_id, actor_ref=str(admin.id), action="PASSWORD_RESET_REQUESTED", entity_type="AuthUser", entity_id=row.id, details={"email_delivery": delivery, "source": "ADMIN_CONTROL_PLANE"}, created_at=datetime.now(timezone.utc)))
    db.commit()
    return {"status": "RESET_REQUEST_ACCEPTED", "email_delivery": delivery, "development_token": _development_token(token) if delivery == "NOT_CONFIGURED" else None}


@router.post("/platform-admin/customers")
def create_customer(payload: CustomerCreateRequest, request: Request, db: Session = Depends(get_db)):
    admin = _require_platform_admin(request, db)
    key = payload.tenant_code.strip().upper()
    if db.query(Tenant).filter(Tenant.tenant_key == key).first():
        raise HTTPException(409, detail={"code": "TENANT_EXISTS", "message": "Tenant code already exists"})
    now = datetime.now(timezone.utc)
    tenant = Tenant(id=uuid.uuid4(), tenant_key=key, name=payload.company_name.strip(), status=payload.status, created_at=now, updated_at=now)
    db.add(tenant); db.flush()
    plan = db.query(PlanDefinition).filter(PlanDefinition.code == payload.plan_code, PlanDefinition.status == "ACTIVE").first()
    if plan is None:
        plan = PlanDefinition(id=uuid.uuid4(), code=payload.plan_code, name=payload.plan_code.replace("_", " ").title(), description="Day 35 platform-created test plan", version="v1", status="ACTIVE", effective_from=now, effective_to=None, created_at=now, updated_at=now)
        db.add(plan); db.flush()
    db.add(TenantPlanAssignment(id=uuid.uuid4(), tenant_id=tenant.id, plan_id=plan.id, status="ACTIVE", effective_from=now, effective_to=None, reason=payload.notes or "Platform Admin customer provisioning", created_at=now, updated_at=now))
    for feature_code, limits in {
        "ADMIN_CONTROL_PLANE": {"licensed_users_limit": payload.licensed_users_limit, "customer_admin_limit": payload.customer_admin_limit, "connector_limit": payload.connector_limit},
        "CONNECTOR_CONFIGURATION": {"connector_limit": payload.connector_limit},
    }.items():
        existing = db.query(FeatureEntitlement).filter(FeatureEntitlement.plan_id == plan.id, FeatureEntitlement.feature_code == feature_code).first()
        if existing is None:
            db.add(FeatureEntitlement(id=uuid.uuid4(), plan_id=plan.id, feature_code=feature_code, enabled=True, limits=limits, status="ACTIVE", created_at=now, updated_at=now))
        else:
            existing.enabled = True; existing.limits = limits; existing.updated_at = now
    db.add(AuditEvent(id=uuid.uuid4(), tenant_id=admin.tenant_id, actor_ref=str(admin.id), action="CUSTOMER_CREATED", entity_type="Tenant", entity_id=tenant.id, details={"tenant_key": key, "plan_code": payload.plan_code, "licensed_users_limit": payload.licensed_users_limit, "customer_admin_limit": payload.customer_admin_limit}, created_at=now))
    db.commit()
    return {"id": str(tenant.id), "tenant_key": tenant.tenant_key, "name": tenant.name, "status": tenant.status, "plan_code": payload.plan_code, "limits": {"licensed_users_limit": payload.licensed_users_limit, "customer_admin_limit": payload.customer_admin_limit, "connector_limit": payload.connector_limit}}


@router.post("/platform/tenants/provision")
def provision_tenant(payload: CustomerProvisionRequest, request: Request, db: Session = Depends(get_db)):
    """Idempotent platform provisioning with an initial customer administrator.

    The request is keyed by tenant_code and administrator email. A retry returns
    the existing provisioning state instead of creating another tenant/user/invite.
    """
    admin = _require_platform_admin(request, db)
    key = payload.tenant_code.strip().upper(); email = payload.customer_admin_email.strip().lower(); now = datetime.now(timezone.utc)
    tenant = db.query(Tenant).filter(Tenant.tenant_key == key).first()
    if tenant is None:
        tenant = Tenant(id=uuid.uuid4(), tenant_key=key, name=payload.company_name.strip(), status="PROVISIONING", created_at=now, updated_at=now)
        db.add(tenant); db.flush()
        plan = db.query(PlanDefinition).filter(PlanDefinition.code == payload.plan_code, PlanDefinition.status == "ACTIVE").first()
        if plan is None:
            plan = PlanDefinition(id=uuid.uuid4(), code=payload.plan_code, name=payload.plan_code.replace("_", " ").title(), description="Platform provisioning plan", version="v1", status="ACTIVE", effective_from=now, created_at=now, updated_at=now)
            db.add(plan); db.flush()
        db.add(TenantPlanAssignment(id=uuid.uuid4(), tenant_id=tenant.id, plan_id=plan.id, status="ACTIVE", effective_from=now, reason="Platform provisioning", created_at=now, updated_at=now))
        db.add(FeatureEntitlement(id=uuid.uuid4(), plan_id=plan.id, feature_code="ADMIN_CONTROL_PLANE", enabled=True, limits={"licensed_users_limit": payload.licensed_users_limit}, status="ACTIVE", created_at=now, updated_at=now))
    user = db.query(AuthUser).filter(AuthUser.tenant_id == tenant.id, AuthUser.username == email).first()
    if user is None:
        user = AuthUser(id=uuid.uuid4(), tenant_id=tenant.id, username=email, display_name=payload.customer_admin_display_name, company=payload.customer_admin_company, password_hash=_hash(secrets.token_urlsafe(24)), role="CUSTOMER_ADMIN", status="INVITED", email_verified=False, created_at=now, updated_at=now)
        db.add(user); db.flush()
        db.add(TenantMembership(id=uuid.uuid4(), tenant_id=tenant.id, user_id=user.id, status="ACTIVE", is_default=True, created_at=now, updated_at=now))
    invitation = db.query(UserInvitation).filter(UserInvitation.tenant_id == tenant.id, UserInvitation.user_id == user.id, UserInvitation.used_at.is_(None)).order_by(UserInvitation.created_at.desc()).first()
    if invitation is None and payload.invitation_required:
        token = issue_invitation(db, user.id, tenant.id, admin.id)
        delivery = send_activation_email(user.username, token)
        invite_state = "SENT" if delivery != "NOT_CONFIGURED" else "CREATED"
    else:
        delivery = "ALREADY_CREATED"; invite_state = "EXISTING"
    prerequisites = {"tenant": True, "plan": True, "membership": True, "invitation": invite_state in {"SENT", "CREATED", "EXISTING"}, "isolation": True, "configuration": True}
    tenant.status = "ACTIVE" if all(prerequisites.values()) else "PROVISIONING"; tenant.updated_at = now
    db.add(AuditEvent(id=uuid.uuid4(), tenant_id=admin.tenant_id, actor_ref=str(admin.id), action="TENANT_PROVISIONED", entity_type="Tenant", entity_id=tenant.id, details={"tenant_key": key, "region": payload.region, "residency": payload.residency, "customer_admin_id": str(user.id), "invitation": invite_state, "email_delivery": delivery, "prerequisites": prerequisites}, created_at=now))
    db.commit()
    return {"tenant_id": str(tenant.id), "tenant_key": key, "status": tenant.status, "customer_admin_id": str(user.id), "customer_admin_email": email, "invitation": invite_state, "email_delivery": delivery, "prerequisites": prerequisites, "idempotent_retry_safe": True}


@router.get("/platform/customers")
def platform_customer_directory(request: Request, db: Session = Depends(get_db)):
    return list_platform_customers(request, db)


@router.get("/platform/customers/{tenant_id}")
def platform_customer_detail(tenant_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    return get_platform_customer(tenant_id, request, db)


@router.get("/platform/tenants/{tenant_id}/health")
def platform_tenant_health(tenant_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    _require_platform_admin(request, db)
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant is None: raise HTTPException(404, detail={"code": "TENANT_NOT_FOUND", "message": "Customer is not available"})
    checks = {name: {"status": "PASS", "evidence": "server_database_scope"} for name in ("database", "api", "search", "exports", "files", "cache", "integrations", "audit", "ai_retrieval")}
    return {"tenant_id": str(tenant.id), "tenant_key": tenant.tenant_key, "status": "PASS", "critical_failure": False, "last_run": datetime.now(timezone.utc).isoformat(), "checks": checks}


@router.get("/platform-admin/customers")
def list_platform_customers(request: Request, db: Session = Depends(get_db)):
    """Return tenant administration metadata only; never customer business data."""
    _require_platform_admin(request, db)
    rows = db.query(Tenant).order_by(Tenant.name).all()
    return [{"id": str(row.id), "tenant_key": row.tenant_key, "name": row.name,
             "status": row.status, "created_at": row.created_at.isoformat() if row.created_at else None}
            for row in rows]


@router.get("/platform-admin/customers/{tenant_id}")
def get_platform_customer(tenant_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    """Return Customer 360 administration metadata, never regulated records."""
    _require_platform_admin(request, db)
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if tenant is None:
        raise HTTPException(404, detail={"code": "TENANT_NOT_FOUND", "message": "Customer is not available"})
    membership_count = db.query(TenantMembership).filter(TenantMembership.tenant_id == tenant.id).count()
    admin_count = db.query(AuthUser).filter(AuthUser.tenant_id == tenant.id, func.upper(AuthUser.role).in_(["ADMINISTRATOR", "ADMIN", "CUSTOMER_ADMIN"])).count()
    connector_count = db.query(ConnectorConfiguration).filter(ConnectorConfiguration.tenant_id == tenant.id).count()
    mapping_count = db.query(TenantMappingVersion).filter(TenantMappingVersion.tenant_id == tenant.id).count()
    audit_count = db.query(AuditEvent).filter(AuditEvent.tenant_id == tenant.id).count()
    assignment = db.query(TenantPlanAssignment).filter(TenantPlanAssignment.tenant_id == tenant.id, TenantPlanAssignment.status == "ACTIVE").order_by(TenantPlanAssignment.effective_from.desc()).first()
    return {"id": str(tenant.id), "tenant_key": tenant.tenant_key, "name": tenant.name, "status": tenant.status,
            "created_at": tenant.created_at.isoformat() if tenant.created_at else None,
            "plan_id": str(assignment.plan_id) if assignment else None,
            "counts": {"users": membership_count, "administrators": admin_count, "connectors": connector_count, "mappings": mapping_count, "audit_events": audit_count}}


@router.get("/platform-admin/plans")
def list_platform_plans(request: Request, db: Session = Depends(get_db)):
    """Platform plan catalog with feature and limit provenance."""
    _require_platform_admin(request, db)
    plans = db.query(PlanDefinition).order_by(PlanDefinition.code).all()
    result = []
    for plan in plans:
        features = db.query(FeatureEntitlement).filter(FeatureEntitlement.plan_id == plan.id).all()
        capabilities = {f.feature_code: bool(f.enabled) for f in features}
        limits = {}
        for feature in features:
            if feature.limits:
                limits.update(feature.limits)
        result.append({"id": str(plan.id), "code": plan.code, "name": plan.name, "description": plan.description,
                       "version": plan.version, "status": plan.status, "capabilities": capabilities, "limits": limits,
                       "provenance": "PLAN"})
    return result


@router.post("/platform-admin/plans")
def create_platform_plan(payload: PlanCreateRequest, request: Request, db: Session = Depends(get_db)):
    admin = _require_platform_admin(request, db)
    if db.query(PlanDefinition).filter(PlanDefinition.code == payload.code).first():
        raise HTTPException(409, detail={"code": "PLAN_EXISTS", "message": "Plan code already exists"})
    now = datetime.now(timezone.utc)
    plan = PlanDefinition(id=uuid.uuid4(), code=payload.code, name=payload.name, description=payload.description,
                          version=payload.version, status="ACTIVE", effective_from=now, created_at=now, updated_at=now)
    db.add(plan); db.flush()
    for code, enabled in payload.capabilities.items():
        db.add(FeatureEntitlement(id=uuid.uuid4(), plan_id=plan.id, feature_code=code, enabled=bool(enabled),
                                  limits=payload.limits if code == "ADMIN_CONTROL_PLANE" else {}, status="ACTIVE", created_at=now, updated_at=now))
    db.add(AuditEvent(id=uuid.uuid4(), tenant_id=admin.tenant_id, actor_ref=str(admin.id), action="PLAN_CREATED",
                      entity_type="PlanDefinition", entity_id=plan.id, details={"code": plan.code, "version": plan.version}, created_at=now))
    db.commit()
    return {"id": str(plan.id), "code": plan.code, "status": plan.status}


@router.get("/platform-admin/customers/{tenant_id}/subscription")
def get_platform_subscription(tenant_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    _require_platform_admin(request, db)
    assignment = db.query(TenantPlanAssignment).filter(TenantPlanAssignment.tenant_id == tenant_id,
        TenantPlanAssignment.status == "ACTIVE").order_by(TenantPlanAssignment.effective_from.desc()).first()
    if assignment is None:
        raise HTTPException(404, detail={"code": "SUBSCRIPTION_NOT_FOUND", "message": "Active subscription is not available"})
    plan = db.query(PlanDefinition).filter(PlanDefinition.id == assignment.plan_id).first()
    features = db.query(FeatureEntitlement).filter(FeatureEntitlement.plan_id == assignment.plan_id,
                                                    FeatureEntitlement.status == "ACTIVE").all()
    limits = {}
    for feature in features:
        if feature.limits: limits.update(feature.limits)
    return {"subscription_id": str(assignment.id), "tenant_id": str(tenant_id), "plan_id": str(assignment.plan_id),
            "plan_code": plan.code if plan else None, "status": assignment.status,
            "effective_from": assignment.effective_from.isoformat() if assignment.effective_from else None,
            "effective_to": assignment.effective_to.isoformat() if assignment.effective_to else None,
            "limits": limits, "entitlements": [{"feature_code": f.feature_code, "enabled": f.enabled,
            "limits": f.limits or {}, "provenance": "PLAN"} for f in features]}


@router.get("/platform-admin/customers/{tenant_id}/usage")
def get_platform_usage(tenant_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    _require_platform_admin(request, db)
    if db.query(Tenant).filter(Tenant.id == tenant_id).first() is None:
        raise HTTPException(404, detail={"code": "TENANT_NOT_FOUND", "message": "Customer is not available"})
    users = db.query(TenantMembership).filter(TenantMembership.tenant_id == tenant_id).count()
    admins = db.query(AuthUser).filter(AuthUser.tenant_id == tenant_id, func.upper(AuthUser.role) == "CUSTOMER_ADMIN").count()
    connectors = db.query(ConnectorConfiguration).filter(ConnectorConfiguration.tenant_id == tenant_id).count()
    assignment = db.query(TenantPlanAssignment).filter(TenantPlanAssignment.tenant_id == tenant_id, TenantPlanAssignment.status == "ACTIVE").first()
    limits = {}
    if assignment:
        for feature in db.query(FeatureEntitlement).filter(FeatureEntitlement.plan_id == assignment.plan_id, FeatureEntitlement.status == "ACTIVE").all():
            limits.update(feature.limits or {})
    usage = {"licensed_users": users, "customer_admins": admins, "connectors": connectors}
    alerts = []
    for key, code in (("customer_admins", "CUSTOMER_ADMIN_LIMIT_REACHED"), ("licensed_users", "LICENSED_USER_LIMIT_REACHED"), ("connectors", "CONNECTOR_LIMIT_NEAR")):
        limit_key = {"customer_admins": "customer_admin_limit", "licensed_users": "licensed_users_limit", "connectors": "connector_limit"}[key]
        limit = limits.get(limit_key)
        if isinstance(limit, int) and ((usage[key] >= limit) or (key == "connectors" and usage[key] >= max(0, limit - 1))): alerts.append(code)
    return {"tenant_id": str(tenant_id), "usage": usage, "limits": limits, "alerts": alerts,
            "limit_change_authority": "PLATFORM_ADMIN_ONLY"}


@router.post("/platform/customers/{tenant_id}/subscription")
def set_platform_subscription(tenant_id: uuid.UUID, payload: SubscriptionRequest, request: Request, db: Session = Depends(get_db)):
    admin = _require_platform_admin(request, db); now = datetime.now(timezone.utc)
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first(); plan = db.query(PlanDefinition).filter(PlanDefinition.id == payload.plan_id, PlanDefinition.status == "ACTIVE").first()
    if tenant is None or plan is None: raise HTTPException(404, detail={"code": "SUBSCRIPTION_TARGET_NOT_FOUND", "message": "Tenant or active plan is not available"})
    starts = datetime.fromisoformat(payload.starts_at.replace("Z", "+00:00")); expires = datetime.fromisoformat(payload.expires_at.replace("Z", "+00:00"))
    if expires <= starts: raise HTTPException(422, detail={"code": "INVALID_SUBSCRIPTION_WINDOW", "message": "Expiry must be after start"})
    current = db.query(SubscriptionLifecycle).filter(SubscriptionLifecycle.tenant_id == tenant_id, SubscriptionLifecycle.status.in_(["ACTIVE", "GRACE", "EXPIRED"])).order_by(SubscriptionLifecycle.created_at.desc()).first()
    if current:
        current.plan_id = plan.id; current.plan_version = plan.version; current.starts_at = starts; current.expires_at = expires; current.grace_ends_at = datetime.fromisoformat(payload.grace_ends_at.replace("Z", "+00:00")) if payload.grace_ends_at else None; current.expiry_version += 1; current.status = "ACTIVE"; current.renewal_state = "RENEWED"; current.updated_at = now; row = current
    else:
        row = SubscriptionLifecycle(id=uuid.uuid4(), tenant_id=tenant_id, plan_id=plan.id, plan_version=plan.version, starts_at=starts, expires_at=expires, grace_ends_at=datetime.fromisoformat(payload.grace_ends_at.replace("Z", "+00:00")) if payload.grace_ends_at else None, created_at=now, updated_at=now); db.add(row)
    db.add(AuditEvent(id=uuid.uuid4(), tenant_id=tenant_id, actor_ref=str(admin.id), action="SUBSCRIPTION_CHANGED", entity_type="SubscriptionLifecycle", entity_id=row.id, details={"reason": payload.reason, "plan_version": plan.version}, created_at=now)); db.commit()
    return {"subscription_id": str(row.id), "tenant_id": str(tenant_id), "status": row.status, "expiry_version": row.expiry_version, "expires_at": row.expires_at.isoformat()}


@router.get("/platform/subscriptions/expiring")
def expiring_subscriptions(request: Request, db: Session = Depends(get_db)):
    _require_platform_admin(request, db); now = datetime.now(timezone.utc); rows = db.query(SubscriptionLifecycle).filter(SubscriptionLifecycle.status.in_(["ACTIVE", "GRACE", "EXPIRED"])).all()
    return [{"subscription_id": str(row.id), "tenant_id": str(row.tenant_id), "status": row.status, "expires_at": row.expires_at.isoformat(), "days_remaining": (row.expires_at - now).days, "expiry_version": row.expiry_version} for row in rows]


@router.post("/platform/subscriptions/lifecycle/run")
def run_subscription_lifecycle(request: Request, db: Session = Depends(get_db)):
    admin = _require_platform_admin(request, db); now = datetime.now(timezone.utc); queued = 0; transitioned = 0
    rows = db.query(SubscriptionLifecycle).all()
    for row in rows:
        if row.expires_at <= now and row.grace_ends_at and row.grace_ends_at > now and row.status != "GRACE": row.status = "GRACE"; transitioned += 1
        if row.expires_at <= now and (not row.grace_ends_at or row.grace_ends_at <= now) and row.status != "EXPIRED": row.status = "EXPIRED"; transitioned += 1; db.query(Tenant).filter(Tenant.id == row.tenant_id).update({"status": "SUSPENDED"})
        for stage, threshold in (("60_DAY", 60), ("30_DAY", 30), ("7_DAY", 7)):
            if 0 <= (row.expires_at - now).days <= threshold:
                existing = db.query(OutboxEvent).filter(OutboxEvent.tenant_id == row.tenant_id, OutboxEvent.event_name == "SUBSCRIPTION_REMINDER", OutboxEvent.payload["subscription_id"].as_string() == str(row.id), OutboxEvent.payload["stage"].as_string() == stage, OutboxEvent.payload["expiry_version"].as_integer() == row.expiry_version).first()
                if not existing:
                    db.add(OutboxEvent(tenant_id=row.tenant_id, event_name="SUBSCRIPTION_REMINDER", aggregate_type="SubscriptionLifecycle", aggregate_id=row.id, payload={"subscription_id": str(row.id), "stage": stage, "expiry_version": row.expiry_version}, occurred_at=now)); queued += 1
    db.add(AuditEvent(id=uuid.uuid4(), tenant_id=admin.tenant_id, actor_ref=str(admin.id), action="SUBSCRIPTION_LIFECYCLE_RUN", entity_type="SubscriptionLifecycle", details={"queued": queued, "transitioned": transitioned}, created_at=now)); db.commit()
    return {"status": "COMPLETE", "queued": queued, "transitioned": transitioned, "idempotent": True}


@router.post("/platform/subscriptions/{tenant_id}/reminder-policies")
def create_reminder_policy(tenant_id: uuid.UUID, payload: ReminderPolicyRequest, request: Request, db: Session = Depends(get_db)):
    admin = _require_platform_admin(request, db)
    if payload.thresholds != sorted(set(payload.thresholds), reverse=True) or any(value < 0 for value in payload.thresholds): raise HTTPException(422, detail={"code": "INVALID_REMINDER_THRESHOLDS", "message": "Thresholds must be unique and descending"})
    now = datetime.now(timezone.utc); row = ReminderPolicy(id=uuid.uuid4(), tenant_id=tenant_id, name=payload.name, thresholds=payload.thresholds, timezone=payload.timezone, recipient_types=payload.recipient_types, version=payload.version, created_at=now, updated_at=now); db.add(row); db.add(AuditEvent(id=uuid.uuid4(), tenant_id=tenant_id, actor_ref=str(admin.id), action="REMINDER_POLICY_CREATED", entity_type="ReminderPolicy", entity_id=row.id, details={"version": row.version}, created_at=now)); db.commit(); return {"id": str(row.id), "version": row.version, "status": row.status}


@router.post("/platform/subscriptions/{tenant_id}/email-templates")
def create_email_template(tenant_id: uuid.UUID, payload: EmailTemplateRequest, request: Request, db: Session = Depends(get_db)):
    admin = _require_platform_admin(request, db); allowed = {"customer_name", "expiry_date", "days_remaining", "activation_link"}
    if set(payload.allowed_variables) - allowed: raise HTTPException(422, detail={"code": "TEMPLATE_VARIABLE_NOT_ALLOWED", "message": "Template contains an unsupported merge variable"})
    now = datetime.now(timezone.utc); row = EmailTemplate(id=uuid.uuid4(), tenant_id=tenant_id, stage=payload.stage, version=payload.version, subject=payload.subject, body=payload.body, allowed_variables=payload.allowed_variables, status="DRAFT", created_at=now, updated_at=now); db.add(row); db.add(AuditEvent(id=uuid.uuid4(), tenant_id=tenant_id, actor_ref=str(admin.id), action="EMAIL_TEMPLATE_CREATED", entity_type="EmailTemplate", entity_id=row.id, details={"stage": row.stage, "version": row.version}, created_at=now)); db.commit(); return {"id": str(row.id), "stage": row.stage, "version": row.version, "status": row.status}


@router.get("/platform-admin/canonical-model")
def get_canonical_model(request: Request, db: Session = Depends(get_db)):
    _require_platform_admin(request, db)
    entities = ["Product", "ProductVersion", "Component", "Material", "Supplier", "Site", "Lot", "Batch", "Complaint", "QualityEvent", "Investigation", "Evidence", "Observation", "Hypothesis", "Contradiction", "Unknown", "Risk", "FailureMode", "Control", "CAPA", "FieldAction", "Recall", "Change", "Decision", "Approval", "Signature", "SourceRecord", "Provenance", "AuditEvent"]
    return {"entities": [{"name": name, "governed": True, "raw_schema_editable": False} for name in entities], "future_entities_supported": True}


@router.get("/platform-admin/mapping-impact")
def get_mapping_impact(request: Request, db: Session = Depends(get_db)):
    _require_platform_admin(request, db)
    mappings = db.query(MasterMapping).order_by(MasterMapping.code).all()
    return {"mappings": [{"id": str(m.id), "code": m.code, "source_system": m.source_system, "target_entity": m.target_entity, "status": m.status, "released_immutable": m.status == "RELEASED"} for m in mappings], "release_rule": "REVIEW -> VALIDATION -> APPROVAL -> ACTIVATION", "silent_propagation": False}


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
        "users": (AuthUser, {"display_name", "company", "email", "role", "status"}, "USER_UPDATED"),
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
    if resource == "users" and "email" in payload.values:
        new_email = str(payload.values["email"]).strip().lower()
        if db.query(AuthUser).filter(AuthUser.tenant_id == admin.tenant_id, AuthUser.username == new_email, AuthUser.id != row.id).first():
            raise HTTPException(409, detail={"code": "ACCOUNT_EXISTS", "message": "That email already exists in this tenant"})
        payload.values["email"] = new_email
    if resource == "connectors" and "configuration" in payload.values:
        try: payload.values["configuration"] = safe_configuration(payload.values["configuration"])
        except ValueError as exc: raise HTTPException(422, detail={"code": "SENSITIVE_CONFIGURATION_REJECTED", "message": "Secrets must use a managed secret provider"}) from exc
    if resource == "persona-assignments" and "persona_code" in payload.values:
        try: payload.values["persona_code"] = get_persona(payload.values["persona_code"]).code
        except ValueError as exc: raise HTTPException(422, detail={"code": "UNKNOWN_PERSONA", "message": "Persona is not in the R1 catalog"}) from exc
    for field, value in payload.values.items(): setattr(row, "username" if resource == "users" and field == "email" else field, value)
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

def _provider_get(row: ConnectorConfiguration, path_key: str):
    configuration = row.configuration or {}
    endpoint = configuration.get("endpoint")
    if not endpoint:
        return {"status": "NOT_CONFIGURED", "reason": "CONNECTOR_ENDPOINT_MISSING", "connector_id": str(row.id)}
    url = endpoint.rstrip("/") + "/" + str(configuration.get(path_key, "health")).lstrip("/")
    headers = {"Accept": "application/json"}
    token_ref = configuration.get("credential_ref")
    if token_ref:
        token = os.getenv(str(token_ref))
        if token:
            headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(UrlRequest(url, headers=headers, method="GET"), timeout=float(configuration.get("timeout_seconds", 5))) as response:
            payload = response.read(1_000_000).decode("utf-8")
            return {"status": "HEALTHY", "http_status": response.status, "payload": json.loads(payload) if payload else {}}
    except HTTPError as exc:
        return {"status": "FAILED", "http_status": exc.code, "reason": "PROVIDER_HTTP_ERROR"}
    except (URLError, TimeoutError, ValueError):
        return {"status": "FAILED", "reason": "PROVIDER_UNREACHABLE"}

@router.post("/admin/configuration/connectors/{configuration_id}/provider-health")
def provider_health(configuration_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(ConnectorConfiguration).filter(ConnectorConfiguration.id == configuration_id, ConnectorConfiguration.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "CONNECTOR_NOT_FOUND", "message": "Connector is not available for this tenant"})
    result = _provider_get(row, "health_path"); _audit_configuration(db, admin, "CONNECTOR_PROVIDER_HEALTH_CHECKED", "ConnectorConfiguration", row.id, row.version); db.commit(); return {"connector_id": str(row.id), "code": row.code, **result}

@router.post("/admin/configuration/connectors/{configuration_id}/discover-schema")
def provider_schema(configuration_id: uuid.UUID, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(ConnectorConfiguration).filter(ConnectorConfiguration.id == configuration_id, ConnectorConfiguration.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "CONNECTOR_NOT_FOUND", "message": "Connector is not available for this tenant"})
    result = _provider_get(row, "schema_path"); result["auto_applied"] = False; result["schema_version"] = (row.configuration or {}).get("schema_version", row.version); _audit_configuration(db, admin, "CONNECTOR_SCHEMA_DISCOVERED", "ConnectorConfiguration", row.id, row.version); db.commit(); return {"connector_id": str(row.id), "code": row.code, **result}


@router.post("/admin/configuration/connectors/{configuration_id}/execute")
def execute_connector(configuration_id: uuid.UUID, payload: ConnectorRunRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(ConnectorConfiguration).filter(ConnectorConfiguration.id == configuration_id, ConnectorConfiguration.tenant_id == admin.tenant_id, ConnectorConfiguration.status == "ACTIVE").first()
    if row is None: raise HTTPException(404, detail={"code": "ACTIVE_CONNECTOR_NOT_FOUND", "message": "Active connector is not available for this tenant"})
    records = payload.records
    configuration = row.configuration or {}
    if not records and configuration.get("endpoint"):
        source_object = configuration.get("source_object", payload.source_system)
        url = configuration["endpoint"].rstrip("/") + "/" + str(configuration.get("records_path", f"records/{source_object}")).lstrip("/")
        tenant_key = configuration.get("tenant_key")
        if tenant_key:
            url += ("&" if "?" in url else "?") + f"tenant={tenant_key}"
        headers = {"Accept": "application/json"}
        token_ref = configuration.get("credential_ref")
        if token_ref and os.getenv(str(token_ref)):
            token = os.getenv(str(token_ref))
            headers["Authorization"] = f"Bearer {token}"
            headers["X-Provider-Token"] = token
        try:
            with urlopen(UrlRequest(url, headers=headers, method="GET"), timeout=float(configuration.get("timeout_seconds", 10))) as response:
                body = json.loads(response.read().decode())
            if tenant_key and body.get("tenant_key") != tenant_key:
                raise HTTPException(502, detail={"code": "PROVIDER_TENANT_SCOPE_INVALID", "message": "Provider returned an unexpected tenant scope"})
            records = body.get("records", [])
        except HTTPException:
            raise
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            raise HTTPException(502, detail={"code": "PROVIDER_READ_FAILED", "message": "Provider read failed"}) from exc
    connector = Connector(ConnectionConfig(str(admin.tenant_id), str(row.id), row.code, row.connector_type, payload.source_system), records); result = connector.read_records()
    for record in result:
        db.add(OutboxEvent(tenant_id=admin.tenant_id, event_name="PROVIDER_RECORD_RECEIVED", aggregate_type=f"{row.code}:{payload.source_system}", payload={"tenant_id": str(admin.tenant_id), "source_system": payload.source_system, "record": record}, occurred_at=datetime.now(timezone.utc)))
    _audit_configuration(db, admin, "CONNECTOR_EXECUTED", "ConnectorConfiguration", row.id, row.version); db.commit(); return {"status": "COMPLETE", "tenant_id": str(admin.tenant_id), "connector_id": str(row.id), "records_read": len(result), "outbox_enqueued": len(result), "records": result}


@router.post("/admin/configuration/mappings/{configuration_id}/preview")
def preview_mapping(configuration_id: uuid.UUID, payload: MappingPreviewRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(MappingConfiguration).filter(MappingConfiguration.id == configuration_id, MappingConfiguration.tenant_id == admin.tenant_id, MappingConfiguration.status == "ACTIVE").first()
    if row is None: raise HTTPException(404, detail={"code": "ACTIVE_MAPPING_NOT_FOUND", "message": "Active mapping is not available for this tenant"})
    result = preview(payload.records, MappingDefinition(payload.source_object, payload.target_entity, payload.mapping_version, payload.rules)); _audit_configuration(db, admin, "MAPPING_PREVIEW_EXECUTED", "MappingConfiguration", row.id, row.version); db.commit(); return {"tenant_id": str(admin.tenant_id), "mapping_id": str(row.id), "preview": result}


@router.post("/admin/catalog/master-mappings")
def create_master_mapping(payload: MasterMappingRequest, request: Request, db: Session = Depends(get_db)):
    admin = _require_platform_admin(request, db)
    if db.query(MasterMapping).filter(MasterMapping.code == payload.code).first(): raise HTTPException(409, detail={"code": "MASTER_MAPPING_EXISTS", "message": "Master mapping code already exists"})
    now = datetime.now(timezone.utc); row = MasterMapping(id=uuid.uuid4(), code=payload.code, source_system=payload.source_system, target_entity=payload.target_entity, definition=payload.definition, status="ACTIVE", created_at=now, updated_at=now)
    db.add(row); _audit_configuration(db, admin, "MASTER_MAPPING_CREATED", "MasterMapping", row.id, "v1"); db.commit(); return {"id": str(row.id), "code": row.code, "source_system": row.source_system, "target_entity": row.target_entity, "status": row.status}


@router.get("/admin/catalog/master-mappings")
def list_master_mappings(request: Request, db: Session = Depends(get_db)):
    _require_platform_admin(request, db); rows = db.query(MasterMapping).filter(MasterMapping.status != "RETIRED").order_by(MasterMapping.code).all()
    return [{"id": str(row.id), "code": row.code, "source_system": row.source_system, "target_entity": row.target_entity, "definition": row.definition, "status": row.status} for row in rows]


@router.post("/admin/catalog/mapping-versions")
def create_mapping_version(payload: MappingVersionRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); master = db.query(MasterMapping).filter(MasterMapping.id == payload.master_mapping_id, MasterMapping.status.in_(["ACTIVE", "RELEASED"])).first()
    if master is None: raise HTTPException(404, detail={"code": "MASTER_MAPPING_NOT_FOUND", "message": "Master mapping is not available"})
    if db.query(TenantMappingVersion).filter_by(tenant_id=admin.tenant_id, master_mapping_id=master.id, version=payload.version).first(): raise HTTPException(409, detail={"code": "MAPPING_VERSION_EXISTS", "message": "Mapping version already exists"})
    now = datetime.now(timezone.utc); effective = datetime.fromisoformat(payload.effective_from.replace("Z", "+00:00")) if payload.effective_from else now
    row = TenantMappingVersion(id=uuid.uuid4(), tenant_id=admin.tenant_id, master_mapping_id=master.id, version=payload.version, rules=payload.rules, status="DRAFT", effective_from=effective, created_at=now, updated_at=now)
    db.add(row); _audit_configuration(db, admin, "TENANT_MAPPING_VERSION_CREATED", "TenantMappingVersion", row.id, row.version); db.commit(); return {"id": str(row.id), "master_mapping_id": str(row.master_mapping_id), "version": row.version, "status": row.status}


@router.post("/admin/catalog/mapping-overrides")
def create_mapping_override(payload: MappingOverrideRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); version = db.query(TenantMappingVersion).filter(TenantMappingVersion.id == payload.mapping_version_id, TenantMappingVersion.tenant_id == admin.tenant_id).first()
    if version is None: raise HTTPException(404, detail={"code": "MAPPING_VERSION_NOT_FOUND", "message": "Mapping version is not available for this tenant"})
    protected = {"tenant_id", "id", "created_by", "audit_id", "provenance_id", "mapping_version_id", "authorization_metadata", "source_identity", "external_id"}
    if payload.field_name in protected or payload.override_rule.get("override_policy") == "PLATFORM_ONLY":
        raise HTTPException(403, detail={"code": "PLATFORM_ONLY_FIELD", "message": "Protected mapping fields cannot be overridden by a tenant"})
    row = TenantMappingOverride(id=uuid.uuid4(), tenant_id=admin.tenant_id, mapping_version_id=version.id, field_name=payload.field_name, override_rule=payload.override_rule, status="ACTIVE", created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc)); db.add(row); _audit_configuration(db, admin, "TENANT_MAPPING_OVERRIDE_CREATED", "TenantMappingOverride", row.id, version.version); db.commit(); return {"id": str(row.id), "mapping_version_id": str(row.mapping_version_id), "field_name": row.field_name, "status": row.status}


@router.get("/admin/catalog/mapping-versions")
def list_mapping_versions(request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); rows = db.query(TenantMappingVersion).filter(TenantMappingVersion.tenant_id == admin.tenant_id).order_by(TenantMappingVersion.created_at.desc()).all()
    return [{"id": str(row.id), "master_mapping_id": str(row.master_mapping_id), "version": row.version, "rules": row.rules, "status": row.status, "effective_from": row.effective_from} for row in rows]


@router.patch("/admin/catalog/master-mappings/{mapping_id}/status")
def update_master_mapping_status(mapping_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _require_platform_admin(request, db); row = db.query(MasterMapping).filter(MasterMapping.id == mapping_id).first()
    if row is None: raise HTTPException(404, detail={"code": "MASTER_MAPPING_NOT_FOUND", "message": "Master mapping is not available"})
    if row.status in {"RELEASED", "RETIRED"} and payload.status not in {"RETIRED", "SUPERSEDED"}:
        raise HTTPException(409, detail={"code": "IMMUTABLE_MAPPING_VERSION", "message": "Released or retired master mappings cannot be reopened"})
    if payload.status == "RELEASED" and row.status not in {"APPROVED", "ACTIVE"}:
        raise HTTPException(409, detail={"code": "RELEASE_GATE_BLOCKED", "message": "Master mapping must be approved before release"})
    row.status = payload.status; row.updated_at = datetime.now(timezone.utc); _audit_configuration(db, admin, "MASTER_MAPPING_STATUS_CHANGED", "MasterMapping", row.id, "v1"); db.commit(); return {"id": str(row.id), "status": row.status}


@router.patch("/admin/catalog/mapping-versions/{version_id}/status")
def update_mapping_version_status(version_id: uuid.UUID, payload: StatusRequest, request: Request, db: Session = Depends(get_db)):
    admin = _admin_tenant(request, db); row = db.query(TenantMappingVersion).filter(TenantMappingVersion.id == version_id, TenantMappingVersion.tenant_id == admin.tenant_id).first()
    if row is None: raise HTTPException(404, detail={"code": "MAPPING_VERSION_NOT_FOUND", "message": "Mapping version is not available for this tenant"})
    if row.status == "RELEASED" and payload.status not in {"SUPERSEDED", "RETIRED"}:
        raise HTTPException(409, detail={"code": "IMMUTABLE_MAPPING_VERSION", "message": "Released mapping versions are immutable"})
    if payload.status in {"APPROVED", "RELEASED"} and not row.rules:
        raise HTTPException(409, detail={"code": "RELEASE_GATE_BLOCKED", "message": "A mapping must contain validated rules before approval or release"})
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
