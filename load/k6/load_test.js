import http from "k6/http";
import { check } from "k6";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const API_KEY = __ENV.API_KEY || "";

const headers = { "Content-Type": "application/json" };
if (API_KEY) {
  headers["X-API-Key"] = API_KEY;
}

export const options = {
  thresholds: {
    http_req_failed: ["rate<0.01"],
    "http_req_duration{endpoint:main}": ["p(95)<1000"],
  },
  scenarios: {
    ramp: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "20s", target: 10 },
        { duration: "40s", target: 50 },
        { duration: "20s", target: 0 },
      ],
      gracefulStop: "10s",
    },
  },
};

const RECIPIENTS = ["Ada", "Alan", "Grace", "Linus"];

export default function () {
  const recipient = RECIPIENTS[Math.floor(Math.random() * RECIPIENTS.length)];
  const res = http.get(`${BASE_URL}/greet?recipient=${recipient}&locale=en`, {
    headers,
    tags: { endpoint: "main" },
  });
  check(res, {
    "status 200": (r) => r.status === 200,
    "message returned": (r) => r.status === 200 && r.json("message") !== undefined,
  });
}
