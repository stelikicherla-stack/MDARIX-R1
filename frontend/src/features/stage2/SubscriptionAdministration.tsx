import { useEffect, useState } from "react";

type Customer = { id: string; name: string; tenant_key: string };
type Plan = { id: string; code?: string; name?: string; version?: string; status?: string };

export function SubscriptionAdministration() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [plans, setPlans] = useState<Plan[]>([]);
  const [tenantId, setTenantId] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [expiring, setExpiring] = useState<any[]>([]);
  const [policy, setPolicy] = useState({ name: "Standard renewal reminders", thresholds: "60,30,7", timezone: "UTC" });
  const [template, setTemplate] = useState({ stage: "30_DAY", subject: "MDARIX subscription renewal reminder", body: "Hello {{customer_name}}, your subscription expires on {{expiry_date}}.", version: "v1" });
  const [change, setChange] = useState({ plan_id: "", starts_at: "", expires_at: "", grace_ends_at: "", reason: "" });

  useEffect(() => {
    const load = async () => {
      try {
        const [customersResponse, plansResponse, expiryResponse] = await Promise.all([
          fetch("/api/v1/platform/customers", { credentials: "include" }),
          fetch("/api/v1/platform-admin/plans", { credentials: "include" }),
          fetch("/api/v1/platform/subscriptions/expiring", { credentials: "include" }),
        ]);
        if (!customersResponse.ok || !plansResponse.ok || !expiryResponse.ok) throw new Error("Subscription data is unavailable");
        const customerRows = await customersResponse.json(); const planRows = await plansResponse.json();
        setCustomers(customerRows); setPlans(planRows.items ?? planRows); setExpiring(await expiryResponse.json());
      } catch (e) { setError(e instanceof Error ? e.message : "Subscription data is unavailable"); }
    };
    load();
  }, []);

  const post = async (url: string, body: unknown) => {
    const response = await fetch(url, { method: "POST", credentials: "include", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await response.json(); if (!response.ok) throw new Error(data.detail?.message ?? "Request failed"); return data;
  };
  const savePolicy = async () => { if (!tenantId) return setError("Select a customer tenant first."); try { const result = await post(`/api/v1/platform/subscriptions/${tenantId}/reminder-policies`, { name: policy.name, thresholds: policy.thresholds.split(",").map(Number), timezone: policy.timezone, recipient_types: ["CUSTOMER_ADMIN"], version: "v1" }); setMessage(`Reminder policy ${result.version} saved.`); setError(""); } catch (e) { setError((e as Error).message); } };
  const saveTemplate = async () => { if (!tenantId) return setError("Select a customer tenant first."); try { const result = await post(`/api/v1/platform/subscriptions/${tenantId}/email-templates`, { ...template, allowed_variables: ["customer_name", "expiry_date", "days_remaining"] }); setMessage(`Email template ${result.stage} ${result.version} saved as ${result.status}.`); setError(""); } catch (e) { setError((e as Error).message); } };
  const runLifecycle = async () => { try { const result = await post("/api/v1/platform/subscriptions/lifecycle/run", {}); setMessage(`Lifecycle run complete: ${result.queued} reminder(s) queued, ${result.transitioned} transition(s).`); setError(""); } catch (e) { setError((e as Error).message); } };
  const changePlan = async () => { if (!tenantId || !change.plan_id || !change.starts_at || !change.expires_at || change.reason.trim().length < 3) return setError("Tenant, published plan, dates, and a reason are required."); try { const result = await post(`/api/v1/platform/customers/${tenantId}/subscription`, change); setMessage(`Subscription changed successfully. Expiry version: ${result.expiry_version}.`); setError(""); } catch (e) { setError((e as Error).message); } };

  return <div className="content governance-view subscription-admin-page">
    <section className="governance-hero"><div><span className="eyebrow">Platform administration</span><h2>Subscriptions &amp; notifications</h2><p>Manage plan lifecycle, renewal reminders, approved communication templates, and bounded grace periods.</p></div><div className="governance-status"><strong>Commercial controls</strong><span>Platform Administrator only · audited</span></div></section>
    <section className="panel subscription-toolbar"><label>Customer tenant<select value={tenantId} onChange={(e) => setTenantId(e.target.value)}><option value="">Select customer</option>{customers.map((customer) => <option key={customer.id} value={customer.id}>{customer.name} ({customer.tenant_key})</option>)}</select></label><button className="primary-action" onClick={runLifecycle}>Run lifecycle check</button></section>
    {message && <p className="review-success" role="status">{message}</p>}{error && <p className="field-error" role="alert">{error}</p>}
    <section className="panel subscription-edit"><div className="section-title">Change plan / subscription</div><p>Changes are versioned, audited, and applied only to the selected tenant. Existing users and records are preserved.</p><div className="admin-form-grid"><label>Published plan<select value={change.plan_id} onChange={(e) => setChange({ ...change, plan_id: e.target.value })}><option value="">Select a published plan</option>{plans.filter((plan) => !plan.status || plan.status === "ACTIVE" || plan.status === "PUBLISHED").map((plan) => <option key={plan.id} value={plan.id}>{plan.name ?? plan.code} · {plan.version ?? "published"}</option>)}</select></label><label>Starts at<input type="datetime-local" value={change.starts_at} onChange={(e) => setChange({ ...change, starts_at: e.target.value })} /></label><label>Expires at<input type="datetime-local" value={change.expires_at} onChange={(e) => setChange({ ...change, expires_at: e.target.value })} /></label><label>Grace ends at<input type="datetime-local" value={change.grace_ends_at} onChange={(e) => setChange({ ...change, grace_ends_at: e.target.value })} /></label><label>Reason<input value={change.reason} onChange={(e) => setChange({ ...change, reason: e.target.value })} /></label></div><button className="primary-action" onClick={changePlan}>Save governed subscription change</button></section>
    <section className="panel subscription-dashboard"><div className="section-title">Expiry and renewal dashboard</div><div className="home-insight-grid"><article><span className="eyebrow">Tracked subscriptions</span><strong>{expiring.length}</strong><p>Active, grace, and expired records</p></article><article><span className="eyebrow">Grace / action required</span><strong>{expiring.filter((row) => ["GRACE", "EXPIRED"].includes(row.status)).length}</strong><p>Requires renewal or suspension review</p></article><article><span className="eyebrow">Next expiry</span><strong>{expiring.filter((row) => row.status === "ACTIVE").sort((a, b) => String(a.expires_at).localeCompare(String(b.expires_at)))[0]?.days_remaining ?? "—"}</strong><p>Days remaining</p></article></div></section>
    <section className="subscription-admin-grid"><article className="panel"><div className="section-title">Reminder policies</div><p>Define ordered expiry thresholds and recipient classes. Thresholds are validated and versioned by the server.</p><label>Policy name<input value={policy.name} onChange={(e) => setPolicy({ ...policy, name: e.target.value })} /></label><label>Thresholds in days<input value={policy.thresholds} onChange={(e) => setPolicy({ ...policy, thresholds: e.target.value })} /><small>Example: 60,30,7</small></label><label>Timezone<input value={policy.timezone} onChange={(e) => setPolicy({ ...policy, timezone: e.target.value })} /></label><button className="primary-action" onClick={savePolicy}>Save reminder policy</button></article><article className="panel"><div className="section-title">Email templates</div><p>Draft versioned renewal messages using approved merge variables. Delivery is tracked by the provider.</p><label>Stage<select value={template.stage} onChange={(e) => setTemplate({ ...template, stage: e.target.value })}><option>60_DAY</option><option>30_DAY</option><option>7_DAY</option><option>GRACE</option><option>EXPIRED</option></select></label><label>Version<input value={template.version} onChange={(e) => setTemplate({ ...template, version: e.target.value })} /></label><label>Subject<input value={template.subject} onChange={(e) => setTemplate({ ...template, subject: e.target.value })} /></label><label>Body<textarea rows={5} value={template.body} onChange={(e) => setTemplate({ ...template, body: e.target.value })} /></label><small>Allowed variables: customer_name, expiry_date, days_remaining</small><button className="primary-action" onClick={saveTemplate}>Save email template</button></article></section>
    <section className="panel subscription-timeline"><div className="section-title">Subscription timeline</div>{expiring.slice(0, 12).map((row) => <div className="audit-row" key={row.subscription_id}><strong>{row.status}</strong><span>{row.tenant_id}</span><small>{row.expires_at} · {row.days_remaining} days</small></div>)}{!expiring.length && <p>No subscription lifecycle records require action.</p>}</section>
  </div>;
}
