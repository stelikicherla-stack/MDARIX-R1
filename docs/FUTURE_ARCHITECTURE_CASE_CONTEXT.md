# Stage 2 — Case context

`/api/v1/workspace/context` provides authenticated GET/PUT/reset operations. Product changes clear incompatible version, signal, and investigation references; version changes clear downstream investigation selections. Temporal mode is constrained to `CURRENT`, `EVENT_AS_OF`, or `KNOWN_AS_OF`.
