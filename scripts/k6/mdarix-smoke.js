// Run only against an approved non-production target:
// k6 run -e BASE_URL=http://127.0.0.1:8007 scripts/k6/mdarix-smoke.js
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  thresholds: {
    http_req_failed: ["rate<0.01"],
    http_req_duration: ["p(95)<500", "p(99)<1000"],
  },
  scenarios: { smoke: { executor: "constant-vus", vus: 2, duration: "30s" } },
};

export default function () {
  const base = __ENV.BASE_URL || "http://127.0.0.1:8007";
  const live = http.get(`${base}/health/live`);
  check(live, { "live endpoint is healthy": (r) => r.status === 200 });
  const ready = http.get(`${base}/health/ready`);
  check(ready, { "ready endpoint responds": (r) => [200, 503].includes(r.status) });
  sleep(1);
}
