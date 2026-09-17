# R1 Electronic Signature Validation

| Test | Requirement | Expected | Actual | Result |
|---|---|---|---|---|
| SIG-003 | Fingerprint changes with material version | Different fingerprint | SHA-256 differs for v3/v4 | PASS |
| SIG-004 | Wrong current password | Re-authentication denied | `INVALID_REAUTHENTICATION` | PASS |
| SIG-005 | Password not persisted in account context | No plaintext password | No plaintext password in hash/context/reset response | PASS |
| SIG-006 | Verification replay | Token rejected | `INVALID_VERIFICATION_TOKEN` | PASS |
| SIG-007 | Full signed browser ceremony | Signed record and audit chain | Not executed in browser | NOT TESTED |
| API-SIG-01 | Correct password and valid controls | Signed approval | HTTP 200 and one signed record | PASS |
| API-SIG-03 | Wrong password | No signature/state transition | HTTP 403 and zero records | PASS |
| API-VERSION-02 | Stale `updated_at` | Reject stale signature | HTTP 409 and zero records | PASS |
| API-REPLAY-01 | Repeated signing request | One signature | Second request HTTP 409; one record | PASS |
| API-SOD-01 | Creator self-approval | Denied | HTTP 403 `SOD_DENIED` | PASS |
| API-TENANT-01/02 | Cross-tenant sign/history | No access/leakage | Sign denied; history empty | PASS |

No test password is recorded in this report. Manual signature ID, browser reviewer, and timestamp evidence remain pending.

Manual results must identify their validation method as `BROWSER`, `API + BROWSER`, or `API`. Controlled API setup must not be reported as browser-only execution.
