# MDARIX R1 Part 3 — Migration and Browser Evidence

## PostgreSQL migration

- Database: `mdarix_r1`
- Host/port: `127.0.0.1:5433`
- Migration command: `python -m alembic upgrade head`
- Result: **PASS**
- Applied revision: `y41subscriptionlifecycle (head)`
- Migration: `x40mappingimpact -> y41subscriptionlifecycle`
- Verified tables:
  - `subscription_lifecycles`
  - `subscription_reminder_policies`
  - `subscription_email_templates`

The migration completed transactionally against the running PostgreSQL container.

## Browser-based evidence

Browser evidence remains a manual/operational gate because no browser-control session
was connected during this run. Capture these screenshots in a running browser:

1. `/app/admin/subscriptions` showing the subscription summary and expiry status.
2. Reminder policy creation/edit form showing thresholds, timezone, recipients and version.
3. Email template creation/edit form showing stage, subject, allowed variables and status.
4. Lifecycle run result showing queued reminder/outbox evidence.
5. Platform admin access denial when a non-platform user opens the subscription page.

For each screenshot record the URL, authenticated persona, tenant, timestamp and
correlation ID. Do not include passwords, tokens or SMTP secrets in screenshots.
