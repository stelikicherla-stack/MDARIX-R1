import Link from "next/link";

const capabilities = [
  ["Product 360", "Connect product, version, component, supplier, lot, complaint and change context.", "/platform/product-360"],
  ["Investigation workspace", "Move from a signal to evidence, competing hypotheses, unknowns and review.", "/platform/investigation"],
  ["Ask MDARIX", "Ask bounded questions against authorized context with provenance and uncertainty visible.", "/platform/ask-mdarix"],
  ["Decision Center", "Keep human approval, evidence gaps and signed decisions traceable.", "/platform/decision-center"],
];

export default function Home() {
  return <main>
    <header className="site-header"><Link className="brand" href="/">MDARIX <span>Product lifecycle intelligence</span></Link><nav aria-label="Primary navigation"><Link href="/platform">Platform</Link><Link href="/solutions">Solutions</Link><Link href="/product-lifecycle">Product lifecycle</Link><Link href="/trust">Trust</Link><Link href="/resources">Resources</Link></nav><div className="actions"><Link href="/signin">Login</Link><Link className="button" href="/request-demo">Request demo</Link></div></header>
    <section className="hero"><div><p className="eyebrow">Medical device lifecycle intelligence</p><h1>Turn post-market signals into defensible product decisions.</h1><p className="lede">MDARIX connects complaints, product reality, evidence and human governance so quality, regulatory and product teams can investigate with confidence.</p><div className="actions"><Link className="button" href="/request-demo">Explore MDARIX</Link><Link className="text-link" href="/platform">See the platform →</Link></div></div><div className="hero-visual" aria-label="MDARIX investigation flow diagram"><div className="visual-title">One connected investigation story</div><div className="flow">{["Product", "Signals", "Evidence", "Unknowns", "Decision"].map((item, i) => <div className={i === 4 ? "flow-card selected" : "flow-card"} key={item}><b>{item}</b><small>{i === 0 ? "version & scope" : i === 1 ? "complaints & change" : i === 2 ? "provenance & gaps" : i === 3 ? "what is missing" : "human review"}</small></div>)}</div><small>Product reality → signals → evidence → governed decision</small></div></section>
    <section className="section"><p className="eyebrow">A clearer path to action</p><h2>From product reality to a reviewable decision.</h2><div className="card-grid">{capabilities.map(([title, copy, href]) => <article className="card" key={title}><p className="eyebrow">MDARIX capability</p><h3>{title}</h3><p>{copy}</p><Link className="text-link" href={href}>Learn more →</Link></article>)}</div></section>
    <footer className="footer"><div><strong>MDARIX</strong><p>System of intelligence, not system of record.</p></div><div><Link href="/security">Security &amp; access</Link><Link href="/pricing">Pricing</Link><Link href="/request-demo">Contact</Link></div></footer>
  </main>;
}
