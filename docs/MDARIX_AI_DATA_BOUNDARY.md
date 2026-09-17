# MDARIX AI Data Boundary — Day 25 foundation

The server constructs AI context from an allowlist after tenant, identity,
role, entitlement, object, record, and field authorization have succeeded.
Browser questions and prompt text never grant access.

`backend.app.ai_boundary.build_context` fails closed on tenant mismatch and
omits unauthorized or secret-like fields before provider construction. It does
not store hidden chain-of-thought.

Current evidence: three focused tests cover allowlisting, cross-tenant denial,
and prompt claims that attempt to expand access. Integration into every future
natural-language retrieval path and the complete authorization matrix remain
pending Day 25 work.
