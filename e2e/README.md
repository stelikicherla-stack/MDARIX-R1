# Stage 4 Browser E2E

Use a browser runner against the locally running frontend and API. Required flows are login, Case Context selection/cascade, tenant-denial, story flow, decision prerequisite messaging, admin separation, and responsive layout. Capture screenshots only in the target environment and never include credentials or tokens.

Manual prerequisite:

```powershell
npm.cmd --prefix frontend install
npm.cmd --prefix frontend run build
```

The repository’s API and deterministic semantic harness are covered by Python tests; browser execution remains an environment gate because no browser automation dependency or running deployment is assumed.
