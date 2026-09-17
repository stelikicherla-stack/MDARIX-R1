# R1 Plan and Entitlement Validation

| Test | Plan/feature | Expected | Actual | Result |
|---|---|---|---|---|
| ENT-001 | Active R1 governance assignment | Entitlement evaluator permits configured feature | Server-side assignment and feature rows are evaluated | PASS |
| ENT-002 | Revoked entitlement | Direct signing API denied | Executed HTTP 403 after entitlement revocation | PASS |
| ENT-003 | Direct API bypass | Hidden UI cannot bypass API | Direct signing request denied server-side | PASS |
| AUTH-03 | Revoked approval authority | Signing denied | Executed HTTP 403 after authority revocation | PASS |
| TENANT-01 | Foreign tenant | No signing/history access | Sign denied and history empty | PASS |

Commercial quota and controlled-override packaging remain outside the executed R1 signature path.
