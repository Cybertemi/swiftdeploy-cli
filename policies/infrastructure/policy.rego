package infrastructure

import future.keywords.if

default allow := false

# collect violations
violations[v] {
    input.disk_free_gb < data.limits.min_disk_free_gb
    v := sprintf("Disk free %.2fGB is below required minimum %.2fGB",
        [input.disk_free_gb, data.limits.min_disk_free_gb])
}

violations[v] {
    input.cpu_load > data.limits.max_cpu_load
    v := sprintf("CPU load %.2f exceeds maximum %.2f",
        [input.cpu_load, data.limits.max_cpu_load])
}

# FINAL DECISION
allow {
    count(violations) == 0
}

# expose reasons
reasons := violations
