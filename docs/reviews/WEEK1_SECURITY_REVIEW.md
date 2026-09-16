# Week 1 Security Review

Scope: Day 0-Day 7 local-development foundation.

Checks:

- `.env`, `.venv`, SQL backups, build output, and `node_modules` are ignored.
- GitHub repository visibility verified as private before review.
- No token patterns found in staged review changes.
- Runtime code does not read evaluation Ground Truth.
- No arbitrary graph query endpoint exists.
- No production IAM was introduced.

Result: PASS.
