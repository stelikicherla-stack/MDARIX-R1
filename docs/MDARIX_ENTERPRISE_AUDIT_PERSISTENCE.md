# Enterprise audit persistence — Day 25 checkpoint

Day 25 extends the existing `AuditEvent` model through a safe event factory
that redacts password, token, secret, credential, API-key, and authorization
fields before persistence. Connector-run and reconciliation tables are added
through migration `i25enterprise` for durable reconstruction of source runs.

Migration execution and end-to-end API audit wiring remain pending validation.
