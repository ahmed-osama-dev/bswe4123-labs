## Step 3: Monitor Output & Explanation of Changes

### Monitor Output

The following output was captured during testing:

```text
[10:53:02] svc-8001: UP (51 ms) | svc-8002: UP (51 ms) | svc-8003: SLOW (877 ms)

[10:53:40] svc-8001: UP (159 ms) | svc-8002: RETRY (1/3 fails) | svc-8003: SLOW (870 ms)
[10:53:42] svc-8001: UP (53 ms) | svc-8002: RETRY (2/3 fails) | svc-8003: SLOW (888 ms)
[10:53:44] svc-8001: UP (66 ms) | svc-8002: DOWN (failed 3x) | svc-8003: SLOW (860 ms)

[10:54:50] svc-8001: UP (144 ms) | svc-8002: SLOW (635 ms) | svc-8003: SLOW (870 ms)
[10:54:52] svc-8001: UP (69 ms) | svc-8002: UP (55 ms) | svc-8003: SLOW (858 ms)
```

### Explanation of Results

1. **Normal service (svc-8001):** It responded successfully with normal response times, so the monitor reported UP.

2. **Slow service (svc-8003):** I configured this service with a 0.8-second delay. Its response time remained above the 500 ms threshold, so it was consistently reported as SLOW.

3. **Stopping svc-8002:** After stopping the service with Ctrl+C, the monitor reported RETRY for the first two consecutive failures, then DOWN after the third failure.

4. **Restarting svc-8002:** After restarting it, the service became available again. The monitor reset its failure counter and reported UP.

## Step 4: Timeout & Consecutive Failures Choice

### Chosen Settings

- Timeout: 1.0 second
- Slow threshold: 500 ms
- Consecutive failed checks required to report DOWN: 3
- Monitoring interval: 2 seconds

### Reasoning & Trade-offs

**Why a 1.0-second timeout?**

The timeout is higher than the configured 0.8-second delay, allowing the slow service to respond and be classified as SLOW rather than timing out.

- **Gain:** The monitor can detect unresponsive services without waiting indefinitely.
- **Loss:** A service that takes longer than 1.0 second to respond may be counted as a failed check, even if it is still running.

**Why 3 consecutive failed checks?**

A single failed request may happen because of a temporary network problem or a service restart. Therefore, the monitor waits for three consecutive failures before reporting DOWN.

- **Gain:** Reduces false DOWN alerts caused by temporary failures.
- **Loss:** Detection is delayed until three consecutive checks fail. With a 2-second monitoring interval, this takes approximately 6 seconds.
