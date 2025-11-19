from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from config.settings import settings

logger = logging.getLogger(__name__)

try:
    import redis  # type: ignore
except Exception:  # pragma: no cover
    redis = None  # type: ignore


class Cache:
    def __init__(self) -> None:
        self._client = None
        self._memory = {}
        if settings.REDIS_URL and redis is not None:
            try:
                self._client = redis.Redis.from_url(settings.REDIS_URL)
                self._client.ping()
                logger.info("Connected to Redis for cache")
            except Exception as exc:
                logger.warning("Redis connection failed: %s", exc)
                self._client = None

    def get(self, key: str) -> Optional[Any]:
        try:
            if self._client is not None:
                data = self._client.get(key)
                if data:
                    return json.loads(data)
            else:
                rec = self._memory.get(key)
                if not rec:
                    return None
                value, exp = rec
                if exp and exp < time.time():
                    self._memory.pop(key, None)
                    return None
                return value
        except Exception as exc:  # pragma: no cover
            logger.warning("Cache get failed: %s", exc)
            return None

    def set(self, key: str, value: Any, ttl: int = 60) -> None:
        try:
            if self._client is not None:
                self._client.setex(key, ttl, json.dumps(value))
            else:
                exp = int(time.time()) + ttl if ttl else 0
                self._memory[key] = (value, exp)
        except Exception as exc:  # pragma: no cover
            logger.warning("Cache set failed: %s", exc)

    def invalidate_prefix(self, prefix: str) -> None:
        try:
            if self._client is not None:
                for k in self._client.scan_iter(match=f"{prefix}*"):
                    self._client.delete(k)
            else:
                for k in list(self._memory.keys()):
                    if k.startswith(prefix):
                        self._memory.pop(k, None)
        except Exception as exc:  # pragma: no cover
            logger.warning("Cache invalidate failed: %s", exc)


cache = Cache()

