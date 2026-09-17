import React, { useEffect, useState } from "react";
import { ChevronRight } from "lucide-react";

type MenuItem = { label: string; href: string; status: "R1" | "Future"; description?: string };
type MenuGroup = { title: string; items: MenuItem[] };

const item = (label: string, href: string, status: "R1" | "Future", description?: string): MenuItem => ({ label, href, status, description });

const menus: Record<string, MenuGroup[]> = {
  "Platform & AI": [
    { title: "MDARIX Platform", items: [item("Platform Overview", "/platform", "R1"), item("Product 360", "/platform/product-360", "R1", "Reconstruct product and version context."), item("Reality Graph", "/platform/reality-graph", "R1", "Relate lifecycle entities and evidence."), item("Ask MDARIX", "/roadmap#ask-mdarix", "Future"), item("Evidence Intelligence", "/platform/evidence", "R1")] },
    { title: "Investigation Intelligence", items: [item("Investigation Workspace", "/platform/investigation", "R1"), item("Timeline Intelligence", "/platform/timeline", "R1"), item("AI Investigator", "/platform/ai-investigator", "R1"), item("Hypothesis Engine", "/platform/hypotheses", "R1"), item("AI Challenger", "/platform/challenger", "R1", "Search for evidence that challenges an explanation."), item("Unknowns Radar", "/platform/unknowns", "R1"), item("Failure Chain Intelligence", "/platform/failure-chain", "R1"), item("Counterfactual Analysis", "/platform/counterfactual", "R1")] },
    { title: "Decision & Trust", items: [item("Decision Center", "/platform/decision-center", "R1"), item("Investigation Brief", "/platform/investigation-brief", "R1"), item("Human Review & Approval", "/platform/human-review", "R1"), item("AI Assurance", "/platform/ai-assurance", "R1"), item("Audit Trail", "/platform/audit-trail", "R1")] },
    { title: "Enterprise", items: [item("Integrations", "/integrations", "R1"), item("Administration", "/roadmap#administration", "R1"), item("Security & Access", "/security", "R1"), item("Plans & Entitlements", "/plans", "R1")] },
  ],
  "Product Lifecycle": [
    { title: "Discover & Define", items: [item("Product Strategy", "/roadmap#product-strategy", "Future"), item("Product Portfolio", "/roadmap#portfolio", "Future"), item("Product Concept", "/roadmap#concept", "Future"), item("User / Clinical Need", "/roadmap#clinical-need", "Future")] },
    { title: "Develop", items: [item("Requirements", "/roadmap#requirements", "Future"), item("Design & Development", "/roadmap#design", "Future"), item("Design Controls", "/roadmap#design-controls", "Future"), item("Risk", "/roadmap#risk", "Future"), item("Verification & Validation", "/roadmap#verification", "Future")] },
    { title: "Prove, Release & Produce", items: [item("Regulatory", "/roadmap#regulatory", "Future"), item("Clinical", "/roadmap#clinical", "Future"), item("Manufacturing", "/roadmap#manufacturing", "Future"), item("Supplier & Component", "/platform/product-360", "R1"), item("Lot / Batch & Change", "/platform/product-360", "R1")] },
    { title: "Monitor & Evolve", items: [item("Complaints", "/post-market", "R1"), item("Investigation Intelligence", "/platform/investigation", "R1"), item("CAPA", "/roadmap#capa", "Future"), item("Field Action / Recall", "/roadmap#recall", "Future"), item("Next Product Version", "/roadmap#next-version", "Future"), item("Product Retirement", "/roadmap#retirement", "Future")] },
  ],
  "Post-Market Intelligence": [
    { title: "Complaint Intelligence", items: [item("Complaint Intelligence", "/post-market", "R1"), item("Complaint Trends", "/post-market", "R1"), item("Similar Failure Intelligence", "/roadmap#similar-failure", "Future")] },
    { title: "PMS & Signal", items: [item("Post-Market Surveillance", "/roadmap#pms", "Future"), item("Signal Intelligence", "/roadmap#signal", "Future"), item("Emerging Patterns", "/roadmap#patterns", "Future"), item("ProductVersion Comparison", "/platform/product-360", "R1")] },
    { title: "Investigation", items: [item("Investigation Workspace", "/platform/investigation", "R1"), item("Timeline Intelligence", "/platform/timeline", "R1"), item("Evidence Intelligence", "/platform/evidence", "R1"), item("AI Investigator", "/platform/ai-investigator", "R1"), item("Hypotheses & Challenger", "/platform/hypotheses", "R1"), item("Unknowns Radar", "/platform/unknowns", "R1")] },
    { title: "Failure & Decision", items: [item("Failure Chain", "/platform/failure-chain", "R1"), item("Component / Supplier / Lot Relationships", "/platform/reality-graph", "R1"), item("Decision Center", "/platform/decision-center", "R1"), item("Human Review", "/platform/human-review", "R1"), item("Investigation Brief", "/platform/investigation-brief", "R1")] },
  ],
  "Trust & Governance": [
    { title: "AI Trust", items: [item("AI Assurance", "/platform/ai-assurance", "R1"), item("Evidence Grounding", "/ai-trust", "R1"), item("Temporal & ProductVersion Validation", "/ai-trust", "R1"), item("Contradiction & Unknown Detection", "/platform/challenger", "R1"), item("AI Provenance", "/ai-trust", "R1")] },
    { title: "Human Governance", items: [item("Decision Center", "/platform/decision-center", "R1"), item("Human Review", "/platform/human-review", "R1"), item("Approval Authority", "/trust-governance", "R1"), item("Electronic Approval / Signature", "/trust-governance", "R1"), item("Segregation of Duties", "/trust-governance", "R1")] },
    { title: "Enterprise Governance", items: [item("Audit Trail", "/platform/audit-trail", "R1"), item("Roles & Permissions", "/trust-governance", "R1"), item("Tenant Isolation", "/security", "R1"), item("Plans & Entitlements", "/plans", "R1"), item("Configuration Governance", "/roadmap#configuration", "Future")] },
    { title: "Security", items: [item("Security Overview", "/security", "R1"), item("Authentication", "/security", "R1"), item("Data Protection", "/security", "R1"), item("Integration Security", "/integrations", "R1")] },
  ],
};

const pages: Record<string, { eyebrow: string; title: string; copy: string }> = {
  "/": { eyebrow: "Medical device product lifecycle intelligence", title: "Turn fragmented lifecycle data into trusted product decisions.", copy: "MDARIX connects existing systems of record, reconstructs product reality, and gives investigation teams evidence-grounded intelligence while authorized humans retain decision authority." },
  "/platform": { eyebrow: "Platform & AI", title: "One connected intelligence layer for medical-device product reality.", copy: "Connect lifecycle evidence, reconstruct what was true when, investigate competing explanations, expose unknowns, and preserve traceable human decisions." },
  "/product-lifecycle": { eyebrow: "Long-term product vision", title: "Intelligence across the medical-device product lifecycle.", copy: "MDARIX is being built to connect strategy, development, release, production, post-market learning, and product evolution. The roadmap clearly separates current R1 capabilities from future modules." },
  "/post-market": { eyebrow: "Initial commercial focus", title: "Post-market intelligence grounded in product reality.", copy: "Relate complaints to product versions, components, suppliers, lots, changes, evidence, and investigations—without replacing the systems that own those records." },
  "/trust-governance": { eyebrow: "Trust & governance", title: "AI recommends. Authorized humans decide.", copy: "Evidence grounding, temporal validation, provenance, role controls, approval authority, segregation of duties, and electronic signatures create a controlled R1 foundation." },
  "/resources": { eyebrow: "Resources", title: "Understand the MDARIX approach.", copy: "Explore the R1 coverage story, product roadmap, AI trust model, security foundation, and integration architecture." },
  "/plans": { eyebrow: "Plans", title: "Start with controlled early access.", copy: "R1 supports a Free / Early Access development journey. Plan entitlements control capability access; commercial packaging remains subject to future approval." },
  "/r1": { eyebrow: "What MDARIX R1 covers", title: "From lifecycle data to assured human decisions.", copy: "R1 delivers a connected post-market investigation vertical slice for quality, regulatory, engineering, IT, and executive reviewers." },
  "/roadmap": { eyebrow: "Product roadmap", title: "Available in R1—and what comes next.", copy: "R1 focuses on product reality, post-market investigation, evidence intelligence, decision support, and assurance. Broader lifecycle modules remain future roadmap capabilities without promised release dates." },
  "/integrations": { eyebrow: "Integrations", title: "Work above the systems you already trust.", copy: "QMS, PLM, ERP, MES, supplier, document, and evidence platforms remain systems of record. MDARIX connects their lifecycle context through a controlled integration foundation." },
  "/security": { eyebrow: "Security & access", title: "Designed for controlled, traceable intelligence.", copy: "Tenant isolation, authentication, role and field authorization, action controls, provenance, and human authority form the R1 security foundation. Independent certification is not claimed." },
  "/ai-trust": { eyebrow: "AI trust", title: "Grounded intelligence with visible limits.", copy: "MDARIX preserves evidence references, temporal context, contradictions, unknowns, provenance, and human review. AI does not create the final regulated decision." },
  "/request-demo": { eyebrow: "Get started", title: "Explore MDARIX in your lifecycle context.", copy: "Use Free / Early Access to create an account, verify email, sign in, and enter the tenant-scoped R1 application." },
};

export function PublicMegaSite({ path }: { path: string }) {
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);
  useEffect(() => { const close = (event: KeyboardEvent) => { if (event.key === "Escape") { setOpenMenu(null); setMobileOpen(false); } }; window.addEventListener("keydown", close); return () => window.removeEventListener("keydown", close); }, []);
  const capability = path.startsWith("/platform/") ? (path.split("/").pop() ?? "capability").replace(/-/g, " ").replace(/\b\w/g, letter => letter.toUpperCase()) : null;
  const page = capability ? { eyebrow: "Available in R1", title: capability, copy: `${capability} is part of the current MDARIX R1 investigation and decision-intelligence vertical slice. It operates within controlled product, version, temporal, evidence, tenant, and human-governance boundaries.` } : pages[path] ?? pages["/"];
  const flow = ["Connect", "Reconstruct", "Relate", "Investigate", "Challenge", "Identify gaps", "Reason", "Decide", "Trust"];
  return <div className="public-shell" onClick={() => openMenu && setOpenMenu(null)}>
    <header className="public-header" onClick={event => event.stopPropagation()}>
      <a className="brand" href="/">MDARIX</a><button className="mobile-menu-button" aria-expanded={mobileOpen} aria-controls="public-navigation" onClick={() => setMobileOpen(!mobileOpen)}>Menu</button>
      <nav id="public-navigation" className={mobileOpen ? "mobile-open" : ""}>{Object.keys(menus).map(name => <button key={name} aria-expanded={openMenu === name} onClick={() => setOpenMenu(openMenu === name ? null : name)}>{name}</button>)}<a href="/resources">Resources</a><a href="/plans">Plans</a></nav>
      <div className="public-actions"><a href="/signin">Sign in</a><a className="primary-action" href="/signup">Get started</a></div>
      {openMenu && <div className="mega-menu" role="region" aria-label={`${openMenu} menu`}>{menus[openMenu].map(group => <section key={group.title}><h2>{group.title}</h2>{group.items.map(entry => <a key={entry.label} href={entry.href}><span><strong>{entry.label}</strong>{entry.description && <em>{entry.description}</em>}</span><small className={entry.status === "R1" ? "status-r1" : "status-future"}>{entry.status}</small></a>)}</section>)}</div>}
    </header>
    <main className="public-main"><section className="public-hero"><span className="eyebrow">{page.eyebrow}</span><h1>{page.title}</h1><p>{page.copy}</p><div className="public-cta"><a className="primary-action" href={path === "/request-demo" ? "/signup" : "/r1"}>{path === "/request-demo" ? "Create account" : "See what R1 covers"}</a><a className="secondary-link" href="/roadmap">View product roadmap →</a></div></section>
      <section className="public-story"><div><span className="eyebrow">Current R1 end-to-end story</span><h2>Connect data. Reconstruct reality. Investigate with evidence. Keep humans in control.</h2></div><div className="lifecycle-flow">{flow.map((step, index) => <React.Fragment key={step}><article><strong>{step}</strong><span className="status-r1">R1</span></article>{index < flow.length - 1 && <ChevronRight aria-hidden="true" />}</React.Fragment>)}</div><div className="public-principle"><strong>MDARIX is not another QMS.</strong><p>Customer QMS, PLM, ERP, MES, supplier, and evidence platforms remain authoritative systems of record. MDARIX provides the connected intelligence layer above them.</p></div></section>
      {path === "/roadmap" && <section className="public-story roadmap-grid"><article><span className="status-r1">Available in R1</span><h2>Post-market investigation intelligence</h2><p>Product 360, Reality Graph, temporal context, evidence intelligence, AI investigation, hypotheses, challenger, unknowns, failure chain, counterfactuals, decisions, assurance, and audit foundations.</p></article><article><span className="status-future">Future</span><h2>Broader lifecycle intelligence</h2><p>Strategy, requirements, design controls, regulatory, clinical, manufacturing operations, CAPA, recall, launch, continuous monitoring, and retirement remain roadmap capabilities.</p></article></section>}
    </main>
    <footer className="public-footer"><span>MDARIX — System of Intelligence, not System of Record.</span><span><a href="/r1">R1 coverage</a> · <a href="/roadmap">Roadmap</a> · <a href="/security">Security</a></span></footer>
  </div>;
}
