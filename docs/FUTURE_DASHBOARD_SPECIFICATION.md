# Stage 3 Dashboard Specification

Command Center answers “what needs attention?” and is backed by `/api/v1/analytics/command-center`. Required dashboard families are Command Center, Product, Signals & Complaints, Investigation, Evidence, Decision, AI Assurance, and Admin. React renders returned aggregates; large analytics are not calculated in the browser. Counts and attention items are tenant-scoped and limitations are visible.
