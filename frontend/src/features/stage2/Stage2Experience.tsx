import { useEffect, useState } from "react";

type Stage2Mode = "signals" | "story" | "evidence" | "persona";

export function Stage2Experience({ mode, investigationId }: { mode: Stage2Mode; investigationId?: string }) {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState("");
  const [persona, setPersona] = useState("investigator");
  useEffect(() => {
    const path = mode === "signals" ? "/api/v1/analytics/signals" : mode === "evidence" ? "/api/v1/analytics/evidence" : mode === "persona" ? `/api/v1/analytics/persona/${persona}` : investigationId ? `/api/v1/story/${investigationId}` : "";
    if (!path) return;
    fetch(path).then((r) => r.ok ? r.json() : Promise.reject(new Error(`${r.status} ${r.statusText}`))).then(setData).catch((e) => setError(e.message));
  }, [mode, investigationId, persona]);
  const title = mode === "signals" ? "Signals & Complaints" : mode === "evidence" ? "Evidence Intelligence" : mode === "persona" ? "Persona Dashboard" : "Connected Story View";
  return <div className="content"><section className="product-header"><div><p className="eyebrow">Stage 2 connected experience</p><h2>{title}</h2><p>Authenticated, tenant-scoped, ProductVersion-aware context. Source facts and derived interpretation remain visibly distinct.</p></div><div className="version-pill">Human review required</div></section>
    {mode === "persona" && <select value={persona} onChange={(e) => setPersona(e.target.value)} aria-label="Persona"><option>investigator</option><option>quality-manager</option><option>regulatory</option><option>risk-manager</option><option>approver</option><option>executive</option></select>}
    {error && <div className="error">{error}</div>}
    {data && <section className="panel"><div className="section-title">Tenant-scoped results</div>{mode === "signals" && <div className="evidence-list">{(data.signals ?? []).map((item: any) => <article key={item.signal_id}><strong>{item.signal_id ?? "Complaint"}</strong><span>{item.description ?? "Description not recorded"}</span><small>{item.severity ?? "Severity not recorded"} · {item.status ?? "Status not recorded"}</small></article>)}</div>}{mode === "evidence" && <div className="evidence-list">{(data.evidence ?? []).map((item: any) => <article key={item.id}><strong>{item.evidence_identifier}</strong><span>{item.title ?? "Title not recorded"}</span><small>{item.evidence_type} · {item.reliability_status ?? "Reliability not recorded"}</small></article>)}</div>}{mode === "story" && <div className="evidence-list">{(data.stages ?? []).map((item: any) => <article key={item.key}><strong>{item.label}</strong><span>{item.status}</span></article>)}</div>}{mode === "persona" && <div className="home-insight-grid"><article><span className="eyebrow">Persona</span><strong>{data.persona}</strong><p>Emphasis: {data.emphasis}</p></article><article><span className="eyebrow">Investigations</span><strong>{data.counts?.investigations ?? 0}</strong><p>Tenant-scoped records</p></article><article><span className="eyebrow">Evidence</span><strong>{data.counts?.evidence ?? 0}</strong><p>Review required</p></article></div>}<ul className="limitations">{(data.limitations ?? []).map((item: string) => <li key={item}>{item}</li>)}</ul></section>}
  </div>;
}
