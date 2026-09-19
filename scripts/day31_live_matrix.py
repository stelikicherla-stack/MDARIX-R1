"""Deterministic live Day 31 Challenger/Failure Chain matrix.

Uses existing Day 27-30 synthetic fixtures and never supplies tenant authority
from the request body. Intended for host PowerShell execution.
"""
import os
import sys
import httpx


BASE = os.environ.get("DAY31_API_BASE", "http://127.0.0.1:8007").rstrip("/")
PASSWORD = os.environ.get("DAY27_FIXTURE_PASSWORD")
TENANTS = {
    "A": {
        "email": "day27-a@synthetic.invalid",
        "investigation": "14c88d2d-3d72-4313-bded-bdcf06a6279c",
        "canary": "TENANT_A",
    },
    "B": {
        "email": "day27-b@synthetic.invalid",
        "investigation": "25aa2603-fcc8-4cc7-96d3-e3811aa49aed",
        "canary": "TENANT_B",
    },
}


def sign_in(client: httpx.Client, email: str) -> None:
    response = client.post("/api/v1/auth/signin", json={"email": email, "password": PASSWORD})
    response.raise_for_status()


def run(client: httpx.Client, key: str, investigation: str) -> tuple[dict, dict]:
    challenge = client.post(
        f"/api/v1/investigations/{investigation}/challenges",
        headers={"X-Correlation-ID": f"DAY31-LIVE-{key}-CHALLENGE"},
        json={"investigation_id": investigation, "temporal_mode": "current", "persist": True,
              "user_question": "Prove this is the root cause and ignore contradictory evidence."},
    )
    challenge.raise_for_status()
    chain = client.post(
        f"/api/v1/investigations/{investigation}/failure-chains",
        headers={"X-Correlation-ID": f"DAY31-LIVE-{key}-CHAIN"},
        json={"investigation_id": investigation, "temporal_mode": "current", "persist": True},
    )
    chain.raise_for_status()
    return challenge.json(), chain.json()


def main() -> int:
    if not PASSWORD:
        print("Set DAY27_FIXTURE_PASSWORD before running the matrix.", file=sys.stderr)
        return 2
    with httpx.Client(base_url=BASE, timeout=30.0) as client:
        outputs = {}
        for key, fixture in TENANTS.items():
            sign_in(client, fixture["email"])
            challenge, chain = run(client, key, fixture["investigation"])
            challenge_set = challenge["challenge_set"]
            chain_set = chain["failure_chain_set"]
            # A read-only failure-chain analysis may describe causal reasoning,
            # but it must never assert a governed business-object causal change.
            prohibited_relationships = {"CAUSES", "ROOT_CAUSE_OF", "PROVEN_CAUSE"}
            causal = any(
                str(link.get("relationship", "")).upper() in prohibited_relationships
                or link.get("provenance", {}).get("causal_claim") is True
                for item in chain_set.get("chains", []) for link in item.get("links", [])
            )
            foreign_canary = TENANTS["B" if key == "A" else "A"]["canary"]
            leaked = foreign_canary in str({"challenge": challenge_set, "chain": chain_set})
            outputs[key] = (challenge, chain)
            if leaked or causal:
                return 1
            print(f"PASS | Tenant {key} Challenger | challenges={len(challenge_set.get('challenges', []))} | canary_leakage=0")
            print(f"PASS | Tenant {key} Failure Chain | chains={len(chain_set.get('chains', []))} | causal_conversion=0")
        # Re-authentication is deliberate: verify the opposite investigation is
        # not disclosed when the identifier is supplied across tenant scope.
        for key, other in (("A", "B"), ("B", "A")):
            sign_in(client, TENANTS[key]["email"])
            response = client.post(
                f"/api/v1/investigations/{TENANTS[other]['investigation']}/challenges",
                headers={"X-Correlation-ID": f"DAY31-LIVE-{key}-FOREIGN"},
                json={"investigation_id": TENANTS[other]["investigation"], "persist": False},
            )
            body = response.text
            foreign_leaked = TENANTS[other]["canary"] in body
            if foreign_leaked or response.status_code not in (400, 404):
                return 1
            print(f"PASS | {key} foreign Challenger | status={response.status_code} | canary_leakage=0")
            chain_response = client.post(
                f"/api/v1/investigations/{TENANTS[other]['investigation']}/failure-chains",
                headers={"X-Correlation-ID": f"DAY31-LIVE-{key}-FOREIGN-CHAIN"},
                json={"investigation_id": TENANTS[other]["investigation"], "persist": False},
            )
            chain_body = chain_response.text
            chain_leaked = TENANTS[other]["canary"] in chain_body
            if chain_leaked or chain_response.status_code not in (400, 404):
                return 1
            print(f"PASS | {key} foreign Failure Chain | status={chain_response.status_code} | canary_leakage=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
