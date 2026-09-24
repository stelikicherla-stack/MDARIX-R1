from uuid import uuid4
from integration.simulator_ingestion import enqueue_provider_records

def test_provider_records_are_idempotent_in_outbox():
    from backend.app.db.models.stage2 import OutboxEvent
    from backend.app.db.session import SessionLocal
    db_session = SessionLocal()
    tenant = db_session.execute(__import__('sqlalchemy').text("select id from tenants limit 1")).scalar_one()
    records = [{"external_id": f"CMP-IDEMP-{uuid4()}", "record_version": "1", "severity": "MAJOR"}]
    assert enqueue_provider_records(db_session, tenant, "TRACKWISE", "TENANT_A", "Complaint", records) == 1
    db_session.commit()
    assert enqueue_provider_records(db_session, tenant, "TRACKWISE", "TENANT_A", "Complaint", records) == 0
    assert db_session.query(OutboxEvent).filter(OutboxEvent.aggregate_type == "TRACKWISE:Complaint").count() >= 1
    db_session.close()
