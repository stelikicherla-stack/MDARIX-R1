# R1 Authentication Validation Evidence

| Test | Expected | Actual | Result |
|---|---|---|---|
| AUTH-001 Signup | Pending sandbox account | Pending verification state | PASS |
| AUTH-002 Password storage | No plaintext | Salted scrypt hash | PASS |
| AUTH-003 Email verification | Single-use token activates account | Active account | PASS |
| AUTH-004 Sign-in | Valid credentials create session | HttpOnly SameSite session | PASS |
| AUTH-005 Sign-out | Session invalidated | Context no longer reusable | PASS |
| AUTH-006 Reset | New password replaces old | New credential works | PASS |
| AUTH-007 Unknown account | No enumeration | Controlled invalid-credentials response | PASS |
| AUTH-008 Public/app separation | Public pages do not expose data | Auth entry is separate | PASS |

No password, hash, session secret, or reset token is included in normal API output.
