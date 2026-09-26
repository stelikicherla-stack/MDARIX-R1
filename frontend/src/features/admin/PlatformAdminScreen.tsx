import { useEffect, useMemo, useState } from "react";
import {
  Activity, AlertTriangle, ArrowLeft, Bell, CheckCircle2, ChevronRight, Clock3,
  Database, ExternalLink, LayoutDashboard, LifeBuoy, LockKeyhole, Plus, RefreshCw,
  Search, Settings2, ShieldCheck, Users,
} from "lucide-react";
import { requestJson } from "../../app/apiClient";

type PlatformAdminScreenProps = {
  securityContext: { display_name: string; active_role: string | null; tenant_id?: string } | null;
  onNavigate: (view: any) => void;
};

type DataKey = "users" | "roles" | "permissions" | "memberships" | "personas" |
  "entitlements" | "connectors" | "mappings" | "dataMappings" | "audit" | "customers" | "plans";

type AdminData = Record<DataKey, any[]> & {
  health: { status?: string; metrics?: Record<string, number>; alerts?: any[]; recent_audit?: any[] };
  ai: any;
  security: any;
  operations: any;
};

const EMPTY_DATA: AdminData = {
  users: [], roles: [], permissions: [], memberships: [], personas: [], entitlements: [],
  connectors: [], mappings: [], dataMappings: [], audit: [], customers: [], plans: [], health: {},
  ai: null, security: null, operations: null,
};

const api = <T,>(path: string) => requestJson<T>(path);
const list = (value: any): any[] => Array.isArray(value) ? value : value?.items ?? value?.results ?? value?.customers ?? value?.plans ?? [];
const text = (value: unknown, fallback = "—") => value === null || value === undefined || value === "" ? fallback : String(value);
const title = (value: string) => value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());

const DOMAINS = [
  ["Platform Overview", "Health, activity and attention", LayoutDashboard, ["Overview"]],
  ["Customers & Tenants", "Directory, provisioning and health", Users, ["Customers", "Tenants", "Administrators", "Provisioning", "Tenant health"]],
  ["Plans & Licensing", "Plans, subscriptions and reminders", Settings2, ["Plans", "Entitlements", "Subscriptions", "Expirations", "Reminder rules"]],
  ["Identity & Access", "Platform users, roles and sessions", LockKeyhole, ["Platform users", "Platform roles", "Permission sets", "MFA & SSO", "Sessions"]],
  ["Data & Configuration", "Master data, mappings and releases", Database, ["Master data", "Data mapping", "Mapping versions", "Configuration releases"]],
  ["Integrations", "Connectors, schemas and ingestion", ExternalLink, ["Connector catalog", "Customer integrations", "Webhooks", "Integration health", "Failures & logs"]],
  ["AI Control Center", "Models, evaluations and assurance", ShieldCheck, ["AI overview", "Models & versions", "Agents & prompts", "Evaluations", "Guardrails", "AI executions"]],
  ["Security & Compliance", "Isolation, encryption and controls", LockKeyhole, ["Security overview", "Tenant isolation", "Encryption & residency", "Retention", "Access reviews"]],
  ["Audit & Evidence", "Events, signatures and release evidence", ShieldCheck, ["Platform audit trail", "Configuration changes", "Electronic signatures", "Release evidence"]],
  ["Operations & Setup", "Queues, monitoring, storage and incidents", LifeBuoy, ["System health", "Jobs & queues", "Storage", "Incidents", "System settings"]],
] as const;

const SOURCES: Array<[string, string, string]> = [
  ["users", "/api/v1/admin/identity/users", "Identity users"],
  ["roles", "/api/v1/admin/identity/roles", "Roles"],
  ["permissions", "/api/v1/admin/identity/permission-sets", "Permission sets"],
  ["memberships", "/api/v1/admin/identity/memberships", "Memberships"],
  ["personas", "/api/v1/admin/identity/persona-assignments", "Personas"],
  ["entitlements", "/api/v1/admin/governance/entitlements", "Entitlements"],
  ["connectors", "/api/v1/admin/configuration/connectors", "Connectors"],
  ["mappings", "/api/v1/admin/configuration/mappings", "Mappings"],
  ["dataMappings", "/api/v1/admin/configuration/data-mappings", "Data mapping fields"],
  ["audit", "/api/v1/admin/audit-history", "Audit history"],
  ["customers", "/api/v1/platform-admin/customers", "Customers"],
  ["plans", "/api/v1/platform-admin/plans", "Plans"],
  ["health", "/api/v1/admin/health-summary", "Platform health"],
  ["ai", "/api/v1/admin/ai-summary", "AI control summary"],
  ["security", "/api/v1/admin/security-summary", "Security summary"],
  ["operations", "/api/v1/admin/operations-summary", "Operations summary"],
];

function RecordTable({ rows, columns, empty }: { rows: any[]; columns: Array<[string, (row: any) => unknown]>; empty: string }) {
  if (!rows.length) return <div className="platform-admin-empty"><Database size={25} /><strong>{empty}</strong><span>No authorized records were returned by the server.</span></div>;
  return <div className="platform-admin-table-wrap"><table className="platform-admin-table"><thead><tr>{columns.map(([label]) => <th key={label}>{label}</th>)}</tr></thead><tbody>{rows.slice(0, 12).map((row, index) => <tr key={row.id ?? row.code ?? row.email ?? index}>{columns.map(([label, get]) => <td key={label}>{text(get(row))}</td>)}</tr>)}</tbody></table></div>;
}

export function PlatformAdminScreen({ securityContext, onNavigate }: PlatformAdminScreenProps) {
  const [data, setData] = useState<AdminData>(EMPTY_DATA);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [activeDomain, setActiveDomain] = useState("Platform Overview");
  const [activeItem, setActiveItem] = useState("Overview");
  const [collapsedDomain, setCollapsedDomain] = useState<string | null>(null);
  const [refreshVersion, setRefreshVersion] = useState(0);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  useEffect(() => {
    let current = true;
    Promise.allSettled(SOURCES.map(([, path]) => api<any>(path))).then((results) => {
      if (!current) return;
      const next: AdminData = { ...EMPTY_DATA };
      const failed: string[] = [];
      results.forEach((result, index) => {
        const [key, , label] = SOURCES[index];
        if (result.status === "rejected") { failed.push(label); return; }
        if (["health", "ai", "security", "operations"].includes(key)) (next as any)[key] = result.value ?? {};
        else (next as any)[key] = list(result.value);
      });
      setData(next);
      setUnavailable(failed);
      setLastUpdated(new Date());
      setLoading(false);
    });
    return () => { current = false; };
  }, [refreshVersion]);

  const selectDomain = (domain: typeof DOMAINS[number]) => {
    setActiveDomain(domain[0]);
    setActiveItem(domain[3][0]);
    setCollapsedDomain(null);
  };
  const metrics = data.health?.metrics ?? {};
  const alerts = data.health?.alerts ?? [];
  const activity = (data.health?.recent_audit ?? data.audit).slice(0, 8);
  const setupItems = DOMAINS.flatMap((domain) => domain[3].map((label) => ({ domain, label })));
  const searchResults = query.trim() ? setupItems.filter(({ domain, label }) => `${domain[0]} ${domain[1]} ${label}`.toLowerCase().includes(query.toLowerCase())).slice(0, 8) : [];
  const filteredActivity = useMemo(() => activity.filter((event: any) => JSON.stringify(event).toLowerCase().includes(query.toLowerCase())), [activity, query]);

  const summary = activeDomain === "AI Control Center" ? data.ai : activeDomain === "Security & Compliance" ? data.security : activeDomain === "Operations & Setup" || activeDomain === "Integrations" ? data.operations : null;

  const signOut = async () => {
    await requestJson("/api/v1/auth/signout", { method: "POST", retries: 0 }).catch(() => undefined);
    window.location.replace("/signin");
  };

  const renderOverview = () => <>
    <section className="platform-admin-command-grid">
      <article className="platform-admin-command-card primary"><span className="eyebrow">Command center</span><h3>Platform operations at a glance</h3><p>Review tenant posture, commercial access, integrations, security controls, AI assurance, and governed activity.</p><div className="platform-admin-quick-actions"><button onClick={() => onNavigate("admin-create-customer")}><Plus size={15} /> Provision customer</button><button onClick={() => { setActiveDomain("Security & Compliance"); setActiveItem("Security overview"); }}><ShieldCheck size={15} /> Review security</button><button onClick={() => { setActiveDomain("Integrations"); setActiveItem("Integration health"); }}><Activity size={15} /> Integration health</button></div></article>
      <article className="platform-admin-command-card posture"><div><span className="platform-admin-status-light healthy" /><span>Platform posture</span><strong>{data.health.status ?? "Status unavailable"}</strong></div><div><span className="platform-admin-status-light" /><span>Authorized data sources</span><strong>{SOURCES.length - unavailable.length} of {SOURCES.length}</strong></div><div><Clock3 size={16} /><span>Last synchronized</span><strong>{lastUpdated ? lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Not synchronized"}</strong></div></article>
    </section>
    <section className="platform-admin-card platform-admin-control-map"><div className="platform-admin-card-title"><div><span className="eyebrow">Governance map</span><h3>One control plane across the product</h3><p>Move from customer boundary and commercial access through data, intelligence, assurance, and operations.</p></div><span className="platform-admin-badge success">Server authorized</span></div><div className="platform-admin-control-flow">{[
      ["Customers & Tenants", "Establish boundaries", Users], ["Plans & Licensing", "Control commercial access", Settings2], ["Data & Configuration", "Govern product context", Database], ["Integrations", "Operate trusted sources", ExternalLink], ["AI Control Center", "Assure advisory AI", ShieldCheck], ["Audit & Evidence", "Preserve accountability", CheckCircle2],
    ].map(([label, description, Icon]: any, index) => <button key={label} onClick={() => { const domain = DOMAINS.find((entry) => entry[0] === label); if (domain) selectDomain(domain); }}><span>{String(index + 1).padStart(2, "0")}</span><Icon size={21} /><strong>{label}</strong><small>{description}</small><ChevronRight size={15} /></button>)}</div></section>
    <section className="platform-admin-metrics">
      {[
        ["Customers", data.customers.length || data.memberships.length, "Customers & Tenants", Users],
        ["Platform users", data.users.length, "Identity & Access", ShieldCheck],
        ["Active connectors", data.connectors.filter((item) => !["INACTIVE", "FAILED"].includes(String(item.status).toUpperCase())).length, "Integrations", Database],
        ["Pending approvals", metrics.pending_approvals ?? 0, "Audit & Evidence", CheckCircle2],
      ].map(([label, value, domainName, Icon]: any) => <button key={label} onClick={() => { const domain = DOMAINS.find((item) => item[0] === domainName); if (domain) selectDomain(domain); }}><Icon size={19} /><span>{label}</span><strong>{value}</strong><small>Open workspace <ChevronRight size={13} /></small></button>)}
    </section>
    <section className="platform-admin-columns">
      <article className="platform-admin-card"><div className="platform-admin-card-title"><div><span className="eyebrow">Action queue</span><h3>Requires attention</h3></div><span className={`platform-admin-badge ${alerts.length ? "warning" : "success"}`}>{alerts.length ? `${alerts.length} open` : "All clear"}</span></div>{alerts.length ? alerts.slice(0, 6).map((alert: any, index: number) => <button className="platform-admin-alert" key={alert.code ?? index} onClick={() => { setActiveDomain("Operations & Setup"); setActiveItem("Incidents"); }}><AlertTriangle size={16} /><span><strong>{alert.label ?? alert.code ?? "Operational alert"}</strong><small>{text(alert.count, "Review")} · {text(alert.severity, "Review")}</small></span><ChevronRight size={15} /></button>) : <div className="platform-admin-empty compact"><CheckCircle2 size={24} /><strong>No active alerts</strong><span>Platform services have not returned an action-required item.</span></div>}</article>
      <article className="platform-admin-card"><div className="platform-admin-card-title"><div><span className="eyebrow">Platform health</span><h3>Service posture</h3></div><span className="platform-admin-badge success">Monitored</span></div>{[["API and database", data.health.status ?? "Unknown"], ["Connector failures", metrics.connector_failures ?? 0], ["Mapping issues", metrics.mapping_issues ?? 0], ["Security events", metrics.security_events ?? 0]].map(([label, value]) => <div className="platform-admin-health-row" key={label}><span>{label}</span><strong>{value}</strong></div>)}</article>
    </section>
    <section className="platform-admin-card"><div className="platform-admin-card-title"><div><span className="eyebrow">Audit evidence</span><h3>Recent platform activity</h3></div><button className="platform-admin-link" onClick={() => { setActiveDomain("Audit & Evidence"); setActiveItem("Platform audit trail"); }}>View audit <ChevronRight size={14} /></button></div>{filteredActivity.length ? filteredActivity.map((event: any, index: number) => <div className="platform-admin-activity" key={event.id ?? index}><span className="platform-admin-activity-dot" /><strong>{event.action ?? "Platform event"}</strong><span>{event.entity_type ?? event.object_type ?? "Administrative record"}</span><small>{event.created_at ? String(event.created_at).slice(0, 19).replace("T", " ") : "Server recorded"}</small></div>) : <div className="platform-admin-empty compact"><ShieldCheck size={24} /><strong>No recent activity</strong><span>No matching authorized audit events were returned.</span></div>}</section>
  </>;

  const renderWorkspace = () => {
    if (activeDomain === "Platform Overview") return renderOverview();
    if (activeDomain === "Customers & Tenants") {
      if (activeItem === "Provisioning") return <section className="platform-admin-card platform-admin-process"><div><span className="eyebrow">Governed onboarding</span><h3>Provision a customer tenant</h3><p>Create immutable customer and tenant identities, assign commercial access, establish security controls, and invite the first Customer Administrator.</p></div><ol><li><strong>Organization</strong><span>Legal identity and approved domains</span></li><li><strong>Tenant boundary</strong><span>Region, residency and immutable identifier</span></li><li><strong>Commercial access</strong><span>Plan version, seats and entitlements</span></li><li><strong>Security baseline</strong><span>MFA, configuration and isolation checks</span></li></ol><button className="platform-admin-primary" onClick={() => onNavigate("admin-create-customer")}><Plus size={15} /> Start provisioning</button></section>;
      if (activeItem === "Tenant health") return <section className="platform-admin-card"><div className="platform-admin-card-title"><div><span className="eyebrow">Isolation and service checks</span><h3>Current tenant posture</h3></div><span className="platform-admin-badge success">Server evaluated</span></div><div className="platform-admin-summary-grid">{[["Customers monitored", data.customers.length], ["Security events", metrics.security_events ?? 0], ["Connector failures", metrics.connector_failures ?? 0], ["Mapping issues", metrics.mapping_issues ?? 0]].map(([label, value]) => <div key={label}><small>{label}</small><strong>{value}</strong></div>)}</div></section>;
      if (activeItem === "Tenants") return <section className="platform-admin-card"><RecordTable rows={data.memberships.length ? data.memberships : data.customers} empty="No tenants available" columns={[["Tenant", (r) => r.tenant_name ?? r.display_name ?? r.name], ["Immutable tenant ID", (r) => r.tenant_id ?? r.id ?? r.tenant_key], ["Environment", (r) => r.environment ?? "Production"], ["Boundary status", (r) => r.tenant_status ?? r.status], ["Residency", (r) => r.data_residency ?? r.region]]} /></section>;
      if (activeItem === "Administrators") return <section className="platform-admin-card"><RecordTable rows={data.users.filter((row) => String(row.active_role ?? row.role ?? "").toLowerCase().includes("admin"))} empty="No customer administrators available" columns={[["Administrator", (r) => r.display_name ?? r.name], ["Email", (r) => r.email], ["Tenant", (r) => r.tenant_id], ["Role", (r) => r.active_role ?? r.role], ["Status", (r) => r.status]]} /></section>;
      return <section className="platform-admin-card"><RecordTable rows={data.customers.length ? data.customers : data.memberships} empty="No customers available" columns={[["Customer", (r) => r.display_name ?? r.legal_name ?? r.name], ["Customer ID", (r) => r.customer_id ?? r.id], ["Tenant", (r) => r.tenant_key ?? r.tenant_id], ["Plan", (r) => r.plan_name ?? r.plan_code], ["Status", (r) => r.status ?? r.tenant_status]]} /></section>;
    }
    if (activeDomain === "Plans & Licensing") {
      if (activeItem === "Reminder rules") return <section className="platform-admin-card platform-admin-policy-view"><div><span className="eyebrow">Lifecycle communications</span><h3>Reminder policy controls</h3><p>Commercial reminders resolve the subscription, policy version, recipients, delivery window, and expiry version before an outbox item is created.</p></div><div className="platform-admin-boundary-list"><span><CheckCircle2 size={16}/> Duplicate-safe lifecycle key</span><span><CheckCircle2 size={16}/> Recipient resolution at send time</span><span><CheckCircle2 size={16}/> Delivery status is audit recorded</span></div></section>;
      const rows = activeItem === "Entitlements" ? data.entitlements : activeItem === "Plans" ? data.plans : data.customers;
      const columns: Array<[string, (row: any) => unknown]> = activeItem === "Plans" ? [["Plan", (r) => r.name ?? r.display_name ?? r.code], ["Version", (r) => r.version], ["Seat rule", (r) => r.seat_cap ?? r.seat_rule], ["Status", (r) => r.status]] : activeItem === "Entitlements" ? [["Entitlement", (r) => r.name ?? r.code], ["Feature", (r) => r.feature_code], ["Limit", (r) => r.limit_value ?? r.value], ["Status", (r) => r.status]] : [["Customer", (r) => r.display_name ?? r.name], ["Plan", (r) => r.plan_name ?? r.plan_code], [activeItem === "Expirations" ? "Expires" : "Subscription status", (r) => activeItem === "Expirations" ? r.expires_at ?? r.expiry_date : r.license_status ?? r.status], ["Seats", (r) => r.seat_usage ?? r.seat_cap]];
      return <section className="platform-admin-card"><RecordTable rows={rows} empty={`No ${activeItem.toLowerCase()} available`} columns={columns} /></section>;
    }
    if (activeDomain === "Identity & Access") {
      if (["MFA & SSO", "Sessions"].includes(activeItem)) return <section className="platform-admin-card platform-admin-policy-view"><div><span className="eyebrow">Identity assurance</span><h3>{activeItem === "Sessions" ? "Session control posture" : "Authentication policy posture"}</h3><p>{activeItem === "Sessions" ? "Review durable sessions, expiry, revocation, and concurrent access controls without exposing session secrets." : "Platform identities use governed MFA and SSO policy boundaries. Tenant administrators cannot grant platform privilege."}</p></div><div className="platform-admin-summary-grid">{[["Platform identities", data.users.length], ["Active roles", data.roles.length], ["Security events", metrics.security_events ?? 0]].map(([label, value]) => <div key={label}><small>{label}</small><strong>{value}</strong></div>)}</div></section>;
      const rows = activeItem === "Platform roles" ? data.roles : activeItem === "Permission sets" ? data.permissions : data.users;
      return <section className="platform-admin-card"><RecordTable rows={rows} empty={`No ${activeItem.toLowerCase()} available`} columns={[["Identity / record", (r) => r.display_name ?? r.name ?? r.email ?? r.code], ["Email / code", (r) => r.email ?? r.code], ["Role", (r) => r.active_role ?? r.role ?? r.role_name], ["Status", (r) => r.status ?? "Configured"]]} /></section>;
    }
    if (activeDomain === "Data & Configuration") {
      if (activeItem === "Data mapping") return <section className="platform-admin-card platform-admin-data-mapping"><div className="platform-admin-card-title"><div><span className="eyebrow">External → MDARIX configuration</span><h3>Customer database field mappings</h3><p>Each row records how an authorized customer source field is transformed into a tenant-scoped MDARIX canonical field.</p></div><span className="platform-admin-badge success">Tenant scoped</span></div><RecordTable rows={data.dataMappings} empty="No field mappings are configured. Create a mapping configuration with source and target field rules." columns={[["External database", (r) => r.source_database], ["External table", (r) => `${r.source_schema ?? "customer"}.${r.source_table ?? "Not configured"}`], ["External field", (r) => r.source_field], ["MDARIX table", (r) => `${r.target_schema ?? "public"}.${r.target_table ?? "Not configured"}`], ["MDARIX field", (r) => r.target_field], ["Transform", (r) => r.transform], ["Required", (r) => r.required ? "Yes" : "No"], ["Status", (r) => `${r.status ?? "DRAFT"} · ${r.version ?? "v1"}`]]} /></section>;
      return <section className="platform-admin-card"><RecordTable rows={data.mappings} empty={`No ${activeItem.toLowerCase()} records available`} columns={activeItem === "Mapping versions" ? [["Mapping", (r) => r.name ?? r.code], ["Version", (r) => r.version], ["Lifecycle", (r) => r.status], ["Updated", (r) => r.updated_at]] : [[activeItem, (r) => r.name ?? r.code ?? r.mapping_name], ["Source", (r) => r.source_system ?? r.source_entity], ["Target", (r) => r.target_entity], ["Status", (r) => r.status]]} /></section>;
    }
    if (activeDomain === "Integrations") { const rows = activeItem === "Failures & logs" ? data.connectors.filter((r) => ["FAILED", "DEGRADED", "ERROR"].includes(String(r.status ?? r.health_status).toUpperCase())) : data.connectors; return <section className="platform-admin-card"><RecordTable rows={rows} empty={activeItem === "Failures & logs" ? "No connector failures recorded" : `No ${activeItem.toLowerCase()} available`} columns={activeItem === "Integration health" || activeItem === "Failures & logs" ? [["Connector", (r) => r.name ?? r.code], ["Health", (r) => r.health_status ?? r.status], ["Last check", (r) => r.last_health_check ?? r.updated_at], ["Failure", (r) => r.last_error ?? r.error_code]] : [["Connector", (r) => r.name ?? r.code ?? r.provider], ["Provider", (r) => r.provider ?? r.connector_type], ["Schema", (r) => r.schema_version], ["Status", (r) => r.status ?? r.health_status]]} /></section>; }
    if (activeDomain === "AI Control Center") return <section className="platform-admin-card platform-admin-control-detail"><div className="platform-admin-card-title"><div><span className="eyebrow">AI governance</span><h3>{activeItem}</h3><p>Review provider configuration, model versions, evaluation evidence, guardrails, and human-review requirements before advisory output reaches a decision workflow.</p></div><span className="platform-admin-badge success">Human review required</span></div><div className="platform-admin-summary-grid">{[["Provider", data.ai?.provider ?? "Configured"], ["Model", data.ai?.model ?? "Versioned"], ["Executions", data.ai?.executions ?? 0], ["Evaluation status", data.ai?.status ?? "Monitored"]].map(([label, value]) => <div key={label}><small>{label}</small><strong>{text(value)}</strong></div>)}</div><div className="platform-admin-boundary-list"><span><CheckCircle2 size={16}/> Authorized tenant context is applied before execution</span><span><CheckCircle2 size={16}/> Evidence provenance and uncertainty remain visible</span><span><CheckCircle2 size={16}/> No hidden chain-of-thought is persisted</span></div></section>;
    if (activeDomain === "Security & Compliance") return <section className="platform-admin-card platform-admin-control-detail"><div className="platform-admin-card-title"><div><span className="eyebrow">Security posture</span><h3>{activeItem}</h3><p>Inspect tenant isolation, encryption, retention, access review, and control evidence from the server-authorized security posture.</p></div><span className={`platform-admin-badge ${data.security?.status === "HEALTHY" ? "success" : "warning"}`}>{data.security?.status ?? "Review"}</span></div><div className="platform-admin-summary-grid">{[["Isolation checks", metrics.isolation_checks ?? "Recorded"], ["Security events", metrics.security_events ?? 0], ["Encryption", data.security?.encryption ?? "Policy controlled"], ["Retention", data.security?.retention ?? "Configured"]].map(([label, value]) => <div key={label}><small>{label}</small><strong>{text(value)}</strong></div>)}</div><div className="platform-admin-boundary-list"><span><CheckCircle2 size={16}/> Cross-tenant access is denied by server policy</span><span><CheckCircle2 size={16}/> Protected fields are excluded from unauthorized responses</span><span><CheckCircle2 size={16}/> Audit evidence is append-only</span></div></section>;
    if (activeDomain === "Operations & Setup") return <section className="platform-admin-card platform-admin-control-detail"><div className="platform-admin-card-title"><div><span className="eyebrow">Operational control</span><h3>{activeItem}</h3><p>Monitor workers, queues, storage, incidents, and system configuration with explicit service state and actionable next steps.</p></div><span className={`platform-admin-badge ${data.operations?.status === "HEALTHY" ? "success" : "warning"}`}>{data.operations?.status ?? "Review"}</span></div><div className="platform-admin-summary-grid">{[["Queue depth", data.operations?.queue_depth ?? metrics.queue_depth ?? 0], ["Failed jobs", metrics.failed_jobs ?? 0], ["Dead letters", metrics.dead_letters ?? 0], ["Storage", data.operations?.storage ?? "Available"]].map(([label, value]) => <div key={label}><small>{label}</small><strong>{text(value)}</strong></div>)}</div><div className="platform-admin-boundary-list"><span><CheckCircle2 size={16}/> Worker heartbeat and retry state are monitored</span><span><CheckCircle2 size={16}/> Dead-letter items remain replayable and audited</span><span><CheckCircle2 size={16}/> Storage access is tenant-scoped</span></div></section>;
    if (activeDomain === "Audit & Evidence") { const term = activeItem === "Electronic signatures" ? "SIGN" : activeItem === "Configuration changes" ? "CONFIG" : activeItem === "Release evidence" ? "RELEASE" : ""; const rows = term ? data.audit.filter((r) => JSON.stringify(r).toUpperCase().includes(term)) : data.audit; return <section className="platform-admin-card"><RecordTable rows={rows} empty={`No ${activeItem.toLowerCase()} available`} columns={[["Action", (r) => r.action], ["Actor", (r) => r.actor_display_name ?? r.user_id], ["Object", (r) => r.entity_type ?? r.object_type], ["Reason", (r) => r.reason], ["Recorded", (r) => r.created_at ?? r.timestamp]]} /></section>; }
    return <section className="platform-admin-card"><div className="platform-admin-card-title"><div><span className="eyebrow">Server-derived status</span><h3>Control status</h3></div><span className={`platform-admin-badge ${summary?.status === "HEALTHY" ? "success" : "warning"}`}>{summary?.status ?? "No status"}</span></div>{Object.keys(summary?.metrics ?? {}).length ? <div className="platform-admin-summary-grid">{Object.entries(summary.metrics).map(([label, value]) => <div key={label}><small>{title(label)}</small><strong>{text(value)}</strong></div>)}</div> : <div className="platform-admin-empty compact"><Database size={24} /><strong>No metrics available</strong><span>This service returned no authorized operational metrics.</span></div>}</section>;
  };

  if (loading) return <div className="content platform-admin-screen"><section className="platform-admin-loading">Loading governed platform data…</section></div>;

  return <div className="content platform-admin-screen">
    <header className="platform-admin-topbar">
      <div className="platform-admin-identity"><span className="platform-admin-brand">MDARIX</span><span className="platform-admin-divider">Platform administration</span></div>
      <div className="platform-admin-search-wrap"><label className="platform-admin-search"><Search size={17} aria-hidden="true" /><input aria-label="Search platform setup" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search customers, integrations, security…" /></label>{searchResults.length > 0 && <div className="platform-admin-search-results">{searchResults.map(({ domain, label }) => <button key={`${domain[0]}-${label}`} onClick={() => { selectDomain(domain); setActiveItem(label); setQuery(""); }}><strong>{label}</strong><small>{domain[0]}</small></button>)}</div>}</div>
      <div className="platform-admin-user"><Bell size={17} aria-label="Notifications" /><span>{securityContext?.display_name ?? "Administrator"}</span><small>{securityContext?.active_role ?? "Platform Administrator"}</small><button className="platform-admin-logout" onClick={signOut}>Logout</button></div>
    </header>
    <section className="platform-admin-hero compact"><div><span className="eyebrow">Administrator control plane</span><h1>Govern the MDARIX platform</h1><p>Customers, access, configuration, integrations, AI assurance, security, and operational evidence in one workspace.</p></div><div className="platform-admin-hero-status"><ShieldCheck size={22} /><strong>Controlled administration</strong><span>Server-authorized · audit recorded</span></div></section>
    <div className="platform-admin-layout">
      <aside className="platform-admin-sidebar" aria-label="Platform administration domains"><span className="platform-admin-sidebar-title">Control plane</span>{DOMAINS.map((domain) => { const [label, description, Icon, items] = domain; const expanded = activeDomain === label && collapsedDomain !== label; return <div className="platform-admin-domain" key={label}><button className={activeDomain === label ? "active" : ""} aria-expanded={items.length > 1 ? expanded : undefined} title="Click to open. Double-click to collapse subsections." onClick={() => { if (activeDomain === label && collapsedDomain === label) setCollapsedDomain(null); else selectDomain(domain); }} onDoubleClick={() => { if (items.length > 1) { setActiveDomain(label); setCollapsedDomain(label); } }}><Icon size={17} /><span><strong>{label}</strong><small>{description}</small></span><ChevronRight className={expanded ? "expanded" : ""} size={15} /></button>{expanded && items.length > 1 && <div className="platform-admin-subnav">{items.map((item) => <button className={activeItem === item ? "selected" : ""} key={item} onClick={() => setActiveItem(item)}>{item}</button>)}</div>}</div>; })}</aside>
      <main className="platform-admin-workspace" data-admin-view={`${activeDomain}:${activeItem}`}>
        {activeDomain !== "Platform Overview" && <div className="platform-admin-heading"><div><button className="platform-admin-back" onClick={() => { setActiveDomain("Platform Overview"); setActiveItem("Overview"); }}><ArrowLeft size={15} /> Platform overview</button><span className="eyebrow">{activeDomain}</span><h2>{activeItem}</h2><p>{DOMAINS.find((domain) => domain[0] === activeDomain)?.[1]}</p></div><div className="platform-admin-heading-actions"><span><Clock3 size={14} /> {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}` : "Awaiting refresh"}</span><button className="platform-admin-refresh" onClick={() => { setLoading(true); setRefreshVersion((value) => value + 1); }} aria-label="Refresh platform data"><RefreshCw size={16} /> Refresh</button>{activeDomain === "Customers & Tenants" && <button className="platform-admin-primary" onClick={() => onNavigate("admin-create-customer")}><Plus size={16} /> New customer</button>}</div></div>}
        {unavailable.length > 0 && <div className="platform-admin-source-warning" role="status"><AlertTriangle size={17} /><span><strong>Some sources are temporarily unavailable.</strong> Available data is shown below.</span><details><summary>View sources</summary>{unavailable.join(", ")}</details></div>}
        {renderWorkspace()}
      </main>
    </div>
  </div>;
}
