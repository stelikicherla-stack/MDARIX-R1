"""Controlled dead-letter replay: python scripts/replay_outbox.py EVENT_UUID."""
import sys
from backend.app.db.session import SessionLocal
from outbox.worker import OutboxWorker

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: python scripts/replay_outbox.py EVENT_UUID")
    db = SessionLocal()
    try:
        row = OutboxWorker.replay(db, sys.argv[1])
        print({"status": "REPLAY_QUEUED", "event_id": str(row.id)}, flush=True)
    finally:
        db.close()
