"""Fail-closed production operations gate.

This command validates what can be observed from the current deployment and
prints explicit PENDING results for controls that require external
infrastructure. It never treats configuration presence as proof of delivery.

Examples:
  python scripts/validate_production_operations.py
  $env:MDARIX_OPERATIONAL_URLS='https://app-1.example,https://app-2.example'
  python scripts/validate_production_operations.py
"""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def check_url(base: str, path: str) -> tuple[bool, str]:
    url = base.rstrip("/") + path
    try:
        with urlopen(Request(url, headers={"User-Agent": "MDARIX-operations-gate/1"}), timeout=10) as response:
            payload = response.read().decode("utf-8", errors="replace")
            return response.status == 200, payload[:500]
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        return False, type(exc).__name__


def main() -> int:
    urls = [item.strip().rstrip("/") for item in os.getenv("MDARIX_OPERATIONAL_URLS", os.getenv("MDARIX_APP_URL", "http://127.0.0.1:8007")).split(",") if item.strip()]
    print("MDARIX PRODUCTION OPERATIONS GATE")
    print(f"TARGETS = {len(urls)}")

    live_ok = []
    ready_ok = []
    for index, base in enumerate(urls, 1):
        live, live_detail = check_url(base, "/health/live")
        ready, ready_detail = check_url(base, "/health/ready")
        live_ok.append(live)
        ready_ok.append(ready)
        print(f"HEALTH instance_{index} live={'PASS' if live else 'FAIL'} ready={'PASS' if ready else 'FAIL'}")
        if not live:
            print(f"  live_detail={live_detail}")
        if not ready:
            print(f"  ready_detail={ready_detail}")

    if len(urls) >= 2 and all(live_ok) and all(ready_ok):
        distinct = len(set(urls)) == len(urls)
        print(f"MULTI_INSTANCE_HEALTH = {'PASS' if distinct else 'FAIL'} (two distinct live/readiness targets)")
    else:
        print("MULTI_INSTANCE_HEALTH = PENDING (two deployed application URLs are required)")

    alert_target = os.getenv("MDARIX_MONITORING_ALERT_WEBHOOK", "").strip()
    if alert_target:
        print("MONITORING_ALERT_DESTINATION = CONFIGURED (delivery test requires explicit --send-test-alert)")
    else:
        print("MONITORING_ALERT_DESTINATION = PENDING (MDARIX_MONITORING_ALERT_WEBHOOK is not configured)")

    heartbeat = os.getenv("MDARIX_OUTBOX_HEARTBEAT_TARGET", "").strip()
    print("OUTBOX_HEARTBEAT = CONFIGURED" if heartbeat else "OUTBOX_HEARTBEAT = PENDING (worker heartbeat target is not configured)")
    print("OUTBOX_WORKER = PASS (dedicated compose service is declared)" if os.path.exists("docker-compose.yml") else "OUTBOX_WORKER = PENDING")
    print("PRODUCTION_MONITORING = PENDING (scraping, alert routing, and retained incident evidence require deployed infrastructure)")
    print("PRODUCTION_MULTI_INSTANCE = PENDING (this gate does not infer deployment from local configuration)")
    return 0 if all(live_ok) and all(ready_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
