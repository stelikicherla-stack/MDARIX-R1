"""Create a secret-free Stage 4 qualification evidence package."""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "future-architecture"


def run(*args: str) -> str:
    try:
        return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=30, check=False).stdout.strip()
    except Exception as exc:
        return f"UNAVAILABLE: {type(exc).__name__}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    safe_env = {key: "PRESENT" for key in ("MDARIX_ENV", "RESEND_API_KEY", "RESEND_FROM_EMAIL", "MDARIX_SMTP_HOST") if os.getenv(key)}
    (OUT / "environment.txt").write_text("Python is controlled by the invoking test command.\n" + "\n".join(f"{k}={v}" for k, v in safe_env.items()) + "\nSecrets intentionally omitted.\n", encoding="utf-8")
    (OUT / "git-state.txt").write_text(run("git", "branch", "--show-current") + "\n" + run("git", "rev-parse", "HEAD") + "\n" + run("git", "status", "--short") + "\n", encoding="utf-8")
    (OUT / "docker-state.txt").write_text(run("docker", "context", "show") + "\n" + run("docker", "compose", "ps") + "\n", encoding="utf-8")
    (OUT / "migration-state.txt").write_text("Run alembic current, heads, and history with the controlled environment.\nSecrets omitted.\n", encoding="utf-8")
    for name, status in {
        "auth-tests.txt": "Run authenticated-route, durable-session, invitation, reset, cookie, and replay tests.",
        "tenant-tests.txt": "Run cross-tenant denial and non-disclosure tests.",
        "context-tests.txt": "Run Case Context cascade, version, temporal, refresh, and stale-version tests.",
        "frontend-build.txt": "Run npm.cmd --prefix frontend run build.",
        "frontend-tests.txt": "Frontend test command is prepared; browser/RTL evidence requires configured frontend test fixtures.",
        "backend-tests.txt": "Run .venv\\Scripts\\python.exe -m pytest -q.",
        "AI-safety-tests.txt": "Run causality restraint, prompt-injection, foreign-scope, unknown, contradiction, and dependency tests.",
        "mapping-tests.txt": "Run master/tenant mapping version and protected-field tests.",
        "admin-tests.txt": "Run platform/customer-admin, entitlement, SoD, SMTP-status, and audit tests.",
        "golden-journey.txt": "VS001-VS012 remain deferred by product decision; final R1 qualification is required.",
        "final-test-summary.txt": "Evidence package generated without secrets. See Stage 4 report for PASS/BLOCKED gates.",
    }.items():
        (OUT / name).write_text(status + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
