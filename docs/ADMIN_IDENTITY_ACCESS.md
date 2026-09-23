# Stage 2 — Identity and access administration

Identity administration is tenant-scoped and uses authenticated request context. Platform users, memberships, personas, role assignments, permission sets, sessions, invitations and password resets are durable records. Sessions expose creation/last-seen/revocation state and revocation is audited. Customer administrators are limited to their tenant administration and are not business-data superusers.

Production validation must still exercise multiple application instances and real cookie/session rotation.
