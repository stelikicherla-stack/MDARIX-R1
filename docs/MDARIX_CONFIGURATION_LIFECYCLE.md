# Configuration lifecycle — Day 25 checkpoint

Material configuration transitions are fail-closed and ordered:
`DRAFT → VALIDATED → APPROVED → ACTIVE → SUPERSEDED`.

The server-side lifecycle utility rejects direct activation, unauthorized
transitions, and tenant spoofing. Persistent configuration-version records and
API/audit integration remain open work.
