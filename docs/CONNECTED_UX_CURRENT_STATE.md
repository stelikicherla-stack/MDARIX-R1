# Connected UX Current State

The application is a React/TypeScript single-page shell with authenticated private routes for Home, Product 360, Investigations, Evidence, Decision Center, AI Assurance, Audit, and administration. The shell currently uses an internal view state for business navigation and retains public URL handling for website/auth entry points.

Trusted server-backed Case Context is available at `/api/v1/workspace/context`; product, ProductVersion, and investigation IDs are validated against the authenticated tenant. Existing screens reuse Product 360 data and temporal controls. Remaining decomposition into route modules and a formal ContextBar/WorkflowStepper package is a controlled follow-up, not a security bypass.
