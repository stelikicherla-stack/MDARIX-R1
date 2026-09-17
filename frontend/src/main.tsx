import React, { useEffect, useMemo, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { AlertTriangle, Boxes, CalendarClock, ChevronRight, CircleDot, ClipboardList, Factory, FileText, GitBranch, History, Layers, Network, ShieldCheck } from "lucide-react";
import "./styles.css";

type Product = {
  id: string;
  product_identifier: string;
  name: string;
  product_family: string | null;
  lifecycle_status: string;
  available_versions: string[];
};
type InvestigationSummary = Record<string, string | null>;
type TemporalMode = "current" | "event" | "known";

type TimelineEvent = {
  event_id: string;
  event_type: string;
  category: string;
  title: string;
  event_time?: string;
  effective_time?: string;
  recorded_time?: string;
  knowledge_available_time?: string;
  description?: string;
  related_entity_type?: string;
  related_entity_id?: string;
  source?: string;
  metadata?: Record<string, unknown>;
  quality_status?: string;
  late_arriving: boolean;
};

type Product360 = {
  product: Record<string, string | null>;
  selected_version: Record<string, string | null> | null;
  versions: Array<Record<string, string | null>>;
  overview: Record<string, number | boolean>;
  configuration: { components: Array<Record<string, string | null>>; suppliers: Array<Record<string, string | null>> };
  changes: Array<Record<string, string | null>>;
  manufacturing: { lots: Array<Record<string, string | null>>; sites: Array<Record<string, string | null>> };
  complaints: Array<Record<string, string | null>>;
  investigations: Array<Record<string, string | null>>;
  risks: Array<Record<string, string | null>>;
  failure_modes: Array<Record<string, string | null>>;
  controls: Array<Record<string, string | null>>;
  evidence: Array<Record<string, string | null>>;
  limitations: Array<{ code: string; severity: string; description: string }>;
  provenance: Array<Record<string, string | null>>;
  timeline: TimelineEvent[];
  temporal_context: Record<string, string | boolean | null>;
};

type WorkspaceEvidence = {
  evidence_identifier: string;
  evidence_type: string;
  title: string;
  reliability_status: string;
  chunks: Array<{ source_anchor: Record<string, unknown>; excerpt: string; materialized: boolean }>;
  observations: Array<{ statement: string; quality_status: string; source_anchor: Record<string, unknown> }>;
  entity_links: Array<{ entity_type: string; resolution_status: string; source: string }>;
};

type InvestigationWorkspace = {
  investigation: Record<string, string | null>;
  product_context: Record<string, unknown>;
  temporal_context: Record<string, string | boolean | number | null>;
  relationship_context: { nodes: unknown[]; relationships: unknown[]; metadata: Record<string, unknown> };
  evidence_context: WorkspaceEvidence[];
  retrieval_context: { status: string; results_count: number; limitations: string[] } | null;
  limitations: Array<{ code: string; severity: string; description: string }>;
  guardrails: Record<string, string | boolean>;
  metadata: Record<string, string | boolean>;
};

type AnalysisItem = {
  item_id: string;
  semantic_type: string;
  statement: string;
  rationale?: string;
  grounding_status: string;
  source_references: unknown[];
};

type InvestigationAnalysis = {
  analysis_id: string;
  status: string;
  observations: AnalysisItem[];
  temporal_patterns: AnalysisItem[];
  evidence_relationships: AnalysisItem[];
  possible_explanations: AnalysisItem[];
  contradictions: AnalysisItem[];
  missing_information: AnalysisItem[];
  questions_to_investigate: AnalysisItem[];
  limitations: AnalysisItem[];
  validation_summary: Record<string, number | string>;
  model_provenance: Record<string, string | boolean>;
};
type InvestigationBrief = { id: string; investigation_id: string; brief_version: number; status: string; title: string; temporal_mode: string; temporal_cutoff?: string | null; human_review_state: string; content: Record<string, any>; provenance: Record<string, any> };

type Hypothesis = {
  hypothesis_id: string;
  statement: string;
  scope: string;
  status: string;
  supporting_evidence: Array<{ relationship_type: string; rationale: string; source_references: unknown[] }>;
  contradicting_evidence: Array<{ relationship_type: string; rationale: string; source_references: unknown[] }>;
  contextual_evidence: Array<{ relationship_type: string; rationale: string; source_references: unknown[] }>;
  assumptions: string[];
  evidence_gaps: string[];
  falsification_conditions: string[];
  temporal_consistency: Record<string, string>;
};

type HypothesisSet = {
  hypothesis_set_id: string;
  status: string;
  hypotheses: Hypothesis[];
  comparison: Array<Record<string, string | number | boolean>>;
  validation_summary: Record<string, number | string>;
  guardrails: Record<string, boolean>;
};
type UnknownSet = { unknowns: Array<{ unknown_id: string; category: string; statement: string; why_it_matters: string; resolution_requirement: string; status: string; materiality: string; provenance: Record<string, unknown> }> };
type FailureChainSet = { chains: Array<{ chain_id: string; chain_statement: string; overall_status: string; links: Array<{ link_id: string; from_entity_or_state: string; relationship: string; to_entity_or_state: string; epistemic_status: string; unknowns: string[] }> }> };
type ChallengeSet = { challenges: Array<{ challenge_id: string; challenge_type: string; statement: string; rationale: string; materiality: string; status: string }> };
type EvidenceSummary = {
  id: string;
  evidence_identifier: string;
  evidence_type: string;
  title: string;
  source_system?: string | null;
  reliability_status?: string | null;
  fact_type?: string | null;
  document_ref?: string | null;
};
type DecisionContext = {
  investigation: Record<string, string | null>;
  product_context: Record<string, any>;
  temporal_context: Record<string, any>;
  evidence: Array<Record<string, any>>;
  observations: Array<Record<string, any>>;
  contradictions: Array<Record<string, any>>;
  hypotheses: Array<Record<string, any>>;
  challenges: Array<Record<string, any>>;
  unknowns: Array<Record<string, any>>;
  failure_chains: Array<Record<string, any>>;
  limitations: Array<Record<string, any>>;
  readiness: { state: string; reasons: string[] };
  decision_options: string[];
};

const api = async <T,>(path: string): Promise<T> => {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
};

function fmt(value?: string | null) {
  if (!value) return "Not recorded";
  return value.slice(0, 10);
}

function humanize(value?: string | null) {
  return (value ?? "Not recorded").replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function App() {
  const [securityContext, setSecurityContext] = useState<{display_name:string; active_role:string|null} | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<string>("");
  const [version, setVersion] = useState<string>("D");
  const [asOf, setAsOf] = useState("2026-02-15");
  const [mode, setMode] = useState<TemporalMode>("event");
  const [view, setView] = useState<Product360 | null>(null);
  const [error, setError] = useState("");
  const [activeView, setActiveView] = useState<"products" | "investigations" | "evidence" | "decision">("products");
  const [selectedInvestigationId, setSelectedInvestigationId] = useState("");
  const [investigations, setInvestigations] = useState<InvestigationSummary[]>([]);
  const [investigationsLoading, setInvestigationsLoading] = useState(false);

  useEffect(() => { api<{display_name:string; active_role:string|null}>("/api/v1/me/context").then(setSecurityContext).catch(() => setSecurityContext(null)); }, []);

  useEffect(() => {
    api<Product[]>("/api/v1/products").then((items) => {
      setProducts(items);
      setSelectedProduct(items[0]?.id ?? "");
    }).catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedProduct) return;
    const params = new URLSearchParams({ version_id: version, as_of: `${asOf}T00:00:00Z`, mode });
    api<Product360>(`/api/v1/products/${selectedProduct}/product-360?${params}`)
      .then((item) => {
        setView(item);
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [selectedProduct, version, asOf, mode]);

  useEffect(() => {
    if (!selectedProduct) return;
    let active = true;
    setInvestigationsLoading(true);
    api<InvestigationSummary[]>(`/api/v1/products/${selectedProduct}/investigations`)
      .then((items) => { if (active) { setInvestigations(items); setSelectedInvestigationId((current) => items.some((item) => item.id === current) ? current : items[0]?.id ?? ""); } })
      .catch((err) => { if (active) setError(`Investigations could not be loaded: ${err.message}`); })
      .finally(() => { if (active) setInvestigationsLoading(false); });
    return () => { active = false; };
  }, [selectedProduct]);

  const selected = useMemo(() => products.find((p) => p.id === selectedProduct), [products, selectedProduct]);

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="brand">MDARIX</div>
        <nav>
          <button className={`nav-link ${activeView === "products" ? "active" : ""}`} onClick={() => setActiveView("products")}>Products</button>
          <button className={`nav-link ${activeView === "investigations" ? "active" : ""}`} onClick={() => setActiveView("investigations")}>Investigations</button>
          <button className={`nav-link ${activeView === "evidence" ? "active" : ""}`} onClick={() => setActiveView("evidence")}>Evidence</button>
          <button className={`nav-link ${activeView === "decision" ? "active" : ""}`} onClick={() => setActiveView("decision")}>Decision Center</button>
        </nav>
      </aside>
      <main>
        <header className="topbar">
          <div>
            <p className="eyebrow">Persistent workflow context</p>
            <h1>{view?.product.name ?? "MDARIX R1"}</h1>
          </div>
          <div className="toolbar">
            {securityContext && <span className="context-summary" aria-label="Authenticated user and active role">{securityContext.display_name} | {securityContext.active_role ?? "No active role"}</span>}
            <select value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)} aria-label="Product">
              {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
            </select>
            <select value={version} onChange={(e) => setVersion(e.target.value)} aria-label="Version">
              {(selected?.available_versions ?? ["D"]).map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <select value={selectedInvestigationId} onChange={(e) => setSelectedInvestigationId(e.target.value)} aria-label="Investigation" disabled={investigationsLoading || !investigations.length}>
              {!investigations.length && <option value="">{investigationsLoading ? "Loading investigations…" : "No investigations"}</option>}
              {investigations.map((item) => <option key={item.id} value={item.id ?? ""}>{item.investigation_identifier ?? "Investigation"} — {item.status ?? "unknown"}</option>)}
            </select>
            <input type="date" value={asOf} onChange={(e) => setAsOf(e.target.value)} aria-label="As of date" />
            <div className="segmented">
              <button className={mode === "current" ? "selected" : ""} onClick={() => setMode("current")}>Current</button>
              <button className={mode === "event" ? "selected" : ""} onClick={() => setMode("event")}>Event</button>
              <button className={mode === "known" ? "selected" : ""} onClick={() => setMode("known")}>Known</button>
            </div>
          </div>
        </header>
        {error && <div className="error">{error}</div>}
        {view && activeView === "products" && <Product360View view={view} />}
        {view && activeView === "investigations" && <InvestigationAccessView view={view} selectedInvestigationId={selectedInvestigationId} onSelect={setSelectedInvestigationId} temporalMode={mode} asOf={asOf} onOpenDecision={() => setActiveView("decision")} />}
        {view && activeView === "evidence" && <EvidenceAccessView productEvidenceCount={view.evidence.length} />}
        {view && activeView === "decision" && selectedInvestigationId && <DecisionCenterView investigationId={selectedInvestigationId} temporalMode={mode} asOf={asOf} />}
        {view && activeView === "decision" && !selectedInvestigationId && <div className="content"><section className="panel empty-state"><h2>Select an investigation first</h2><p>Open Investigations and select a live investigation before entering Decision Center.</p></section></div>}
      </main>
    </div>
  );
}

function Product360View({ view }: { view: Product360 }) {
  const [expandedEventId, setExpandedEventId] = useState<string | null>(null);
  return (
    <div className="content">
      <section className="product-header">
        <div>
          <p className="eyebrow">{view.product.product_identifier}</p>
          <h2>{view.product.name}</h2>
          <p>{view.product.product_family} · {view.product.lifecycle_status}</p>
        </div>
        <div className="version-pill"><Layers size={16} /> {view.selected_version?.version_identifier ?? "No version selected"}</div>
      </section>

      <section className="metric-strip">
        <Metric icon={<Boxes />} label="Components" value={view.overview.component_count} />
        <Metric icon={<Factory />} label="Lots" value={view.overview.lot_count} />
        <Metric icon={<AlertTriangle />} label="Complaints" value={view.overview.complaint_count} />
        <Metric icon={<FileText />} label="Evidence" value={view.overview.evidence_count} />
      </section>

      <section className="two-col">
        <Panel title="Configuration" icon={<GitBranch />}>
          <DenseTable rows={view.configuration.components.slice(0, 8)} columns={["component_identifier", "name", "revision", "status"]} />
          <h3>Supplier Context</h3>
          <DenseTable rows={view.configuration.suppliers.slice(0, 8)} columns={["supplier_identifier", "name", "component_identifier"]} />
        </Panel>
        <Panel title="Data Quality / Limitations" icon={<ShieldCheck />}>
          <ul className="limitations">
            {view.limitations.map((item) => <li key={item.code}><strong>{item.code}</strong><span>{item.description}</span></li>)}
          </ul>
        </Panel>
      </section>

      <section className="two-col">
        <Panel title="Changes" icon={<History />}>
          <DenseTable rows={view.changes.slice(0, 8)} columns={["change_identifier", "change_type", "effective_timestamp"]} />
        </Panel>
        <Panel title="Manufacturing / Lots" icon={<Factory />}>
          <DenseTable rows={view.manufacturing.lots.slice(0, 10)} columns={["lot_identifier", "site_identifier", "traceability_state", "manufactured_timestamp"]} />
        </Panel>
      </section>

      <section className="two-col">
        <Panel title="Field / Complaints" icon={<AlertTriangle />}>
          <DenseTable rows={view.complaints.slice(0, 10)} columns={["complaint_identifier", "event_timestamp", "recorded_timestamp", "status"]} />
        </Panel>
        <Panel title="Evidence" icon={<FileText />}>
          <DenseTable rows={view.evidence.slice(0, 10)} columns={["evidence_identifier", "evidence_type", "reliability_status", "ingestion_timestamp"]} />
        </Panel>
      </section>

      <section className="two-col">
        <Panel title="Risk & Controls" icon={<ShieldCheck />}>
          <DenseTable rows={view.risks.slice(0, 6)} columns={["risk_identifier", "description", "status"]} />
          <DenseTable rows={view.controls.slice(0, 6)} columns={["control_identifier", "control_type", "status"]} />
        </Panel>
        <Panel title="Provenance" icon={<CircleDot />}>
          <DenseTable rows={view.provenance.slice(0, 8)} columns={["canonical_entity_type", "source_value", "resolution_rule", "resolution_status"]} />
        </Panel>
      </section>

      <section className="timeline-section">
        <div className="section-title"><CalendarClock size={18} /> Lifecycle Timeline</div>
        <div className="timeline">
          {view.timeline.slice(0, 40).map((event) => (
            <article key={event.event_id} className={expandedEventId === event.event_id ? "timeline-event expanded" : "timeline-event"}>
              <div className="event-date">{fmt(event.event_time ?? event.effective_time)}</div>
              <div className="event-body">
                <span className="category">{event.category}</span>
                <h3>{event.title}</h3>
                <p>Event {fmt(event.event_time)} · Effective {fmt(event.effective_time)} · Recorded {fmt(event.recorded_time)} · Known {fmt(event.knowledge_available_time)}</p>
                {event.late_arriving && <span className="late">Late-arriving evidence</span>}
                {expandedEventId === event.event_id && <div className="event-details"><p><strong>Description:</strong> {event.description ?? "No additional description recorded."}</p><p><strong>Related entity:</strong> {event.related_entity_type ?? "Not recorded"} / {event.related_entity_id ?? "Not recorded"}</p><p><strong>Source:</strong> {event.source ?? "Not recorded"}</p><p><strong>Provenance:</strong> {event.metadata?.provenance_available === false ? "Not available" : "Available when recorded by the source context."}</p></div>}
              </div>
              <button className="timeline-toggle" aria-label={`${expandedEventId === event.event_id ? "Collapse" : "Expand"} ${event.title}`} aria-expanded={expandedEventId === event.event_id} onClick={() => setExpandedEventId((current) => current === event.event_id ? null : event.event_id)}><ChevronRight size={16} /></button>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function InvestigationAccessView({ view, selectedInvestigationId, onSelect, temporalMode, asOf, onOpenDecision }: { view: Product360; selectedInvestigationId: string; onSelect: (id: string) => void; temporalMode: TemporalMode; asOf: string; onOpenDecision: () => void }) {
  const [investigations, setInvestigations] = useState<Array<Record<string, string | null>>>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const selected = investigations.find((investigation) => investigation.id === selectedInvestigationId);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api<Array<Record<string, string | null>>>(`/api/v1/products/${view.product.id}/investigations`)
      .then((items) => {
        if (!active) return;
        setInvestigations(items);
        onSelect(items.some((investigation) => investigation.id === selectedInvestigationId) ? selectedInvestigationId : items[0]?.id ?? "");
        setLoadError("");
      })
      .catch((err) => { if (active) setLoadError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [view.product.id]);

  return (
    <div className="content">
      <section className="product-header">
        <div>
          <p className="eyebrow">Investigation access</p>
          <h2>{view.product.name}</h2>
          <p>Version {view.selected_version?.version_identifier ?? "not recorded"}. Select an available investigation to open the existing Day 10–14 workspace.</p>
        </div>
        <div className="version-pill"><ClipboardList size={16} /> {loading ? "Loading" : `${investigations.length} available`}</div>
      </section>
      {loadError && <div className="error">Investigations could not be loaded: {loadError}</div>}
      {!loading && !loadError && investigations.length === 0 ? (
        <section className="panel empty-state">
          <h2>No investigations available</h2>
          <p>The selected product has no investigation records in the current Product 360 result. No workspace has been created or inferred.</p>
        </section>
      ) : (
        <>
          <section className="panel">
            <div className="section-title"><ClipboardList size={18} /> Available investigations</div>
            <div className="investigation-list">
              {investigations.map((investigation) => (
                <button key={investigation.id} className={`investigation-option ${investigation.id === selectedInvestigationId ? "selected" : ""}`} onClick={() => onSelect(investigation.id ?? "")}>
                  <strong>{investigation.investigation_identifier ?? investigation.id}</strong>
                  <span>{investigation.investigation_question ?? "No question recorded."}</span>
                  <small>ID: {investigation.id} | Status: {investigation.status ?? "not recorded"}</small>
                </button>
              ))}
            </div>
          </section>
          {selectedInvestigationId && <InvestigationWorkspacePanel key={selectedInvestigationId} investigationId={selectedInvestigationId} temporalMode={temporalMode} asOf={asOf} onOpenDecision={onOpenDecision} />}
          {!selected && <div className="error inline">The selected investigation is not available in this Product 360 result.</div>}
        </>
      )}
    </div>
  );
}

function EvidenceAccessView({ productEvidenceCount }: { productEvidenceCount: number }) {
  const [evidence, setEvidence] = useState<EvidenceSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setLoading(true);
    api<EvidenceSummary[]>("/api/v1/evidence?limit=50")
      .then((items) => { if (active) { setEvidence(items); setError(""); } })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, []);

  return (
    <div className="content">
      <section className="product-header">
        <div>
          <p className="eyebrow">Evidence access</p>
          <h2>Tenant evidence records</h2>
          <p>Product 360 currently shows {productEvidenceCount} evidence record{productEvidenceCount === 1 ? "" : "s"} linked to the selected product scope. This list is tenant-scoped and does not imply a product link.</p>
        </div>
        <div className="version-pill"><FileText size={16} /> {loading ? "Loading" : `${evidence.length} available`}</div>
      </section>
      {error && <div className="error">Evidence could not be loaded: {error}</div>}
      {!loading && !error && evidence.length === 0 && (
        <section className="panel empty-state"><h2>No evidence records available</h2><p>No tenant-scoped evidence records were returned. This is an empty state, not a conclusion about the selected product.</p></section>
      )}
      {!loading && evidence.length > 0 && (
        <section className="panel">
          <div className="section-title"><FileText size={18} /> Available evidence</div>
          <div className="evidence-list">
            {evidence.map((item) => (
              <article key={item.id}>
                <strong>{item.evidence_identifier}</strong>
                <span>{item.title}</span>
                <small>{item.evidence_type} | {item.reliability_status ?? "reliability not recorded"} | {item.source_system ?? "source not recorded"}</small>
              </article>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}

function DecisionCenterView({ investigationId, temporalMode, asOf }: { investigationId: string; temporalMode: TemporalMode; asOf: string }) {
  const [context, setContext] = useState<DecisionContext | null>(null);
  const [advisory, setAdvisory] = useState<any>(null);
  const [selectedAction, setSelectedAction] = useState("NO_DECISION_YET");
  const [rationale, setRationale] = useState("");
  const [message, setMessage] = useState("");
  const [decision, setDecision] = useState<any>(null);
  const [reviewDisposition, setReviewDisposition] = useState("APPROVED");
  const [reviewComments, setReviewComments] = useState("");
  const [reviewSubmitted, setReviewSubmitted] = useState(false);
  const rationaleRef = useRef<HTMLTextAreaElement>(null);
  const [rationaleError, setRationaleError] = useState("");
  useEffect(() => {
    let active = true;
    const params = new URLSearchParams({ temporal_mode: temporalMode });
    if (temporalMode !== "current") params.set("as_of", `${asOf}T00:00:00Z`);
    api<DecisionContext>(`/api/v1/investigations/${investigationId}/decision-context?${params}`)
      .then((item) => { if (active) { setContext(item); setMessage(""); } })
      .catch((err) => { if (active) setMessage(`Decision context unavailable: ${err.message}`); });
    return () => { active = false; };
  }, [investigationId, temporalMode, asOf]);
  const temporalBody = JSON.stringify({ temporal_mode: temporalMode, as_of: temporalMode === "current" ? null : `${asOf}T00:00:00Z` });
  const runAdvisory = () => fetch(`/api/v1/investigations/${investigationId}/decision-advisory`, { method: "POST", headers: { "Content-Type": "application/json" }, body: temporalBody })
    .then((response) => { if (!response.ok) throw new Error(`${response.status} ${response.statusText}`); return response.json(); }).then(setAdvisory).catch((err) => setMessage(err.message));
  const recordDecision = () => {
    if (!rationale.trim()) { setRationaleError("Enter a human rationale before recording this decision."); setMessage("Human rationale is required before recording a decision."); rationaleRef.current?.focus(); return; }
    fetch(`/api/v1/investigations/${investigationId}/decisions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ selected_action: selectedAction, rationale, authorized_by_ref: "CONTROLLED_DEVELOPMENT_REVIEWER", temporal_mode: temporalMode, as_of: temporalMode === "current" ? null : `${asOf}T00:00:00Z` }) })
      .then((response) => { if (!response.ok) throw new Error(`${response.status} ${response.statusText}`); return response.json(); }).then((payload) => { setDecision(payload); setMessage("Decision recorded as REQUIRES_REVIEW. Complete Human Review below."); }).catch((err) => setMessage(err.message));
  };
  const submitReview = () => fetch(`/api/v1/investigations/decisions/${decision.id}/reviews`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ disposition: reviewDisposition, reviewer_ref: "CONTROLLED_DEVELOPMENT_REVIEWER", comments: reviewComments }) })
    .then((response) => { if (!response.ok) throw new Error(`${response.status} ${response.statusText}`); return response.json(); }).then(() => { setDecision({ ...decision, decision_status: reviewDisposition === "APPROVED" ? "DECIDED" : "REQUIRES_ADDITIONAL_EVIDENCE" }); setReviewSubmitted(true); setMessage(`Human review recorded: ${reviewDisposition}.`); }).catch((err) => setMessage(`Human review could not be submitted: ${err.message}`));
  return <div className="content">
    <section className="product-header"><div><p className="eyebrow">Decision Center</p><h2>{context?.investigation.identifier ?? "Loading investigation"}</h2><p>AI recommends. Authorized humans decide. Temporal context: {String(context?.temporal_context.mode ?? temporalMode)} as of {asOf}.</p></div><div className="version-pill"><ShieldCheck size={16} /> Human review required</div></section>
    {message && <div className="error">{message}</div>}
    {context && <>
      <section className="panel readiness-panel"><div className="section-title"><ShieldCheck size={18} /> Decision Readiness</div><h2>{context.readiness.state}</h2><ul className="limitations">{context.readiness.reasons.map((reason) => <li key={reason}><strong>LIMITATION</strong><span>{reason}</span></li>)}</ul></section>
      <div className="two-col"><Panel title="What We Know" icon={<FileText />}><DecisionItems items={context.observations} empty="No persisted observations available." /></Panel><Panel title="Challenges / Contradictions" icon={<AlertTriangle />}><DecisionItems items={[...context.contradictions, ...context.challenges]} empty="No challenge output available." /></Panel></div>
      <div className="two-col"><Panel title="Competing Hypotheses" icon={<GitBranch />}><DecisionItems items={context.hypotheses} empty="No hypotheses available." /></Panel><Panel title="Unknowns Radar" icon={<CircleDot />}><DecisionItems items={context.unknowns} empty="No unknowns recorded." /></Panel></div>
      <Panel title="Failure Chain" icon={<Network />}><DecisionItems items={context.failure_chains} empty="No supportable failure chain available." /></Panel>
      <section className="panel"><div className="section-title"><ClipboardList size={18} /> Decision Options</div><select value={selectedAction} onChange={(event) => setSelectedAction(event.target.value)} aria-label="Decision option">{context.decision_options.map((option) => <option key={option}>{option}</option>)}</select><label className="required-field" htmlFor="decision-rationale">Human rationale <span>(required)</span></label><textarea id="decision-rationale" ref={rationaleRef} aria-required="true" aria-invalid={Boolean(rationaleError)} value={rationale} onChange={(event) => { setRationale(event.target.value); setRationaleError(""); if (message.includes("rationale is required")) setMessage(""); }} placeholder="Explain why this option is supportable or why no decision should be made." rows={4} />{rationaleError && <p className="field-error" role="alert">{rationaleError}</p>}<div className="toolbar"><button className="primary-action secondary" onClick={runAdvisory}>Generate AI Advisory</button><button className="primary-action" onClick={recordDecision}>Record Human Decision</button></div>{advisory && <div className="advisory-box"><strong>AI Advisory — not a human decision</strong><p>Recommended action: {advisory.advisory.recommended_action}</p><p>{advisory.advisory.additional_evidence_needed.join(" ") || "No additional evidence need was identified by the controlled advisory."}</p></div>}{decision && <div className="human-review-box"><strong>Human Review — required before finalization</strong><p>Decision status: {decision.decision_status}</p><select value={reviewDisposition} onChange={(event) => setReviewDisposition(event.target.value)} disabled={reviewSubmitted}><option value="APPROVED">APPROVED</option><option value="REJECTED">REJECTED</option><option value="REQUIRES_ADDITIONAL_EVIDENCE">REQUIRES_ADDITIONAL_EVIDENCE</option></select><textarea value={reviewComments} onChange={(event) => setReviewComments(event.target.value)} placeholder="Human review comments" rows={3} disabled={reviewSubmitted} /><button className="primary-action" onClick={submitReview} disabled={reviewSubmitted}>{reviewSubmitted ? "Human Review Submitted" : "Submit Human Review"}</button>{reviewSubmitted && <p className="review-success">Review saved successfully. The human disposition is preserved in Decision Memory and audit history.</p>}</div>}</section>
    </>}
  </div>;
}

function DecisionItems({ items, empty }: { items: Array<Record<string, any>>; empty: string }) {
  if (!items.length) return <p className="empty-copy">{empty}</p>;
  return <div className="decision-items">{items.slice(0, 8).map((item, index) => <article key={String(item.item_id ?? item.hypothesis_id ?? item.unknown_id ?? item.chain_id ?? index)}><strong>{String(item.semantic_type ?? item.category ?? item.overall_status ?? "Structured context")}</strong><span>{String(item.statement ?? item.text ?? item.chain_statement ?? item.description ?? "No statement recorded.")}</span></article>)}</div>;
}

function InvestigationWorkspacePanel({ investigationId, temporalMode: mode, asOf, onOpenDecision }: { investigationId: string; temporalMode: TemporalMode; asOf: string; onOpenDecision: () => void }) {
  const [workspace, setWorkspace] = useState<InvestigationWorkspace | null>(null);
  const [analysis, setAnalysis] = useState<InvestigationAnalysis | null>(null);
  const [hypothesisSet, setHypothesisSet] = useState<HypothesisSet | null>(null);
  const [unknownSet, setUnknownSet] = useState<UnknownSet | null>(null);
  const [failureChains, setFailureChains] = useState<FailureChainSet | null>(null);
  const [challengeSet, setChallengeSet] = useState<ChallengeSet | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "evidence" | "analysis" | "hypotheses" | "challenger" | "unknowns" | "failure-chain" | "counterfactual" | "brief" | "assurance" | "decision">("overview");
  const [brief, setBrief] = useState<InvestigationBrief | null>(null);
  const [counterfactual, setCounterfactual] = useState<any>(null);
  const [counterfactualTarget, setCounterfactualTarget] = useState("Component Rev B");
  const [counterfactualType, setCounterfactualType] = useState("REMOVE_CHANGE");
  const [counterfactualStatus, setCounterfactualStatus] = useState("IDLE");
  const [error, setError] = useState("");
  const [actionStatus, setActionStatus] = useState("");
  const [pendingAction, setPendingAction] = useState<string | null>(null);
  const requestSequence = useRef(0);

  useEffect(() => {
    const sequence = ++requestSequence.current;
    const params = new URLSearchParams({ temporal_mode: mode, retrieval_top_k: "8" });
    if (mode !== "current") params.set("as_of", `${asOf}T00:00:00Z`);
    api<InvestigationWorkspace>(`/api/v1/investigations/${investigationId}/workspace?${params}`)
      .then((item) => {
        if (sequence !== requestSequence.current) return;
        setWorkspace(item);
        setAnalysis(null);
        setHypothesisSet(null);
        setUnknownSet(null);
        setFailureChains(null);
        setChallengeSet(null);
        setError("");
        setActionStatus("");
        setPendingAction(null);
      })
      .catch((err) => { if (sequence === requestSequence.current) { setError(err.message); setActionStatus("BACKEND ERROR: Investigation context could not be loaded."); setPendingAction(null); } });
  }, [investigationId, mode, asOf]);

  const runAnalysis = () => {
    const sequence = requestSequence.current;
    setPendingAction("Run Analysis"); setActionStatus("RUNNING: AI Investigator analysis..."); setError("");
    const body = {
      investigation_id: investigationId,
      temporal_mode: mode,
      as_of: mode === "current" ? null : `${asOf}T00:00:00Z`,
      analysis_mode: "standard",
      retrieval_top_k: 8,
    };
    fetch(`/api/v1/investigations/${investigationId}/analysis`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then((response) => {
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.json();
      })
      .then((payload) => {
        if (sequence !== requestSequence.current) return;
        setAnalysis(payload.analysis);
        setActionStatus(payload.analysis?.observations?.length ? "SUCCESS: Analysis results are displayed below." : "EMPTY RESULT: No observations were returned for this context.");
        setPendingAction(null);
        setError("");
      })
      .catch((err) => { if (sequence === requestSequence.current) { setError(err.message); setActionStatus(`BACKEND ERROR: Analysis could not be completed (${err.message}).`); setPendingAction(null); } });
  };

  const runHypotheses = () => {
    const sequence = requestSequence.current;
    setPendingAction("Generate Hypotheses"); setActionStatus("RUNNING: Generating competing hypotheses..."); setError("");
    const body = {
      investigation_id: investigationId,
      temporal_mode: mode,
      as_of: mode === "current" ? null : `${asOf}T00:00:00Z`,
      investigator_question: "Generate competing hypotheses from the validated investigation analysis.",
    };
    fetch(`/api/v1/investigations/${investigationId}/hypotheses`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then((response) => {
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.json();
      })
      .then((payload) => {
        if (sequence !== requestSequence.current) return;
        setHypothesisSet(payload.hypothesis_set);
        const count = payload.hypothesis_set?.hypotheses?.length ?? 0;
        setActionStatus(count ? `SUCCESS: ${count} competing hypothesis result(s) are displayed below.` : "INSUFFICIENT EVIDENCE: No supportable hypotheses are available for this temporal context.");
        setPendingAction(null);
        setError("");
      })
      .catch((err) => { if (sequence === requestSequence.current) { setError(err.message); setActionStatus(`BACKEND ERROR: Hypotheses could not be generated (${err.message}).`); setPendingAction(null); } });
  };

  const runDay14 = () => {
    const sequence = requestSequence.current;
    setPendingAction("Run Unknowns & Chain"); setActionStatus("RUNNING: Evaluating Unknowns Radar and Failure Chain..."); setError("");
    const body = { investigation_id: investigationId, temporal_mode: mode, as_of: mode === "current" ? null : `${asOf}T00:00:00Z` };
    fetch(`/api/v1/investigations/${investigationId}/challenges`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) })
      .then((response) => { if (!response.ok) throw new Error(`${response.status} ${response.statusText}`); return response.json(); })
      .then((payload) => { if (sequence !== requestSequence.current) return Promise.reject(new Error("STALE_CONTEXT")); setChallengeSet(payload.challenge_set); return fetch(`/api/v1/investigations/${investigationId}/unknowns`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); })
      .then((response) => { if (!response.ok) throw new Error(`${response.status} ${response.statusText}`); return response.json(); })
      .then((payload) => { if (sequence !== requestSequence.current) return Promise.reject(new Error("STALE_CONTEXT")); setUnknownSet(payload.unknown_set); return fetch(`/api/v1/investigations/${investigationId}/failure-chains`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) }); })
      .then((response) => { if (!response.ok) throw new Error(`${response.status} ${response.statusText}`); return response.json(); })
      .then((payload) => { if (sequence !== requestSequence.current) return; setFailureChains(payload.failure_chain_set); setActionStatus(payload.failure_chain_set?.chains?.length ? "SUCCESS: Unknowns and Failure Chain results are displayed below." : "INSUFFICIENT EVIDENCE: No supportable failure chain is available; the controlled result remains unresolved."); setPendingAction(null); setError(""); })
      .catch((err) => { if (sequence === requestSequence.current && err.message !== "STALE_CONTEXT") { setError(err.message); setActionStatus(`BACKEND ERROR: Unknowns and Failure Chain could not be completed (${err.message}).`); setPendingAction(null); } });
  };
  const runCounterfactual = () => {
    const sequence = requestSequence.current;
    setCounterfactualStatus("VALIDATING");
    setCounterfactual(null);
    fetch(`/api/v1/investigations/${investigationId}/counterfactuals`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ temporal_mode: mode, as_of: mode === "current" ? null : `${asOf}T00:00:00Z`, intervention_type: counterfactualType, intervention_target: counterfactualTarget, intervention_description: `Explore the constrained alternative condition where ${counterfactualTarget} is removed from the candidate explanation.` }) })
      .then(async (response) => { const payload = await response.json(); if (!response.ok) throw new Error(payload.detail?.message ?? response.statusText); return payload; })
      .then((payload) => { if (sequence !== requestSequence.current) return; setCounterfactual(payload.result); setCounterfactualStatus(payload.status ?? "SUCCESS"); })
      .catch((err) => { if (sequence === requestSequence.current) setCounterfactualStatus(err.message.includes("INSUFFICIENT") ? "INSUFFICIENT EVIDENCE" : `ERROR: ${err.message}`); });
  };
  const generateBrief = () => {
    setActionStatus("RUNNING: Generating Investigation Brief...");
    fetch(`/api/v1/investigations/${investigationId}/briefs`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ temporal_mode: mode, as_of: mode === "current" ? null : `${asOf}T00:00:00Z` }) })
      .then(async (response) => { const payload = await response.json(); if (!response.ok) throw new Error(payload.detail?.message ?? response.statusText); return payload; })
      .then((payload) => { setBrief(payload); setActiveTab("brief"); setActionStatus(`SUCCESS: Investigation Brief v${payload.brief_version} generated for review.`); })
      .catch((err) => setActionStatus(`BACKEND ERROR: Brief could not be generated (${err.message}).`));
  };

  return (
    <section id="investigation-workspace" className="workspace-section">
      <div className="workspace-header">
        <div>
          <div className="section-title"><ClipboardList size={18} /> Investigation Workspace</div>
          <h2>{workspace?.investigation.investigation_identifier ?? "Investigation context"}</h2>
          <p>{workspace?.investigation.investigation_question ?? "Loading deterministic investigation context."}</p>
        </div>
        <div className="toolbar compact">
          <span className="context-summary">{humanize(mode)} {mode === "current" ? "context" : `as of ${asOf}`}</span>
          <div className="segmented">
            {(["current", "event", "known"] as const).map((item) => (
              <button key={item} className={mode === item ? "selected" : ""} disabled>{item}</button>
            ))}
          </div>
          <button className="primary-action" onClick={runAnalysis} disabled={Boolean(pendingAction)}> {pendingAction === "Run Analysis" ? "Running Analysis…" : "Run Analysis"}</button>
          <button className="primary-action secondary" onClick={runHypotheses} disabled={Boolean(pendingAction)}> {pendingAction === "Generate Hypotheses" ? "Generating…" : "Generate Hypotheses"}</button>
          <button className="primary-action secondary" onClick={runDay14} disabled={Boolean(pendingAction)}> {pendingAction === "Run Unknowns & Chain" ? "Running Unknowns & Chain…" : "Run Unknowns & Chain"}</button><button className="primary-action" onClick={generateBrief}>Generate Investigation Brief</button>
        </div>
      </div>
      <div className="workflow-tabs" role="tablist" aria-label="Investigation workflow">
        {(["overview", "evidence", "analysis", "hypotheses", "challenger", "unknowns", "failure-chain", "counterfactual", "brief", "assurance", "decision"] as const).map((tab) => <button key={tab} role="tab" aria-selected={activeTab === tab} className={activeTab === tab ? "active" : ""} onClick={() => { setActiveTab(tab); document.getElementById(`workflow-${tab}`)?.scrollIntoView({ behavior: "smooth", block: "start" }); }}>{humanize(tab)}</button>)}
      </div>
      {(actionStatus || pendingAction) && <div className={`action-feedback ${actionStatus.startsWith("BACKEND") ? "error-feedback" : ""}`} role="status">{pendingAction ? actionStatus : actionStatus}</div>}
      {error && <div className="error inline">{error}</div>}
      {workspace && (
        <div id="workflow-overview" className="workspace-grid">
          <Panel title="Context Health" icon={<ShieldCheck />}>
            <div className="context-health">
              <Metric icon={<FileText />} label="Evidence" value={workspace.evidence_context.length} />
              <Metric icon={<Network />} label="Graph Nodes" value={workspace.relationship_context.metadata.node_count ?? workspace.relationship_context.nodes.length} />
              <Metric icon={<GitBranch />} label="Relationships" value={workspace.relationship_context.metadata.relationship_count ?? workspace.relationship_context.relationships.length} />
            </div>
            <ul className="limitations">
              {workspace.limitations.slice(0, 5).map((item) => <li key={item.code}><strong>{item.code}</strong><span>{item.description}</span></li>)}
            </ul>
          </Panel>
          <Panel title="Evidence Context" icon={<FileText />}>
            <div className="evidence-list">
              {workspace.evidence_context.slice(0, 6).map((item) => (
                <article key={item.evidence_identifier}>
                  <strong>{item.evidence_identifier}</strong>
                  <span>{item.title}</span>
                  <small>{item.evidence_type} | {item.reliability_status} | anchors {item.chunks.filter((chunk) => chunk.source_anchor).length}</small>
                </article>
              ))}
            </div>
          </Panel>
          <Panel title="Retrieval & Guardrails" icon={<CircleDot />}>
            <div className="guardrail-list">
              <p><strong>Retrieval:</strong> {workspace.retrieval_context?.status ?? "Not requested"} ({workspace.retrieval_context?.results_count ?? 0} results)</p>
              <p><strong>Temporal mode:</strong> {String(workspace.temporal_context.mode)} {workspace.temporal_context.as_of ? `as of ${workspace.temporal_context.as_of}` : ""}</p>
              <p><strong>Human authority:</strong> {workspace.guardrails.human_authority_required ? "Required" : "Not recorded"}</p>
              <p><strong>Causality:</strong> {workspace.guardrails.generates_causality ? "Generated" : "Not generated"}</p>
            </div>
          </Panel>
        </div>
      )}
      <section id="workflow-analysis" className="workflow-action"><h3>Analysis</h3><p>Grounded observations and possible explanations for the selected context.</p><button className="primary-action" onClick={runAnalysis} disabled={Boolean(pendingAction)}>{pendingAction === "Run Analysis" ? "Running Analysis…" : "Run Analysis"}</button></section>
      {analysis && (
        <div className="analysis-grid">
          <AnalysisPanel title="Key Observations" items={analysis.observations.slice(0, 4)} />
          <AnalysisPanel title="Possible Explanations" items={analysis.possible_explanations.slice(0, 4)} />
          <AnalysisPanel title="Contradictory Evidence" items={analysis.contradictions.slice(0, 4)} />
          <AnalysisPanel title="Missing Information" items={analysis.missing_information.slice(0, 4)} />
          <AnalysisPanel title="Questions To Investigate" items={analysis.questions_to_investigate.slice(0, 5)} />
          <Panel title="Validation / Provenance" icon={<ShieldCheck />}>
            <div className="guardrail-list">
              <p><strong>Status:</strong> {analysis.status}</p>
              <p><strong>Grounding:</strong> {String(analysis.validation_summary.material_grounding_coverage)}</p>
              <p><strong>Source anchors:</strong> {String(analysis.validation_summary.evidence_source_anchor_coverage)}</p>
              <p><strong>Provider:</strong> {String(analysis.model_provenance.provider)}</p>
            </div>
          </Panel>
        </div>
      )}
      <section id="workflow-hypotheses" className="workflow-action"><h3>Competing hypotheses</h3><p>Preserves support, contradiction, gaps, and falsification conditions without choosing a winner.</p><button className="primary-action secondary" onClick={runHypotheses} disabled={Boolean(pendingAction)}>{pendingAction === "Generate Hypotheses" ? "Generating…" : "Generate Hypotheses"}</button></section>
      {hypothesisSet && (
        <div className="hypothesis-section">
          <div className="section-title"><GitBranch size={18} /> Competing Hypotheses</div>
          {hypothesisSet.hypotheses.length === 0 && <div className="empty-result">No supportable hypotheses are available for the selected temporal context. This is a controlled abstention, not a negative conclusion.</div>}
          <div className="hypothesis-grid">
            {hypothesisSet.hypotheses.map((hypothesis) => (
              <article className="hypothesis-card" key={hypothesis.hypothesis_id}>
                <span className="category">{hypothesis.status}</span>
                <h3>{hypothesis.statement}</h3>
                <p><strong>Temporal fit:</strong> {hypothesis.temporal_consistency.status}</p>
                <p><strong>Support:</strong> {hypothesis.supporting_evidence[0]?.rationale ?? "No supporting evidence recorded."}</p>
                <p><strong>Contradiction:</strong> {hypothesis.contradicting_evidence[0]?.rationale ?? "No contradiction recorded."}</p>
                <p><strong>Gap:</strong> {hypothesis.evidence_gaps[0] ?? "No gap recorded."}</p>
                <p><strong>Would weaken:</strong> {hypothesis.falsification_conditions[0] ?? "No falsification condition recorded."}</p>
              </article>
            ))}
          </div>
          <Panel title="Hypothesis Validation" icon={<ShieldCheck />}>
            <div className="guardrail-list">
              <p><strong>Status:</strong> {hypothesisSet.status}</p>
              <p><strong>Grounding:</strong> {String(hypothesisSet.validation_summary.material_grounding_coverage)}</p>
              <p><strong>Source anchors:</strong> {String(hypothesisSet.validation_summary.source_anchor_coverage)}</p>
              <p><strong>No winner score:</strong> {hypothesisSet.comparison.every((row) => row.no_winner_score) ? "Preserved" : "Check required"}</p>
            </div>
          </Panel>
        </div>
      )}
      <section id="workflow-challenger" className="workflow-action"><h3>Challenger, unknowns, and failure chain</h3><p>Surfaces challenges and material unknowns. An unresolved failure chain is a valid controlled result.</p><button className="primary-action secondary" onClick={runDay14} disabled={Boolean(pendingAction)}>{pendingAction === "Run Unknowns & Chain" ? "Running controlled checks…" : "Run Challenger, Unknowns & Chain"}</button></section>
      {challengeSet && <div className="analysis-grid"><Panel title="AI Challenger" icon={<ShieldCheck />}><div className="analysis-list">{challengeSet.challenges.length === 0 && <p className="empty">No material challenge identified.</p>}{challengeSet.challenges.map((item) => <article key={item.challenge_id}><span>{item.challenge_type} | {item.status} | {item.materiality}</span><p>{item.statement}</p><small>{item.rationale}</small></article>)}</div></Panel></div>}
      {unknownSet && <div id="workflow-unknowns" className="analysis-grid">
        <Panel title="Unknowns Radar" icon={<AlertTriangle />}>
          <div className="analysis-list">{unknownSet.unknowns.length === 0 && <p className="empty">No material unknowns identified.</p>}{unknownSet.unknowns.map((item) => <article key={item.unknown_id}><span>{item.category} | {item.status} | {item.materiality}</span><p><strong>{item.statement}</strong></p><p>Why it matters: {item.why_it_matters}</p><small>Resolution: {item.resolution_requirement}</small></article>)}</div>
        </Panel>
        <div id="workflow-failure-chain"><Panel title="Failure Chain Intelligence" icon={<GitBranch />}>
          <div className="analysis-list">{!failureChains?.chains.length && <p className="empty">No supportable failure chain is available for this context. The chain remains unresolved.</p>}{failureChains?.chains.map((chain) => <article key={chain.chain_id}><span>{chain.overall_status}</span><p>{chain.chain_statement}</p>{chain.links.map((link) => <small key={link.link_id}>{link.from_entity_or_state} — {link.relationship} → {link.to_entity_or_state} [{link.epistemic_status}]</small>)}</article>)}</div>
        </Panel></div>
      </div>}
      <section id="workflow-evidence" className="panel empty-state"><h3>Evidence review</h3><p>Use the evidence context above to see identifiers, reliability, and source anchors for the selected investigation.</p></section>
      <section id="workflow-counterfactual" className="panel counterfactual-panel"><div className="section-title"><GitBranch size={18} /> Constrained Counterfactual</div><p className="helper-copy">Explore how the current explanation changes under a controlled alternative condition. Results are hypothetical and are not observed evidence.</p><div className="counterfactual-controls"><select value={counterfactualType} onChange={(event) => setCounterfactualType(event.target.value)} aria-label="Intervention type"><option value="REMOVE_CHANGE">Remove change</option><option value="REPLACE_COMPONENT_REVISION">Replace component revision</option><option value="REMOVE_SUPPLIER_CHANGE">Remove supplier change</option><option value="REMOVE_FAILURE_CHAIN_LINK">Remove failure-chain link</option></select><input value={counterfactualTarget} onChange={(event) => setCounterfactualTarget(event.target.value)} aria-label="Counterfactual target" placeholder="Readable target, e.g. Component Rev B" /><button className="primary-action" onClick={runCounterfactual} disabled={counterfactualStatus === "VALIDATING"}>{counterfactualStatus === "VALIDATING" ? "Validating…" : "Run Counterfactual"}</button></div><p className="action-feedback" role="status">Status: {counterfactualStatus}</p>{counterfactual && <div className="counterfactual-result"><strong>{counterfactual.label}</strong><h3>What stays the same</h3><ul>{counterfactual.invariants?.map((item: string) => <li key={item}>{item}</li>)}</ul><h3>What changes / becomes unsupported</h3><ul>{counterfactual.relationships_no_longer_supported?.map((item: string) => <li key={item}>{item}</li>)}</ul><h3>What remains unexplained</h3><ul>{counterfactual.observations_still_unexplained?.map((item: string) => <li key={item}>{item}</li>)}</ul><h3>Limitations</h3><ul>{counterfactual.limitations?.map((item: any, index: number) => <li key={index}>{typeof item === "string" ? item : item.description}</li>)}</ul><p><strong>Conclusion:</strong> {counterfactual.conclusion}</p></div>}</section>
      <section id="workflow-brief" className="panel brief-panel"><div className="section-title"><FileText size={18} /> Investigation Brief</div>{!brief ? <><p>Assemble a versioned, evidence-grounded package for human review.</p><button className="primary-action" onClick={generateBrief}>Generate Investigation Brief</button></> : <><h2>{brief.title}</h2><p>Version {brief.brief_version} · {brief.status} · {brief.temporal_mode}</p><div className="advisory-box"><strong>AI-assisted content requires human review.</strong><p>This Brief does not establish root cause or causality.</p></div>{Object.entries(brief.content).map(([key, value]) => <article key={key}><h3>{humanize(key)}</h3><pre>{JSON.stringify(value, null, 2)}</pre></article>)}<details><summary>Provenance</summary><pre>{JSON.stringify(brief.provenance, null, 2)}</pre></details></>}</section>
      <section id="workflow-assurance" className="panel"><div className="section-title"><ShieldCheck size={18} /> AI Assurance</div><h2>Deterministic Trust Engine</h2><p>Assurance validates evidence grounding, citation integrity, tenant and ProductVersion context, temporal context, unsupported claims, causality restraint, provenance, and human authority.</p><div className="guardrail-list"><p><strong>Status:</strong> Assurance results are persisted per AI execution.</p><p><strong>Policy:</strong> MDARIX_AI_TRUST_POLICY_R1_V1</p><p><strong>Causality:</strong> NOT ESTABLISHED by assurance.</p><p><strong>Human review:</strong> REQUIRED. Assurance does not approve decisions.</p><p><strong>Confidence:</strong> No fabricated numeric confidence score is used.</p></div></section>
      <section id="workflow-decision" className="panel empty-state"><h3>Decision readiness</h3><p>AI outputs inform the workflow. Authorized humans record decisions in the Decision Center.</p><button className="primary-action" onClick={onOpenDecision}>Open Decision Center</button></section>
    </section>
  );
}

function AnalysisPanel({ title, items }: { title: string; items: AnalysisItem[] }) {
  return (
    <Panel title={title} icon={<ClipboardList />}>
      <div className="analysis-list">
        {items.length === 0 && <p className="empty">No items for this analysis.</p>}
        {items.map((item) => (
          <article key={item.item_id}>
            <span>{item.semantic_type} | {item.grounding_status} | sources {item.source_references.length}</span>
            <p>{item.statement}</p>
          </article>
        ))}
      </div>
    </Panel>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: unknown }) {
  return <div className="metric">{icon}<span>{label}</span><strong>{String(value)}</strong></div>;
}

function Panel({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return <section className="panel"><div className="section-title">{icon}{title}</div>{children}</section>;
}

function DenseTable({ rows, columns }: { rows: Array<Record<string, string | null>>; columns: string[] }) {
  if (!rows.length) return <p className="empty">No records for this view.</p>;
  return (
    <table>
      <thead><tr>{columns.map((column) => <th key={column}>{column.replace(/_/g, " ")}</th>)}</tr></thead>
      <tbody>{rows.map((row, index) => <tr key={index}>{columns.map((column) => <td key={column}>{fmt(row[column]) === "Not recorded" ? (row[column] ?? "—") : fmt(row[column])}</td>)}</tr>)}</tbody>
    </table>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
