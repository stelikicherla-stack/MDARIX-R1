from datetime import datetime, timedelta, timezone
import logging
import time
from dataclasses import dataclass, asdict
from backend.app.db.models.stage2 import OutboxEvent
from backend.app.db.session import SessionLocal

logger = logging.getLogger(__name__)

@dataclass
class WorkerMetrics:
    cycles: int = 0
    published: int = 0
    failed: int = 0
    dead_lettered: int = 0
    last_cycle_at: str | None = None
    last_error: str | None = None

    def snapshot(self):
        return asdict(self)

class OutboxWorker:
    def __init__(self, publisher, max_attempts=5, base_delay_seconds=2, alert=None):
        if max_attempts < 1: raise ValueError("max_attempts must be positive")
        self.publisher = publisher; self.max_attempts = max_attempts; self.base_delay_seconds = base_delay_seconds
        self.alert = alert; self.metrics = WorkerMetrics()
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
                    self.metrics.last_error = row.last_error
                    logger.warning("outbox delivery failed event=%s attempt=%s", row.id, row.attempts)
                    if row.attempts >= self.max_attempts:
                        row.dead_lettered_at = now; row.next_attempt_at = None; stats['dead_lettered'] += 1
                        logger.error("outbox dead-letter alert event=%s attempts=%s", row.id, row.attempts)
                        if self.alert is not None:
                            try:
                                self.alert({"type": "OUTBOX_DEAD_LETTERED", "event_id": str(row.id), "event_name": row.event_name, "attempts": row.attempts, "error": row.last_error})
                            except Exception as alert_exc:
                                self.metrics.last_error = f"{type(alert_exc).__name__}: alert delivery failed"
                                logger.exception("outbox alert delivery failed event=%s", row.id)
                    else:
                        row.next_attempt_at = now + timedelta(seconds=min(300, self.base_delay_seconds ** row.attempts))
            db.commit()
            self.metrics.cycles += 1; self.metrics.published += stats['published']; self.metrics.failed += stats['failed']; self.metrics.dead_lettered += stats['dead_lettered']; self.metrics.last_cycle_at = now.isoformat()
            return stats
        finally: db.close()

    def run_forever(self, *, limit=50, interval_seconds=5, stop=None):
        """Continuously drain the outbox until a shutdown signal is received."""
        stopped = stop or (lambda: False)
        logger.info("outbox worker started batch_size=%s interval_seconds=%s", limit, interval_seconds)
        while not stopped():
            started = time.monotonic()
            stats = self.process_once(limit=limit)
            logger.info("outbox metrics=%s cycle_published=%s cycle_failed=%s cycle_dead_lettered=%s duration_ms=%s", self.metrics.snapshot(), stats['published'], stats['failed'], stats['dead_lettered'], int((time.monotonic() - started) * 1000))
            if stopped(): break
            time.sleep(max(0, interval_seconds))
        logger.info("outbox worker stopped gracefully")

    @staticmethod
    def replay(db, event_id):
        """Make one dead-lettered event eligible for a controlled replay."""
        row = db.query(OutboxEvent).filter(OutboxEvent.id == event_id).with_for_update().one_or_none()
        if row is None: raise ValueError("OUTBOX_EVENT_NOT_FOUND")
        row.dead_lettered_at = None; row.next_attempt_at = datetime.now(timezone.utc); row.last_error = None
        db.commit(); logger.warning("outbox replay requested event=%s", event_id)
        return row
