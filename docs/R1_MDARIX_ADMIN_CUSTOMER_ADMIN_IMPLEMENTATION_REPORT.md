# MDARIX R1 Admin And Customer Admin Implementation Report

Status: DEVELOPMENT BLOCK IMPLEMENTED, FOCUSED VALIDATION REQUIRED

## Scope Implemented

This Day 35 extension implements the first controlled path for MDARIX Admin and Customer Admin administration inside the authenticated MDARIX App. It extends the existing Day 35 control plane rather than creating a parallel framework.

Implemented scope:

- Platform customer creation endpoint with tenant, plan, subscription, and limit metadata.
- Admin-created user invitation flow with no administrator-entered password.
- Customer Admin and ordinary user invite workflow using secure activation tokens.
- Activation page for users to create their own password.
- Password reset request and reset completion flow.
- SMTP-backed activation and reset email dispatch through environment variables.
- Server-side licensed-user and Customer Admin seat enforcement.
- Server-side platform-role assignment protection.
- Server-side tenant-scope enforcement for Customer Admin operations.
- Admin UI updates for invitation-only user creation.
- Admin route hides the product workflow context header.

## Existing Architecture Reused

Reused:

- Existing authenticated app shell in `frontend/src/main.tsx`.
- Existing `/api/v1/me/context` identity context.
- Existing `AuthUser`, `TenantMembership`, `Tenant`, `PlanDefinition`, `FeatureEntitlement`, `TenantPlanAssignment`, and `AuditEvent` tables.
- Existing `auth_service` token machinery.
- Existing `auth/emailer.py` SMTP pattern.
- Existing enterprise `audit_events` framework.

No competing audit framework or identity framework was introduced.

## Routes Added Or Changed

Changed:

- `POST /api/v1/admin/identity/users`
  - Now creates an invited user and sends activation email.
  - No password input is accepted.

Added:

- `POST /api/v1/platform-admin/customers`
- `POST /api/v1/admin/identity/users/password-reset`
- `POST /api/v1/auth/activate-account`
- Extended `POST /api/v1/auth/reset-password` for persisted invited users.

Frontend routes added:

- `/activate-account`
- `/reset-password`

## Components Added Or Changed

Changed:

- `AdministratorControlPlane`
- `AdminCreateForms`
- `AuthPage`

Frontend behavior:

- User creation form no longer exposes a temporary password field.
- Admin invitation result shows email delivery status.
- Development token is shown only when SMTP is not configured.
- Activation/reset pages collect token and user-created password.

## Backend APIs Consumed

The admin UI consumes the existing Day 35 admin APIs and the changed invitation endpoint:

- `/api/v1/admin/identity/users`
- `/api/v1/admin/identity/roles`
- `/api/v1/admin/identity/permission-sets`
- `/api/v1/admin/identity/memberships`
- `/api/v1/admin/identity/persona-assignments`
- `/api/v1/admin/governance/entitlements`
- `/api/v1/admin/configuration/connectors`
- `/api/v1/admin/configuration/mappings`
- `/api/v1/admin/governance/policies`
- `/api/v1/admin/audit-history`

## Backend Changes Required

Implemented:

- Token issue/consume helpers in `auth.service`.
- Activation and password reset email helpers in `auth.emailer`.
- Persisted-user activation and reset endpoints in `auth_router`.
- Invitation-only user creation and platform customer creation in `access_router`.
- Server-side seat and admin-seat checks.

Deferred:

- Durable invitation table with token hash, invitation lifecycle, resend/cancel states, and expiry reporting.
- Full subscription-management screens for every commercial field.
- Full MFA and SSO policy implementation.

## Customer Admin Workflow

Customer Admin can invite users within their own tenant. The backend derives tenant scope from the authenticated session unless a Platform Admin supplies an authorized target tenant.

Customer Admin cannot:

- Assign `PLATFORM_ADMIN`.
- Administer a foreign tenant.
- Exceed licensed-user limit.
- Exceed Customer Admin limit.
- See or set a user password.

## MDARIX Admin Workflow

Platform Admin can create a customer tenant and subscription metadata through `POST /api/v1/platform-admin/customers`.

Platform Admin can create invited users for an authorized tenant, including the first Customer Admin, without seeing a password.

## Password Activation And Reset Handling

Activation:

- Admin creates user.
- User is persisted as `INVITED`.
- Activation token is generated.
- Activation email is sent if SMTP is configured.
- User opens `/activate-account?token=...`.
- User creates password.
- Backend hashes password.
- User becomes `ACTIVE` and `email_verified=True`.

Reset:

- Admin or user initiates reset.
- Reset token is generated.
- Reset email is sent if SMTP is configured.
- User opens `/reset-password?token=...`.
- Backend hashes new password.

No plaintext password is stored or emailed.

## User-Limit Enforcement

Server-side helper checks `FeatureEntitlement.limits` for:

- `licensed_users_limit`
- `customer_admin_limit`

Seat-consuming statuses:

- `INVITED`
- `ACTIVE`
- `PENDING_VERIFICATION`

## Customer Admin Limit Enforcement

Customer Admin count is derived from tenant `AuthUser` records with role `CUSTOMER_ADMIN` and seat-consuming status.

If the limit is reached, the backend returns:

- `CUSTOMER_ADMIN_LIMIT_REACHED`

## Plan And Entitlement Enforcement

Current implementation reads active plan assignments and feature entitlement limits. Plan and subscription management UI is present only as an initial control-plane surface.

## Role And Permission Behavior

Implemented:

- Platform role assignment is blocked for Customer Admin.
- Customer Admin foreign tenant operations are blocked.
- Admin navigation remains permission-driven from `/api/v1/me/context`.

Deferred:

- Full action/field permission matrix enforcement across every admin operation.

## Integration Behavior

Existing connector configuration screens and APIs remain tenant-scoped and reuse Day 35 connector safety filtering.

## Mapping Behavior

Existing master mapping and tenant mapping version APIs remain in place. No automatic tenant mapping replacement was introduced.

## Security Controls

Implemented:

- No admin-visible password field.
- No password hash in UI.
- SMTP credentials read only from environment variables.
- Invitation/reset audit events omit raw tokens and passwords.
- Tenant scope is server-side.
- Customer Admin cannot assign Platform Admin.
- Platform Admin does not automatically gain customer business-data route access.

## Focused Tests Executed

Focused tests added:

- `tests/test_day35_admin_invitation_flow.py`

Required checks:

- No temporary password UI.
- Invitation-only user creation.
- Activation and reset routes.
- SMTP helper configuration.
- Server-side role, tenant, and limit controls.

## Known Limitations

- Invitation token persistence is in-memory for this development block.
- Invitation status reporting is represented through `AuthUser.status` and audit events.
- SMTP is environment-configured; no SMTP admin UI has been added yet.
- Full SSO, MFA, session revocation, and formal password-reset session invalidation are deferred.

## Deferred Validation Items

- Formal adversarial matrix.
- Full R1 qualification evidence.
- VS001-VS012 Golden Scenarios, deferred to final R1 validation.
- Browser screenshot validation of every admin screen.

## Screens/Pages Implemented

- Administration dashboard.
- Create administrator record.
- Edit administrator record.
- Activation page.
- Reset password page.

## Remaining Development Blockers

No blocker prevents continued Day 35 admin extension development. Full R1 closure remains pending durable invitation lifecycle, deeper permission enforcement, SMTP operational proof, and final validation.
