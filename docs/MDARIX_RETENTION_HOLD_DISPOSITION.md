# Retention, Hold, and Disposition — Day 25 foundation

Retention expiry never directly deletes a record. The controlled state is
`ELIGIBLE_FOR_REVIEW`, followed by authorization and an audited execution.
An active hold blocks disposition, a tenant mismatch denies it, and execution
failure is represented as `FAILED` rather than success.

The current implementation is a pure fail-closed decision foundation in
`backend.app.retention`. Persistent policy, hold, review, and disposition
records remain open Day 25 work.
