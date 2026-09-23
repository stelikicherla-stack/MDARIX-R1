"""Run one transactional-outbox delivery pass; suitable for a scheduler/container."""
import os
import time
from outbox.worker import OutboxWorker

def publish(event_name, payload):
    # Production deployments replace this adapter with the configured broker.
    if os.getenv('MDARIX_OUTBOX_PUBLISHER', 'noop') == 'noop':
        return
    raise RuntimeError('OUTBOX_PUBLISHER_NOT_IMPLEMENTED')

if __name__ == '__main__':
    worker = OutboxWorker(publish, max_attempts=int(os.getenv('MDARIX_OUTBOX_MAX_ATTEMPTS', '5')))
    interval = int(os.getenv('MDARIX_OUTBOX_INTERVAL_SECONDS', '0'))
    while True:
        print(worker.process_once(limit=int(os.getenv('MDARIX_OUTBOX_BATCH_SIZE', '50'))), flush=True)
        if interval <= 0: break
        time.sleep(interval)
