package canary

# ── Decision: allow or deny promotion to canary ───────────
# Input: {error_rate: float, p99_latency_ms: float}
# Data:  data.limits (from data.json)

default allow = false

allow {
    error_rate_ok
    latency_ok
}

error_rate_ok {
    input.error_rate <= data.limits.max_error_rate
}

latency_ok {
    input.p99_latency_ms <= data.limits.max_p99_latency_ms
}

# ── Reasons: explain WHY it was denied ────────────────────
reasons[msg] {
    input.error_rate > data.limits.max_error_rate
    msg := sprintf(
        "Error rate %.2f%% exceeds maximum %.2f%%",
        [input.error_rate * 100, data.limits.max_error_rate * 100]
    )
}

reasons[msg] {
    input.p99_latency_ms > data.limits.max_p99_latency_ms
    msg := sprintf(
        "P99 latency %.0fms exceeds maximum %.0fms",
        [input.p99_latency_ms, data.limits.max_p99_latency_ms]
    )
}
