# Package 4 — Files, reports, frontend, and accessibility

## Implemented or verified in code

- Object storage has a provider abstraction with local development and S3-compatible production backends.
- Object keys are tenant-prefixed and cross-tenant reads are rejected.
- Per-object and per-tenant quotas are enforced before local writes; S3 deployments must enforce the durable quota at the attachment metadata layer.
- Malware scanning hooks are available through `MDARIX_MALWARE_SCANNER_COMMAND`, with a safe development fallback.
- S3 server-side encryption metadata, retention metadata, signed URLs, tenant-safe reads, and storage audit hooks are implemented.
- Supplier attachment upload enforces tenant scope, size/type checks, quota, malware scanning, and upload audit events.
- Reports support JSON, CSV, and PDF output, report versioning, watermarking, tenant-scoped background jobs, retries, authorization, tenant-safe temporary paths, and download audit events.
- Direct report generation now also writes a `REPORT_GENERATED` audit event.
- Compliance reports include tenant-scoped audit and signature-verification data.
- CSV/PDF generation applies the supplied hidden-field policy recursively through the report service.
- A shared consent/compliance banner was extracted from `main.tsx` into `frontend/src/features/shared/ConsentBanner.tsx`; existing shared UI utilities remain extracted in `frontend/src/app/ui.tsx`.
- Frontend unit tests: 13 passed. Backend file/report tests: 8 passed. Frontend production build passed.
- Browser evidence scenarios cover desktop/mobile layouts, authenticated admin/customer-admin paths, Mapping Studio, decision approval, Ask MDARIX, and investigation workflow screenshots when the environment is available.

## Pending operational evidence

- Configure and validate a real S3-compatible provider, malware scanner, lifecycle/retention policy, encryption keys, and production quotas.
- Run authenticated Playwright against the live backend/frontend and retain desktop/mobile screenshots.
- Perform manual keyboard and screen-reader review with NVDA or an equivalent tool and retain evidence.
- Complete full browser regression and production multi-instance validation.

These items are operational evidence gates and are not marked passed by local unit/build results.
