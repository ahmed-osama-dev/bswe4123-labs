import time
import httpx

SERVICES = {
    "svc-8001": "http://127.0.0.1:8001/health",
    "svc-8002": "http://127.0.0.1:8002/health",
    "svc-8003": "http://127.0.0.1:8003/health",
}

INTERVAL_SECONDS = 2
SLOW_THRESHOLD_MS = 500.0
TIMEOUT_SECONDS = 1.0
FAIL_THRESHOLD = 3

consecutive_failures = {name: 0 for name in SERVICES}


def check_service(name: str, url: str) -> str:
    start = time.perf_counter()
    try:
        response = httpx.get(url, timeout=TIMEOUT_SECONDS)
        elapsed_ms = (time.perf_counter() - start) * 1000

        if response.status_code == 200:
            consecutive_failures[name] = 0
            if elapsed_ms > SLOW_THRESHOLD_MS:
                return f"{name}: SLOW ({elapsed_ms:.0f} ms)"
            return f"{name}: UP ({elapsed_ms:.0f} ms)"

        consecutive_failures[name] += 1
    except httpx.RequestError:
        consecutive_failures[name] += 1

    if consecutive_failures[name] >= FAIL_THRESHOLD:
        return f"{name}: DOWN (failed {consecutive_failures[name]}x)"
    return f"{name}: RETRY ({consecutive_failures[name]}/{FAIL_THRESHOLD} fails)"


def main():
    while True:
        round_start = time.perf_counter()
        statuses = [check_service(name, url) for name, url in SERVICES.items()]
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] " + " | ".join(statuses))

        elapsed = time.perf_counter() - round_start
        sleep_for = max(0.0, INTERVAL_SECONDS - elapsed)
        time.sleep(sleep_for)


if __name__ == "__main__":
    main()
