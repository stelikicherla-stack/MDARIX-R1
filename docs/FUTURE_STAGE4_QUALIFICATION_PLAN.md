# Stage 4 Qualification Plan

## Functional flow

Login → Home → Product → ProductVersion → Signal → Investigation → Evidence → Ask MDARIX → Analysis → Hypotheses → Challenger → Unknowns → Failure Chain → Scenario → Decision Brief → Decision → Approval → Assurance → Audit → Report.

## Security gates

- Every customer-owned route requires authenticated durable context.
- Cross-tenant requests return non-disclosing denial.
- Viewer writes, foreign admin actions, and external write-back are denied.
- Invitation/reset replay, expiry, revocation, secure cookies, and webhook verification are tested.
- AI and agents cannot approve, reject, declare root cause, or write approved records.

## Context gates

Product and ProductVersion changes clear incompatible downstream scope; browser refresh, multiple tabs, stale context versions, temporal modes, and decision snapshot replay are tested.

## Qualification evidence

`scripts/stage4_qualification.py` creates `evidence/future-architecture/` with secret-free evidence placeholders and current repository state. Live provider, browser screenshot, and deployment evidence must be attached only from the target environment.
