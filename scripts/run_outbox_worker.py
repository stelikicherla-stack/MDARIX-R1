"""Run the continuously operating transactional-outbox worker."""
import os
import logging
import signal
import json
import urllib.request
from outbox.worker import OutboxWorker

def publish(event_name, payload):
    # Production deployments replace this adapter with the configured broker.
    if os.getenv('MDARIX_OUTBOX_PUBLISHER', 'noop') == 'noop':
        return
    raise RuntimeError('OUTBOX_PUBLISHER_NOT_IMPLEMENTED')

def alert_dead_letter(payload):
    """Deliver an operational alert without exposing event payload data."""
    target = os.getenv('MDARIX_OUTBOX_ALERT_WEBHOOK', '').strip()
    if not target:
        logging.getLogger(__name__).warning('outbox alert delivery not configured alert=%s', payload)
        return
    body = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(target, data=body, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=float(os.getenv('MDARIX_OUTBOX_ALERT_TIMEOUT_SECONDS', '5'))) as response:
        if response.status >= 300:
            raise RuntimeError(f'OUTBOX_ALERT_HTTP_{response.status}')

if __name__ == '__main__':
    logging.basicConfig(level=os.getenv('MDARIX_LOG_LEVEL', 'INFO'), format='%(asctime)s %(levelname)s %(message)s')
    def stop(_signum, _frame):
        nonlocal_stop[0] = True
    nonlocal_stop = [False]
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    worker = OutboxWorker(publish, max_attempts=int(os.getenv('MDARIX_OUTBOX_MAX_ATTEMPTS', '5')), alert=alert_dead_letter)
    worker.run_forever(limit=int(os.getenv('MDARIX_OUTBOX_BATCH_SIZE', '50')), interval_seconds=int(os.getenv('MDARIX_OUTBOX_INTERVAL_SECONDS', '5')), stop=lambda: nonlocal_stop[0])
