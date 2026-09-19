# MDARIX R1 Day 33 — Information Architecture and Traceability

The shared Investigation Workspace is the convergence point for dashboard
signals, controlled plain-language investigation prompts, existing complaints,
and Product 360 issue entry. Persona suggestions change the experience; server
authorization remains the source of truth.

| Persona | Customer problem / prompt | User story | Backend capability | API / contract | Frontend screen | Required state | Acceptance evidence |
|---|---|---|---|---|---|---|---|
| P1 Quality/PMS Investigator | Why did complaints increase? | Investigate a signal from evidence to unknowns and next action. | Tenant-scoped investigation workspace and evidence summary. | Investigation workspace; evidence summary contract. | Investigation Workspace: Overview, Timeline, Evidence, Hypotheses, Unknowns, Scenarios, Decision. | Normal, partial, unknown, contradiction, missing evidence. | Day 33 evidence classification and workspace tests. |
| P2 Product/Design Quality | What changed across versions/components/suppliers? | Trace product lifecycle context to supporting and conflicting evidence. | Product 360, lifecycle timeline, evidence provenance. | Product 360 and evidence provenance contracts. | Product 360 + Lifecycle. | Current, event-as-of, known-as-of, stale evidence. | Existing Day 29 temporal tests plus provenance checks. |
| P3 Regulatory/PMS Reviewer | Is the evidence complete and defensible? | Review source facts, derived observations, contradictions, unknowns, and limitations. | Evidence Intelligence summary and controlled provenance. | `GET /api/v1/evidence/{id}` summary. | Evidence + Timeline + Investigation. | Sufficient, partially sufficient, insufficient, dependency unavailable. | Day 33 focused evidence tests and negative access tests. |
| P4 Quality/Regulatory Approver | Is an authorized human decision ready? | Review a bounded brief and make a governed human decision. | Decision Brief and existing approval/signature controls. | Brief and Decision Center contracts. | Decision Center. | Human review required, blocked by missing evidence, re-authentication. | Day 23 signature controls and Day 32 brief integration. |
| P5 Product/Quality Leader | Which issues need attention? | Drill from portfolio signal into the same investigation workspace. | Tenant-scoped dashboard and controlled drill-down. | Dashboard and investigation contracts. | Dashboard + controlled drill-down. | Empty, loading, partial retrieval, unresolved. | Dashboard regression and tenant isolation coverage. |
| P6 MDARIX Administrator | How are access and connectors governed? | Configure roles, connector references, mappings, and health policies. | Existing administration, entitlements, and governance services. | Administration/configuration contracts. | Administration. | Unauthorized, validation error, dependency unavailable. | Day 21/22/25 governance validation; connector framework is follow-up. |

## Evidence display contract

Evidence screens must distinguish source facts, derived observations,
AI-assisted interpretations, hypotheses, supporting evidence, contradictory
evidence, unknowns, evidence gaps, limitations, provenance, and human decisions.
Missing data is never rendered as negative evidence. Internal UUIDs, SQL,
credentials, model names, and raw execution details stay out of the primary
customer workflow.

## Day 33 scope boundary

Day 33 locks the information architecture and evidence contract. Full connector
configuration, the complete approval ceremony, and the broader security
campaign remain scheduled follow-up work in Days 34–45.
