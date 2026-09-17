# MDARIX R1 Day 23 Enterprise Governance and Signature Validation

## Status

**VALIDATION IN PROGRESS — NOT YET RELEASE-COMPLETE.**

Day 23 extends authentication with tenant plan entitlement, approval authority, identity-based SoD, password re-authentication, exact decision-version binding, SHA-256 fingerprints, signed approval/rejection records, and audit events.

## Executed evidence

- Alembic governance migration applied successfully.
- Frontend production build passed.
- Python governance router compilation passed.
- Full repository regression: 223 passed, 3 dependency/cache warnings.
- Targeted Day 23 API security matrix: 7 passed. It executed entitlement revocation, authority revocation, creator SoD, correct/wrong-password signing, stale-version rejection, duplicate replay prevention, cross-tenant signing denial, and cross-tenant history isolation.
- Earlier Day 23 + Day 21 + Day 22 focused tests: 12 passed.
- `git diff --check`: passed.

## Control coverage

Plans and entitlements, server-side entitlement checks, approval-authority deny-by-default, creator-based SoD, mandatory decision/remarks/password, current-password verification, version-bound fingerprints, duplicate protection, audit events, material-change re-review, historical signatures, stale-version rejection, and re-signature API are implemented.

The signing dialog derives user and role from the authenticated session and clears the password after the ceremony. The backend does not trust client-supplied signer identity, role, tenant, authority, or SoD values.

## Lifecycle behavior

The signed version remains historical after a material change. The decision receives a new `updated_at` version and `REQUIRES_REVIEW` state. The old signature cannot sign the new version; a new signature is required.

## Pending gates

The five manual journeys are recorded below as provisional PASS based on the current controlled UI/API evidence. They must be re-executed later for final confirmation before Day 23 is declared frozen. Investigation Brief signed-state validation and final security/compliance review remain follow-up gates.

## Manual journey evidence matrix

| Journey | Validation method | Persona | Record/version | Expected | Actual | Signature/audit evidence | Result |
|---|---|---|---|---|---|---|---|
| Approval and wrong-password block | BROWSER | Current controlled UI evidence; re-test later | Pending | Wrong password blocked; correct password signed | PROVISIONAL PASS | Current UI evidence | Re-test required |
| Controlled rejection | BROWSER | Current controlled UI evidence; re-test later | Pending | Signed rejection with mandatory remarks/password | PROVISIONAL PASS | Current UI evidence | Re-test required |
| Creator and role-switch SoD | API + BROWSER | Current controlled evidence; re-test later | Pending | Creator denied across role switch; different approver allowed | PROVISIONAL PASS | Current API/UI evidence | Re-test required |
| Stale-version signing | API + BROWSER | Current controlled evidence; re-test later | T1 → T2 | T1 signing denied with no transition | PROVISIONAL PASS | Current API/UI evidence | Re-test required |
| Material change and re-signature | API + BROWSER + API history | Current controlled evidence; re-test later | v3 → v4 | v3 preserved; v4 re-reviewed and separately signed | PROVISIONAL PASS | Current API/UI evidence | Re-test required |

### Provisional status note

The five journey results are accepted for the current working validation cycle at the user’s direction. This is not final browser evidence or a frozen Day 23 release sign-off. Repeat all five journeys later and replace each provisional result with dated persona, record/version, signature, audit, and screenshot references.

The three validation methods are defined in `docs/R1_KNOWN_LIMITATIONS.md`. API preparation must not be represented as browser-only execution.

## Known limitations

This is an electronic-signature foundation, not a 21 CFR Part 11, EU Annex 11, eIDAS-qualified signature, MFA, SSO, or external penetration-test certification.

The R1 UI does not include a historical-decision picker, a material-change initiation control, or a complete version-by-version signature-history viewer. The underlying controlled APIs and persistent history remain authoritative; see `docs/R1_KNOWN_LIMITATIONS.md`.
