import { useEffect, useState } from "react";
import { ClipboardList } from "lucide-react";

export function Stage3CommandCenter() {
  const [summary, setSummary] = useState<any | null>(null);
  useEffect(() => { fetch("/api/v1/analytics/command-center").then(response => response.ok ? response.json() : Promise.reject()).then(setSummary).catch(() => setSummary(null)); }, []);
  if (!summary) return null;
  const counts = summary.counts ?? {};
  return <section className="content stage3-command-center" aria-label="Command center summary">
    <div className="section-title"><ClipboardList size={18} /> What needs attention</div>
    <div className="home-insight-grid">
      <article><span className="eyebrow">Open investigations</span><strong>{counts.investigations ?? 0}</strong><p>Tenant-scoped investigations available for authorized review.</p></article>
      <article><span className="eyebrow">Evidence</span><strong>{counts.evidence ?? 0}</strong><p>Evidence records in the active tenant context.</p></article>
      <article><span className="eyebrow">Review posture</span><strong>Human review required</strong><p>AI assists analysis; authorized humans decide.</p></article>
    </div>
  </section>;
}
