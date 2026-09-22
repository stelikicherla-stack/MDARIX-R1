from datetime import datetime, timedelta, timezone
from backend.app.db.models.stage2 import OutboxEvent
from backend.app.db.session import SessionLocal

class OutboxWorker:
    def __init__(self, publisher, max_attempts=5): self.publisher=publisher; self.max_attempts=max_attempts
    def process_once(self, limit=50):
        db=SessionLocal(); now=datetime.now(timezone.utc); stats={'published':0,'failed':0,'dead_lettered':0}
        try:
            rows=db.query(OutboxEvent).filter(OutboxEvent.published_at.is_(None), OutboxEvent.dead_lettered_at.is_(None), (OutboxEvent.next_attempt_at.is_(None) | (OutboxEvent.next_attempt_at <= now))).order_by(OutboxEvent.occurred_at).limit(limit).with_for_update(skip_locked=True).all()
            for row in rows:
                try:
                    self.publisher(row.event_name, row.payload); row.published_at=now; stats['published']+=1
                except Exception as exc:
                    row.attempts += 1; row.last_error='delivery failed'; stats['failed']+=1
                    if row.attempts >= self.max_attempts: row.dead_lettered_at=now; stats['dead_lettered']+=1
                    else: row.next_attempt_at=now + timedelta(seconds=min(300, 2 ** row.attempts))
            db.commit(); return stats
        finally: db.close()
