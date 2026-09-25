"""Small dependency-free API benchmark for release evidence."""
from __future__ import annotations
import argparse, json, statistics, time
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:8007")
    parser.add_argument("--requests", type=int, default=20)
    args = parser.parse_args()
    samples=[]; failures=0
    for _ in range(max(1,args.requests)):
        started=time.perf_counter()
        try:
            with urlopen(args.base_url.rstrip("/")+"/health/live", timeout=10) as response:
                response.read()
                if response.status >= 400: failures += 1
        except (HTTPError, URLError, TimeoutError, OSError):
            failures += 1
        samples.append((time.perf_counter()-started)*1000)
    ordered=sorted(samples)
    def percentile(value: float) -> float: return ordered[min(len(ordered)-1, int(len(ordered)*value))]
    result={"base_url":args.base_url,"requests":len(samples),"failures":failures,"p50_ms":round(statistics.median(samples),2),"p95_ms":round(percentile(.95),2),"p99_ms":round(percentile(.99),2)}
    print(json.dumps(result, indent=2))
    return 1 if failures else 0

if __name__ == "__main__":
    raise SystemExit(main())
