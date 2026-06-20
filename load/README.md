# Load testing (k6)

Reproducible load test for the main request path, used to size pods and calibrate the HPA on
measured numbers rather than guesses.

`k6/load_test.js` ramps virtual users hammering the endpoint:

- Ramp: 0 → 10 VUs (20s) → 50 VUs (40s) → 0 (20s).
- Thresholds (the run **fails** if breached): `http_req_failed < 1%`, and `p95` latency `< 1000ms`.

```bash
make run                                  # start the app (offline defaults need no keys)
make load                                 # against http://localhost:8000
make load BASE_URL=https://app.example    # against a deployment
```

Requires [k6](https://k6.io/docs/get-started/installation/) (`brew install k6`).

## Calibrating the HPA

Watch where p95 starts climbing as VUs rise: that VU count is the **saturation point per pod**. Set
the HPA `targetCPUUtilizationPercentage` so a pod scales out *before* that point, and `minReplicas`
for your baseline RPS. Run twice — once against fakes (framework ceiling) and once against the real
dependencies (true end-to-end) — to separate app overhead from provider latency.
