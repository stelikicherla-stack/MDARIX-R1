# MDARIX Context Cascade Rules

1. Tenant is derived from the authenticated durable session.
2. Product must belong to the active tenant.
3. ProductVersion must belong to that Product and tenant.
4. Signal/complaint scope must be compatible with ProductVersion.
5. Investigation must belong to the tenant and be compatible with the selected product scope.
6. Changing Product clears ProductVersion, signal, investigation, decision, and downstream review context.
7. Changing ProductVersion clears incompatible signal/investigation and refreshes evidence, Ask, Decision, Assurance, and Audit context.
8. Invalid or stale context is rejected or reset; it is never silently accepted.
