import React, { useEffect, useMemo, useState } from "react";
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

type TimelineEvent = {
  event_id: string;
  event_type: string;
  category: string;
  title: string;
  event_time?: string;
  effective_time?: string;
  recorded_time?: string;
  knowledge_available_time?: string;
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

const api = async <T,>(path: string): Promise<T> => {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
  return response.json();
};

function fmt(value?: string | null) {
  if (!value) return "Not recorded";
  return value.slice(0, 10);
}

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<string>("");
  const [version, setVersion] = useState<string>("D");
  const [asOf, setAsOf] = useState("2026-02-15");
  const [mode, setMode] = useState<"event" | "known">("event");
  const [view, setView] = useState<Product360 | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api<Product[]>("/api/v1/products").then((items) => {
      setProducts(items);
      setSelectedProduct(items[0]?.id ?? "");
    }).catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!selectedProduct) return;
    const params = new URLSearchParams({ version_id: version, as_of: `${asOf}T00:00:00Z`, mode });
    api<Product360>(`/api/v1/products/${selectedProduct}/product-360?${params}`).then(setView).catch((err) => setError(err.message));
  }, [selectedProduct, version, asOf, mode]);

  const selected = useMemo(() => products.find((p) => p.id === selectedProduct), [products, selectedProduct]);

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="brand">MDARIX</div>
        <nav>
          <span className="active">Products</span>
          <span>Decision Center</span>
          <span>Investigations</span>
          <span>Evidence</span>
        </nav>
      </aside>
      <main>
        <header className="topbar">
          <div>
            <p className="eyebrow">Product 360</p>
            <h1>{view?.product.name ?? "Lifecycle Reality"}</h1>
          </div>
          <div className="toolbar">
            <select value={selectedProduct} onChange={(e) => setSelectedProduct(e.target.value)} aria-label="Product">
              {products.map((product) => <option key={product.id} value={product.id}>{product.name}</option>)}
            </select>
            <select value={version} onChange={(e) => setVersion(e.target.value)} aria-label="Version">
              {(selected?.available_versions ?? ["D"]).map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
            <input type="date" value={asOf} onChange={(e) => setAsOf(e.target.value)} aria-label="As of date" />
            <div className="segmented">
              <button className={mode === "event" ? "selected" : ""} onClick={() => setMode("event")}>Event</button>
              <button className={mode === "known" ? "selected" : ""} onClick={() => setMode("known")}>Known</button>
            </div>
          </div>
        </header>
        {error && <div className="error">{error}</div>}
        {view && <Product360View view={view} />}
      </main>
    </div>
  );
}

function Product360View({ view }: { view: Product360 }) {
  const investigationId = view.investigations[0]?.id;

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

      {investigationId && <InvestigationWorkspacePanel investigationId={investigationId} />}

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
            <article key={event.event_id}>
              <div className="event-date">{fmt(event.event_time ?? event.effective_time)}</div>
              <div className="event-body">
                <span className="category">{event.category}</span>
                <h3>{event.title}</h3>
                <p>Event {fmt(event.event_time)} · Effective {fmt(event.effective_time)} · Recorded {fmt(event.recorded_time)} · Known {fmt(event.knowledge_available_time)}</p>
                {event.late_arriving && <span className="late">Late-arriving evidence</span>}
              </div>
              <ChevronRight size={16} />
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}

function InvestigationWorkspacePanel({ investigationId }: { investigationId: string }) {
  const [workspace, setWorkspace] = useState<InvestigationWorkspace | null>(null);
  const [analysis, setAnalysis] = useState<InvestigationAnalysis | null>(null);
  const [mode, setMode] = useState<"current" | "event" | "known">("current");
  const [asOf, setAsOf] = useState("2026-02-15");
  const [error, setError] = useState("");

  useEffect(() => {
    const params = new URLSearchParams({ temporal_mode: mode, retrieval_top_k: "8" });
    if (mode !== "current") params.set("as_of", `${asOf}T00:00:00Z`);
    api<InvestigationWorkspace>(`/api/v1/investigations/${investigationId}/workspace?${params}`)
      .then((item) => {
        setWorkspace(item);
        setAnalysis(null);
        setError("");
      })
      .catch((err) => setError(err.message));
  }, [investigationId, mode, asOf]);

  const runAnalysis = () => {
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
        setAnalysis(payload.analysis);
        setError("");
      })
      .catch((err) => setError(err.message));
  };

  return (
    <section className="workspace-section">
      <div className="workspace-header">
        <div>
          <div className="section-title"><ClipboardList size={18} /> Investigation Workspace</div>
          <h2>{workspace?.investigation.investigation_identifier ?? "Investigation context"}</h2>
          <p>{workspace?.investigation.investigation_question ?? "Loading deterministic investigation context."}</p>
        </div>
        <div className="toolbar compact">
          <input type="date" value={asOf} onChange={(event) => setAsOf(event.target.value)} aria-label="Workspace as of date" />
          <div className="segmented">
            {(["current", "event", "known"] as const).map((item) => (
              <button key={item} className={mode === item ? "selected" : ""} onClick={() => setMode(item)}>{item}</button>
            ))}
          </div>
          <button className="primary-action" onClick={runAnalysis}>Run Analysis</button>
        </div>
      </div>
      {error && <div className="error inline">{error}</div>}
      {workspace && (
        <div className="workspace-grid">
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
