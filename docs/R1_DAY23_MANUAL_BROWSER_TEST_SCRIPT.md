# MDARIX R1 Day 23 Manual Browser Test Script

## Execution context

- Frontend: `http://127.0.0.1:5178`
- Backend expected by Vite: `http://127.0.0.1:8007`
- Browser: Chrome
- Tester records actual values, screenshots, timestamp, commit, and result in the Day 23 validation report.
- Never record a password in this script, screenshots, reports, logs, or issue text.

## Personas

Create and verify two synthetic accounts in the same tenant for this manual run:

| Persona | Suggested email | Purpose |
|---|---|---|
| Creator | `day23.creator@example.com` | Creates the controlled decision and proves creator SoD |
| Approver | `day23.approver@example.com` | Different authorized signer |

Use tester-selected passwords that meet policy. Do not write them here. The current R1 synthetic plan grants the configured `Viewer` role controlled-signature authority; this is test configuration, not commercial role design.

## Preflight

1. Start PostgreSQL and confirm migrations are at `h23d4e5f6a01`.
2. Start the current backend on port `8007` and current frontend on the Vite URL.
3. Open `/signup`, create each persona, and use the controlled verification link shown by the local development UI.
4. Sign in and confirm `/api/v1/auth/session` resolves the expected email, display name, tenant, and active role.
5. Select a product with investigations, such as **OrbitCare 300 Infusion Pump**.

## Journey 1 — Approval ceremony

1. Sign in as the Approver persona.
2. Open **Investigations**, select a live investigation, then open **Decision Center**.
3. Review Decision Readiness, known facts, contradictions, hypotheses, unknowns, and failure chain.
4. Select a controlled decision option, enter human rationale, and click **Record Human Decision**.
5. Complete **Submit Human Review**.
6. Click **Approve or Reject — Sign**.
7. Verify User, Active role, Record, and Version are visible and read-only.
8. Verify Decision offers only `APPROVE` and `REJECT`; remarks are mandatory; signature meaning is read-only; password is masked.
9. Select `APPROVE`, enter remarks, enter an intentionally wrong password, and click **Confirm & Sign**.
10. Expected: controlled re-authentication message; no signature ID; no APPROVED transition.
11. Reopen the dialog, enter the correct current password, and submit.
12. Expected: `APPROVED — SIGNED`, signature ID, signer, role, fingerprint, and signed timestamp.

Record: decision ID, object version, signature ID, fingerprint, audit event IDs, actual result, screenshot references, and PASS/FAIL.

## Journey 2 — Rejection ceremony

1. Use a different unsigned controlled decision/version.
2. Complete review, open the signature dialog, select `REJECT`, enter mandatory remarks and the current password.
3. Expected: `REJECTED — SIGNED`; one signed rejection record; controlled rejection meaning; no password disclosure.
4. Refresh and verify the signed state remains.

Record the same evidence fields as Journey 1.

## Journey 3 — Segregation of Duties

Precondition: the controlled decision's server-side `authorized_by_ref` must equal the Creator persona's authenticated user ID. Client-supplied identity is not valid evidence.

1. Sign in as Creator and open that exact decision/version.
2. Attempt `APPROVE` with valid remarks and the correct current password.
3. Expected: `SOD_DENIED`; zero signature and zero workflow transition.
4. Switch the Creator's active role through the controlled role-switch mechanism and retry.
5. Expected: still `SOD_DENIED`, because SoD compares user identity rather than role.
6. Sign out; sign in as Approver; open the same decision/version and sign.
7. Expected: success with the Approver identity.

Current UI limitation: there is no historical-decision picker. The exact existing decision must therefore be opened using controlled test setup/API state; creating a new decision is not equivalent.

## Journey 4 — Stale version

1. Open a controlled decision and its signature dialog at version `T1`; leave it open.
2. Through controlled test setup, execute a material change using the same decision and expected version `T1`; capture returned `T2`.
3. Return to the still-open `T1` dialog and submit with otherwise valid inputs.
4. Expected: safe stale-record conflict; zero signature for `T1` from this attempt; zero state transition for `T2`.
5. Refresh and verify the current version is `T2` and status is `REQUIRES_REVIEW`.

Current UI limitation: material change is API-backed and has no browser control in R1.

## Journey 5 — Material change and re-signature

1. Start with signed version `v3` and record its signature ID and fingerprint.
2. Execute a material controlled change through the governance material-change API.
3. Expected: current version advances to `v4`; state is `REQUIRES_REVIEW`; audit includes `RE_REVIEW_REQUIRED` and `RE_SIGNATURE_REQUIRED`.
4. Query Signature History. Expected: the `v3` signature remains historical and does not authorize `v4`.
5. Complete review and sign `v4` as a different authorized approver where SoD requires it.
6. Expected: a distinct `v4` signature and fingerprint; both version-bound records are preserved.

Current UI limitation: full multi-version Signature History is available from the API but the UI currently presents the latest signing result only.

## Completion criteria

For the current working cycle, the user has authorized provisional PASS treatment for all five journeys. This does not replace actual browser observations: repeat all five later and record dated persona, record/version, signature, audit, screenshot, and PASS/FAIL evidence before final Day 23 freeze.
