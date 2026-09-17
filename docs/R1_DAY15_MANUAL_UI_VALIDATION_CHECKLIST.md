# Day 15 Decision Center Manual UI Validation Checklist

Run the frontend and backend against the canonical R1 PostgreSQL database. Do not mark a check PASS without observing it in the browser.

| Area | Manual check | Expected result | Result |
|---|---|---|---|
| Navigation | Open Decision Center from the sidebar | Decision Center is active; Day 15 label is gone | PENDING |
| Investigation | Select a live AsterFlow investigation | Current live investigation ID and context load | PENDING |
| Readiness | Review readiness state and reasons | State is categorical and reasons are explicit | PENDING |
| What We Know | Review observations | Source-grounded observations are shown | PENDING |
| Contradictions | Review contradictions and Challenger findings | Challenges remain visibly distinct from facts | PENDING |
| Hypotheses | Review competing explanations | Hypotheses remain labelled as hypotheses | PENDING |
| Unknowns | Review Unknowns Radar | Unknowns are not rendered as negative facts | PENDING |
| Failure Chain | Review chain links | Weak, broken, hypothesized, and source-supported states remain distinct | PENDING |
| Options | Select a decision option | Controlled options only; no automatic action executes | PENDING |
| AI Advisory | Generate advisory | Advisory is clearly separate from human decision | PENDING |
| Human decision | Enter rationale and record decision | Missing rationale is rejected; saved decision remains pending review | PENDING |
| Human review | Review/approve or reject | Human disposition changes status and is audited | PENDING |
| Disagreement | Choose a disposition different from advisory | Human outcome remains authoritative and advisory is preserved | PENDING |
| Provenance | Inspect context/advisory references | Upstream AI execution and evidence references are visible or retrievable | PENDING |
| Temporal | Switch Current/Event/Known and as-of date | Context changes without future leakage or stale overwrite | PENDING |
| Empty/partial/error | Exercise unavailable upstream outputs and invalid ID | Honest empty/error states; no stack traces or fabricated facts | PENDING |
