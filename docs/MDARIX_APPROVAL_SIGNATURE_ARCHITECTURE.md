# MDARIX Approval and Signature Architecture

The controlled chain is: authenticated session → active tenant → plan entitlement → authenticated user and role → approval authority → identity-based SoD → exact `updated_at` version → explicit decision and remarks → current-password re-authentication → canonical SHA-256 fingerprint → signed record → workflow transition → audit event.

`SignedApprovalRecord` preserves the tenant, object, exact version, decision, remarks, signer identity, role snapshot, signature meaning, fingerprint, and signature hash. Passwords and password hashes are never written to signed records or audit details.

Material controlled changes advance the decision `updated_at` value and return the workflow to `REQUIRES_REVIEW`. Historical signatures remain preserved and are not inherited by the new version. Re-signature is required for the new version.

Approval authority is configuration-driven and deny-by-default. SoD compares authenticated user identity, not merely active role names. The current R1 foundation uses authenticated electronic signatures; formal Part 11, Annex 11, eIDAS-qualified signature, MFA, SSO, and external penetration testing remain future validation work.
