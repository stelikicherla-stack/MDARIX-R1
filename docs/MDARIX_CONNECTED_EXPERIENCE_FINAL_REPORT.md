# MDARIX R1 Connected Experience — Stage 4 Qualification Report

Status: **MVP DESIGN-PARTNER GO WITH EXPLICIT LIMITATIONS**

## Scope

Stage 4 consolidates the connected Case Context experience across Product,
ProductVersion, Signals, Investigations, Evidence, Ask MDARIX, Decision,
Assurance, Audit, Reporting, and communication workflows. The repository uses
tenant-scoped authenticated context and keeps analysis read-only with human
approval required for governed decisions.

## Automated implementation and qualification

- Context cascade and scope controls are covered by backend regression tests.
- Ask MDARIX has a dedicated route and structured response panels.
- Decision approval creates a durable ContextSnapshot and preserves versioned
  approval context.
- Case audit and administrative audit remain separate concerns.
- Outbound email uses a provider abstraction; inbound webhook signatures and
  durable replay identifiers are checked before processing.
- Reports, object storage abstraction, tenant denial, prompt-injection safety,
  contradiction/unknown handling, and decision prerequisites are covered by
  repository tests.
- A secret-free evidence package is generated under `evidence/connected-mdarix`.

## Required Stage 4 journey

The supported journey is Product → ProductVersion → Case Context → Product 360
→ Signal/Complaint → Investigation → Evidence → Ask MDARIX → hypotheses,
unknowns, challenger, failure chain, scenario → Decision Brief → human decision
and reauthentication → Assurance → Audit/Provenance → report.

The semantic and API portions are automated. Browser navigation, responsive
screenshots, and live external providers require the manual gates below.

## Security and tenant matrix

Tenant A and Tenant B access is authenticated and server-derived. Foreign
Product, ProductVersion, Complaint, Signal, Investigation, Evidence, Ask,
Decision, Audit, Email, Attachment, and Report requests must fail without
disclosing existence. Incoming email is untrusted evidence content; prompt-like
strings cannot authorize actions, change tenant, approve decisions, or establish
root cause.

## Manual gates still required

These cannot be truthfully completed by repository code alone:

1. Live GenAI provider execution with approved credentials and assurance evidence.
2. Live Resend/SMTP outbound delivery and inbound webhook delivery.
3. Browser E2E screenshots across desktop, tablet, and mobile.
4. Production-like multi-instance deployment/session validation.
5. GitHub-hosted CI run and external deployment health evidence.
6. Final VS001–VS012 golden journey sign-off if deferred by the release decision.

No secret, token, password, webhook secret, or customer payload belongs in the
evidence package. The final release decision should remain **GO WITH EXPLICIT
LIMITATIONS** until the manual gates are recorded.
