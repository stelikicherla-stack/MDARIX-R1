from datetime import datetime, timezone
import threading
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

def test_outbox_worker_schedules_retry_and_preserves_error(monkeypatch):
    from backend.app.db.session import SessionLocal
    from backend.app.db.models.stage2 import OutboxEvent
    db=SessionLocal(); tenant=db.execute(__import__('sqlalchemy').text("select id from tenants limit 1")).scalar_one()
    row=OutboxEvent(tenant_id=tenant,event_name='RETRY',aggregate_type='Test',payload={},occurred_at=datetime.now(timezone.utc))
    db.add(row); db.commit(); row_id=row.id; db.close()
    result=OutboxWorker(lambda *_: (_ for _ in ()).throw(ValueError('failure')), max_attempts=3).process_once()
    assert result['failed'] >= 1 and result['dead_lettered'] == 0
    db=SessionLocal(); saved=db.query(OutboxEvent).filter(OutboxEvent.id == row_id).one()
    assert saved.attempts == 1 and saved.next_attempt_at is not None and 'ValueError' in saved.last_error
    db.delete(saved); db.commit(); db.close()

def test_concurrent_workers_do_not_publish_same_event(monkeypatch):
    from backend.app.db.session import SessionLocal
    from backend.app.db.models.stage2 import OutboxEvent
    from sqlalchemy import text
    db = SessionLocal(); tenant = db.execute(text("select id from tenants limit 1")).scalar_one()
    row = OutboxEvent(tenant_id=tenant, event_name='LOCKED', aggregate_type='Test', payload={}, occurred_at=datetime.now(timezone.utc))
    db.add(row); db.commit(); row_id = row.id; db.close()
    entered = threading.Event(); release = threading.Event(); seen = []
    def blocking_publisher(name, payload):
        seen.append(name); entered.set(); release.wait(timeout=5)
    first_result = []
    first = threading.Thread(target=lambda: first_result.append(OutboxWorker(blocking_publisher).process_once()))
    first.start(); assert entered.wait(timeout=5)
    second_result = OutboxWorker(lambda name, payload: seen.append(f"duplicate:{name}")).process_once()
    release.set(); first.join(timeout=5)
    assert second_result["published"] == 0
    assert seen == ["LOCKED"]
    db = SessionLocal(); saved = db.query(OutboxEvent).filter(OutboxEvent.id == row_id).one(); db.delete(saved); db.commit(); db.close()

def test_outbox_replay_requeues_dead_letter(monkeypatch):
    from backend.app.db.session import SessionLocal
    from backend.app.db.models.stage2 import OutboxEvent
    from sqlalchemy import text
    db = SessionLocal(); tenant = db.execute(text("select id from tenants limit 1")).scalar_one()
    row = OutboxEvent(tenant_id=tenant, event_name='REPLAY', aggregate_type='Test', payload={},
                      occurred_at=datetime.now(timezone.utc), attempts=5,
                      dead_lettered_at=datetime.now(timezone.utc), last_error='delivery failed')
    db.add(row); db.commit(); row_id = row.id
    replayed = OutboxWorker.replay(db, row_id)
    assert replayed.dead_lettered_at is None
    assert replayed.next_attempt_at is not None
    assert replayed.last_error is None
    db.delete(replayed); db.commit(); db.close()

def test_outbox_worker_stops_gracefully_after_requested_stop():
    worker = OutboxWorker(lambda *_: None)
    calls = []
    def process_once(limit=50):
        calls.append(limit)
        return {'published': 0, 'failed': 0, 'dead_lettered': 0}
    worker.process_once = process_once
    worker.run_forever(limit=7, interval_seconds=0, stop=lambda: len(calls) >= 1)
    assert calls == [7]
