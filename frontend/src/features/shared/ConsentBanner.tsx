import React, { useEffect, useState } from "react";

export function ConsentBanner() {
  const [visible, setVisible] = useState(false);
  useEffect(() => { setVisible(localStorage.getItem("mdarix-compliance-consent") !== "accepted"); }, []);
  if (!visible) return null;
  const accept = () => { localStorage.setItem("mdarix-compliance-consent", "accepted"); setVisible(false); };
  return <section className="consent-banner" role="dialog" aria-label="Privacy and compliance consent"><div><strong>Privacy and compliance notice</strong><p>MDARIX uses essential session storage and tenant-scoped audit records to operate this workspace. Review your organization&apos;s GDPR/HIPAA obligations before entering regulated data.</p></div><div className="consent-actions"><button className="secondary-action" onClick={() => setVisible(false)}>Dismiss</button><button className="primary-action" onClick={accept}>Acknowledge</button></div></section>;
}
