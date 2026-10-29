"""Failure simulation script.

Usage:
    python tests/simulate_failures.py normal      # healthy traffic (fills dashboard)
    python tests/simulate_failures.py auth        # Scenario 1: invalid authentication (401)
    python tests/simulate_failures.py timeout     # Scenario 2: slow responses
    python tests/simulate_failures.py error       # Scenario 3: HTTP 500
    python tests/simulate_failures.py ratelimit   # Scenario 4: HTTP 429
    python tests/simulate_failures.py all         # runs all scenarios one by one

Optional: --duration 90 (seconds each scenario runs)
"""
import argparse
import threading
import time

import requests

BASE = "http://localhost:8000"


def fire(path, headers=None):
    try:
        r = requests.get(BASE + path, headers=headers, timeout=20)
        print(f"  {path} -> {r.status_code} ({r.elapsed.total_seconds():.2f}s)")
    except requests.RequestException as exc:
        print(f"  {path} -> ERROR {exc}")


def run(label, paths, headers=None, duration=90, interval=1.0):
    print(f"\n=== {label} (running {duration}s) ===")
    end = time.time() + duration
    i = 0
    while time.time() < end:
        path = paths[i % len(paths)]
        threading.Thread(target=fire, args=(path, headers), daemon=True).start()
        i += 1
        time.sleep(interval)
    time.sleep(6)  # let slow requests finish


SCENARIOS = {
    "normal": ("Normal traffic", ["/health", "/users", "/products"], None),
    "auth": ("Scenario 1: Invalid authentication", ["/protected"], {"X-API-Key": "wrong-key"}),
    "timeout": ("Scenario 2: API timeout", ["/simulate-timeout"], None),
    "error": ("Scenario 3: Server error", ["/simulate-error"], None),
    "ratelimit": ("Scenario 4: Rate limit exceeded", ["/simulate-rate-limit"], None),
}

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("scenario", choices=list(SCENARIOS) + ["all"])
    p.add_argument("--duration", type=int, default=90)
    a = p.parse_args()

    names = list(SCENARIOS)[1:] if a.scenario == "all" else [a.scenario]
    for n in names:
        label, paths, headers = SCENARIOS[n]
        run(label, paths, headers, a.duration)
    print("\nDone. Check Grafana (localhost:3000), Prometheus Alerts (localhost:9090/alerts), Slack and Email.")
