# R1 Access-Control Validation Evidence

| Test | Requirement | Configured Result | Actual Result |
|---|---|---|---|
| AC-001 | Deny by default | Unknown object has no permission | DENIED / PASS |
| AC-002 | Hidden field | Complaint.InternalNote hidden | Field omitted / PASS |
| AC-003 | Read-only field | Customer B Complaint.Description read-only | Update denied / PASS |
| AC-004 | Editable field | Customer A Complaint.Description editable | Allowed / PASS |
| AC-005 | Export authorization | Export explicitly false | Denied / PASS |
| AC-006 | Role switching | Assigned Auditor role | Switch allowed; permissions recalculated / PASS |
| AC-007 | Unauthorized role switch | Unassigned Administrator role | Denied / PASS |
| AC-008 | Tenant isolation | User A targets tenant B | Denied / PASS |
| AC-009 | Inactive user | User status INACTIVE | No effective permissions / PASS |
| AC-010 | Customer configuration | A/B/C different roles, same engine | Configuration-only difference / PASS |

No passwords, hashes, secrets, or customer-specific security branches are used.
