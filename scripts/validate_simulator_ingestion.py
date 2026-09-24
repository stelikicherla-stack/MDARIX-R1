"""Validate provider read -> tenant-scoped outbox enqueue and idempotency."""
import os
from uuid import UUID
from integration.simulator_ingestion import read_provider, enqueue_provider_records
from backend.app.db.session import SessionLocal

def main():
    provider = os.getenv("SIMULATOR_PROVIDER", "TRACKWISE").upper()
    entity = os.getenv("SIMULATOR_ENTITY", "Complaint")
    tenant_key = os.getenv("SIMULATOR_TENANT_KEY", "TENANT_A")
    token = os.getenv("SIMULATOR_PROVIDER_TOKEN", "sim-a")
    tenant_id = os.getenv("MDARIX_TENANT_ID")
    if not tenant_id:
        raise SystemExit("Set MDARIX_TENANT_ID to enqueue into the MDARIX database")
    records = read_provider(provider, tenant_key, token, entity)
    db = SessionLocal()
    try:
        first = enqueue_provider_records(db, UUID(tenant_id), provider, tenant_key, entity, records)
        db.commit()
        second = enqueue_provider_records(db, UUID(tenant_id), provider, tenant_key, entity, records)
        db.commit()
    finally:
        db.close()
    print(f"PROVIDER_READ={len(records)} OUTBOX_CREATED={first} REPLAY_DUPLICATES={len(records)-second}")

if __name__ == "__main__":
    main()
