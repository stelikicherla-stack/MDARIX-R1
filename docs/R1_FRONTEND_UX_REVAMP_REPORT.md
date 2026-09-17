# MDARIX R1 Frontend UX Revamp Report

## Scope

Day 15.5 refactors the React frontend only. No backend routes, database models, temporal semantics, tenant boundaries, or evidence semantics were changed.

## Delivered changes

- Added a persistent header context for product, version, investigation, temporal mode (Current/Event/Known), and as-of date.
- Added direct investigation selection in the shared context so Product 360, Investigation Workspace, and Decision Center use the same selected investigation.
- Reordered primary navigation into the workflow order: Products, Investigations, Evidence, Decision Center.
- Added investigation workflow navigation for Overview, Evidence, Analysis, Hypotheses, Challenger, Unknowns, Failure Chain, and Decision, with direct section movement and clear action entry points.
- Preserved explicit action feedback for running, success, controlled empty/insufficient outcomes, and backend failures.
- Improved Decision Center labels so AI advisory and human decision/review authority are visibly separated and option labels are readable.
- Retained clickable lifecycle timeline details and the distinction between product-scoped and tenant-scoped evidence.

## Validation

- `npm.cmd --prefix frontend run build` passes.
- The accompanying manual checklist covers persistent context, workflow actions, Decision Center feedback, lifecycle timeline expansion, and evidence scope language.

## Controlled-behavior notes

The UI does not infer a workspace, a causal conclusion, a product-to-evidence relationship, or a human decision. Empty, unresolved, insufficient-evidence, and review-required outcomes remain explicit.
