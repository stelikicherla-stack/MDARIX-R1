from datetime import datetime, timezone
from outbox.worker import OutboxWorker

def test_outbox_worker_publishes(monkeypatch):
    from backend.app.db.session import SessionLocal
    from backend.app.db.models.stage2 import OutboxEvent
    from uuid import uuid4
    db=SessionLocal(); tenant=db.execute(__import__('sqlalchemy').text("select id from tenants limit 1")).scalar_one()
    row=OutboxEvent(tenant_id=tenant,event_name='TEST',aggregate_type='Test',payload={'ok':True},occurred_at=datetime.now(timezone.utc))
    db.add(row); db.commit(); db.close()
    seen=[]; result=OutboxWorker(lambda name,payload: seen.append((name,payload))).process_once()
    assert result['published'] >= 1 and ('TEST',{'ok':True}) in seen

def test_outbox_worker_dead_letters_after_retries(monkeypatch):
    from backend.app.db.session import SessionLocal
    from backend.app.db.models.stage2 import OutboxEvent
    db=SessionLocal(); tenant=db.execute(__import__('sqlalchemy').text("select id from tenants limit 1")).scalar_one()
    row=OutboxEvent(tenant_id=tenant,event_name='FAIL',aggregate_type='Test',payload={},occurred_at=datetime.now(timezone.utc),attempts=4)
    db.add(row); db.commit(); db.close()
    result=OutboxWorker(lambda *_: (_ for _ in ()).throw(RuntimeError('failure')), max_attempts=5).process_once()
    assert result['dead_lettered'] >= 1
