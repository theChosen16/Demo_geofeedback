import argparse
import json
import os
import sys
import time
from datetime import datetime
from urllib import error, request


DEFAULT_URL = os.environ.get(
    "GEOFEEDBACK_MONITOR_URL",
    "https://demogeofeedback-production.up.railway.app",
)
DEFAULT_ENDPOINTS = (
    "/",
    "/api/v1/health",
    "/api/v1/stats",
    "/api/v1/observability",
)


def fetch_endpoint(base_url, endpoint, timeout=10):
    full_url = f"{base_url.rstrip('/')}{endpoint}"
    started_at = time.time()
    body = ""
    status_code = None

    try:
        with request.urlopen(full_url, timeout=timeout) as response:
            status_code = response.status
            body = response.read().decode("utf-8", errors="replace")
    except error.HTTPError as exc:
        status_code = exc.code
        body = exc.read().decode("utf-8", errors="replace")
    except error.URLError as exc:
        elapsed_ms = (time.time() - started_at) * 1000
        return {
            "endpoint": endpoint,
            "status_code": None,
            "elapsed_ms": elapsed_ms,
            "healthy": False,
            "reason": str(exc.reason),
            "payload": None,
        }

    elapsed_ms = (time.time() - started_at) * 1000
    payload = None
    try:
        payload = json.loads(body) if body else None
    except json.JSONDecodeError:
        payload = None

    healthy, reason = evaluate_response(endpoint, status_code, payload)
    return {
        "endpoint": endpoint,
        "status_code": status_code,
        "elapsed_ms": elapsed_ms,
        "healthy": healthy,
        "reason": reason,
        "payload": payload,
    }


def evaluate_response(endpoint, status_code, payload):
    if endpoint == "/":
        return status_code == 200, "landing page unavailable" if status_code != 200 else "ok"

    if endpoint == "/api/v1/health":
        if status_code != 200:
            return False, f"unexpected health status {status_code}"
        if not isinstance(payload, dict) or payload.get("status") != "healthy":
            return False, "health payload invalid"
        return True, "ok"

    if endpoint == "/api/v1/stats":
        if status_code != 200:
            return False, f"unexpected stats status {status_code}"
        if not isinstance(payload, dict):
            return False, "stats payload invalid"
        visits = payload.get("visits")
        analyses = payload.get("analyses")
        if not isinstance(visits, int) or not isinstance(analyses, int):
            return False, "stats payload missing integer counters"
        return True, "ok"

    if endpoint == "/api/v1/observability":
        if not isinstance(payload, dict):
            return False, "observability payload invalid"
        if payload.get("status") != "healthy":
            return False, "observability reports degraded state"
        critical_checks = payload.get("critical_checks", {})
        analytics = payload.get("analytics", {})
        if not isinstance(critical_checks, dict) or not all(critical_checks.values()):
            return False, "critical observability check failed"
        if not analytics.get("ready"):
            return False, "analytics bootstrap still not ready"
        return status_code == 200, f"unexpected observability status {status_code}" if status_code != 200 else "ok"

    return status_code == 200, "ok" if status_code == 200 else f"unexpected status {status_code}"


def print_result(result):
    timestamp = datetime.now().strftime("%H:%M:%S")
    status_label = result["status_code"] if result["status_code"] is not None else "ERR"
    state = "OK" if result["healthy"] else "FAIL"
    print(
        f"[{timestamp}] {result['endpoint']:<22} | {status_label:<4} | {state:<4} | "
        f"{result['elapsed_ms']:.0f}ms | {result['reason']}"
    )


def run_checks(base_url, endpoints):
    results = [fetch_endpoint(base_url, endpoint) for endpoint in endpoints]
    for result in results:
        print_result(result)
    return all(result["healthy"] for result in results)


def run_with_retries(base_url, endpoints, retries=1, retry_delay=5):
    attempts = max(int(retries), 1)
    last_result = False

    for attempt in range(1, attempts + 1):
        last_result = run_checks(base_url, endpoints)
        if last_result:
            return True
        if attempt < attempts:
            print(f"[!] Check failed. Retrying in {retry_delay}s ({attempt}/{attempts - 1})...")
            time.sleep(retry_delay)

    return last_result


def build_parser():
    parser = argparse.ArgumentParser(description="Monitor GeoFeedback deployment health and observability.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Base URL to monitor.")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between checks in loop mode.")
    parser.add_argument("--once", action="store_true", help="Run a single monitoring cycle and exit.")
    parser.add_argument("--retries", type=int, default=1, help="How many times to retry before failing in once mode.")
    parser.add_argument("--retry-delay", type=int, default=5, help="Seconds to wait between retries in once mode.")
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    print(f"Monitoring {args.url}")
    print("-" * 72)
    try:
        while True:
            if args.once:
                all_healthy = run_with_retries(
                    args.url,
                    DEFAULT_ENDPOINTS,
                    retries=args.retries,
                    retry_delay=args.retry_delay,
                )
                return 0 if all_healthy else 1

            all_healthy = run_checks(args.url, DEFAULT_ENDPOINTS)
            if not all_healthy:
                print("[!] One or more checks failed.")
            print("-" * 72)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nMonitor stopped")
        return 130


if __name__ == "__main__":
    sys.exit(main())
