import { useState } from "react";

function displayValue(value: unknown): string {
  if (Array.isArray(value)) return value.length ? value.map(item => typeof item === "string" ? item : JSON.stringify(item)).join(" ") : "None recorded";
  if (value && typeof value === "object") return JSON.stringify(value, null, 2);
  return value == null || value === "" ? "None recorded" : String(value);
}

export function AskMdarixPage({ investigationId, productVersionId }: { investigationId?: string; productVersionId?: string }) {
  const [question, setQuestion] = useState(""); const [result, setResult] = useState<any>(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(false);
  const ask = async () => {
    if (!question.trim() || loading) return;
    setError(""); setResult(null); setLoading(true);
    try {
      const response = await fetch("/api/v1/stage3/interactions", { method: "POST", credentials: "include", headers: { "Content-Type": "application/json", "X-Correlation-ID": `UI-ASK-${Date.now()}` }, body: JSON.stringify({ prompt: question.trim(), investigation_id: investigationId || null, product_version_id: productVersionId || null, page_context: "ASK_MDARIX", temporal_mode: "CURRENT" }) });
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.detail?.message || payload.detail || "Ask request failed");
      setResult(payload);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Ask request failed"); }
    finally { setLoading(false); }
  };
  const response = result?.response || {};
  return <div className="content"><section className="product-header"><div><p className="eyebrow">Ask MDARIX</p><h2>Ask about the active case</h2><p>Your question inherits the authenticated tenant, role, ProductVersion, investigation, and temporal Case Context.</p></div><div className="version-pill">Human review required</div></section><section className="panel"><label htmlFor="ask-question">Question</label><textarea id="ask-question" rows={5} value={question} onChange={e => setQuestion(e.target.value)} placeholder="What is known, what changed, and what evidence is missing?"/><button className="primary-action" onClick={ask} disabled={!question.trim() || loading}>{loading ? "Retrieving authorized context…" : "Ask MDARIX"}</button>{error && <p className="error" role="alert">{error}</p>}</section>{result && <section className="panel"><div className="section-title">Structured response</div>{response.provider_output?.answer && <article className="decision-items"><strong>AI advisory</strong><span>{response.provider_output.answer}</span></article>}{Object.entries(response).filter(([key]) => key !== "provider_output").map(([key, value]) => <article className="decision-items" key={key}><strong>{key.replace(/_/g, " ")}</strong><span style={{ whiteSpace: "pre-wrap" }}>{displayValue(value)}</span></article>)}</section>}</div>;
}
