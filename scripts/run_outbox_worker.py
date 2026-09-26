"""Run the continuously operating transactional-outbox worker."""
import os
import logging
import signal
import json
import urllib.request
import sys
from datetime import datetime, timezone
from pathlib import Path

# The worker is launched as ``python scripts/run_outbox_worker.py`` inside
# the image, so Python initially searches ``/app/scripts``. Add the image
# root explicitly so repository packages resolve consistently in containers.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

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

def write_heartbeat(metrics):
    """Publish a small, secret-free heartbeat for a local/sidecar monitor."""
    target = os.getenv('MDARIX_OUTBOX_HEARTBEAT_FILE', '').strip()
    if not target:
        return
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps({
        'service': 'mdarix-outbox-worker',
        'updated_at': datetime.now(timezone.utc).isoformat(),
        'metrics': metrics,
    }, separators=(',', ':')), encoding='utf-8')
    temporary.replace(path)

if __name__ == '__main__':
    logging.basicConfig(level=os.getenv('MDARIX_LOG_LEVEL', 'INFO'), format='%(asctime)s %(levelname)s %(message)s')
    def stop(_signum, _frame):
        nonlocal_stop[0] = True
    nonlocal_stop = [False]
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    worker = OutboxWorker(publish, max_attempts=int(os.getenv('MDARIX_OUTBOX_MAX_ATTEMPTS', '5')), alert=alert_dead_letter)
    interval = int(os.getenv('MDARIX_OUTBOX_INTERVAL_SECONDS', '5'))
    while not nonlocal_stop[0]:
        stats = worker.process_once(limit=int(os.getenv('MDARIX_OUTBOX_BATCH_SIZE', '50')))
        write_heartbeat({**worker.metrics.snapshot(), 'last_cycle': stats})
        logging.getLogger(__name__).info('outbox metrics=%s cycle=%s', worker.metrics.snapshot(), stats)
        import time
        time.sleep(max(0, interval))
    logging.getLogger(__name__).info('outbox worker stopped gracefully')
