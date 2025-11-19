from __future__ import annotations

import threading
from collections import defaultdict
from typing import Dict, Tuple


_lock = threading.Lock()
_request_count: Dict[Tuple[str, str, int], int] = defaultdict(int)
_latency_sum_ms: Dict[str, float] = defaultdict(float)
_latency_count: Dict[str, int] = defaultdict(int)
_error_count: Dict[str, int] = defaultdict(int)
_rate_limit_hits: int = 0


def inc_request_count(path: str, method: str, status: int) -> None:
    with _lock:
        _request_count[(path, method, status)] += 1
        if status >= 500:
            _error_count[path] += 1


def observe_latency(path: str, duration_ms: float) -> None:
    with _lock:
        _latency_sum_ms[path] += float(duration_ms)
        _latency_count[path] += 1


def inc_rate_limit() -> None:
    global _rate_limit_hits
    with _lock:
        _rate_limit_hits += 1


def render_prometheus() -> str:
    lines = []
    lines.append("# HELP request_count Total HTTP requests by path, method, status")
    lines.append("# TYPE request_count counter")
    with _lock:
        for (path, method, status), cnt in _request_count.items():
            lines.append(f'request_count{{path="{path}",method="{method}",status="{status}"}} {cnt}')

        lines.append("# HELP request_latency_ms Average request latency in ms by path")
        lines.append("# TYPE request_latency_ms gauge")
        for path, sum_ms in _latency_sum_ms.items():
            cnt = max(_latency_count.get(path, 1), 1)
            avg = sum_ms / cnt
            lines.append(f'request_latency_ms{{path="{path}"}} {avg:.2f}')

        lines.append("# HELP error_count Total 5xx errors by path")
        lines.append("# TYPE error_count counter")
        for path, cnt in _error_count.items():
            lines.append(f'error_count{{path="{path}"}} {cnt}')

        lines.append("# HELP rate_limit_hits Total rate limit hits")
        lines.append("# TYPE rate_limit_hits counter")
        lines.append(f'rate_limit_hits { _rate_limit_hits }')

    return "\n".join(lines) + "\n"

