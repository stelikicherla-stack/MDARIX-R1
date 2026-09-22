"""Run one transactional-outbox delivery pass; suitable for a scheduler/container."""
import os
from outbox.worker import OutboxWorker

def publish(event_name, payload):
    # Production deployments replace this adapter with the configured broker.
    if os.getenv('MDARIX_OUTBOX_PUBLISHER', 'noop') == 'noop':
        return
    raise RuntimeError('OUTBOX_PUBLISHER_NOT_IMPLEMENTED')

if __name__ == '__main__':
    print(OutboxWorker(publish).process_once())
