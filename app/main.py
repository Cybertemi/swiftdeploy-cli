"""
SwiftDeploy API Service
FastAPI + uvicorn
Runs in stable or canary mode via MODE environment variable
"""
import os
import time
import random
import threading
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse
import uvicorn

# ── Config from environment ────────────────────────────────
MODE = os.getenv("MODE", "stable")
VERSION = os.getenv("APP_VERSION", "1.0.0")
PORT = int(os.getenv("APP_PORT", "3000"))
START_TIME = time.time()

# ── Chaos state ────────────────────────────────────────────
chaos_state = {"mode": None, "duration": 0, "rate": 0.0}
chaos_lock = threading.Lock()

# ── Metrics state ──────────────────────────────────────────
metrics_lock = threading.Lock()
request_counts = {}       # {(method, path, status): count}
request_durations = {}    # {(method, path): [durations]}

HISTOGRAM_BUCKETS = [0.005, 0.01, 0.025, 0.05,
                     0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]

app = FastAPI()


def record_metric(method, path, status, duration):
    """Record a request in metrics counters"""
    with metrics_lock:
        key = (method, path, str(status))
        request_counts[key] = request_counts.get(key, 0) + 1

        dur_key = (method, path)
        if dur_key not in request_durations:
            request_durations[dur_key] = []
        request_durations[dur_key].append(duration)


def get_chaos_active():
    """Return chaos numeric state: 0=none, 1=slow, 2=error"""
    with chaos_lock:
        m = chaos_state["mode"]
    if m == "slow":
        return 1
    if m == "error":
        return 2
    return 0


def make_response(data: dict, status: int = 200):
    """Build JSON response adding X-Mode header in canary mode"""
    response = JSONResponse(content=data, status_code=status)
    if MODE == "canary":
        response.headers["X-Mode"] = "canary"
    return response


# ── Middleware: track metrics + apply chaos ────────────────
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Skip metrics tracking for /metrics endpoint itself
    start = time.time()

    # Apply chaos
    with chaos_lock:
        current = dict(chaos_state)

    if current["mode"] == "slow":
        time.sleep(current["duration"])

    if current["mode"] == "error":
        if request.url.path != "/metrics":
            if random.random() < current["rate"]:
                duration = time.time() - start
                record_metric(
                    request.method,
                    request.url.path,
                    500, duration
                )
                resp = JSONResponse(
                    content={"error": "chaos error injection",
                             "mode": MODE},
                    status_code=500
                )
                if MODE == "canary":
                    resp.headers["X-Mode"] = "canary"
                return resp

    response = await call_next(request)
    duration = time.time() - start

    # Record metric
    if request.url.path != "/metrics":
        record_metric(
            request.method,
            request.url.path,
            response.status_code,
            duration
        )

    # Add X-Mode header in canary mode
    if MODE == "canary":
        response.headers["X-Mode"] = "canary"

    return response


# ── GET / ──────────────────────────────────────────────────
@app.get("/")
def root():
    return make_response({
        "message": "Welcome to SwiftDeploy API",
        "mode": MODE,
        "version": VERSION,
        "timestamp": time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    })


# ── GET /healthz ───────────────────────────────────────────
@app.get("/healthz")
def healthz():
    return make_response({
        "status": "ok",
        "mode": MODE,
        "version": VERSION,
        "uptime_seconds": round(time.time() - START_TIME, 2),
    })


# ── GET /metrics ───────────────────────────────────────────
@app.get("/metrics")
def metrics():
    """
    Expose metrics in Prometheus text format.
    Tracks: request counts, latency histogram, uptime, mode, chaos
    """
    lines = []

    # ── http_requests_total ────────────────────────────────
    lines.append("# HELP http_requests_total Total HTTP requests")
    lines.append("# TYPE http_requests_total counter")
    with metrics_lock:
        counts_copy = dict(request_counts)
        durations_copy = dict(request_durations)

    for (method, path, status), count in counts_copy.items():
        lines.append(
            f'http_requests_total{{'
            f'method="{method}",'
            f'path="{path}",'
            f'status_code="{status}"'
            f'}} {count}'
        )

    # ── http_request_duration_seconds (histogram) ──────────
    lines.append(
        "# HELP http_request_duration_seconds "
        "Request duration in seconds"
    )
    lines.append(
        "# TYPE http_request_duration_seconds histogram"
    )
    for (method, path), durations in durations_copy.items():
        total = sum(durations)
        count = len(durations)
        for bucket in HISTOGRAM_BUCKETS:
            b_count = sum(1 for d in durations if d <= bucket)
            lines.append(
                f'http_request_duration_seconds_bucket{{'
                f'method="{method}",'
                f'path="{path}",'
                f'le="{bucket}"'
                f'}} {b_count}'
            )
        lines.append(
            f'http_request_duration_seconds_bucket{{'
            f'method="{method}",'
            f'path="{path}",'
            f'le="+Inf"'
            f'}} {count}'
        )
        lines.append(
            f'http_request_duration_seconds_sum{{'
            f'method="{method}",'
            f'path="{path}"'
            f'}} {total}'
        )
        lines.append(
            f'http_request_duration_seconds_count{{'
            f'method="{method}",'
            f'path="{path}"'
            f'}} {count}'
        )

    # ── app_uptime_seconds ─────────────────────────────────
    lines.append("# HELP app_uptime_seconds App uptime in seconds")
    lines.append("# TYPE app_uptime_seconds gauge")
    lines.append(
        f"app_uptime_seconds {round(time.time() - START_TIME, 2)}"
    )

    # ── app_mode ──────────────────────────────────────────
    lines.append(
        "# HELP app_mode Current mode: 0=stable 1=canary"
    )
    lines.append("# TYPE app_mode gauge")
    lines.append(f"app_mode {1 if MODE == 'canary' else 0}")

    # ── chaos_active ──────────────────────────────────────
    lines.append(
        "# HELP chaos_active Chaos state: "
        "0=none 1=slow 2=error"
    )
    lines.append("# TYPE chaos_active gauge")
    lines.append(f"chaos_active {get_chaos_active()}")

    return PlainTextResponse(
        "\n".join(lines) + "\n",
        media_type="text/plain; version=0.0.4"
    )


# ── POST /chaos ────────────────────────────────────────────
@app.post("/chaos")
async def chaos(request: Request):
    if MODE != "canary":
        return make_response(
            {"error": "chaos endpoint only available in canary mode"},
            403
        )

    try:
        data = await request.json()
    except Exception:
        return make_response({"error": "invalid JSON"}, 400)

    chaos_mode = data.get("mode")

    with chaos_lock:
        if chaos_mode == "slow":
            chaos_state["mode"] = "slow"
            chaos_state["duration"] = float(data.get("duration", 1))
            chaos_state["rate"] = 0.0
            return make_response({
                "chaos": "activated",
                "mode": "slow",
                "duration": chaos_state["duration"]
            })

        elif chaos_mode == "error":
            chaos_state["mode"] = "error"
            chaos_state["rate"] = float(data.get("rate", 0.5))
            chaos_state["duration"] = 0
            return make_response({
                "chaos": "activated",
                "mode": "error",
                "rate": chaos_state["rate"]
            })

        elif chaos_mode == "recover":
            chaos_state["mode"] = None
            chaos_state["duration"] = 0
            chaos_state["rate"] = 0.0
            return make_response({
                "chaos": "deactivated",
                "mode": "recovered"
            })

        else:
            return make_response({
                "error": "unknown chaos mode",
                "valid": ["slow", "error", "recover"]
            }, 400)


# ── Entry point ────────────────────────────────────────────
if __name__ == "__main__":
    print(f"[swiftdeploy-api] Starting in {MODE} mode")
    print(f"[swiftdeploy-api] Version: {VERSION}")
    print(f"[swiftdeploy-api] Listening on 0.0.0.0:{PORT}")
    uvicorn.run(
        "main:app", host="0.0.0.0",
        port=PORT, log_level="info"
    )
