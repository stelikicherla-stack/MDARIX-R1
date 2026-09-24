import { useEffect, useState } from "react";

type Stage2Mode = "signals" | "story" | "evidence" | "persona";

const personas = ["investigator", "quality-manager", "regulatory", "risk-manager", "approver", "executive"];

export function Stage2Experience({ mode, investigationId }: { mode: Stage2Mode; investigationId?: string }) {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [persona, setPersona] = useState("investigator");

  useEffect(() => {
    const path = mode === "signals"
      ? "/api/v1/analytics/signals"
      : mode === "evidence"
        ? "/api/v1/analytics/evidence"
        : mode === "persona"
          ? `/api/v1/analytics/persona/${persona}`
          : investigationId ? `/api/v1/story/${investigationId}` : "";
    if (!path) return;
    setError("");
    fetch(path).then((response) => response.ok ? response.json() : Promise.reject(new Error(`${response.status} ${response.statusText}`)))
      .then(setData).catch((reason) => setError(reason.message));
  }, [mode, investigationId, persona]);

  const content = mode === "signals"
    ? { title: "Signals & Complaints", copy: "Start with what changed in the field. Review complaint patterns with product, version, lot, supplier, and investigation context before deciding whether a signal needs action." }
    : mode === "evidence"
      ? { title: "Evidence Intelligence", copy: "See the evidence behind the investigation. Each record stays connected to its source, product scope, time context, provenance, limitations, and review status." }
      : mode === "persona"
        ? { title: "Persona Dashboard", copy: "Focus the workspace on the decisions and evidence that matter to the selected role. Access remains tenant-scoped and governed by the authenticated session." }
        : { title: "Connected Story View", copy: "Follow one investigation from the opening signal through product context, evidence review, assessment, and an accountable human decision." };

  return <div className="content stage2-experience">
    <section className="product-header">
      <div><p className="eyebrow">MDARIX investigation journey</p><h2>{content.title}</h2><p>{content.copy}</p></div>
      <div className="version-pill">Human review required</div>
    </section>
    <nav className="journey-strip" aria-label="Investigation journey">
      <span className={mode === "signals" ? "active" : ""}>01 Signal</span><span>02 Product context</span><span className={mode === "evidence" ? "active" : ""}>03 Evidence</span><span className={mode === "story" ? "active" : ""}>04 Assessment</span><span>05 Human decision</span>
    </nav>
    {mode === "persona" && <select className="persona-select" value={persona} onChange={(event) => setPersona(event.target.value)} aria-label="Persona">{personas.map((item) => <option key={item} value={item}>{item.replace("-", " ")}</option>)}</select>}
    {error && <div className="error">{error}</div>}
    {data && <section className="panel stage2-results"><div className="section-title">Tenant-scoped results</div>
      {mode === "signals" && <div className="evidence-list">{(data.signals ?? []).map((item: any) => <article key={item.signal_id}><strong>{item.signal_id ?? "Complaint"}</strong><span>{item.description ?? "Description not recorded"}</span><small>{item.severity ?? "Severity not recorded"} · {item.status ?? "Status not recorded"}</small></article>)}</div>}
      {mode === "evidence" && <div className="evidence-list">{(data.evidence ?? []).map((item: any) => <article key={item.id}><strong>{item.evidence_identifier}</strong><span>{item.title ?? "Title not recorded"}</span><small>{item.evidence_type} · {item.reliability_status ?? "Reliability not recorded"}</small></article>)}</div>}
      {mode === "story" && <div className="evidence-list">{(data.stages ?? []).map((item: any) => <article key={item.key}><strong>{item.label}</strong><span>{item.status}</span></article>)}</div>}
      {mode === "persona" && <div className="home-insight-grid"><article><span className="eyebrow">Persona</span><strong>{data.persona}</strong><p>Primary review emphasis</p><span>{data.emphasis}</span></article><article><span className="eyebrow">Investigations</span><strong>{data.counts?.investigations ?? 0}</strong><p>Tenant-scoped workspaces</p></article><article><span className="eyebrow">Evidence</span><strong>{data.counts?.evidence ?? 0}</strong><p>Records available for review</p></article></div>}
      <ul className="limitations">{(data.limitations ?? []).map((item: string) => <li key={item}>{item}</li>)}</ul>
    </section>}
  </div>;
}
