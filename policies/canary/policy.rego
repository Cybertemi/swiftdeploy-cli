package canary

import future.keywords.if

default allow := false

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
        "P99 latency %.1fms exceeds maximum %.1fms",
        [input.p99_latency_ms, data.limits.max_p99_latency_ms]
    )
}

allow {
    count(reasons) == 0
}
