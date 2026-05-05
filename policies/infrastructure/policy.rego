package infrastructure

default allow = false

#  Allow when everything is OK
allow {
  input.disk_free_gb >= 10
  input.cpu_load <= 2.0
}

#  Violations
violations[msg] {
  input.disk_free_gb < 10
  msg := "Disk free < 10GB"
}

violations[msg] {
  input.cpu_load > 2.0
  msg := "CPU load > 2.0"
}

# Expose reasons
reasons := violations
