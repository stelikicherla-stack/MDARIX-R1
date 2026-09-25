# Developer and Demo Readiness Tooling

## Current repository status

| Area | Tool | Status | Evidence or next action |
| --- | --- | --- | --- |
| Browser automation/screenshots | Playwright | **Available** | `frontend/package.json`, `frontend/playwright.config.ts`, `frontend/e2e/` |
| Accessibility checks | axe-core + axe-playwright | **Available** | Frontend dependencies are installed; run through Playwright evidence tests |
| Web security scanning | OWASP ZAP | **Manual/local** | Run against a started frontend and backend; do not treat an empty local scan as production proof |
| Secret scanning | Gitleaks | **Not wired into CI** | Install locally or add an approved CI action before release |
| SMTP capture | Mailpit/MailHog | **Not in Compose** | Add only for local email-flow testing; production delivery still requires a real provider |
| API testing | Bruno/Insomnia/Postman | **Optional manual** | Use the checked-in PowerShell/API scripts and redacted request evidence; tool choice is not a product dependency |
| Database inspection | pgAdmin/DBeaver Community | **Optional manual** | Useful for inspection; never use it as an authorization boundary |
| Load testing | k6 OSS | **Not in repository** | Add an approved scenario and target environment before performance claims |
| Container scanning | Trivy | **Not wired into CI** | Scan built images in a Docker-enabled CI or release environment |
| Python dependency scanning | pip-audit | **Available and CI-wired** | `.github/workflows/ci.yml` runs `pip-audit -r requirements.txt` |
| JavaScript dependency scanning | npm audit | **Available and CI-wired** | `.github/workflows/ci.yml` runs `npm audit --audit-level=high` |
| Python quality | Ruff/mypy | **Not configured** | Add configuration and baseline before making lint/type claims |
| JavaScript quality | ESLint | **Not configured** | Add config and scripts before making lint claims |
| Object storage simulation | MinIO/LocalStack | **Not in Compose** | Current local object storage remains a development fallback; production storage is still external |
| Metrics | Prometheus/Grafana | **Not in Compose** | Worker emits structured metrics logs; production scraping/dashboard setup remains required |
| Error tracking | Sentry/OpenTelemetry | **Not configured** | Structured logs exist; external error collection requires an approved destination |

## Implemented checks

The existing CI already covers Python 3.13, PostgreSQL/pgvector service startup,
migrations, Python compilation, backend tests, `pip-audit`, frontend dependency
audit, and frontend production build. Playwright is configured for desktop and
mobile projects with JSON browser evidence and failure traces.

The outbox worker emits structured heartbeat metrics and supports configurable
dead-letter webhook alerts through `MDARIX_OUTBOX_ALERT_WEBHOOK`.

## Manual setup sequence

1. Start Docker Desktop and verify `docker info`.
2. Start PostgreSQL and the simulator services with `docker compose up -d`.
3. Start Mailpit for local email capture, if email-flow testing is required.
4. Start MinIO for object-storage contract testing, if attachment testing is required.
5. Start the backend and frontend using the repository run commands.
6. Run Playwright desktop/mobile evidence and axe checks.
7. Run ZAP against the local API/frontend with test credentials only.
8. Run Trivy against images and `gitleaks` against the repository.
9. Run k6 only against a dedicated non-production target.
10. Configure Prometheus/Grafana and an approved error destination for operational testing.

## Important limitations

Tool installation does not prove production readiness. Real SMTP/provider
delivery, object storage, customer connector health, multi-instance behavior,
hosted CI execution, and production monitoring require their corresponding
external credentials and deployment environments.
