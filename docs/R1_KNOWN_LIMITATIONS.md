# MDARIX R1 Known Limitations

## Day 23 governance and electronic signatures

- The Decision Center does not currently provide a historical-decision picker. Controlled test setup or an exact API record reference is required to reopen a specific creator-owned historical decision.
- Material controlled changes are supported through the authenticated governance API, but R1 does not expose a dedicated browser control for initiating them.
- Complete version-by-version signature history is retained, tenant-isolated, immutable through the application API, auditable, and retrievable through the governance API. The current UI presents the latest signing result rather than a complete history viewer.
- These UI limitations do not replace or weaken server-side entitlement, approval-authority, SoD, re-authentication, version, fingerprint, tenant-isolation, replay, or audit controls.
- Formal 21 CFR Part 11 and EU Annex 11 validation has not been completed. R1 does not claim an eIDAS-qualified or PKI document signature.
- MFA, federated SSO re-authentication, external penetration testing, and a full operational signature-administration experience remain future work.

## Validation-method terminology

- `BROWSER`: the entire journey is executed through the user interface.
- `API + BROWSER`: controlled state preparation or transition uses the authenticated API, followed by browser validation of the user-facing behavior.
- `API`: the backend control is validated directly where R1 intentionally has no UI surface.

An `API + BROWSER` result must not be reported as browser-only evidence.
