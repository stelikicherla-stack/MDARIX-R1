# Stage 2 — Identity and authenticated context

Stage 2 adds a reusable `AuthenticatedRequestContext` dependency and durable schema primitives for revocable sessions and authentication events. The context derives identity and tenant from the authenticated server session; request payload tenant identifiers are never trusted. Existing legacy routers remain an explicit migration surface and must be moved to this dependency before production release.
