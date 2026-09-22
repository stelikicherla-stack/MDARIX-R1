# Stage 3 UX Information Architecture

MDARIX uses one authenticated application shell with a trusted Case Context. Business navigation is Home/Command Center, Product 360, Signals, Investigations, Evidence, Ask MDARIX, Decision, Assurance, Audit, and Reports. Platform Administration and Customer Administration remain separate areas and are permission-gated.

The existing React shell already carries Product/ProductVersion and temporal controls. Stage 3 adds governed API contracts for command-center analytics, story view, report catalog, agent catalog, and assurance metrics. Future extraction into `apps/` and `packages/` is intentionally deferred until the current modular monolith has stable contracts.
