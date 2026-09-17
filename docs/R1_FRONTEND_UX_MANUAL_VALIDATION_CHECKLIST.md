# MDARIX R1 Frontend UX Manual Validation Checklist

## Persistent context

- [ ] Select a product, version, investigation, temporal mode, and as-of date in the header.
- [ ] Move between Products, Investigations, Evidence, and Decision Center; confirm the same context remains selected.
- [ ] Change temporal mode to Current, Event, and Known; confirm a fresh context is loaded and stale results are cleared.

## Investigation workflow

- [ ] Open Investigations and select an investigation from the header or list.
- [ ] Use the workflow navigation to reach Overview, Evidence, Analysis, Hypotheses, Challenger, Unknowns, Failure Chain, and Decision.
- [ ] Run Analysis, Generate Hypotheses, and Run Challenger/Unknowns/Chain; confirm each action shows running, success, controlled empty, or backend-error feedback.
- [ ] Confirm evidence identifiers, reliability, source-anchor counts, hypothesis contradictions/gaps, unknown resolution requirements, and failure-chain epistemic status remain readable.

## Decision Center

- [ ] Open Decision Center from the workflow or navigation with a selected investigation.
- [ ] Generate AI Advisory and confirm it is explicitly labelled as non-decisional.
- [ ] Record a human decision with a rationale; confirm the human-review panel appears.
- [ ] Submit a human review and confirm visible success feedback.

## Product and evidence

- [ ] Expand lifecycle timeline chevrons and confirm details appear.
- [ ] Confirm Evidence states whether it is product-scoped or tenant-scoped.
