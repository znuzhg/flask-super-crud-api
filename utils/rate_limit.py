from __future__ import annotations

import time
from typing import Callable, Dict, Tuple
from functools import wraps
from flask import request
import logging
from utils import metrics as metrics_util

logger = logging.getLogger(__name__)


_buckets: Dict[Tuple[str, str], Tuple[int, int]] = {}


def ratelimit(key: str, limit: int, window_sec: int = 60, identity_fn=None):
    """Simple in-memory rate limiter.

    key: name of the bucket category
    limit: max requests per window
    window_sec: sliding window seconds
    Identity is based on remote IP; for login, combine with email.
    """

    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            ip = request.headers.get("X-Forwarded-For", request.remote_addr or "")
            identity = None
            if identity_fn is not None:
                try:
                    identity = identity_fn()
                except Exception:
                    identity = None
            bucket_id = f"{ip}:{identity}" if identity else ip
            bucket_key = (key, bucket_id)
            now = int(time.time())
            window_start, count = _buckets.get(bucket_key, (now, 0))
            if now - window_start >= window_sec:
                window_start, count = now, 0
            count += 1
            _buckets[bucket_key] = (window_start, count)
            if count > limit:
                from utils.response import error_response
                logger.warning("Rate limit exceeded: key=%s ip=%s count=%s", key, ip, count)
                metrics_util.inc_rate_limit()
                return error_response("RATE_LIMITED", "Too many requests", status=429, details={"retry_in": window_sec - (now - window_start)})
            return fn(*args, **kwargs)

        return wrapper

    return decorator
