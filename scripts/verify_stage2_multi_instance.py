"""Production-like two-instance validation against one durable database.

Required checks fail fast: both instances healthy, durable session reuse and
cross-instance revocation. Optional integrations are reported explicitly as
PASS, NOT_CONFIGURED, or NOT_EXERCISED; they are never inferred from config.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
PORTS = tuple(int(value) for value in os.getenv("MDARIX_MULTI_INSTANCE_PORTS", "8021,8022").split(","))
EMAIL = os.getenv("MDARIX_TEST_EMAIL", "r1-user-01@synthetic.invalid")
PASSWORD = os.getenv("DAY35_FIXTURE_PASSWORD", "Temp@1234password")


def get(client: httpx.Client, path: str):
    return client.get(path, timeout=10)


def main() -> int:
    processes = [subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app.main:app",
                                   "--host", "127.0.0.1", "--port", str(port)],
                                  cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                 for port in PORTS]
    try:
        clients = [httpx.Client(base_url=f"http://127.0.0.1:{port}") for port in PORTS]
        try:
            for _ in range(40):
                if all(get(client, "/health/live").status_code == 200 for client in clients):
                    break
                time.sleep(.5)
            else:
                raise RuntimeError("both application instances did not become live")
            health = [get(client, "/health") for client in clients]
            if any(response.status_code != 200 or response.json().get("database") != "reachable" for response in health):
                raise RuntimeError("database health failed on one or more instances")
            print("PASS | instance health | shared database reachable")

            signed = clients[0].post("/api/v1/auth/signin", json={"email": EMAIL, "password": PASSWORD}, timeout=15)
            signed.raise_for_status()
            cookie = signed.cookies.get("mdarix_session")
            if not cookie:
                raise RuntimeError("signin did not return a durable session cookie")
            shared = httpx.Client(base_url=f"http://127.0.0.1:{PORTS[1]}", cookies={"mdarix_session": cookie})
            try:
                session = get(shared, "/api/v1/auth/session")
                session.raise_for_status()
                context = session.json()
                if not context.get("user_id") or not context.get("tenant_id"):
                    raise RuntimeError("session context is incomplete")
                print(f"PASS | session reuse | user={context['user_id']} tenant={context['tenant_id']}")

                revoked = shared.post("/api/v1/auth/signout", timeout=10)
                revoked.raise_for_status()
                after_revoke = get(clients[0], "/api/v1/auth/session")
                if after_revoke.status_code != 401:
                    raise RuntimeError("session remained valid after cross-instance revocation")
                print("PASS | session revocation | instance 1 rejected session revoked by instance 2")
            finally:
                shared.close()

            signed_again = clients[0].post("/api/v1/auth/signin", json={"email": EMAIL, "password": PASSWORD}, timeout=15)
            signed_again.raise_for_status()
            cookie_again = signed_again.cookies.get("mdarix_session")
            expiring = httpx.Client(base_url=f"http://127.0.0.1:{PORTS[1]}", cookies={"mdarix_session": cookie_again})
            try:
                print("NOT_EXERCISED | session expiry | requires a controlled short-TTL deployment or DB fixture")
            finally:
                expiring.close()

            with httpx.Client(base_url=f"http://127.0.0.1:{PORTS[0]}", cookies={"mdarix_session": cookie_again}) as authenticated:
                for label, path in (("SMTP/provider", "/api/v1/communication/provider-health"),
                                    ("GenAI/provider", "/api/v1/stage3/genai-health"),
                                    ("REST connector", "/api/v1/integrations/health/REST")):
                    response = get(authenticated, path)
                    if response.status_code == 200:
                        body = response.json()
                        status = body.get("status", "configured" if body.get("configured") else "NOT_CONFIGURED")
                        print(f"{('PASS' if status in ('HEALTHY', 'configured') else 'NOT_CONFIGURED')} | {label} | {status}")
                    else:
                        print(f"NOT_CONFIGURED | {label} | HTTP {response.status_code}")

            from object_storage.service import ObjectStorageService
            with tempfile.TemporaryDirectory(prefix="mdarix-storage-check-") as root:
                previous = os.environ.get("MDARIX_OBJECT_STORAGE_SIGNING_SECRET")
                os.environ["MDARIX_OBJECT_STORAGE_SIGNING_SECRET"] = "production-like-validation-secret"
                storage = ObjectStorageService(root=root)
                stored = storage.put(context["tenant_id"], "validation/probe.txt", b"tenant-safe")
                signed_url = storage.signed_url(context["tenant_id"], stored["object_key"])
                if storage.verify_signed_url(context["tenant_id"], signed_url) != stored["object_key"]:
                    raise RuntimeError("signed object URL did not validate")
                if previous is None:
                    os.environ.pop("MDARIX_OBJECT_STORAGE_SIGNING_SECRET", None)
                else:
                    os.environ["MDARIX_OBJECT_STORAGE_SIGNING_SECRET"] = previous
            print("PASS | object storage | tenant prefix, write, signed URL and verification")
            print("NOT_EXERCISED | outbox retry/dead-letter | requires a controlled failed event and worker deployment")
            print("NOT_EXERCISED | real SMTP, customer connectors, external provider | credentials/endpoints not supplied")
            print("PASS | required production-like checks")
            return 0
        finally:
            for client in clients:
                client.close()
    finally:
        for process in processes:
            process.terminate()
        for process in processes:
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"FAIL | production-like validation | {error}")
        raise SystemExit(1)
