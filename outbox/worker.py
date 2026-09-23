from datetime import datetime, timedelta, timezone
import logging
from backend.app.db.models.stage2 import OutboxEvent
from backend.app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class OutboxWorker:
    def __init__(self, publisher, max_attempts=5, base_delay_seconds=2):
        if max_attempts < 1: raise ValueError("max_attempts must be positive")
        self.publisher = publisher; self.max_attempts = max_attempts; self.base_delay_seconds = base_delay_seconds
    def process_once(self, limit=50):
        db=SessionLocal(); now=datetime.now(timezone.utc); stats={'published':0,'failed':0,'dead_lettered':0}
        try:
            rows=db.query(OutboxEvent).filter(OutboxEvent.published_at.is_(None), OutboxEvent.dead_lettered_at.is_(None), (OutboxEvent.next_attempt_at.is_(None) | (OutboxEvent.next_attempt_at <= now))).order_by(OutboxEvent.occurred_at).limit(limit).with_for_update(skip_locked=True).all()
            for row in rows:
                try:
                    self.publisher(row.event_name, row.payload)
                    row.published_at = now; row.next_attempt_at = None; row.last_error = None; stats['published'] += 1
                except Exception as exc:
                    row.attempts += 1; row.last_error = f"{type(exc).__name__}: delivery failed"; stats['failed'] += 1
                    logger.warning("outbox delivery failed event=%s attempt=%s", row.id, row.attempts)
                    if row.attempts >= self.max_attempts:
                        row.dead_lettered_at = now; row.next_attempt_at = None; stats['dead_lettered'] += 1
                    else:
                        row.next_attempt_at = now + timedelta(seconds=min(300, self.base_delay_seconds ** row.attempts))
            db.commit(); return stats
        finally: db.close()
