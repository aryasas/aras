from collections import deque
import time as _time
from typing import Dict, Any, List
from fastapi import APIRouter

dev_metrics_router = APIRouter(tags=["Developer Metrics"])

# In-memory circular buffer for error logs (claude-sonnet-4-6)
MAX_ERROR_LOG_ENTRIES = 200
error_log_entries = deque(maxlen=MAX_ERROR_LOG_ENTRIES)

# Request metrics — in-memory rolling counters (claude-opus-4-7)
request_metrics = {
    "total": 0,
    "errors": 0,
    "by_status": {},  # status_code: count
    "recent_latencies": deque(maxlen=200),  # (timestamp, ms) tuples
    "recent_requests": deque(maxlen=100),  # {ts, method, path, status, ms}
    "started_at": _time.time(),
}

def record_request(method: str, path: str, status_code: int, latency_ms: float):
    """Called by middleware to record a request."""
    request_metrics["total"] += 1
    if status_code >= 400:
        request_metrics["errors"] += 1
    sc = str(status_code)
    request_metrics["by_status"][sc] = request_metrics["by_status"].get(sc, 0) + 1
    now = _time.time()
    request_metrics["recent_latencies"].append((now, latency_ms))
    request_metrics["recent_requests"].append({
        "ts": now, "method": method, "path": path,
        "status": status_code, "ms": round(latency_ms, 1),
    })

# claude-opus-4-7
@dev_metrics_router.get("/dev/metrics")
def get_metrics():
    """Live request metrics: rate, error rate, latency percentiles."""
    now = _time.time()
    uptime = now - request_metrics["started_at"]
    recent = [(ts, ms) for ts, ms in request_metrics["recent_latencies"] if now - ts < 60]
    rate = len(recent) / 60.0 if recent else 0
    lats = sorted([ms for _, ms in recent])
    p50 = lats[len(lats) // 2] if lats else 0
    p95 = lats[int(len(lats) * 0.95)] if lats else 0
    p99 = lats[int(len(lats) * 0.99)] if lats else 0
    error_rate = (request_metrics["errors"] / request_metrics["total"]) if request_metrics["total"] else 0
    # Spark series: bucket last 60s into 30 bins of 2s each
    buckets = [0] * 30
    for ts, _ms in recent:
        idx = min(29, int((now - ts) / 2))
        buckets[29 - idx] += 1
    return {
        "uptime_seconds": round(uptime, 1),
        "total_requests": request_metrics["total"],
        "total_errors": request_metrics["errors"],
        "error_rate": round(error_rate * 100, 2),
        "rate_per_second": round(rate, 2),
        "latency_p50": round(p50, 1),
        "latency_p95": round(p95, 1),
        "latency_p99": round(p99, 1),
        "by_status": request_metrics["by_status"],
        "spark": buckets,
        "recent_requests": list(request_metrics["recent_requests"])[-25:],
    }
