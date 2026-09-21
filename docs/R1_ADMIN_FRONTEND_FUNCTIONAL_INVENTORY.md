# R1 Admin Frontend Functional Inventory

| Area | Page | Route | Persona | Tenant Scoped? | Plan Controlled? | Permission Controlled? | Backend API | Implemented? | Focused Test? | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| Authentication | Sign In | `/signin` | All | Yes | No | Yes | `/api/v1/auth/signin` | Yes | Existing | Uses persisted `AuthUser`. |
| Authentication | Activate Account | `/activate-account` | Invited user | Yes | No | Token | `/api/v1/auth/activate-account` | Yes | Yes | User creates own password. |
| Authentication | Forgot Password | `/forgot-password` | All | Yes | No | Token | `/api/v1/auth/forgot-password` | Yes | Existing | Sends reset where SMTP is configured. |
| Authentication | Reset Password | `/reset-password` | All | Yes | No | Token | `/api/v1/auth/reset-password` | Yes | Yes | No admin-visible password. |
| Customer Admin | Dashboard | `/app/admin` | Customer Admin | Yes | Yes | Yes | Admin summary APIs | Yes | Existing | Same control-plane surface, tenant-scoped. |
| Customer Admin | Users | `/app/admin` | Customer Admin | Yes | Yes | Yes | `/api/v1/admin/identity/users` | Yes | Yes | Invite-only creation. |
| Customer Admin | Roles | `/app/admin` | Customer Admin | Yes | Deferred | Yes | `/api/v1/admin/identity/roles` | Yes | Existing | Platform role assignment blocked server-side. |
| Customer Admin | Permission Sets | `/app/admin` | Customer Admin | Yes | Deferred | Yes | `/api/v1/admin/identity/permission-sets` | Yes | Existing | Field/action matrix stored as JSON. |
| Customer Admin | Integrations | `/app/admin` | Customer Admin | Yes | Yes | Yes | `/api/v1/admin/configuration/connectors` | Yes | Existing | Secrets rejected by configuration safety. |
| Customer Admin | Mappings | `/app/admin` | Customer Admin | Yes | Yes | Yes | `/api/v1/admin/configuration/mappings` | Yes | Existing | Tenant mapping scope preserved. |
| Customer Admin | Administrative Audit | `/app/admin` | Customer Admin | Yes | No | Yes | `/api/v1/admin/audit-history` | Yes | Existing | Tenant-scoped events. |
| MDARIX Admin | Platform Customers | API-backed | Platform Admin | Platform | Yes | Yes | `/api/v1/platform-admin/customers` | Backend yes | Yes | Dedicated frontend route deferred. |
| MDARIX Admin | Customer Admin Invite | `/app/admin` | Platform Admin | Authorized target tenant | Yes | Yes | `/api/v1/admin/identity/users` | Yes | Yes | `target_tenant_id` accepted only for Platform Admin. |
| MDARIX Admin | Plans And Subscriptions | API-backed | Platform Admin | Platform | Yes | Yes | Plan/entitlement models | Partial | No | Full screen deferred. |
| MDARIX Admin | Connector Catalog | `/app/admin` | Platform Admin | Platform | Deferred | Yes | Existing connector APIs | Partial | Existing | Platform catalog editing remains future work. |
| MDARIX Admin | Master Mapping | `/app/admin` | Platform Admin | Platform | Deferred | Yes | `/api/v1/admin/catalog/master-mappings` | Partial | Existing | Existing tenant mapping is not auto-replaced. |
| MDARIX Admin | Platform Audit | `/app/admin` | Platform Admin | Platform | No | Yes | `/api/v1/admin/audit-history` | Partial | Existing | Broader platform audit views deferred. |
