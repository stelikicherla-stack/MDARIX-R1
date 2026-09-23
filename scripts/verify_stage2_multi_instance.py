"""Verify two app instances accept the same durable database-backed session."""
import os, subprocess, sys, time
import httpx

ROOT = os.path.dirname(os.path.dirname(__file__))
ports = (8021, 8022)
processes = [subprocess.Popen([sys.executable, "-m", "uvicorn", "backend.app.main:app", "--host", "127.0.0.1", "--port", str(port)], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for port in ports]
try:
    for _ in range(30):
        try:
            if all(httpx.get(f"http://127.0.0.1:{p}/health").json().get("status") == "ok" for p in ports): break
        except Exception: pass
        time.sleep(.5)
    else: raise SystemExit("FAIL: both instances did not become healthy")
    with httpx.Client(base_url=f"http://127.0.0.1:{ports[0]}") as first:
        signed = first.post("/api/v1/auth/signin", json={"email":"r1-user-01@synthetic.invalid", "password":os.getenv("DAY35_FIXTURE_PASSWORD", "Temp@1234password")})
        signed.raise_for_status(); cookie = first.cookies.get("mdarix_session")
    if not cookie: raise SystemExit("FAIL: signin did not return a durable session cookie")
    with httpx.Client(base_url=f"http://127.0.0.1:{ports[1]}", cookies={"mdarix_session": cookie}) as second:
        session = second.get("/api/v1/auth/session"); session.raise_for_status(); body = session.json()
    if not body.get("user_id") or not body.get("tenant_id"): raise SystemExit("FAIL: second instance rejected durable session")
    print(f"PASS | multi-instance session | user={body['user_id']} tenant={body['tenant_id']}")
finally:
    for process in processes: process.terminate()
    for process in processes: process.wait(timeout=10)
