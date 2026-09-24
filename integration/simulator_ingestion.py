"""Tenant-safe reads from provider simulators into the MDARIX outbox.

The module deliberately separates provider transport from MDARIX persistence:
provider records are never inserted directly into business tables. Each read is
represented by an idempotent outbox event for the normal ingestion pipeline.
"""
import hashlib
import json
from urllib.request import Request, urlopen
from uuid import UUID
from sqlalchemy.orm import Session
from backend.app.db.models.stage2 import OutboxEvent
from source_simulator.provider_catalog import PROVIDER_PORTS

def read_provider(provider: str, tenant_key: str, token: str, entity: str, host: str = "127.0.0.1") -> list[dict]:
    provider = provider.upper()
    url = f"http://{host}:{PROVIDER_PORTS[provider]}/records/{entity}?tenant={tenant_key}"
    request = Request(url, headers={"X-Provider-Token": token, "Accept": "application/json"})
    with urlopen(request, timeout=10) as response:
        body = json.loads(response.read().decode())
    if body.get("tenant_key") != tenant_key:
        raise ValueError("provider returned an unexpected tenant scope")
    return body.get("records", [])

def enqueue_provider_records(db: Session, tenant_id: UUID, provider: str, tenant_key: str, entity: str, records: list[dict]) -> int:
    created = 0
    for record in records:
        external_id = str(record.get("external_id", ""))
        fingerprint = hashlib.sha256(json.dumps(record, sort_keys=True).encode()).hexdigest()
        event_name = "PROVIDER_RECORD_RECEIVED"
        duplicate = db.query(OutboxEvent).filter(OutboxEvent.tenant_id == tenant_id, OutboxEvent.event_name == event_name, OutboxEvent.aggregate_type == f"{provider}:{entity}", OutboxEvent.payload["external_id"].as_string() == external_id, OutboxEvent.payload["fingerprint"].as_string() == fingerprint).first()
        if duplicate:
            continue
        db.add(OutboxEvent(tenant_id=tenant_id, event_name=event_name, aggregate_type=f"{provider}:{entity}", payload={"tenant_key": tenant_key, "provider": provider, "entity": entity, "external_id": external_id, "fingerprint": fingerprint, "record": record}, occurred_at=__import__('datetime').datetime.now(__import__('datetime').timezone.utc)))
        created += 1
    return created
