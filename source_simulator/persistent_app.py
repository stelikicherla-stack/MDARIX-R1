"""Production-like provider API simulator, isolated from MDARIX storage."""
import hashlib
import os
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field
from source_simulator.persistent_store import history, list_records, upsert
from source_simulator.provider_catalog import PROVIDER_PORTS, schema_for

PROVIDER = os.getenv("SIMULATOR_PROVIDER", "TRACKWISE").upper()
TOKEN_MAP = {token: tenant for tenant, token in (item.strip().split("=", 1) for item in os.getenv("SIMULATOR_TENANT_TOKENS", "TENANT_A=sim-a,TENANT_B=sim-b,TENANT_C=sim-c,TENANT_D=sim-d").split(",") if "=" in item)}
TENANTS = {"TENANT_A", "TENANT_B", "TENANT_C", "TENANT_D"}

app = FastAPI(title=f"{PROVIDER} External Provider Simulator", version="1.0")

def tenant_from_token(token: str | None, requested: str | None) -> str:
    if not token or token not in TOKEN_MAP:
        raise HTTPException(401, detail="PROVIDER_AUTHENTICATION_REQUIRED")
    tenant = TOKEN_MAP[token]
    if requested and requested.upper() != tenant:
        raise HTTPException(403, detail="TENANT_SCOPE_DENIED")
    if tenant not in TENANTS:
        raise HTTPException(403, detail="TENANT_SCOPE_DENIED")
    return tenant

class RecordRequest(BaseModel):
    external_id: str = Field(min_length=1, max_length=255)
    record_version: str = Field(default="1", min_length=1, max_length=80)
    payload: dict

@app.get("/health")
def health():
    return {"status": "ok", "provider": PROVIDER, "database": "isolated", "port": PROVIDER_PORTS.get(PROVIDER)}

@app.get("/ready")
def ready():
    return {"status": "ready", "provider": PROVIDER, "database": "isolated"}

@app.get("/schema/{entity}")
def schema(entity: str, x_provider_token: str | None = Header(None), tenant: str | None = Query(None)):
    tenant_key = tenant_from_token(x_provider_token, tenant)
    fields = schema_for(PROVIDER, entity)
    return {"provider": PROVIDER, "tenant_key": tenant_key, "entity": entity, "schema_version": "v1", "fields": fields, "field_count": len(fields)}

@app.get("/records/{entity}")
def records(entity: str, x_provider_token: str | None = Header(None), tenant: str | None = Query(None)):
    tenant_key = tenant_from_token(x_provider_token, tenant)
    return {"provider": PROVIDER, "tenant_key": tenant_key, "entity": entity, "records": list_records(PROVIDER, tenant_key, entity)}

@app.get("/records/{entity}/{external_id}/history")
def record_history(entity: str, external_id: str, x_provider_token: str | None = Header(None), tenant: str | None = Query(None)):
    tenant_key = tenant_from_token(x_provider_token, tenant)
    return {"provider": PROVIDER, "tenant_key": tenant_key, "entity": entity, "external_id": external_id, "history": history(PROVIDER, tenant_key, entity, external_id)}

@app.post("/records/{entity}")
def write_record(entity: str, payload: RecordRequest, x_provider_token: str | None = Header(None), tenant: str | None = Query(None)):
    tenant_key = tenant_from_token(x_provider_token, tenant)
    return {"provider": PROVIDER, "tenant_key": tenant_key, "entity": entity, "record": upsert(PROVIDER, tenant_key, entity, payload.external_id, payload.record_version, payload.payload)}
