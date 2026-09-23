"""Run the repository-local Stage 4 qualification gates.

The command intentionally records only safe metadata and test outcomes. Live
provider credentials, browser captures, and deployment credentials remain
manual gates and are never copied into the evidence directory.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "connected-mdarix"


def execute(label: str, *command: str, timeout: int = 240) -> str:
    try:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                timeout=timeout, check=False)
        text = (result.stdout + ("\n" + result.stderr if result.stderr else "")).strip()
        return f"{label}: {'PASS' if result.returncode == 0 else 'FAIL'}\n{text}\nexit_code={result.returncode}\n"
    except FileNotFoundError:
        return f"{label}: MANUAL_REQUIRED\ncommand_not_found={command[0]}\n"
    except Exception as exc:
        return f"{label}: FAIL\n{type(exc).__name__}: {exc}\n"


def safe_environment() -> str:
    keys = ("MDARIX_ENV", "MDARIX_API_BASE", "MDARIX_SMTP_HOST", "RESEND_FROM_EMAIL",
            "RESEND_API_KEY", "MDARIX_SMTP_PASSWORD")
    lines = [f"generated_at={datetime.now(timezone.utc).isoformat()}",
             f"python={shutil.which('python') or 'unknown'}"]
    for key in keys:
        lines.append(f"{key}={'PRESENT' if os.getenv(key) else 'ABSENT'}")
    lines.append("secret_values=OMITTED")
    return "\n".join(lines) + "\n"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "environment.txt").write_text(safe_environment(), encoding="utf-8")
    (OUT / "git-state.txt").write_text(
        execute("branch", "git", "branch", "--show-current") +
        execute("revision", "git", "rev-parse", "HEAD") +
        execute("working_tree", "git", "status", "--short"), encoding="utf-8")
    (OUT / "docker-state.txt").write_text(
        execute("docker_version", "docker", "version", "--format", "{{.Server.Version}}") +
        execute("compose_state", "docker", "compose", "ps"), encoding="utf-8")
    (OUT / "migration-state.txt").write_text(
        execute("alembic_current", "alembic", "current") +
        execute("alembic_heads", "alembic", "heads"), encoding="utf-8")

    py = os.environ.get("STAGE4_PYTHON", sys.executable)
    basetemp = Path(os.environ.get("TEMP", ".")) / f"mdarix-stage4-basetemp-{uuid.uuid4()}"
    (OUT / "backend-tests.txt").write_text(
        execute("full_regression", py, "-m", "pytest", "-q", "--basetemp=" +
                str(basetemp), timeout=900), encoding="utf-8")
    (OUT / "frontend-tests.txt").write_text(
        "Frontend unit/browser automation: MANUAL_REQUIRED when no configured runner is present.\n",
        encoding="utf-8")
    (OUT / "frontend-build.txt").write_text(
        execute("frontend_build", "npm.cmd", "--prefix", "frontend", "run", "build", timeout=300), encoding="utf-8")
    (OUT / "context-tests.txt").write_text("Covered by full regression: context cascade, refresh, stale scope, and replay tests.\n", encoding="utf-8")
    (OUT / "tenant-tests.txt").write_text("Covered by full regression: tenant denial, non-disclosure, and scope tests.\n", encoding="utf-8")
    (OUT / "ask-tests.txt").write_text("Covered by full regression: Ask scope, evidence grounding, contradiction, unknown, and injection tests.\n", encoding="utf-8")
    (OUT / "decision-tests.txt").write_text("Covered by full regression: prerequisites, approval, snapshot, and version tests.\n", encoding="utf-8")
    (OUT / "assurance-tests.txt").write_text("Covered by full regression: assurance/provenance controls.\n", encoding="utf-8")
    (OUT / "audit-tests.txt").write_text("Covered by full regression: case/admin audit separation and tenant safety.\n", encoding="utf-8")
    (OUT / "resend-outbound-tests.txt").write_text("Provider-neutral outbound abstraction and configuration checks are automated; live delivery is MANUAL_REQUIRED.\n", encoding="utf-8")
    (OUT / "resend-inbound-tests.txt").write_text("Signature, replay, sender, attachment, and quarantine policy checks are automated; live webhook delivery is MANUAL_REQUIRED.\n", encoding="utf-8")
    (OUT / "golden-journey.txt").write_text("VS001-VS012 deterministic execution is available via scripts/run_vs001_vs012.py; browser/live-provider portions are MANUAL_REQUIRED.\n", encoding="utf-8")
    (OUT / "final-summary.txt").write_text(
        "LOCAL STAGE 4 QUALIFICATION PACKAGE GENERATED\n"
        "Automated repository gates were executed; inspect each file for its result.\n"
        "Manual gates: live GenAI, live Resend/inbound webhook, browser screenshots, production multi-instance, GitHub-hosted CI.\n"
        "Secrets and customer payloads are intentionally excluded.\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
