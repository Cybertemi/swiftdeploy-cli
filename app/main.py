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
from fastapi.responses import JSONResponse
import uvicorn

# ── Config from environment ────────────────────────────────
MODE = os.getenv("MODE", "stable")
VERSION = os.getenv("APP_VERSION", "1.0.0")
PORT = int(os.getenv("APP_PORT", "3000"))
START_TIME = time.time()

# ── Chaos state ────────────────────────────────────────────
chaos_state = {"mode": None, "duration": 0, "rate": 0.0}
chaos_lock = threading.Lock()

app = FastAPI()


def make_response(data: dict, status: int = 200):
    """Build JSON response, adding X-Mode header in canary mode"""
    response = JSONResponse(content=data, status_code=status)
    if MODE == "canary":
        response.headers["X-Mode"] = "canary"
    return response


# ── Middleware: apply chaos to every request ───────────────
@app.middleware("http")
async def chaos_middleware(request: Request, call_next):
    with chaos_lock:
        current = dict(chaos_state)

    # Slow mode — sleep before responding
    if current["mode"] == "slow":
        time.sleep(current["duration"])

    # Error mode — randomly return 500
    if current["mode"] == "error":
        if random.random() < current["rate"]:
            return make_response(
                {"error": "chaos error injection", "mode": MODE}, 500)

    response = await call_next(request)

    # Always add X-Mode header in canary mode
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
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
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


# ── POST /chaos ────────────────────────────────────────────
@app.post("/chaos")
async def chaos(request: Request):
    # Only available in canary mode
    if MODE != "canary":
        return make_response(
            {"error": "chaos endpoint only available in canary mode"}, 403)

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
    uvicorn.run("main:app", host="0.0.0.0", port=PORT, log_level="info")
